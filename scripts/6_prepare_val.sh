#!/bin/bash
# filepath: /home/ubuntu/datasets/bscc/scripts/prepare_val.sh

set -e  # Exit on error

# Check if yq is installed for parsing YAML
if ! command -v yq &> /dev/null; then
    echo "Error: yq is required for parsing YAML. Please install it."
    echo "You can install it with: sudo snap install yq"
    exit 1
fi

# Define the config file path
CONFIG_FILE="./config/config.yaml"

# Check if config file exists
if [ ! -f "$CONFIG_FILE" ]; then
    echo "Error: Config file not found at $CONFIG_FILE"
    exit 1
fi

# Read config values using yq
echo "Reading configuration from $CONFIG_FILE..."

# Base directories
DATA_DIR=$(yq -r '.base_dirs.data' "$CONFIG_FILE")

# Get paths from config using yq
PLAIN_DIR=$(yq -r '.dataset.output_dirs.val_source' "$CONFIG_FILE" | sed "s|\${base_dirs.data}|$DATA_DIR|g")
COLORED_DIR=$(yq -r '.paths.val_colored_mask_dir' "$CONFIG_FILE" | sed "s|\${base_dirs.data}|$DATA_DIR|g")
PROMPT_FILE=$(yq -r '.paths.val_prompt_output_path' "$CONFIG_FILE" | sed "s|\${base_dirs.data}|$DATA_DIR|g")
SAMPLES_DIR="${DATA_DIR}/samples"
NUM_CLASSES=$(yq -r '.settings.num_classes' "$CONFIG_FILE")

echo "PLAIN_DIR: $PLAIN_DIR"
echo "COLORED_DIR: $COLORED_DIR"
echo "PROMPT_FILE: $PROMPT_FILE"
echo "SAMPLES_DIR: $SAMPLES_DIR"
echo "NUM_CLASSES: $NUM_CLASSES"

echo "Step 1: Creating colored visualizations of masks for validation set"
# Run the color masks script
python scripts/4_color_masks.py \
    --input_dir "$PLAIN_DIR" \
    --output_dir "$COLORED_DIR" \
    --num_classes "$NUM_CLASSES" \
    --ext "png" \
    --dataset_split "val" \
    --config_path "$CONFIG_FILE"

echo "Step 2: Generating text prompts from masks for validation set"
# Run the text prompt creation script
python scripts/5_create_text_prompt.py \
    --config_path "$CONFIG_FILE" \
    --dataset_split "val" \
    --use_augmentation False

echo "Validation set processing complete!"