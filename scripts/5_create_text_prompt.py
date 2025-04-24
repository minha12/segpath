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

def process_mask(mask_path, label_to_name, config, filter_background=False, filter_threshold=False, use_augmentation=False):
    # Read the mask
    mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
    if mask is None:
        print(f"\nError: Could not load mask at {mask_path}")
        return None

    # Get unique labels and their counts in the mask
    unique_labels, counts = np.unique(mask, return_counts=True)
    total_pixels = mask.size
    
    # Filter out masks with only background and tissue unknown if requested
    if filter_background and set(unique_labels).issubset({0, 1}):
        return None
    
    # Check for empty masks (mostly background)
    if filter_threshold:
        empty_mask_threshold = config["settings"].get("empty_mask_threshold", 0.98)
        if 0 in unique_labels:
            zero_idx = np.where(unique_labels == 0)[0][0]
            zero_percentage = counts[zero_idx] / total_pixels
            if zero_percentage > empty_mask_threshold:
                return None
    
    # Calculate percentages and create prompt
    class_percentages = []
    min_class_percentage = config["settings"].get("min_class_percentage", 1.0)
    for label, count in zip(unique_labels, counts):
        # Include all labels, including background (0) if it's in label_to_name
        if label in label_to_name:
            percentage = (count / total_pixels) * 100
            if percentage > min_class_percentage:
                clean_name = clean_class_name(label_to_name[label])
                class_percentages.append((clean_name, percentage))

    # Sort by percentage in ascending order (smallest first)
    class_percentages.sort(key=lambda x: x[1])
    
    # Create prompt with full names
    prompt_template = config["settings"].get("prompt_template", "pathology image: {class_descriptions}")
    prompt = create_prompt(class_percentages, prompt_template)
    
    # Handle case of empty prompt (ensure it returns something)
    if not class_percentages:
        # If no classes meet the criteria, create a default prompt
        prompt = prompt_template.format(class_descriptions="background")
        
    return prompt

def main(
    use_augmentation=False, 
    dataset_split="train", 
    config_path="./config/config.yaml",
    filter_background=False,
    filter_threshold=False
):
    """
    Create text prompts from mask images.
    
    Args:
        use_augmentation: Whether to augment the generated prompts
        dataset_split: Dataset split to process ('train' or 'val')
        config_path: Path to configuration file
    """
    # Load configuration
    config = load_config(config_path)
    
    # Get the appropriate paths based on dataset split
    if dataset_split not in ["train", "val"]:
        raise ValueError("Dataset split must be either 'train' or 'val'")
    
    # Path to the ground truth codes TSV file
    tsv_path = Path(resolve_variables(config, config["paths"]["labels_tsv"]))
    
    # Path for the source and target directories based on dataset split
    source_dir = Path(resolve_variables(config, config["paths"][f"{dataset_split}_mask_dir"]))
    target_dir = Path(resolve_variables(config, config["paths"][f"{dataset_split}_target_dir"]))
    
    # Path for output file
    output_path = Path(resolve_variables(config, config["paths"][f"{dataset_split}_prompt_output_path"]))
    
    # Create output directory if not exists
    os.makedirs(output_path.parent, exist_ok=True)
    
    # Load ground truth labels
    labels = load_labels_from_tsv(tsv_path)
    
    # Reverse the dictionary for label to name lookup
    label_to_name = labels
    
    # Find all mask files
    mask_files = list(source_dir.glob(f"*.{config['settings']['mask_file_extension']}"))
    total_files = len(mask_files)
    processed_files = 0
    augmented_prompts = 0
    
    print(f"Found {total_files} mask files in {dataset_split} set")
    print(f"Background-only check: {'Enabled' if filter_background else 'Disabled'}")
    print(f"Background threshold check: {'Enabled' if filter_threshold else 'Disabled'}")
    
    # Process all mask files and write results to JSON file
    with open(output_path, 'w') as f:
        for mask_path in tqdm(mask_files, desc=f"Processing {dataset_split} masks", unit="file"):
            prompt = process_mask(mask_path, label_to_name, config, 
                                 filter_background=False,
                                 filter_threshold=False)
            
            # Only include results with non-empty prompts
            if prompt and prompt.endswith(": ") == False:
                # Get filename for source and target
                source_name = mask_path.name
                target_name = source_name
                
                # Get the source and target directory names from the config
                source_dir_name = Path(config["paths"][f"{dataset_split}_colored_mask_dir"]).name
                target_dir_name = Path(config["paths"][f"{dataset_split}_target_dir"]).name
                
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
