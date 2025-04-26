#!/usr/bin/env python3
import numpy as np
import cv2
import json
import os
import random
import shutil
import csv
import yaml
from pathlib import Path
from collections import defaultdict
from fire import Fire
from tqdm import tqdm

from utils import resolve_variables

def load_config(config_path):
    """Load configuration from YAML file"""
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)

def extract_class_name(filename):
    """Extract class name from filename like 'CD235a_RBC_033_026624_045056_mask.png'"""
    parts = filename.split('_')
    if len(parts) >= 2:
        # First two components should be the class name (e.g., 'CD235a_RBC')
        return f"{parts[0]}_{parts[1]}"
    return None

def load_class_codes(tsv_path):
    """Load class codes from TSV file"""
    class_codes = {}
    with open(tsv_path, 'r') as f:
        reader = csv.reader(f, delimiter='\t')
        next(reader)  # Skip header
        for row in reader:
            if len(row) >= 2:
                label, code = row[0], int(row[1])
                class_codes[label] = code
    return class_codes

def clean_class_name(class_name):
    """Clean up class names by removing special characters and converting to lowercase."""
    # Replace underscores and commas with spaces
    cleaned = class_name.replace('_', ' ').replace(',', ' ')
    # Convert to lowercase
    cleaned = cleaned.lower()
    # Remove multiple spaces
    cleaned = ' '.join(cleaned.split())
    return cleaned

def create_prompt(class_percentages, prompt_template):
    """Create prompt string with full class names."""
    class_descriptions = ", ".join([f"{class_name} {percentage:.2f}%" 
                                  for class_name, percentage in class_percentages])
    prompt = prompt_template.format(class_descriptions=class_descriptions)
    return prompt

