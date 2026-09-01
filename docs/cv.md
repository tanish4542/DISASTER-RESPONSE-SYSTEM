# Computer Vision Guide - Disaster Response System

## Overview

The CV module uses deep learning to detect and classify damage from satellite and aerial imagery. This document describes the model architecture, training process, and deployment strategy.

## Objective

**Detect buildings and classify damage severity in post-disaster imagery to guide rescue operations and resource allocation.**

## Damage Classification Scale

| Level | Class | Criteria | Priority |
|-------|-------|----------|----------|
| 0 | No Damage | Building intact, no visible damage | Low |
| 1 | Minor Damage | Slight damage, roof/walls partially affected | Medium |
| 2 | Moderate Damage | Significant damage, structural issues visible | High |
| 3 | Severe Damage | Major damage, building partially destroyed | Critical |
| 4 | Destroyed | Complete destruction, building uninhabitable | Critical |

## Model Architecture

### YOLOv8 Building Detection

```
Input Image (RGB, 512x512)
    ↓
Backbone (CSPDarknet)
    ├─ Conv layers (3x3)
    ├─ SPP (Spatial Pyramid Pooling)
    └─ PAN (Path Aggregation Network)
    ↓
Detection Head
    ├─ Bounding box regression
    ├─ Object confidence
    └─ Class prediction
    ↓
Output: Bounding boxes + confidence scores
```

### Damage Classification Model

```
Cropped Building Image (from YOLO)
    ↓
Backbone (ResNet50)
    ├─ Conv1
    ├─ ResLayer1-4
    └─ GlobalAvgPool
    ↓
Classifier Head
    ├─ FC layer (2048 → 512)
    ├─ BatchNorm + ReLU
    ├─ Dropout (0.5)
    └─ FC layer (512 → 5)
    ↓
Output: Damage class probabilities
```

### Combined Pipeline

```
Raw Satellite Image
    ↓
YOLOv8 Detection
    ├─ Building bounding boxes
    └─ Confidence scores
    ↓
Crop & Preprocess
    ├─ Extract ROI
    ├─ Normalize
    └─ Resize
    ↓
Damage Classifier
    └─ Classification scores
    ↓
Post-Processing
    ├─ Confidence thresholding
    ├─ NMS (Non-Maximum Suppression)
    └─ Spatial filtering
    ↓
Output: Damage map + heatmap
```

## Dataset Preparation

### xView2 Dataset

- **Images**: Pre/post-disaster satellite imagery
- **Resolution**: ~1m per pixel (Maxar satellite)
- **Bands**: RGB (3 channels)
- **Geographic Coverage**: Multiple disaster locations
- **Annotation Format**: JSON with building polygons and damage labels

### Dataset Split

```
Total: 10,000 images

Training: 7,000 images (70%)
  ├─ No damage: 1,400
  ├─ Minor: 1,400
  ├─ Moderate: 1,400
  ├─ Severe: 1,400
  └─ Destroyed: 1,400

Validation: 1,500 images (15%)
  └─ Balanced distribution

Test: 1,500 images (15%)
  └─ Held-out evaluation
```

### Data Preprocessing

```python
def preprocess_image(image_path):
    # Load image
    image = cv2.imread(image_path)
    
    # Normalize to [0, 1]
    image = image.astype(np.float32) / 255.0
    
    # Resize to 512x512
    image = cv2.resize(image, (512, 512), interpolation=cv2.INTER_LINEAR)
    
    # Standardize (ImageNet normalization)
    mean = np.array([0.485, 0.456, 0.406])
    std = np.array([0.229, 0.224, 0.225])
    image = (image - mean) / std
    
    return image
```

### Data Augmentation

Training augmentations:
- **Rotation**: ±15 degrees
- **Flip**: Horizontal & vertical (50% probability)
- **Brightness**: ±20%
- **Contrast**: ±20%
- **Saturation**: ±10%
- **Hue**: ±5 degrees
- **Noise**: Gaussian noise (σ=0.02)
- **Blur**: Kernel size 3-5

```python
def augment_image(image, label):
    # Random rotation
    angle = np.random.uniform(-15, 15)
    image = cv2.rotate(image, angle)
    
    # Random flip
    if np.random.rand() > 0.5:
        image = cv2.flip(image, 1)
    
    # Random brightness/contrast
    brightness = np.random.uniform(0.8, 1.2)
    image = np.clip(image * brightness, 0, 1)
    
    return image, label
```

