#!/usr/bin/env python3
"""
Evaluate typography estimation accuracy against a labeled dataset.
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

def load_dataset(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def crop_image(image, bbox):
    x_min, y_min, x_max, y_max = bbox
    # Ensure bbox is within image bounds
    h, w = image.shape[:2]
    x_min = max(0, min(x_min, w))
    x_max = max(0, min(x_max, w))
    y_min = max(0, min(y_min, h))
    y_max = max(0, min(y_max, h))
    return image[y_min:y_max, x_min:x_max]

def evaluate(dataset_path, images_dir):
    data = load_dataset(dataset_path)
    estimator = TypographyEstimator()
    
    total_samples = 0
    correct_font = 0
    correct_size_name = 0
    point_size_errors = []
    
    print(f"Loading dataset from {dataset_path}...")
    
    for img_entry in data['images']:
        image_path = images_dir / Path(img_entry['image_path']).name
        if not image_path.exists():
            # Try finding it in the images_dir directly if the path in json has a prefix
            image_path = images_dir / Path(img_entry['image_path']).name
            if not image_path.exists():
                # Try absolute path if it was absolute in json (unlikely but possible)
                pass
        
        if not image_path.exists():
             print(f"Warning: Image not found {image_path}")
             continue

        # Read image
        img = cv2.imread(str(image_path))
        if img is None:
            print(f"Warning: Could not read image {image_path}")
            continue
            
        book_size = img_entry.get('book_size', '16k')
        image_width = img_entry.get('image_width', 0)
        
        # Find anchor for this image
        anchor_height = None
        for ann in img_entry['annotations']:
            text = ann.get('text', '').strip()
            if '人工智能' in text or '机器学习' in text:
                bbox = ann['bbox']
                anchor_height = bbox[3] - bbox[1]
                break
        
        for ann in img_entry['annotations']:
            gt_font = ann.get('font_family')
            gt_size_name = ann.get('font_size_name')
            gt_point_size = ann.get('point_size')
            
            # Skip if ground truth is missing or empty
            if not gt_font or not gt_point_size:
                continue
                
            bbox = ann['bbox']
            text = ann['text']
            
            crop = crop_image(img, bbox)
            if crop.size == 0:
                continue
                
            # Estimate
            # Note: The estimate method expects box as list of points [[x,y], [x,y], [x,y], [x,y]]
            # bbox is [xmin, ymin, xmax, ymax]
            box = [
                [float(bbox[0]), float(bbox[1])],
                [float(bbox[2]), float(bbox[1])],
                [float(bbox[2]), float(bbox[3])],
                [float(bbox[0]), float(bbox[3])]
            ]
            
            result = estimator.estimate(
                text=text,
                crop=crop,
                box=box,
                image_width=image_width,
                book_size=book_size,
                anchor_height=anchor_height
            )
            
            total_samples += 1
            
            # Check Font Family
            # Normalize: replace underscores with spaces (classifier uses underscores for file safety)
            pred_font = result.font_family.replace('_', ' ')
            gt_font_norm = gt_font.replace('_', ' ')
            
            if pred_font == gt_font_norm:
                correct_font += 1
            else:
                # Optional: print mismatch for debugging
                print(f"Mismatch: Pred='{pred_font}' vs GT='{gt_font_norm}'")
                pass
            
            # Check Size Name
            if result.font_size_name == gt_size_name:
                correct_size_name += 1
                
            # Check Point Size
            error = abs(result.point_size - gt_point_size)
            point_size_errors.append(error)

    if total_samples == 0:
        print("No valid samples found.")
        return

    print("-" * 40)
    print(f"Total Samples: {total_samples}")
    print(f"Font Family Accuracy: {correct_font / total_samples:.2%}")
    print(f"Size Name Accuracy:   {correct_size_name / total_samples:.2%}")
    print(f"Point Size MAE:       {sum(point_size_errors) / total_samples:.2f} pt")
    print("-" * 40)

if __name__ == "__main__":
    dataset_file = REPO_ROOT / "data/annotations/auto_bbox_with_fonts.json"
    images_folder = REPO_ROOT / "data/aiphoto"
    evaluate(dataset_file, images_folder)
