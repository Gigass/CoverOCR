#!/usr/bin/env python3
"""
Diagnose typography calculation for a single image.
"""
import json
import sys
from pathlib import Path
import cv2
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.app.services.typography import TypographyEstimator

def diagnose(image_name, dataset_path, images_dir):
    data = None
    with open(dataset_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    target_entry = None
    for img in data['images']:
        if image_name in img['image_path']:
            target_entry = img
            break
            
    if not target_entry:
        print(f"Image {image_name} not found in dataset.")
        return

    image_path = images_dir / Path(target_entry['image_path']).name
    if not image_path.exists():
        print(f"Image file {image_path} not found.")
        return
        
    img = cv2.imread(str(image_path))
    if img is None:
        print("Failed to read image.")
        return
        
    estimator = TypographyEstimator()
    
    print(f"=== Diagnosing {image_name} ===")
    print(f"Image Width (JSON): {target_entry.get('image_width')}")
    print(f"Image Width (Actual): {img.shape[1]}")
    print(f"Book Size: {target_entry.get('book_size', '16k')}")
    
    # Use the first annotation as a sample
    for ann in target_entry['annotations']:
        text = ann['text']
        gt_pt = ann.get('point_size')
        bbox = ann['bbox']
        
        print(f"\n--- Text: {text} ---")
        print(f"Ground Truth Point Size: {gt_pt}")
        print(f"BBox: {bbox}")
        
        y_min = bbox[1]
        y_max = bbox[3]
        bbox_height = y_max - y_min
        print(f"BBox Height (px): {bbox_height}")
        
        # Re-run estimate logic manually to show steps
        image_width = target_entry.get('image_width', img.shape[1])
        book_size = target_entry.get('book_size', '16k')
        book_width_inch = estimator.BOOK_SIZES.get(book_size, 7.28)
        
        print(f"Book Width (inch): {book_width_inch}")
        
        # Current Logic in Code
        k_factor = 26.2
        term = (bbox_height / image_width) * book_width_inch
        calc_pt = k_factor * term
        
        print(f"Calculation: {k_factor} * ({bbox_height} / {image_width}) * {book_width_inch}")
        print(f"           = {k_factor} * {bbox_height/image_width:.6f} * {book_width_inch}")
        print(f"           = {calc_pt:.4f}")
        
        rounded_pt = round(calc_pt * 2) / 2
        print(f"Rounded Result: {rounded_pt}")
        print(f"Error: {rounded_pt - gt_pt:.2f}")
        
        # Inverse calculation: What k would make it correct?
        # gt = k * term -> k = gt / term
        if term > 0:
            ideal_k = gt_pt / term
            print(f"Ideal k for this sample: {ideal_k:.4f}")
            
        print("-" * 20)

if __name__ == "__main__":
    dataset_file = REPO_ROOT / "data/annotations/auto_bbox_with_fonts.json"
    images_folder = REPO_ROOT / "data/aiphoto"
    # Pick the first image in the dataset usually
    diagnose("IMG_2972.JPG", dataset_file, images_folder)
