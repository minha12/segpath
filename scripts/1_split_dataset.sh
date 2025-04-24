#!/bin/bash

set -e  # Exit on error

# Check if yq is installed for parsing YAML
if ! command -v yq &> /dev/null; then
    echo "Error: yq is required for parsing YAML. Please install it."
    echo "You can install it with: sudo snap install yq"
    exit 1
fi

CONFIG_FILE="config/config.yaml"

# Check if config file exists
if [ ! -f "$CONFIG_FILE" ]; then
    echo "Error: Config file not found at $CONFIG_FILE"
    exit 1
fi

# Read config values
echo "Reading configuration from $CONFIG_FILE..."

# First get the base directories
DATA_DIR=$(yq -r '.base_dirs.data' "$CONFIG_FILE")
META_DIR=$(yq -r '.base_dirs.meta' "$CONFIG_FILE")
RESULTS_DIR=$(yq -r '.base_dirs.results' "$CONFIG_FILE")
TEMP_DIR=$(yq -r '.base_dirs.temp' "$CONFIG_FILE")

# Create temp directory if it doesn't exist
mkdir -p "$TEMP_DIR"

# Data synchronization settings
SOURCE_PATH=$(yq -r '.data_sync.source_path' "$CONFIG_FILE")
DESTINATION_PATH=$(yq -r '.data_sync.destination_path' "$CONFIG_FILE" | sed "s|\${base_dirs.data}|$DATA_DIR|g")

# Source directories
TRAIN_IMAGES_DIR=$(yq -r '.dataset.source_dirs.train_images' "$CONFIG_FILE" | sed "s|\${base_dirs.data}|$DATA_DIR|g")
TRAIN_MASKS_DIR=$(yq -r '.dataset.source_dirs.train_masks' "$CONFIG_FILE" | sed "s|\${base_dirs.data}|$DATA_DIR|g")
VAL_IMAGES_DIR=$(yq -r '.dataset.source_dirs.val_images' "$CONFIG_FILE" | sed "s|\${base_dirs.data}|$DATA_DIR|g")
VAL_MASKS_DIR=$(yq -r '.dataset.source_dirs.val_masks' "$CONFIG_FILE" | sed "s|\${base_dirs.data}|$DATA_DIR|g")

# Output directories
TRAIN_TARGET_DIR=$(yq -r '.dataset.output_dirs.train_target' "$CONFIG_FILE" | sed "s|\${base_dirs.data}|$DATA_DIR|g")
TRAIN_SOURCE_DIR=$(yq -r '.dataset.output_dirs.train_source' "$CONFIG_FILE" | sed "s|\${base_dirs.data}|$DATA_DIR|g")
VAL_TARGET_DIR=$(yq -r '.dataset.output_dirs.val_target' "$CONFIG_FILE" | sed "s|\${base_dirs.data}|$DATA_DIR|g")
VAL_SOURCE_DIR=$(yq -r '.dataset.output_dirs.val_source' "$CONFIG_FILE" | sed "s|\${base_dirs.data}|$DATA_DIR|g")

# Split configuration
TRAIN_PERCENTAGE=$(yq -r '.dataset.split.train_percentage' "$CONFIG_FILE")

# Temporary files
TEMP_ALL_SHUFFLED=$(yq -r '.temp_files.all_shuffled' "$CONFIG_FILE" | sed "s|\${base_dirs.temp}|$TEMP_DIR|g")
TEMP_TRAIN_LIST=$(yq -r '.temp_files.train_list' "$CONFIG_FILE" | sed "s|\${base_dirs.temp}|$TEMP_DIR|g")
TEMP_VAL_LIST=$(yq -r '.temp_files.val_list' "$CONFIG_FILE" | sed "s|\${base_dirs.temp}|$TEMP_DIR|g")

# Cleanup configuration
REMOVE_OLD_DIRS=$(yq -r '.cleanup.remove_old_dirs' "$CONFIG_FILE")

# First, sync the data from source to destination
echo "Syncing data from ${SOURCE_PATH} to ${DESTINATION_PATH}..."
mkdir -p "$DESTINATION_PATH"
rsync -ah "$SOURCE_PATH" "$DESTINATION_PATH"
echo "Data synchronization complete."

# Create the new directory structure
echo "Creating directory structure..."
mkdir -p "$TRAIN_SOURCE_DIR" "$TRAIN_TARGET_DIR" "$VAL_SOURCE_DIR" "$VAL_TARGET_DIR"