def select_samples(
    config_path: str = "./config/config.yaml",
    filename: str = "combined_mask",
    random_seed: int = 42
):
    """
    Select one mask per class, combine them into a single visualization,
    calculate area percentages, and create a corresponding prompt.

    Args:
        config_path: Path to configuration file
        filename: Base filename for output files (without extension)
        random_seed: Random seed for reproducibility
    """
    # Set random seed for reproducibility
    random.seed(random_seed)
    
    # Load configuration
    config = load_config(config_path)
    
    # Get results directory from config
    results_dir = Path(resolve_variables(config, config["paths"]["results_dir"]))
    
    # Create results directory if it doesn't exist
    os.makedirs(results_dir, exist_ok=True)
    print(f"Output directory: {results_dir}")
    
    # Path to the class codes TSV file
    class_codes_path = Path(resolve_variables(config, config["paths"]["labels_tsv"]))
    
    # Path to the validation masks directory
    mask_dir = Path(resolve_variables(config, config["dataset"]["output_dirs"]["val_source"]))
    
    # Path to the detailed labels TSV
    detailed_labels_path = Path(resolve_variables(config, config["paths"]["labels_detailed_tsv"]))
    
    # Load class codes
    class_codes = load_class_codes(class_codes_path)
    print(f"Loaded {len(class_codes)} class codes from {class_codes_path}")
    
    # Create reverse mapping (code -> name)
    code_to_name = {}
    for name, code in class_codes.items():
        code_to_name[code] = name

    # Load detailed labels for better descriptions
    detailed_labels = {}
    with open(detailed_labels_path, 'r') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            detailed_labels[int(row['GT_code'])] = row['label']
    
    # Get all mask files
    mask_files = list(mask_dir.glob("*.png"))
    print(f"Found {len(mask_files)} mask files in {mask_dir}")
    
    # Group files by class
    class_groups = defaultdict(list)
    for mask_path in mask_files:
        class_name = extract_class_name(mask_path.name)
        if class_name in class_codes:
            class_groups[class_name].append(mask_path)
    
    # Check if we have masks for all classes
    if len(class_groups) < len(class_codes):
        missing_classes = set(class_codes.keys()) - set(class_groups.keys())
        print(f"Warning: Missing masks for classes: {missing_classes}")
    
    print(f"Found masks for {len(class_groups)} out of {len(class_codes)} classes")
    
    # Select one mask per class
    selected_masks = {}
    reference_shape = None
    
    for class_name, masks in class_groups.items():
        if masks:
            selected = random.choice(masks)
            selected_masks[class_name] = selected
            
            # Read the first mask to get the shape
            if reference_shape is None:
                mask = cv2.imread(str(selected), cv2.IMREAD_GRAYSCALE)
                if mask is not None:
                    reference_shape = mask.shape
    
    print(f"Selected {len(selected_masks)} masks, one per available class")
    
    if reference_shape is None:
        print("Error: Could not determine reference shape from any mask")
        return
    
    # Create combined mask
    combined_mask = np.zeros(reference_shape, dtype=np.uint8)
    
    # Dictionary to track class areas
    class_areas = {0: 0}  # Start with background
    for code in class_codes.values():
        class_areas[code] = 0
    
    total_pixels = reference_shape[0] * reference_shape[1]
    
    # Add each mask to the combined image with its class index
    for class_name, mask_path in selected_masks.items():
        class_idx = class_codes[class_name]
        mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
        
        if mask is not None and mask.shape == reference_shape:
            # For binary masks, foreground is class_idx, background remains 0
            foreground = (mask > 0)
            combined_mask[foreground] = class_idx
            
            # Track area
            class_areas[class_idx] = np.sum(foreground)
        else:
            print(f"Warning: Mask {mask_path} has wrong shape or could not be read")
    
    # Calculate background area (any pixel still 0)
    class_areas[0] = total_pixels - sum([v for k, v in class_areas.items() if k > 0])
    
    # Calculate percentages
    percentages = {class_idx: (count / total_pixels) * 100 for class_idx, count in class_areas.items()}
    
    # Create class percentages list for prompt (excluding background)
    class_percentages = []
    for class_idx, percentage in percentages.items():
        if class_idx > 0 and percentage > 0:  # Skip background and empty classes
            if class_idx in detailed_labels:
                class_name = clean_class_name(detailed_labels[class_idx])
                class_percentages.append((class_name, percentage))
    
    # Sort by percentage (smallest first)
    class_percentages.sort(key=lambda x: x[1])
    
    # Create prompt
    prompt_template = config["settings"].get("prompt_template", "pathology image: {class_descriptions}")
    prompt = create_prompt(class_percentages, prompt_template)
    
    # Create a colored version of the combined mask
    colors = config["settings"]["colors"]
    colored_mask = np.zeros((reference_shape[0], reference_shape[1], 3), dtype=np.uint8)
    
    for class_idx in range(min(len(colors), 9)):  # Make sure we don't exceed color map
        if class_idx < len(colors):
            # Convert hex color to RGB
            hex_color = colors[class_idx].lstrip('#')
            rgb_color = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            # Apply color to the mask where class_idx matches
            colored_mask[combined_mask == class_idx] = rgb_color
    
    # Save files with consistent naming
    # 1. Colored mask
    colored_mask_path = results_dir / f"{filename}.png"
    cv2.imwrite(str(colored_mask_path), colored_mask)
    print(f"Saved colored mask to {colored_mask_path}")
    
    # 2. Grayscale mask with class indices
    gray_mask_path = results_dir / f"{filename}_gray.png"
    cv2.imwrite(str(gray_mask_path), combined_mask)
    print(f"Saved grayscale mask to {gray_mask_path}")
    
    # 3. Prompt text file
    prompt_path = results_dir / f"{filename}_prompt.txt"
    with open(prompt_path, 'w') as f:
        f.write(prompt)
    print(f"Created prompt file at {prompt_path}")
    
    # 4. Class percentages CSV
    csv_path = results_dir / f"{filename}_stats.csv"
    with open(csv_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Class ID', 'Class Name', 'Pixel Count', 'Percentage'])
        
        # Sort by percentage (descending)
        sorted_items = sorted(class_areas.items(), key=lambda x: percentages[x[0]], reverse=True)
        
        for class_idx, count in sorted_items:
            class_name = code_to_name.get(class_idx, 'Background' if class_idx == 0 else 'Unknown')
            percentage = percentages[class_idx]
            writer.writerow([class_idx, class_name, count, f"{percentage:.4f}"])
    
    print(f"Wrote class statistics to {csv_path}")
    print("\nClass percentages in combined mask:")
    for class_idx, percentage in sorted(percentages.items(), key=lambda x: x[1], reverse=True):
        if percentage > 0:
            class_name = code_to_name.get(class_idx, 'Background' if class_idx == 0 else 'Unknown')
            print(f"  {class_name}: {percentage:.2f}%")
    
    print(f"\nFinal prompt:\n{prompt}")

if __name__ == "__main__":
    Fire(select_samples)