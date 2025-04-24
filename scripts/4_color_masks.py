import os
from pathlib import Path
import numpy as np
from PIL import Image
import concurrent.futures
from tqdm import tqdm
import yaml
from fire import Fire

from utils import resolve_variables  # Import the resolve_variables function

def load_config(config_path):
    """Load configuration from YAML file"""
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)

def process_image(filename, input_dir, output_dir, color_map):
    """Process a single image file."""
    try:
        # Read the mask image
        img_path = input_dir / filename
        mask = np.array(Image.open(img_path))
        
        # Create an RGB image with the same size as mask
        colored = np.zeros((*mask.shape, 3), dtype=np.uint8)
        
        # Fill colors based on mask values
        for class_idx, color in color_map.items():
            colored[mask == class_idx] = color
            
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
    config_path: str = "./config/config.yaml"
):
    """
    Create colored visualization of mask images.
    
    Args:
        num_classes: Number of classes in the masks (5, 6, 9, or 10)
        input_dir: Directory containing mask images
        output_dir: Directory to save colored images
        ext: File extension of mask images
        dataset_split: Dataset split to process ('train' or 'val')
        config_path: Path to configuration file
    """
    # Validate dataset split
    if dataset_split not in ["train", "val"]:
        raise ValueError("Dataset split must be either 'train' or 'val'")
    
    # Load configuration
    config = load_config(config_path)
    
    # Use provided values or defaults from config
    num_classes = num_classes or config["settings"]["num_classes"]
    ext = ext or config["settings"]["mask_file_extension"]
    
    # Use paths based on dataset split
    if input_dir is None:
        input_dir = resolve_variables(config, config["paths"][f"{dataset_split}_mask_dir"])
    
    if output_dir is None:
        output_dir = resolve_variables(config, config["paths"][f"{dataset_split}_colored_mask_dir"])
    
    # Convert string paths to Path objects
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    
    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Get colors for the specified number of classes
    colors = config["settings"]["colors"]
    
    # Convert hex colors to RGB tuples
    color_map = {
        i: tuple(int(color.lstrip('#')[j:j+2], 16) for j in (0, 2, 4))
        for i, color in enumerate(colors)
    }
    
    # Get list of all PNG files
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
                lambda f: process_image(f, input_dir, output_dir, color_map), 
                image_files
            ),
            total=total_files,
            desc=f"Processing {dataset_split} images ({num_classes} classes)",
            unit="image"
        ))
    
    print(f"Completed coloring {total_files} {dataset_split} mask images.")

if __name__ == "__main__":
    Fire(color_masks)