## Training

### YOLOv8 Training

```python
from ultralytics import YOLO
import torch

# Load pre-trained YOLOv8m model
model = YOLO('yolov8m.pt')

# Train on building detection
results = model.train(
    data='data/buildings_dataset.yaml',
    epochs=100,
    imgsz=512,
    batch=16,
    device=0,  # GPU device
    workers=4,
    patience=20,  # Early stopping
    save=True,
    augment=True,
    mosaic=1.0,
    flipud=0.5,
    fliplr=0.5,
    degrees=15,
    translate=0.1,
    scale=0.5
)

# Save best model
model.save('models/yolo_detector.pt')
```

### Damage Classification Training

```python
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision.models import resnet50

# Load pre-trained ResNet50
model = resnet50(pretrained=True)

# Replace classifier
num_classes = 5
model.fc = nn.Sequential(
    nn.Linear(2048, 512),
    nn.BatchNorm1d(512),
    nn.ReLU(),
    nn.Dropout(0.5),
    nn.Linear(512, num_classes)
)

# Training setup
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = model.to(device)

criterion = nn.CrossEntropyLoss(weight=class_weights)
optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
    optimizer, mode='min', factor=0.5, patience=5
)

# Training loop
for epoch in range(num_epochs):
    for images, labels in train_loader:
        images, labels = images.to(device), labels.to(device)
        
        # Forward pass
        outputs = model(images)
        loss = criterion(outputs, labels)
        
        # Backward pass
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
    
    # Validation
    val_loss = validate(model, val_loader, device)
    scheduler.step(val_loss)
    
    print(f"Epoch {epoch}: Loss={loss:.4f}, Val Loss={val_loss:.4f}")

# Save model
torch.save(model.state_dict(), 'models/damage_classifier.pt')
```

## Inference Pipeline

### Single Image Analysis

```python
def analyze_image(image_path):
    # 1. Load and preprocess
    image = cv2.imread(image_path)
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # 2. Building detection with YOLOv8
    yolo_model = YOLO('models/yolo_detector.pt')
    detections = yolo_model(image_rgb, conf=0.5)
    
    buildings = []
    
    # 3. Damage classification for each building
    classifier = load_classifier('models/damage_classifier.pt')
    
    for det in detections[0].boxes:
        x1, y1, x2, y2 = det.xyxy[0]
        confidence = det.conf[0].item()
        
        # Crop building ROI
        building_roi = image_rgb[int(y1):int(y2), int(x1):int(x2)]
        
        # Classify damage
        building_roi_prep = preprocess_image(building_roi)
        damage_scores = classifier(building_roi_prep)
        damage_class = np.argmax(damage_scores)
        damage_confidence = damage_scores[damage_class]
        
        buildings.append({
            'bbox': [x1, y1, x2, y2],
            'detection_confidence': confidence,
            'damage_class': damage_class,
            'damage_confidence': damage_confidence,
            'location': [(x1+x2)/2, (y1+y2)/2]  # Center
        })
    
    return buildings
```

### Batch Processing

```python
def process_image_batch(image_dir, output_dir, batch_size=8):
    yolo_model = YOLO('models/yolo_detector.pt')
    classifier = load_classifier('models/damage_classifier.pt')
    
    image_files = sorted(glob.glob(f"{image_dir}/*.tif"))
    
    for batch_start in range(0, len(image_files), batch_size):
        batch_files = image_files[batch_start:batch_start+batch_size]
        images = [cv2.imread(f) for f in batch_files]
        
        # Batch detection
        detections_list = yolo_model(images, conf=0.5)
        
        for img_path, image, detections in zip(batch_files, images, detections_list):
            # Process detections...
            results = []
            
            # Save results
            output_path = f"{output_dir}/{Path(img_path).stem}_results.json"
            with open(output_path, 'w') as f:
                json.dump(results, f)
```

## Heatmap Generation

### Create Damage Heatmap

