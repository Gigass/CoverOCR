#!/usr/bin/env python3
import paddle
import paddle.nn as nn
import paddle.vision.transforms as T
from paddle.io import Dataset, DataLoader
from paddle.vision.models import resnet18
from pathlib import Path
import cv2
import numpy as np
import json
import sys
import random

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

class FontDataset(Dataset):
    def __init__(self, data_dir, transform=None):
        self.data_dir = Path(data_dir)
        self.transform = transform
        self.samples = []
        # Filter out .DS_Store and other non-directories
        self.classes = sorted([d.name for d in self.data_dir.iterdir() if d.is_dir() and not d.name.startswith('.')])
        self.class_to_idx = {cls_name: i for i, cls_name in enumerate(self.classes)}
        
        for cls_name in self.classes:
            cls_dir = self.data_dir / cls_name
            for img_path in cls_dir.glob("*.jpg"):
                self.samples.append((str(img_path), self.class_to_idx[cls_name]))
        
        print(f"Found {len(self.samples)} images in {len(self.classes)} classes: {self.classes}")

    def __getitem__(self, idx):
        img_path, label = self.samples[idx]
        img = cv2.imread(img_path)
        if img is None:
            # Return a black image if read fails (should not happen)
            img = np.zeros((224, 224, 3), dtype=np.uint8)
        else:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            
        if self.transform:
            img = self.transform(img)
        return img, label

    def __len__(self):
        return len(self.samples)

def train(data_dir, output_dir, epochs=20, batch_size=32):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Transforms with augmentation
    transform = T.Compose([
        T.Resize((224, 224)),
        T.RandomRotation(10),
        T.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
        T.ToTensor(),
        T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    dataset = FontDataset(data_dir, transform=transform)
    if len(dataset) == 0:
        print("No data found!")
        return

    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True, num_workers=0)
    
    # Model
    model = resnet18(pretrained=True)
    # Check input features of fc
    in_features = model.fc.weight.shape[0]
    # Replace fc
    model.fc = nn.Linear(in_features, len(dataset.classes))
    
    model.train()
    
    criterion = nn.CrossEntropyLoss()
    optimizer = paddle.optimizer.Adam(parameters=model.parameters(), learning_rate=0.001)
    
    print("Starting training...")
    for epoch in range(epochs):
        total_loss = 0
        correct = 0
        total = 0
        
        for i, (images, labels) in enumerate(loader):
            outputs = model(images)
            loss = criterion(outputs, labels)
            
            loss.backward()
            optimizer.step()
            optimizer.clear_grad()
            
            total_loss += loss.item()
            acc = paddle.metric.accuracy(input=outputs, label=labels.unsqueeze(1))
            correct += acc.item() * len(labels)
            total += len(labels)
            
        print(f"Epoch {epoch+1}/{epochs}, Loss: {total_loss/len(loader):.4f}, Acc: {correct/total:.4f}")
        
    # Save model
    model_path = output_dir / "font_resnet18.pdparams"
    paddle.save(model.state_dict(), str(model_path))
    print(f"Model saved to {model_path}")
    
    # Save class mapping
    mapping_path = output_dir / "class_mapping.json"
    with open(mapping_path, 'w', encoding='utf-8') as f:
        json.dump(dataset.classes, f, ensure_ascii=False)
    print(f"Class mapping saved to {mapping_path}")

if __name__ == "__main__":
    data_folder = REPO_ROOT / "data/font_train"
    model_folder = REPO_ROOT / "models/custom_font_classifier"
    train(data_folder, model_folder)
