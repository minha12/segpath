# SegPath Dataset Preparation and Analysis

This repository contains tools for preparing and analyzing the SegPath dataset. The dataset consists of histopathology images with pixel-wise segmentation masks for different tissue and cell types.

## About SegPath

SegPath is a large-scale dataset for semantic segmentation of cancer histology images. It was created using a restaining-based annotation workflow involving H&E and immunofluorescence (IF) staining. The dataset contains annotations for eight major cell/tissue types:
- Epithelium
- Smooth muscle/myofibroblast
- Lymphocyte
- Leukocyte
- Endothelial cell
- Plasma cell
- Myeloid cell
- Red blood cell

It includes over 158,000 annotated patches from 1,583 patients across 18 different organs, making it one of the largest annotation datasets for cancer histology segmentation.

## Prerequisites

Before beginning, make sure to install the following dependencies:

```bash
sudo apt install yq  # Required for YAML parsing in shell scripts
```

## Dataset Structure

The dataset is organized with the following main directories:

- `data/` - Contains all dataset files and class directories
- `meta/` - Contains metadata files like class mappings
- `config/` - Contains configuration files
- `results/` - Contains analysis outputs
- `scripts/` - Contains data processing scripts
- `notebooks/` - Contains Jupyter notebooks for analysis

## Dataset Preparation Process

Follow these steps to prepare the dataset:

### 1. Split the Dataset

First, split the dataset into training and validation sets:

```bash
bash scripts/1_split_dataset.sh
```

This script:
- Reads configuration from `config/config.yaml`
- Creates train/validation splits based on the specified percentage
- Organizes images and masks into appropriate directories

### 2. Count Pixel Classes

Analyze the distribution of pixel classes in the dataset:

```bash
python scripts/2_count_pixel_classes.py
```

This script:
- Reads all mask files from the dataset
- Counts pixels belonging to each class
- Generates a CSV file with class distributions in the results directory

### 3. Reduce Mask Classes (if applicable)

If your workflow requires class reduction:

```bash
python scripts/3_reduce_mask_classes.py
```

This script:
- Uses a class mapping defined in the configuration
- Converts the original multi-class masks to a simplified format
- Saves the simplified masks to the output directory

### 4. Create Colored Masks

Generate colored visualizations of the masks for easier inspection:

```bash
python scripts/4_color_masks.py
```

This script:
- Takes the mask images
- Creates colored versions using a predefined color map
- Saves the colored masks for visualization or training

### 5. Generate Text Prompts

Create text descriptions from the mask images:

```bash
python scripts/5_create_text_prompt.py
```

This script:
- Analyzes each mask image
- Identifies the classes present and their percentages
- Generates descriptive text prompts for each image
- Optionally augments the prompts with technical details when enabled

### 6. Prepare Validation Set

Prepare the validation set in a single command:

```bash
bash scripts/6_prepare_val.sh
```

This script:
- Automates the processing pipeline for the validation set
- Creates colored visualizations of masks for the validation set
- Generates text prompts from masks for the validation set

### 7. Prepare Training Set

Similarly, prepare the training set:

```bash
bash scripts/7_prepare_train.sh
```

This script:
- Automates the processing pipeline for the training set
- Creates colored visualizations of masks for the training set
- Generates text prompts from masks for the training set

## Dataset Analysis

After preparation, you can analyze the dataset using the provided Jupyter notebook in the notebooks directory.

## Configuration

The dataset processing is controlled by the `config/config.yaml` file, which defines:

- Directory paths
- Class mappings
- Color schemes for visualization
- Processing parameters

Modify this file to adjust the dataset preparation process.
