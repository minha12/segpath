#!/bin/bash
# Script to prepare the training set

echo "Step 1: Reducing mask classes for training set"
# Run the mask reduction script using default configuration
python3 /home/ubuntu/datasets/bscc/scripts/3_reduce_mask_classes.py

echo "Step 2: Creating colored visualizations of masks for training set"
# Run the color masks script
python3 /home/ubuntu/datasets/bscc/scripts/4_color_masks.py

echo "Step 3: Generating text prompts from masks for training set"
# Run the text prompt creation script with augmentation enabled
python3 /home/ubuntu/datasets/bscc/scripts/5_create_text_prompt.py \
    --use_augmentation False

echo "Training set processing complete!"