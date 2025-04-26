import csv
import re

import yaml


def resolve_variables(config, value):
    if isinstance(value, str):
        # Find all ${base_dirs.xxx} patterns
        pattern = r'\${([^}]+)}'
        matches = re.findall(pattern, value)
        
        resolved_value = value
        for match in matches:
            # Split by dot to navigate nested config
            parts = match.split('.')
            # Get the referenced value
            ref_value = config
            for part in parts:
                ref_value = ref_value[part]
            # Replace the variable reference with its value
            resolved_value = resolved_value.replace(f"${{{match}}}", ref_value)
        
        return resolved_value
    return value

# Load configuration
def load_config(config_path):
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)


def extract_class_name(filename):
    """Extract class name from filename like 'CD235a_RBC_033_026624_045056_mask.png'"""
    parts = filename.split('_')
    if len(parts) >= 2:
        # First two components should be the class name (e.g., 'CD235a_RBC')
        return f"{parts[0]}_{parts[1]}"
    return None


def load_class_codes(tsv_path):
    """Load class codes from TSV file"""
    class_codes = {}
    with open(tsv_path, 'r') as f:
        reader = csv.reader(f, delimiter='\t')
        next(reader)  # Skip header
        for row in reader:
            if len(row) >= 2:
                label, code = row[0], int(row[1])
                class_codes[label] = code
    return class_codes


def clean_class_name(class_name):
    """Clean up class names by removing special characters and converting to lowercase."""
    # Replace underscores and commas with spaces
    cleaned = class_name.replace('_', ' ').replace(',', ' ')
    # Convert to lowercase
    cleaned = cleaned.lower()
    # Remove multiple spaces
    cleaned = ' '.join(cleaned.split())
    return cleaned


def create_prompt(class_percentages, prompt_template):
    """Create prompt string with full class names."""
    class_descriptions = ", ".join([f"{class_name} {percentage:.2f}%"
                                  for class_name, percentage in class_percentages])
    prompt = prompt_template.format(class_descriptions=class_descriptions)
    return prompt