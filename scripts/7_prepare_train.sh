#!/bin/bash
# Script to prepare the training set

echo "Step 1: Creating colored visualizations of masks for training set"
# Run the color masks script
python3 /home/ubuntu/datasets/bscc/scripts/4_color_masks.py

echo "Step 2: Generating text prompts from masks for training set"
# Run the text prompt creation script with augmentation enabled
python3 /home/ubuntu/datasets/bscc/scripts/5_create_text_prompt.py \
    --use_augmentation False

echo "Training set processing complete!"