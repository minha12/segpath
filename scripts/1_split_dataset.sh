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

# Base directories
DATA_DIR=$(yq -r '.base_dirs.data' "$CONFIG_FILE")
TEMP_DIR=$(yq -r '.base_dirs.temp' "$CONFIG_FILE")

# Output directories
TRAIN_TARGET_DIR=$(yq -r '.dataset.output_dirs.train_target' "$CONFIG_FILE" | sed "s|\${base_dirs.data}|$DATA_DIR|g")
TRAIN_SOURCE_DIR=$(yq -r '.dataset.output_dirs.train_source' "$CONFIG_FILE" | sed "s|\${base_dirs.data}|$DATA_DIR|g")
VAL_TARGET_DIR=$(yq -r '.dataset.output_dirs.val_target' "$CONFIG_FILE" | sed "s|\${base_dirs.data}|$DATA_DIR|g")
VAL_SOURCE_DIR=$(yq -r '.dataset.output_dirs.val_source' "$CONFIG_FILE" | sed "s|\${base_dirs.data}|$DATA_DIR|g")

# Split configuration
TRAIN_PERCENTAGE=$(yq -r '.dataset.split.train_percentage' "$CONFIG_FILE")

# Temporary files
TEMP_ALL_IMAGES=$(yq -r '.temp_files.all_shuffled' "$CONFIG_FILE" | sed "s|\${base_dirs.temp}|$TEMP_DIR|g")
TEMP_TRAIN_LIST=$(yq -r '.temp_files.train_list' "$CONFIG_FILE" | sed "s|\${base_dirs.temp}|$TEMP_DIR|g")
TEMP_VAL_LIST=$(yq -r '.temp_files.val_list' "$CONFIG_FILE" | sed "s|\${base_dirs.temp}|$TEMP_DIR|g")

# Source directories - get tissue type directories from config
mapfile -t TISSUE_DIRS < <(yq -r '.dataset.source_dirs.tissue_dirs[]' "$CONFIG_FILE")
HE_SUFFIX=$(yq -r '.dataset.source_dirs.he_suffix' "$CONFIG_FILE")
MASK_SUFFIX=$(yq -r '.dataset.source_dirs.mask_suffix' "$CONFIG_FILE")

# Cleanup configuration
REMOVE_OLD_DIRS=$(yq -r '.cleanup.remove_old_dirs' "$CONFIG_FILE")

# Create the new directory structure
echo "Creating directory structure..."

# Remove old directories if specified
if [ "$REMOVE_OLD_DIRS" = "true" ]; then
    echo "Removing old output directories..."
    rm -rf "$TRAIN_SOURCE_DIR" "$TRAIN_TARGET_DIR" "$VAL_SOURCE_DIR" "$VAL_TARGET_DIR"
fi

# Create output directories
mkdir -p "$TRAIN_SOURCE_DIR" "$TRAIN_TARGET_DIR" "$VAL_SOURCE_DIR" "$VAL_TARGET_DIR"

# Generate list of all image files, filtering for HE images only
echo "Collecting all HE image files..."
> "$TEMP_ALL_IMAGES"
for dir in "${TISSUE_DIRS[@]}"; do
    find "${DATA_DIR}/${dir}" -name "*${HE_SUFFIX}" >> "$TEMP_ALL_IMAGES"
done

# Count total number of images
TOTAL_COUNT=$(wc -l < "$TEMP_ALL_IMAGES")
TRAIN_COUNT=$((TOTAL_COUNT * TRAIN_PERCENTAGE / 100))
VAL_COUNT=$((TOTAL_COUNT - TRAIN_COUNT))

echo "Total images found: $TOTAL_COUNT"
echo "Training set size (${TRAIN_PERCENTAGE}%): $TRAIN_COUNT"
echo "Validation set size ($((100 - TRAIN_PERCENTAGE))%): $VAL_COUNT"

# Shuffle and split the file list
shuf "$TEMP_ALL_IMAGES" > "${TEMP_ALL_IMAGES}.shuf"
head -n "$TRAIN_COUNT" "${TEMP_ALL_IMAGES}.shuf" > "$TEMP_TRAIN_LIST"
tail -n "$VAL_COUNT" "${TEMP_ALL_IMAGES}.shuf" > "$TEMP_VAL_LIST"

echo "Moving files to training directory..."
while IFS= read -r img_path; do
    # Extract the base filename
    filename=$(basename "$img_path")
    # Construct mask filename by replacing HE suffix with mask suffix
    mask_filename="${filename/${HE_SUFFIX}/${MASK_SUFFIX}}"
    # Get directory path
    dir_path=$(dirname "$img_path")
    mask_path="${dir_path}/${mask_filename}"
    
    # Check if mask file exists
    if [ -f "$mask_path" ]; then
        # Copy files to training directories
        cp "$img_path" "${TRAIN_TARGET_DIR}/${filename}"
        cp "$mask_path" "${TRAIN_SOURCE_DIR}/${mask_filename}"
    else
        echo "Warning: Mask file not found for $img_path"
    fi
done < "$TEMP_TRAIN_LIST"

echo "Moving files to validation directory..."
while IFS= read -r img_path; do
    # Extract the base filename
    filename=$(basename "$img_path")
    # Construct mask filename by replacing HE suffix with mask suffix
    mask_filename="${filename/${HE_SUFFIX}/${MASK_SUFFIX}}"
    # Get directory path
    dir_path=$(dirname "$img_path")
    mask_path="${dir_path}/${mask_filename}"
    
    # Check if mask file exists
    if [ -f "$mask_path" ]; then
        # Copy files to validation directories
        cp "$img_path" "${VAL_TARGET_DIR}/${filename}"
        cp "$mask_path" "${VAL_SOURCE_DIR}/${mask_filename}"
    else
        echo "Warning: Mask file not found for $img_path"
    fi
done < "$TEMP_VAL_LIST"

# Clean up temporary files
rm "$TEMP_ALL_IMAGES" "$TEMP_TRAIN_LIST" "$TEMP_VAL_LIST" "${TEMP_ALL_IMAGES}.shuf"

# Create additional required directories from config
mkdir -p "${DATA_DIR}/train/source-plain" "${DATA_DIR}/train/source" 
mkdir -p "${DATA_DIR}/val/source-plain" "${DATA_DIR}/val/source"

# Print summary
echo "Dataset reorganization complete!"
echo "Train images: $(ls "$TRAIN_TARGET_DIR" | wc -l)"
echo "Train masks: $(ls "$TRAIN_SOURCE_DIR" | wc -l)"
echo "Validation images: $(ls "$VAL_TARGET_DIR" | wc -l)"
echo "Validation masks: $(ls "$VAL_SOURCE_DIR" | wc -l)"