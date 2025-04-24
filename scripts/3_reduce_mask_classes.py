import numpy as np
from PIL import Image
import os
from pathlib import Path
from tqdm import tqdm
from fire import Fire
import yaml

from utils import resolve_variables  # Import the resolve_variables function

def load_config(config_path):
    """Load configuration from YAML file"""
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)

def load_yaml_mapper(yaml_path):
    """Load class mapping from YAML file"""
    with open(yaml_path, 'r') as f:
        mapping = yaml.safe_load(f)
    # Convert keys and values to integers (just to be safe)
    return {int(k): int(v) for k, v in mapping.items()}

def reduce_mask_classes(mask_path, output_path, label_map):
    mask = Image.open(mask_path)
    mask_array = np.array(mask)
    
    # Create output array filled with unknown class (0)
    output_array = np.zeros_like(mask_array)
    
    # Apply label mapping for known classes
    for old_label, new_label in label_map.items():
        output_array[mask_array == old_label] = new_label
        
    # Any unmapped values will remain 0 (unknown class)
    new_mask = Image.fromarray(output_array.astype(np.uint8))
    new_mask.save(output_path)

def process_directory(
    input_dir: str = None,
    output_dir: str = None,
    num_classes: int = None,
    mapper_yaml: str = None,
    ext: str = None,
    dataset_split: str = "train",
    config_path: str = "./config/config.yaml"
):
    """
    Process mask images to reduce number of classes.
    Args:
        input_dir: Directory containing mask images
        output_dir: Directory to save processed masks
        num_classes: Number of classes to reduce to (5, 6, 9, or 10)
        mapper_yaml: Path to YAML file containing class mapping
        ext: File extension of mask images ('png' or 'jpg')
        dataset_split: Dataset split to process ('train' or 'val')
        config_path: Path to configuration file
    """
    # Validate dataset split
    if dataset_split not in ["train", "val"]:
        raise ValueError("Dataset split must be either 'train' or 'val'")
    
    # Load configuration
    config = load_config(config_path)
    
    # Use provided values or defaults from config based on dataset split
    if input_dir is None:
        input_dir = resolve_variables(config, config["paths"][f"{dataset_split}_mask_dir"])
    
    num_classes = num_classes or config["settings"]["num_classes"]
    ext = ext or config["settings"]["mask_file_extension"]
    
    # Determine output directory based on class config and dataset split
    if output_dir is None:
        # Use the plain mask directory path instead of colored_mask_dir
        output_dir = resolve_variables(config, config["paths"][f"{dataset_split}_plain_mask_dir"])
    
    # Determine mapper file
    if mapper_yaml is None:
        mapper_yaml = resolve_variables(config, config["files"]["mapper"])
    
    # Load the class mapping
    print(f"Loading class mapping from {mapper_yaml}")
    label_map = load_yaml_mapper(mapper_yaml)
    
    if label_map is None:
        raise ValueError(f"Invalid class mapping in {mapper_yaml}")
    
    desc = f"Processing {dataset_split} masks ({num_classes} classes)"
    
    os.makedirs(output_dir, exist_ok=True)
    mask_files = list(Path(input_dir).glob(f'*.{ext}'))
    
    print(f"Found {len(mask_files)} mask files in {input_dir}")
    
    for mask_file in tqdm(mask_files, desc=desc):
        # Keep original filename without adding _mask
        output_file = Path(output_dir) / mask_file.name
        
        reduce_mask_classes(mask_file, output_file, label_map)
    
    print(f"\nProcessed {len(mask_files)} {dataset_split} masks from {input_dir}")
    print(f"Results saved to {output_dir}")

if __name__ == "__main__":
    Fire(process_directory)