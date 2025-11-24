#!/usr/bin/env python3
"""
Calibrate the coefficient for point size estimation.
Formula: point_size = k * (bbox_height / image_width) * book_width_inch
We want to find k.
k = point_size / ((bbox_height / image_width) * book_width_inch)
"""
import json
import sys
from pathlib import Path
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Import BOOK_SIZES from typography to ensure consistency
from backend.app.services.typography import TypographyEstimator

def load_dataset(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def calibrate(dataset_path):
    data = load_dataset(dataset_path)
    
    k_values = []
    
    print(f"Loading dataset from {dataset_path}...")
    
    for img_entry in data['images']:
        image_width = img_entry.get('image_width', 0)
        book_size = img_entry.get('book_size', '16k')
        
        # Get book width in inches
        book_width_inch = TypographyEstimator.BOOK_SIZES.get(book_size, 7.28)
        
        if image_width == 0:
            continue
            
        for ann in img_entry['annotations']:
            gt_point_size = ann.get('point_size')
            bbox = ann.get('bbox')
            
            if not gt_point_size or not bbox:
                continue
                
            # Calculate bbox height
            y_min = bbox[1]
            y_max = bbox[3]
            bbox_height = y_max - y_min
            
            if bbox_height <= 0:
                continue
                
            # Calculate k for this sample
            # point_size = k * (bbox_height / image_width) * book_width_inch
            # k = point_size / ((bbox_height / image_width) * book_width_inch)
            
            term = (bbox_height / image_width) * book_width_inch
            if term == 0:
                continue
                
            k = gt_point_size / term
            k_values.append(k)
            
    if not k_values:
        print("No valid samples for calibration.")
        return

    k_array = np.array(k_values)
    mean_k = np.mean(k_array)
    median_k = np.median(k_array)
    std_k = np.std(k_array)
    
    print("-" * 40)
    print(f"Total Samples: {len(k_values)}")
    print(f"Mean k:   {mean_k:.4f}")
    print(f"Median k: {median_k:.4f}")
    print(f"Std Dev:  {std_k:.4f}")
    print("-" * 40)
    
    # Current logic in typography.py:
    # estimated_char_height_px = pixel_height * 0.8
    # point_size = estimated_char_height_px * (72.0 / dpi)
    # dpi = image_width / book_width_inch
    # point_size = (pixel_height * 0.8) * (72.0 / (image_width / book_width_inch))
    # point_size = (pixel_height * 0.8 * 72.0 * book_width_inch) / image_width
    # point_size = (0.8 * 72.0) * (pixel_height / image_width) * book_width_inch
    # So current k = 0.8 * 72.0 = 57.6
    
    print(f"Current k (theoretical): {0.8 * 72.0}")
    print(f"Proposed k (median):     {median_k:.4f}")
    print("-" * 40)

if __name__ == "__main__":
    dataset_file = REPO_ROOT / "data/annotations/auto_bbox_with_fonts.json"
    calibrate(dataset_file)
