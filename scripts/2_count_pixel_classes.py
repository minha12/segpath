import numpy as np
import cv2
from pathlib import Path
import csv
from tqdm import tqdm
import os
import yaml
import re
from fire import Fire  # Add Fire for command-line arguments

from utils import resolve_variables

# Load configuration
def load_config(config_path):
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)

# Extract class name from filename
def extract_class_name(filename):
    """Extract class name from filename like 'CD235a_RBC_033_026624_045056_mask.png'"""
    parts = filename.split('_')
    if len(parts) >= 2:
        # First two components should be the class name (e.g., 'CD235a_RBC')
        return f"{parts[0]}_{parts[1]}"
    return None

# Read the labels from the TSV file
def read_labels_from_tsv(tsv_path):
    labels = {}
    with open(tsv_path, 'r') as file:
        # Skip header
        next(file)
        for line in file:
            line = line.strip()
            if line:
                parts = line.split('\t')
                if len(parts) >= 2:
                    label, code = parts[0], int(parts[1])
                    labels[label] = code
    return labels

def main(config_path="./config/config.yaml", mask_dir=None, dataset_split="train"):
    """
    Count pixel classes in binary mask images.
    
    Args:
        config_path: Path to configuration file
        mask_dir: Directory containing mask files (overrides config if provided)
        dataset_split: Dataset split to process ('train' or 'val')
    """
    # Load configuration
    config = load_config(config_path)
    
    # Validate dataset split
    if dataset_split not in ["train", "val"]:
        raise ValueError("Dataset split must be either 'train' or 'val'")
    
    # Path to the TSV file with label information
    labels_tsv_path = Path(resolve_variables(config, config["paths"]["labels_tsv"]))
    
    # Read labels from the TSV file - this gives us class_name -> class_code mapping
    class_codes = read_labels_from_tsv(labels_tsv_path)
    
    # Print loaded class codes for verification
    print(f"Loaded {len(class_codes)} class codes from {labels_tsv_path}")
    
    # Reverse the dictionary for label to name lookup (class_code -> class_name)
    label_to_name = {v: k for k, v in class_codes.items()}
    
    # Initialize a dictionary to hold pixel counts per class
    pixel_counts = {0: 0}  # Start with background class (0)
    for code in class_codes.values():
        pixel_counts[code] = 0
    
    # Total number of pixels
    total_pixels = 0
    
    # Path to the target directory (masks)
    if mask_dir is None:
        # Use the appropriate mask directory based on dataset split - using output_dirs definition
        mask_dir_key = f"{dataset_split}_source"
        mask_dir = Path(resolve_variables(config, config["dataset"]["output_dirs"][mask_dir_key]))
    else:
        mask_dir = Path(mask_dir)
    
    print(f"Processing masks from: {mask_dir}")
    
    # Get list of all mask files and count them
    mask_files = list(mask_dir.glob("*.png"))
    total_files = len(mask_files)
    print(f"Found {total_files} mask files in {mask_dir}")
    
    # Dictionary to track masks per class
    masks_per_class = {name: 0 for name in class_codes.keys()}
    unknown_classes = 0
    
    # Loop through all mask files with proper progress bar
    for mask_path in tqdm(mask_files, 
                         total=total_files,
                         desc=f"Processing {dataset_split} mask files",
                         unit="file"):
        # Extract class name from filename
        class_name = extract_class_name(mask_path.name)
        
        if not class_name or class_name not in class_codes:
            print(f"\nWarning: Could not determine class for {mask_path.name}")
            unknown_classes += 1
            continue
            
        # Get the class index for this mask
        class_idx = class_codes[class_name]
        
        # Track the class occurrence
        masks_per_class[class_name] += 1
        
        # Read the mask
        mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
        if mask is None:
            print(f"\nError: Could not load mask at {mask_path}")
            continue
        
        # Count foreground and background pixels
        foreground_count = np.sum(mask > 0)
        background_count = mask.size - foreground_count
        
        # Update total pixels
        total_pixels += mask.size
        
        # Accumulate counts - background (0) and foreground (class_idx)
        pixel_counts[0] += background_count
        pixel_counts[class_idx] += foreground_count
    
    # Calculate percentages
    percentages = {label_id: (count / total_pixels) * 100 for label_id, count in pixel_counts.items()}
    
    # Create results directory if it doesn't exist
    results_dir = Path(resolve_variables(config, config["paths"]["results_dir"]))
    if not results_dir.exists():
        os.makedirs(results_dir, exist_ok=True)
        print(f"Created directory {results_dir}")
    
    # Write results to a CSV file - include dataset split in filename
    output_filename = f"{dataset_split}_{config['files']['output_file']}"
    output_file = results_dir / output_filename
    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        # Section 1: Pixel counts and percentages
        writer.writerow(['Label ID', 'Class Name', 'Pixel Count', 'Percentage', 'Mask Count'])
        
        # Sort by percentage (descending) to show most common classes first
        sorted_items = sorted(pixel_counts.items(), key=lambda x: percentages[x[0]], reverse=True)
        
        for label_id, count in sorted_items:
            class_name = label_to_name.get(label_id, 'Unknown')
            percentage = percentages[label_id]
            mask_count = 0
            if label_id > 0:  # For non-background classes
                for name, code in class_codes.items():
                    if code == label_id:
                        mask_count = masks_per_class.get(name, 0)
                        break
            writer.writerow([label_id, class_name, count, f"{percentage:.4f}", mask_count])
        
        # Add a separator and a section for masks per class summary
        writer.writerow([])
        writer.writerow(['Class Name', 'Mask Count', 'Description'])
        
        # Sort by mask count (descending)
        sorted_masks = sorted(masks_per_class.items(), key=lambda x: x[1], reverse=True)
        
        for class_name, count in sorted_masks:
            if count > 0:
                writer.writerow([class_name, count, f"Number of masks for {class_name}"])
    
    print(f"\nResults written to {output_file}")
    print(f"Total masks processed: {total_files - unknown_classes}")
    print(f"Unknown class masks: {unknown_classes}")
    print("\nMasks per class:")
    for class_name, count in sorted(masks_per_class.items(), key=lambda x: x[1], reverse=True):
        if count > 0:
            print(f"  {class_name}: {count}")

if __name__ == "__main__":
    Fire(main)