# %%
import os
os.chdir("..")

# %%
import cv2
import numpy as np
from pathlib import Path

# Sample a few masks
mask_dir = Path("data/5-classes/train/source")
sample_masks = list(mask_dir.glob("*.png"))[:5]  # Check first 5 masks

for mask_path in sample_masks:
    mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
    unique_labels = np.unique(mask)
    print(f"Mask {mask_path.name} contains labels: {unique_labels}")
# %%
import os
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
import random

# Path to the source (mask) and target images
mask_path = "./data/train/source"
image_path = "./data/train/target"

# Load a mask from the source directory
mask_files = os.listdir(mask_path)
if mask_files:
    # Get a random mask file
    mask_file = random.choice(mask_files)
    mask = Image.open(os.path.join(mask_path, mask_file))
    
    # Display information about the mask
    print(f"Mask filename: {mask_file}")
    print(f"Mask size: {mask.size}")
    print(f"Mask mode: {mask.mode}")
    print(f"Mask format: {mask.format}")
    
    # Convert to numpy array and show more information
    mask_array = np.array(mask)
    print(f"Mask shape: {mask_array.shape}")
    print(f"Mask data type: {mask_array.dtype}")
    print(f"Mask min value: {mask_array.min()}")
    print(f"Mask max value: {mask_array.max()}")
    
    # Print unique values in the mask and their counts
    unique_values, counts = np.unique(mask_array, return_counts=True)
    print("\nUnique values in the mask:")
    for value, count in zip(unique_values, counts):
        print(f"Value {value}: {count} pixels ({count/mask_array.size*100:.2f}%)")
    
    # Display the mask
    plt.figure(figsize=(10, 5))
    plt.subplot(1, 2, 1)
    plt.title("Mask Image")
    plt.imshow(mask, cmap='gray')
    
    # Load a corresponding target image
    target_files = os.listdir(image_path)
    if target_files:
        # Try to find matching target file or choose random one
        target_file = mask_file if mask_file in target_files else random.choice(target_files)
        target = Image.open(os.path.join(image_path, target_file))
        
        # Display information about the target image
        print(f"\nTarget image filename: {target_file}")
        print(f"Target image size: {target.size}")
        print(f"Target image mode: {target.mode}")
        print(f"Target image format: {target.format}")
        
        # Display the target image
        plt.subplot(1, 2, 2)
        plt.title("Target Image")
        plt.imshow(target)
    
    plt.tight_layout()
    plt.show()
else:
    print("No mask files found in the specified directory.")

# %%
import subprocess
subprocess.run(["python", "./scripts/count_pixel_classes.py"])
# %%
# Display the CSV data in a more readable format
import pandas as pd
from IPython.display import display
df = pd.read_csv("results/pixel_class_percentages.csv")
display(df)  # This will show as a nice table in Jupyter


# %%
import matplotlib.pyplot as plt
import seaborn as sns

# Load the data
df = pd.read_csv("results/pixel_class_percentages.csv")

# Sort by percentage (descending)
df = df.sort_values('Percentage', ascending=False)

# Create a figure with appropriate size
plt.figure(figsize=(14, 8))

# Create bar plot
sns.barplot(x='Class Name', y='Percentage', data=df, palette='viridis')

# Customize the plot
plt.xticks(rotation=90)
plt.title('Pixel Class Distribution (Log Scale)', fontsize=16)
plt.ylabel('Percentage (%)', fontsize=14)
plt.xlabel('Class Name', fontsize=14)
plt.yscale('log')  # Use log scale to show the full range of values
plt.grid(axis='y', linestyle='--', alpha=0.7)

# Add percentage labels on top of each bar
for i, row in enumerate(df.itertuples()):
    if row.Percentage > 0.01:
        plt.text(i, row.Percentage, f"{row.Percentage:.2f}%", 
                 ha='center', va='bottom', rotation=0, fontsize=9)

plt.tight_layout()
plt.savefig('results/pixel_class_distribution.png', dpi=300)
plt.show()
# %%
# Create a pie chart for top classes
plt.figure(figsize=(12, 8))

# Group small classes (less than 1%) as "Other"
threshold = 1.0
top_classes = df[df['Percentage'] >= threshold].copy()
other_sum = df[df['Percentage'] < threshold]['Percentage'].sum()

# Create a new row for "Other" categories
if other_sum > 0:
    other_row = pd.DataFrame({
        'Label ID': [-1], 
        'Class Name': ['Other (<1%)'],
        'Pixel Count': [df[df['Percentage'] < threshold]['Pixel Count'].sum()],
        'Percentage': [other_sum]
    })
    pie_data = pd.concat([top_classes, other_row])
else:
    pie_data = top_classes

# Create pie chart
plt.pie(pie_data['Percentage'], labels=pie_data['Class Name'], 
        autopct='%1.1f%%', startangle=90, shadow=True)
plt.axis('equal')
plt.title('Distribution of Pixel Classes (Classes ≥1%)', fontsize=16)
plt.savefig('results/pixel_class_pie_chart.png', dpi=300)
plt.show()
# %%
