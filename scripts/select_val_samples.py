#!/usr/bin/env python3
# filepath: /home/ubuntu/datasets/bscc/scripts/select_val_samples.py
import json
import os
import random
import shutil
from fire import Fire

def select_samples(
    prompt_file: str,
    colored_dir: str,
    output_dir: str,
    num_samples: int = 2
):
    """
    Randomly select samples from validation prompt file and copy corresponding images
    with text prompt files to the output directory.

    Args:
        prompt_file: Path to the JSON file containing image prompts
        colored_dir: Directory containing source images
        output_dir: Directory where sample images and prompt text files will be saved
        num_samples: Number of samples to randomly select (default: 2)
    """
    print(f"Selecting {num_samples} random samples from {prompt_file}")
    
    # Load prompt JSON file
    try:
        prompts = []
        with open(prompt_file, 'r') as f:
            for line in f:
                if line.strip():  # Skip empty lines
                    prompts.append(json.loads(line))
    except json.JSONDecodeError:
        print(f"Error: Could not parse JSON file {prompt_file}")
        return
    except FileNotFoundError:
        print(f"Error: JSON file not found at {prompt_file}")
        return

    # Handle different possible JSON structures
    prompt_list = []

    # Since we're loading JSONL, we now have a list of dicts
    for item in prompts:
        if 'source' in item and 'prompt' in item:
            # Extract just the filename without the path
            image_name = os.path.basename(item['source'])
            prompt_list.append((image_name, item['prompt']))

    if not prompt_list:
        print("Error: Could not extract image names and prompts from JSON file")
        print(f"JSON content sample: {str(prompts)[:200]}...")
        return

    # Check if we have enough samples
    actual_samples = min(num_samples, len(prompt_list))
    if actual_samples < num_samples:
        print(f"Warning: Only {actual_samples} samples available (requested {num_samples})")
    
    # Randomly select samples
    selected_samples = random.sample(prompt_list, actual_samples)

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    print(f"Output directory: {output_dir}")

    # Process each selected sample
    for idx, (image_name, prompt) in enumerate(selected_samples):
        print(f'Selected sample {idx+1}: {image_name}')
        
        # Source image path (from the colored masks directory)
        source_path = os.path.join(colored_dir, image_name)
        
        # Target paths
        target_image_path = os.path.join(output_dir, image_name)
        target_prompt_path = os.path.join(output_dir, os.path.splitext(image_name)[0] + '.txt')
        
        # Copy the image file
        if os.path.exists(source_path):
            shutil.copy2(source_path, target_image_path)
            print(f'  Copied image to {target_image_path}')
        else:
            print(f'  Warning: Source image not found at {source_path}')
            print(f'  Looked for: {source_path}')
        
        # Write the prompt to a text file
        with open(target_prompt_path, 'w') as f:
            f.write(prompt)
        print(f'  Created prompt file {target_prompt_path}')
    
    print(f"Successfully processed {actual_samples} sample(s)")

if __name__ == "__main__":
    Fire(select_samples)