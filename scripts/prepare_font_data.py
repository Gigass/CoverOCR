#!/usr/bin/env python3
import json
import sys
from pathlib import Path
import cv2
import shutil
from tqdm import tqdm

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

def load_dataset(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def prepare_data(dataset_path, images_dir, output_dir):
    data = load_dataset(dataset_path)
    output_dir = Path(output_dir)
    
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)
    
    print(f"Preparing data from {dataset_path}...")
    
    count = 0
    
    for img_entry in tqdm(data['images']):
        image_path = images_dir / Path(img_entry['image_path']).name
        if not image_path.exists():
            # Try finding it in the images_dir directly if the path in json has a prefix
            image_path = images_dir / Path(img_entry['image_path']).name
            if not image_path.exists():
                pass
        
        if not image_path.exists():
            continue
            
        img = cv2.imread(str(image_path))
        if img is None:
            continue
            
        for ann in img_entry['annotations']:
            font_family = ann.get('font_family')
            if not font_family:
                continue
                
            # Clean font family name for directory
            safe_font_name = font_family.replace(' ', '_').replace('(', '').replace(')', '')
            
            class_dir = output_dir / safe_font_name
            class_dir.mkdir(exist_ok=True)
            
            bbox = ann['bbox']
            x_min, y_min, x_max, y_max = bbox
            
            # Ensure bounds
            h, w = img.shape[:2]
            x_min = max(0, min(x_min, w))
            x_max = max(0, min(x_max, w))
            y_min = max(0, min(y_min, h))
            y_max = max(0, min(y_max, h))
            
            if x_max <= x_min or y_max <= y_min:
                continue
                
            crop = img[y_min:y_max, x_min:x_max]
            if crop.size == 0:
                continue
                
            # Save crop
            file_name = f"{Path(img_entry['image_path']).stem}_{ann['id']}.jpg"
            cv2.imwrite(str(class_dir / file_name), crop)
            count += 1
            
    print(f"Extracted {count} font samples to {output_dir}")

if __name__ == "__main__":
    dataset_file = REPO_ROOT / "data/annotations/auto_bbox_with_fonts.json"
    images_folder = REPO_ROOT / "data/aiphoto"
    output_folder = REPO_ROOT / "data/font_train"
    prepare_data(dataset_file, images_folder, output_folder)
