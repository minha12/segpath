import numpy as np
import cv2
from pathlib import Path
import json
import csv
from tqdm import tqdm
import sys
import os
import yaml
from fire import Fire  # Import Fire

from prompt_augmenter import augment_prompt
from utils import resolve_variables  # Import the resolve_variables function

def load_config(config_path):
    """Load configuration from YAML file"""
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)

def load_labels_from_tsv(tsv_path):
    """Load labels from TSV file."""
    labels = {}
    with open(tsv_path, 'r') as file:
        reader = csv.DictReader(file, delimiter='\t')
        for row in reader:
            labels[int(row['GT_code'])] = row['label']
    return labels

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

def process_mask(mask_path, label_to_name, class_codes, config, filter_background=False):
    """Process a binary mask image to create a text prompt."""
    # Extract class name from filename
    class_name = extract_class_name(mask_path.name)
    if not class_name or class_name not in class_codes:
        print(f"\nWarning: Could not determine class for {mask_path.name}")
        return None
        
    # Get the class index for this mask
    class_idx = class_codes[class_name]
    
    # Read the mask
    mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
    if mask is None:
        print(f"\nError: Could not load mask at {mask_path}")
        return None

    # For binary masks, we need to create our own labeled version
    # Create an empty array with the same shape as the mask
    labeled_mask = np.zeros_like(mask)
    # Set foreground pixels to the class index
    labeled_mask[mask > 0] = class_idx
    
    # Get unique labels and their counts
    unique_labels = np.array([0, class_idx])  # Background (0) and the class index
    counts = np.array([np.sum(mask == 0), np.sum(mask > 0)])
    total_pixels = mask.size
    
    # Filter out masks with only background if requested
    if filter_background and counts[1] == 0:
        return None
    
    # Calculate percentages and create prompt
    class_percentages = []
    for label, count in zip(unique_labels, counts):
        # Include all labels, including background (0) if it's in label_to_name
        if label in label_to_name:
            percentage = (count / total_pixels) * 100
            clean_name = clean_class_name(label_to_name[label])
            class_percentages.append((clean_name, percentage))

    # Sort by percentage in ascending order (smallest first)
    class_percentages.sort(key=lambda x: x[1])
    
    # Create prompt with full names
    prompt_template = config["settings"].get("prompt_template", "pathology image: {class_descriptions}")
    prompt = create_prompt(class_percentages, prompt_template)
    
    # Handle case of empty prompt
    if not class_percentages:
        prompt = prompt_template.format(class_descriptions="background")
        
    return prompt

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

def main(
    use_augmentation=False, 
    dataset_split="train", 
    config_path="./config/config.yaml",
    filter_background=False,
    use_detailed_labels=True,
    class_codes_path=None  # Added parameter for class codes
):
    """
    Create text prompts from binary mask images.
    """
    # Load configuration
    config = load_config(config_path)
    
    # Get the appropriate paths based on dataset split
    if dataset_split not in ["train", "val"]:
        raise ValueError("Dataset split must be either 'train' or 'val'")
    
    # Path to the ground truth codes TSV file - choose detailed or standard
    labels_key = "labels_detailed_tsv" if use_detailed_labels else "labels_tsv"
    tsv_path = Path(resolve_variables(config, config["paths"][labels_key]))
    
    # Path for the class codes if not provided
    if class_codes_path is None:
        class_codes_path = resolve_variables(config, config["paths"]["labels_tsv"])
    
    print(f"Using {'detailed' if use_detailed_labels else 'standard'} class descriptions from {tsv_path}")
    print(f"Using class codes from {class_codes_path}")
    
    # Load ground truth labels for detailed descriptions
    labels = load_labels_from_tsv(tsv_path)
    
    # Load class codes mapping class names to codes
    class_codes = load_class_codes(class_codes_path)
    print(f"Loaded {len(class_codes)} class codes")
    
    # Reverse the dictionary for label to name lookup
    label_to_name = labels
    
    # Path for the source and target directories based on dataset split
    source_dir = Path(resolve_variables(config, config["dataset"]["output_dirs"][f"{dataset_split}_source"]))
    target_dir = Path(resolve_variables(config, config["dataset"]["output_dirs"][f"{dataset_split}_target"]))
    
    # Path for output file - only defined in paths section
    output_path = Path(resolve_variables(config, config["paths"][f"{dataset_split}_prompt_output_path"]))
    
    # Create output directory if not exists
    os.makedirs(output_path.parent, exist_ok=True)
    
    # Find all mask files
    mask_files = list(source_dir.glob(f"*.{config['settings']['mask_file_extension']}"))
    total_files = len(mask_files)
    processed_files = 0
    augmented_prompts = 0
    
    print(f"Found {total_files} mask files in {dataset_split} set")
    print(f"Background-only check: {'Enabled' if filter_background else 'Disabled'}")
    
    # Process all mask files and write results to JSON file
    with open(output_path, 'w') as f:
        for mask_path in tqdm(mask_files, desc=f"Processing {dataset_split} masks", unit="file"):
            prompt = process_mask(mask_path, label_to_name, class_codes, config, filter_background)
            
            # Only include results with non-empty prompts
            if prompt and prompt.endswith(": ") == False:
                # Get filename for source and target
                source_name = mask_path.name
                target_name = source_name
                
                # Get the source and target directory names from the config
                source_dir_name = Path(config["paths"][f"{dataset_split}_colored_mask_dir"]).name
                target_dir_name = Path(config["dataset"]["output_dirs"][f"{dataset_split}_target"]).name
                
                # Augment prompt if specified and track augmentations
                original_length = len(prompt.split())
                prompt = augment_prompt(prompt, use_augmentation)
                if len(prompt.split()) > original_length:
                    augmented_prompts += 1
                
                # Write result directly to file in JSON format with proper directory prefixes
                result = {
                    "source": f"{source_dir_name}/{source_name}",
                    "target": f"{target_dir_name}/{target_name}",
                    "prompt": prompt
                }
                f.write(f"{json.dumps(result)}\n")
                processed_files += 1

    # Print summary
    print("\nProcessing Summary:")
    print(f"Total {dataset_split} files processed: {total_files}")
    print(f"Valid prompts generated: {processed_files}")
    print(f"Filtered out: {total_files - processed_files}")
    if use_augmentation:
        print(f"Prompts augmented: {augmented_prompts}")
    print(f"\nResults saved to {output_path}")

if __name__ == "__main__":
    # Replace argparse with Fire
    Fire(main)
