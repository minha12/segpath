import random

technical_details = [
    # Overview details
    "BCSS dataset contains over 20,000 segmentation annotations from breast cancer histopathology images.",
    "Images are sourced from The Cancer Genome Atlas (TCGA), a well-known repository of cancer-related data.",
    "Dataset designed for training convolutional neural networks (CNNs) for semantic segmentation in pathology.",
    "Annotations created through a structured crowdsourcing approach involving pathologists, residents, and students.",
    "The dataset was annotated using the Digital Slide Archive platform for collaborative work.",
    
    # Technical specifications
    "Dataset enables automatic identification of different tissue types in breast cancer images.",
    "Annotations were created by experts in diagnosing diseases through tissue examination.",
    "Dataset is publicly available through a GitHub repository for research purposes.",
    "Associated paper: 'Structured crowdsourcing enables convolutional segmentation of histology images' (2019).",
    "DOI of the associated paper: 10.1093/bioinformatics/btz083.",
    
    # Applications
    "BCSS is used for training models that automatically identify tissue types in breast cancer images.",
    "The dataset supports advancements in digital pathology tools for automated diagnosis.",
    "Applications extend to improving diagnostic accuracy and reducing manual workload for pathologists.",
    "Dataset used for benchmarking new segmentation algorithms in computational pathology.",
    "Enables research on breast cancer pathology using machine learning techniques.",
    
    # Additional context
    "Annotations visualizable through an interactive online platform by clicking the 'eye' icon.",
    "Created through collaboration between pathologists, residents, and medical students.",
    "The crowdsourcing framework enhances accuracy through consensus and expert review.",
    "Dataset aims to advance research in computational pathology for cancer diagnosis.",
    "Segmentation masks identify critical tissue structures relevant to breast cancer diagnosis.",
]

def augment_prompt(original_prompt, use_augmentation=False):
    """Augment prompt with technical context if use_augmentation is True."""
    if not use_augmentation or len(original_prompt.split()) >= 55:
        return original_prompt
    
    technical_context = random.choice(technical_details)
    return f"{original_prompt}\nContext: {technical_context}"
