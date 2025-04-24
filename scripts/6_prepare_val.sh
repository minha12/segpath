#!/bin/bash
# filepath: /home/ubuntu/datasets/bscc/scripts/prepare_val.sh

# Define the input directory and output directory
INPUT_DIR="data/5-classes/val/source-original"
PLAIN_DIR="data/5-classes/val/source-plain"
COLORED_DIR="data/5-classes/val/source"
MAPPER_YAML="meta/mapper_5.yaml"  # Update with the actual path to your YAML mapper file
NUM_CLASSES=5  # Update this value as needed
CONFIG_FILE="./config/config.yaml"  # Add config file path
PROMPT_FILE="data/5-classes/val/prompt.json"
SAMPLES_DIR="data/5-classes/samples"

echo "Step 1: Reducing mask classes for validation set"
# Run the mask reduction script
python3 /home/ubuntu/datasets/bscc/scripts/3_reduce_mask_classes.py \
    --input_dir "$INPUT_DIR" \
    --output_dir "$PLAIN_DIR" \
    --num_classes "$NUM_CLASSES" \
    --mapper_yaml "$MAPPER_YAML" \
    --ext "png" \
    --dataset_split "val"

echo "Step 2: Creating colored visualizations of masks for validation set"
# Run the color masks script
python3 /home/ubuntu/datasets/bscc/scripts/4_color_masks.py \
    --input_dir "$PLAIN_DIR" \
    --output_dir "$COLORED_DIR" \
    --num_classes "$NUM_CLASSES" \
    --ext "png" \
    --dataset_split "val"

echo "Step 3: Generating text prompts from masks for validation set"
# Run the text prompt creation script
python3 /home/ubuntu/datasets/bscc/scripts/5_create_text_prompt.py \
    --config_path "$CONFIG_FILE" \
    --dataset_split "val" \
    --use_augmentation False

echo "Step 4: Selecting random samples and creating prompt text files"
python3 /home/ubuntu/datasets/bscc/scripts/select_val_samples.py \
    --prompt_file "$PROMPT_FILE" \
    --colored_dir "$COLORED_DIR" \
    --output_dir "$SAMPLES_DIR" \
    --num_samples 2

echo "Validation set processing complete!"