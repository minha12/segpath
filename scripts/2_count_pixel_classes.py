import numpy as np
import cv2
from pathlib import Path
import csv
from tqdm import tqdm
import os
import yaml
import re

from utils import resolve_variables

# Load configuration
def load_config(config_path):
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)


# Set config path and load configuration
config_path = Path("./config/config.yaml")
config = load_config(config_path)

# Read the labels from the TSV file
def read_labels_from_tsv(tsv_path):
    labels = {}
    with open(tsv_path, 'r') as file:
        # Skip header
        next(file)
        for line in file:
            line = line.strip()
            if line:
                label, code = line.split('\t')
                labels[label] = int(code)
    return labels

# Path to the TSV file with label information
labels_tsv_path = Path(resolve_variables(config, config["paths"]["labels_tsv"]))

# Read labels from the TSV file
labels = read_labels_from_tsv(labels_tsv_path)

# Print loaded labels for verification
print(f"Loaded {len(labels)} labels from {labels_tsv_path}")

# Reverse the dictionary for label to name lookup
label_to_name = {v: k for k, v in labels.items()}

# Initialize a dictionary to hold pixel counts per class
pixel_counts = {label_id: 0 for label_id in labels.values()}

# Total number of pixels
total_pixels = 0

# Path to the target directory (masks)
mask_dir = Path(resolve_variables(config, config["paths"]["mask_dir"]))

# Get list of all mask files and count them
mask_files = list(mask_dir.glob("*.png"))
total_files = len(mask_files)
print(f"Found {total_files} mask files in {mask_dir}")

# Loop through all mask files with proper progress bar
for mask_path in tqdm(mask_files, 
                     total=total_files,
                     desc="Processing mask files",
                     unit="file"):
    # Read the mask
    mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
    if mask is None:
        print(f"\nError: Could not load mask at {mask_path}")
        continue

    # Update total pixels
    total_pixels += mask.size

    # Get unique labels and their counts in the mask
    unique_labels, counts = np.unique(mask, return_counts=True)

    # Accumulate counts per label
    for label, count in zip(unique_labels, counts):
        if label in pixel_counts:
            pixel_counts[label] += count
        else:
            print(f"Warning: Found unknown label {label} in {mask_path}")
            pixel_counts[label] = count

# Calculate percentages
percentages = {label_id: (count / total_pixels) * 100 for label_id, count in pixel_counts.items()}

# Create results directory if it doesn't exist
results_dir = Path(resolve_variables(config, config["paths"]["results_dir"]))
if not results_dir.exists():
    os.makedirs(results_dir, exist_ok=True)
    print(f"Created directory {results_dir}")

# Write results to a CSV file
output_file = results_dir / config["files"]["output_file"]
with open(output_file, 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['Label ID', 'Class Name', 'Pixel Count', 'Percentage'])
    
    # Sort by percentage (descending) to show most common classes first
    sorted_items = sorted(pixel_counts.items(), key=lambda x: percentages[x[0]], reverse=True)
    
    for label_id, count in sorted_items:
        class_name = label_to_name.get(label_id, 'Unknown')
        percentage = percentages[label_id]
        writer.writerow([label_id, class_name, count, f"{percentage:.4f}"])

print(f"Results written to {output_file}")