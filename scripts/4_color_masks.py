import os
from pathlib import Path
import numpy as np
from PIL import Image
import concurrent.futures
from tqdm import tqdm
import yaml
import csv
from fire import Fire

from utils import resolve_variables  # Import the resolve_variables function

def load_config(config_path):
    """Load configuration from YAML file"""
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)

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

def extract_class_name(filename):
    """Extract class name from filename."""
    # Parse filenames like 'CD235a_RBC_033_026624_045056_mask.png'
    parts = filename.split('_')
    if len(parts) >= 2:
        # First two components should be the class name (e.g., 'CD235a_RBC')
        return f"{parts[0]}_{parts[1]}"
    return None

def process_image(filename, input_dir, output_dir, color_map, class_codes):
    """Process a single binary mask image."""
    try:
        # Extract class name from filename
        class_name = extract_class_name(filename)
        if not class_name or class_name not in class_codes:
            print(f"Warning: Could not determine class for {filename}")
            return
            
        # Get the class index for this mask
        class_idx = class_codes[class_name]
        
        # Read the mask image (binary)
        img_path = input_dir / filename
        mask = np.array(Image.open(img_path))
        
        # Create an RGB image with the same size as mask
        colored = np.zeros((*mask.shape, 3), dtype=np.uint8)
        
        # Set background color (class 0)
        colored[:] = color_map[0]  
        
        # Set foreground color based on class index
        colored[mask > 0] = color_map[class_idx]
            
        # Save the colored image
        output_path = output_dir / filename
        Image.fromarray(colored).save(output_path)
        
    except Exception as e:
        print(f"Error processing {filename}: {str(e)}")

def color_masks(
    num_classes: int = None,
    input_dir: str = None,
    output_dir: str = None,
    ext: str = None,
    dataset_split: str = "train",
    config_path: str = "./config/config.yaml",
    class_codes_path: str = None
):
    """
    Create colored visualization of mask images.
    
    Args:
        num_classes: Number of classes in the masks (9 for new format)
        input_dir: Directory containing mask images
        output_dir: Directory to save colored images
        ext: File extension of mask images
        dataset_split: Dataset split to process ('train' or 'val')
        config_path: Path to configuration file
        class_codes_path: Path to class codes TSV file (optional, will use config value if not provided)
    """
    # Validate dataset split
    if dataset_split not in ["train", "val"]:
        raise ValueError("Dataset split must be either 'train' or 'val'")
    
    # Load configuration
    config = load_config(config_path)
    
    # Use provided values or defaults from config
    num_classes = num_classes or config["settings"]["num_classes"]
    ext = ext or config["settings"]["mask_file_extension"]
    
    # Use paths based on dataset split - using earlier definitions from dataset.output_dirs
    if input_dir is None:
        input_dir = resolve_variables(config, config["dataset"]["output_dirs"][f"{dataset_split}_source"])
    
    # Keep using colored_mask_dir from paths as it's not defined in dataset.output_dirs
    if output_dir is None:
        output_dir = resolve_variables(config, config["paths"][f"{dataset_split}_colored_mask_dir"])
    
    # Use class_codes_path from config if not provided
    if class_codes_path is None:
        class_codes_path = resolve_variables(config, config["paths"]["labels_tsv"])
    
    # Convert string paths to Path objects
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    class_codes_path = Path(class_codes_path)
    
    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load class codes
    class_codes = load_class_codes(class_codes_path)
    print(f"Loaded {len(class_codes)} class codes")
    
    # Get colors for the specified number of classes
    colors = config["settings"]["colors"]
    
    # Convert hex colors to RGB tuples
    color_map = {
        i: tuple(int(color.lstrip('#')[j:j+2], 16) for j in (0, 2, 4))
        for i, color in enumerate(colors)
    }
    
    # Get list of all mask files
    image_files = [f for f in os.listdir(input_dir) if f.endswith(f'.{ext}')]
    total_files = len(image_files)
    
    print(f"Found {total_files} {dataset_split} images to process")
    print(f"Processing from {input_dir} to {output_dir}")
    
    # Using ThreadPoolExecutor for parallel processing
    thread_multiplier = config["settings"].get("thread_multiplier", 2)
    max_workers = os.cpu_count() * thread_multiplier
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Create a progress bar
        list(tqdm(
            executor.map(
                lambda f: process_image(f, input_dir, output_dir, color_map, class_codes), 
                image_files
            ),
            total=total_files,
            desc=f"Processing {dataset_split} images ({num_classes} classes)",
            unit="image"
        ))
    
    print(f"Completed coloring {total_files} {dataset_split} mask images.")

if __name__ == "__main__":
    Fire(color_masks)