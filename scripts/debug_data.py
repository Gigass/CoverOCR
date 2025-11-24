#!/usr/bin/env python3
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# Load both files
template_path = REPO_ROOT / "data/annotations/template_cover.json"
ocr_path = REPO_ROOT / "data/annotations/auto_bbox_with_fonts.json"

with open(template_path, 'r', encoding='utf-8') as f:
    template = json.load(f)

with open(ocr_path, 'r', encoding='utf-8') as f:
    ocr_data = json.load(f)

print("=== TEMPLATE TEXTS ===")
for ann in template['images'][0]['annotations']:
    print(f"- '{ann['text']}'")

print("\n=== OCR TEXTS (first 20) ===")
count = 0
for img in ocr_data['images'][:3]:  # First 3 images
    print(f"\nImage: {img['image_path']}")
    for ann in img['annotations'][:5]:  # First 5 annotations per image
        print(f"  - '{ann['text']}'")
        count += 1
        if count >= 20:
            break
    if count >= 20:
        break