# First, let's count all unique filenames without considering paths
echo "Collecting all unique image names..."
ALL_IMAGES=$(ls "$TRAIN_IMAGES_DIR" "$VAL_IMAGES_DIR" | sort | uniq)
TOTAL_COUNT=$(echo "$ALL_IMAGES" | wc -l)
TRAIN_COUNT=$((TOTAL_COUNT * TRAIN_PERCENTAGE / 100))
VAL_COUNT=$((TOTAL_COUNT - TRAIN_COUNT))

echo "Total unique images: $TOTAL_COUNT"
echo "Training set size (${TRAIN_PERCENTAGE}%): $TRAIN_COUNT"
echo "Validation set size ($((100 - TRAIN_PERCENTAGE))%): $VAL_COUNT"

# Create temporary file of shuffled image names
echo "$ALL_IMAGES" | shuf > "$TEMP_ALL_SHUFFLED"

# Take the first TRAIN_COUNT for training
head -n $TRAIN_COUNT "$TEMP_ALL_SHUFFLED" > "$TEMP_TRAIN_LIST"

# Take the remaining for validation
tail -n $VAL_COUNT "$TEMP_ALL_SHUFFLED" > "$TEMP_VAL_LIST"

echo "Moving files to training directory..."
while IFS= read -r img; do
    # Check if the file exists in train_512, if not try val_512
    if [ -f "${TRAIN_IMAGES_DIR}${img}" ]; then
        cp "${TRAIN_IMAGES_DIR}${img}" "${TRAIN_TARGET_DIR}${img}"
        cp "${TRAIN_MASKS_DIR}${img}" "${TRAIN_SOURCE_DIR}${img}"
    elif [ -f "${VAL_IMAGES_DIR}${img}" ]; then
        cp "${VAL_IMAGES_DIR}${img}" "${TRAIN_TARGET_DIR}${img}"
        cp "${VAL_MASKS_DIR}${img}" "${TRAIN_SOURCE_DIR}${img}"
    fi
done < "$TEMP_TRAIN_LIST"

echo "Moving files to validation directory..."
while IFS= read -r img; do
    # Check if the file exists in train_512, if not try val_512
    if [ -f "${TRAIN_IMAGES_DIR}${img}" ]; then
        cp "${TRAIN_IMAGES_DIR}${img}" "${VAL_TARGET_DIR}${img}"
        cp "${TRAIN_MASKS_DIR}${img}" "${VAL_SOURCE_DIR}${img}"
    elif [ -f "${VAL_IMAGES_DIR}${img}" ]; then
        cp "${VAL_IMAGES_DIR}${img}" "${VAL_TARGET_DIR}${img}"
        cp "${VAL_MASKS_DIR}${img}" "${VAL_SOURCE_DIR}${img}"
    fi
done < "$TEMP_VAL_LIST"

# Clean up temporary files
rm "$TEMP_ALL_SHUFFLED" "$TEMP_TRAIN_LIST" "$TEMP_VAL_LIST"

# Print summary
echo "Dataset reorganization complete!"
echo "Train images: $(ls "$TRAIN_TARGET_DIR" | wc -l)"
echo "Train masks: $(ls "$TRAIN_SOURCE_DIR" | wc -l)"
echo "Validation images: $(ls "$VAL_TARGET_DIR" | wc -l)"
echo "Validation masks: $(ls "$VAL_SOURCE_DIR" | wc -l)"

# Check if the new structure is complete before cleaning
if [ "$(ls "$TRAIN_TARGET_DIR" | wc -l)" -gt 0 ] && \
   [ "$(ls "$TRAIN_SOURCE_DIR" | wc -l)" -gt 0 ] && \
   [ "$(ls "$VAL_TARGET_DIR" | wc -l)" -gt 0 ] && \
   [ "$(ls "$VAL_SOURCE_DIR" | wc -l)" -gt 0 ]; then
    
    if [ "$REMOVE_OLD_DIRS" = "true" ]; then
        echo "Cleaning up old folders..."
        # Remove old directories after successful transfer
        rm -rf "$TRAIN_IMAGES_DIR" "$TRAIN_MASKS_DIR" "$VAL_IMAGES_DIR" "$VAL_MASKS_DIR"
        echo "Old folders have been cleaned up."
    else
        echo "Cleanup of old directories is disabled in config. Old folders were not removed."
    fi
else
    echo "WARNING: New data structure appears incomplete. Old folders were not removed."
    echo "Please check the data and manually remove old folders if needed."
fi