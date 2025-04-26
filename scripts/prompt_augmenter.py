import random

technical_details = [
    # Overview details
    "SegPath is a large-scale dataset for semantic segmentation of cancer histology images[cite: 1, 18].",
    "Created using a restaining-based annotation workflow involving H&E and immunofluorescence (IF) staining[cite: 1, 19, 51, 226].",
    "Dataset designed for training deep learning models for accurate tissue/cell segmentation in pathology[cite: 4, 11, 17, 224].",
    "Contains annotations for eight major cell/tissue types: epithelium, smooth muscle/myofibroblast, lymphocyte, leukocyte, endothelial cell, plasma cell, myeloid cell, and red blood cell[cite: 1, 18, 86, 111].",
    "Includes over 158,000 annotated patches from 1,583 patients across 18 different organs[cite: 1, 96, 97].",

    # Technical specifications & Advantages
    "Claims to be the largest annotation dataset (>10x larger than previous public datasets) for cancer histology segmentation[cite: 18, 95].",
    "IF-based annotations aim to be more accurate and less morphologically biased than conventional human annotations by pathologists[cite: 3, 13, 20, 52, 165, 231].",
    "Annotation workflow uses carefully selected antibodies specific to target cell types[cite: 53, 99, 100].",
    "Dataset generation involves multi-step image registration to align H&E and IF images accurately[cite: 62, 63, 76, 297, 298].",
    "Segmentation masks are generated based on IF intensity cut-offs, refined iteratively using deep learning models[cite: 68, 78, 84, 87, 338].",

    # Applications & Availability
    "Enables the development of accurate segmentation models for computer-aided diagnosis and cancer research[cite: 4, 14, 26, 247].",
    "Models trained on SegPath can potentially identify cells with atypical morphologies missed by pathologists[cite: 21, 153, 175, 187, 251].",
    "Supports research into the tumor microenvironment through detailed cell distribution analysis[cite: 16, 225].",
    "The dataset is publicly available via Zenodo, with links provided on a dedicated webpage[cite: 55, 256, 257].",
    "Associated paper: 'Restaining-based annotation for cancer histology segmentation to overcome annotation-related limitations among pathologists' (Komura et al., 2023, Patterns)[cite: 1, 7].",
]

def augment_prompt(original_prompt, use_augmentation=False):
    """Augment prompt with technical context if use_augmentation is True."""
    if not use_augmentation or len(original_prompt.split()) >= 55:
        return original_prompt
    
    technical_context = random.choice(technical_details)
    return f"{original_prompt}\nContext: {technical_context}"
