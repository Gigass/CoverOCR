#!/usr/bin/env python3
"""
Train a machine learning model to predict point size.
Uses anchor-based normalization with the book title as reference.
"""
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.ensemble import RandomForestRegressor
import pickle

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

def load_template(template_path):
    """Load the ground truth template."""
    with open(template_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_ocr_data(ocr_path):
    """Load OCR results with bboxes."""
    with open(ocr_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def fuzzy_match_text(text1, text2, threshold=0.8):
    """Simple fuzzy text matching."""
    from difflib import SequenceMatcher
    return SequenceMatcher(None, text1, text2).ratio() >= threshold

def build_training_data(template, ocr_data):
    """Build training dataset by matching template with OCR results."""
    
    # Build template lookup from the single template image's annotations
    template_lookup = {}
    if template.get('images') and len(template['images']) > 0:
        for ann in template['images'][0].get('annotations', []):
            text = ann.get('text', '').strip()
            if text:
                template_lookup[text] = ann
    
    samples = []
    
    print(f"Template has {len(template_lookup)} entries")
    print(f"OCR data has {len(ocr_data['images'])} images")
    
    images_with_anchor = 0
    total_annotations = 0
    matched_annotations = 0
    
    for img_entry in ocr_data['images']:
        image_width = img_entry.get('image_width', 0)
        
        # Find anchor (book title)
        anchor_height = None
        for ann in img_entry['annotations']:
            text = ann.get('text', '').strip()
            if '人工智能' in text or '机器学习' in text:
                bbox = ann['bbox']
                anchor_height = bbox[3] - bbox[1]
                break
        
        if not anchor_height or anchor_height == 0:
            continue  # Skip images without anchor
        
        images_with_anchor += 1
            
        # Process each annotation
        for ann in img_entry['annotations']:
            total_annotations += 1
            ocr_text = ann.get('text', '').strip()
            bbox = ann['bbox']
            
            # Exact match with template (OCR results are already clean)
            matched_template = template_lookup.get(ocr_text)
            
            if not matched_template:
                continue  # Skip if no template match
            
            matched_annotations += 1
                
            # Extract features
            bbox_height = bbox[3] - bbox[1]
            bbox_width = bbox[2] - bbox[0]
            
            # Core features
            features = {
                'bbox_height': bbox_height,
                'bbox_width': bbox_width,
                'image_width': image_width,
                'text_length': len(ocr_text),
                'is_chinese': int(any('\u4e00' <= ch <= '\u9fff' for ch in ocr_text)),
                'is_all_caps': int(ocr_text.isupper() and ocr_text.isascii()),
                'is_title_case': int(ocr_text[0].isupper() and not ocr_text.isupper() and ocr_text.isascii()) if ocr_text else 0,
                
                # Anchor-based features (KEY!)
                'height_ratio_to_anchor': bbox_height / anchor_height,
                'relative_height': bbox_height / image_width,
                'aspect_ratio': bbox_width / bbox_height if bbox_height > 0 else 0,
            }
            
            # Target
            target = matched_template.get('point_size', 0)
            
            if target > 0:
                features['point_size'] = target
                samples.append(features)
    
    print(f"Images with anchor: {images_with_anchor}")
    print(f"Total annotations processed: {total_annotations}")
    print(f"Matched annotations: {matched_annotations}")
    print(f"Final samples: {len(samples)}")
    
    return pd.DataFrame(samples)

def train_model(df):
    """Train XGBoost model."""
    
    # Separate features and target
    feature_cols = [col for col in df.columns if col != 'point_size']
    X = df[feature_cols]
    y = df['point_size']
    
    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    # Train
    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=10,
        random_state=42,
        n_jobs=-1
    )
    
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred_train = model.predict(X_train)
    y_pred_test = model.predict(X_test)
    
    print("=" * 50)
    print("Training Results:")
    print(f"Train MAE: {mean_absolute_error(y_train, y_pred_train):.2f} pt")
    print(f"Test MAE:  {mean_absolute_error(y_test, y_pred_test):.2f} pt")
    print(f"Train R²:  {r2_score(y_train, y_pred_train):.3f}")
    print(f"Test R²:   {r2_score(y_test, y_pred_test):.3f}")
    print("=" * 50)
    
    # Feature importance
    print("\nTop 5 Important Features:")
    importance = pd.DataFrame({
        'feature': feature_cols,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    print(importance.head(5))
    
    return model, feature_cols

def main():
    template_path = REPO_ROOT / "data/annotations/template_cover.json"
    ocr_path = REPO_ROOT / "data/annotations/auto_bbox_with_fonts.json"
    output_dir = REPO_ROOT / "models/point_size_model"
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("Loading data...")
    template = load_template(template_path)
    ocr_data = load_ocr_data(ocr_path)
    
    print("Building training dataset...")
    df = build_training_data(template, ocr_data)
    
    print(f"Total training samples: {len(df)}")
    print(f"Point size distribution:\n{df['point_size'].value_counts().sort_index()}")
    
    if len(df) < 10:
        print("ERROR: Not enough training samples!")
        return
    
    print("\nTraining model...")
    model, feature_cols = train_model(df)
    
    # Save model
    model_path = output_dir / "xgboost_model.pkl"
    with open(model_path, 'wb') as f:
        pickle.dump({'model': model, 'feature_cols': feature_cols}, f)
    
    print(f"\nModel saved to {model_path}")

if __name__ == "__main__":
    main()