```python
def create_damage_heatmap(buildings, image_shape, cell_size=50):
    height, width = image_shape[:2]
    grid_height = (height + cell_size - 1) // cell_size
    grid_width = (width + cell_size - 1) // cell_size
    
    # Initialize heatmap
    heatmap = np.zeros((grid_height, grid_width))
    damage_counts = np.zeros((grid_height, grid_width))
    
    # Accumulate damage scores
    for building in buildings:
        x, y = int(building['location'][0]), int(building['location'][1])
        grid_x = x // cell_size
        grid_y = y // cell_size
        
        if 0 <= grid_x < grid_width and 0 <= grid_y < grid_height:
            # Weight by damage class (0-4)
            damage_score = building['damage_class'] / 4.0
            heatmap[grid_y, grid_x] += damage_score
            damage_counts[grid_y, grid_x] += 1
    
    # Average damage
    heatmap = np.divide(
        heatmap, 
        damage_counts, 
        where=damage_counts>0, 
        out=np.zeros_like(heatmap)
    )
    
    # Normalize to [0, 1]
    heatmap = heatmap / np.max(heatmap) if np.max(heatmap) > 0 else heatmap
    
    # Upscale for visualization
    heatmap_full = cv2.resize(
        heatmap, 
        (width, height), 
        interpolation=cv2.INTER_CUBIC
    )
    
    return heatmap_full
```

### Visualize Heatmap

```python
def visualize_results(image, buildings, heatmap):
    # Draw buildings with damage colors
    result = image.copy()
    
    colors = [
        (0, 255, 0),      # No damage - green
        (255, 255, 0),    # Minor - yellow
        (255, 165, 0),    # Moderate - orange
        (255, 0, 0),      # Severe - red
        (128, 0, 0)       # Destroyed - dark red
    ]
    
    for building in buildings:
        x1, y1, x2, y2 = [int(x) for x in building['bbox']]
        damage_class = building['damage_class']
        color = colors[damage_class]
        
        # Draw bounding box
        cv2.rectangle(result, (x1, y1), (x2, y2), color, 2)
        
        # Label
        text = f"Dmg:{damage_class} ({building['damage_confidence']:.2f})"
        cv2.putText(result, text, (x1, y1-5), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    
    # Overlay heatmap
    heatmap_colored = cv2.applyColorMap(
        (heatmap * 255).astype(np.uint8), 
        cv2.COLORMAP_JET
    )
    result = cv2.addWeighted(result, 0.7, heatmap_colored, 0.3, 0)
    
    return result
```

## Evaluation Metrics

### Detection Metrics
- **mAP@0.5**: Mean Average Precision at IoU threshold 0.5
- **mAP@0.75**: At IoU threshold 0.75
- **mAP@0.5:0.95**: Averaged across IoU thresholds
- **Target**: mAP > 0.85 at 0.5, > 0.75 at 0.5:0.95

### Classification Metrics
```python
from sklearn.metrics import classification_report, confusion_matrix

y_pred = predictions
y_true = ground_truth

# Per-class metrics
print(classification_report(y_true, y_pred, 
                          target_names=['No', 'Minor', 'Moderate', 'Severe', 'Destroyed']))

# Confusion matrix
cm = confusion_matrix(y_true, y_pred)
print(cm)

# Overall accuracy
accuracy = np.trace(cm) / np.sum(cm)
print(f"Accuracy: {accuracy:.3f}")
```

## Model Optimization

### Quantization for Deployment

```python
# Quantize YOLOv8 model
from ultralytics import YOLO

model = YOLO('models/yolo_detector.pt')

# Export to ONNX for inference
model.export(format='onnx', imgsz=512)

# Export to TensorRT for GPU inference
model.export(format='engine', imgsz=512, device=0)
```

## Backend Integration

```python
# backend/app/services/damage_service.py
import cv2
from cv.inference.detector import DamageDetector

class DamageAnalysisService:
    def __init__(self):
        self.detector = DamageDetector()
    
    async def analyze_image(self, image_path: str):
        buildings = self.detector.detect(image_path)
        
        # Generate heatmap
        image = cv2.imread(image_path)
        heatmap = self.detector.create_heatmap(buildings, image.shape)
        
        # Store results
        return {
            'buildings': buildings,
            'damage_distribution': self._get_statistics(buildings),
            'heatmap_url': await self._save_heatmap(heatmap)
        }
    
    def _get_statistics(self, buildings):
        distribution = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}
        for b in buildings:
            distribution[b['damage_class']] += 1
        return distribution
```

---

**Version**: 1.0  
**Phase**: 1 (Design & Planning)  
**Last Updated**: August 2026  
**Status**: ✅ Ready for Phase 6 (Implementation)
