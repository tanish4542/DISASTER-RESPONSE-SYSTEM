# Computer Vision - Disaster Response System

## Overview

The **CV module** implements damage detection and assessment using deep learning. It analyzes satellite and aerial imagery to:

- **Detect structural damage** - Buildings, roads, bridges
- **Classify damage levels** - No damage, minor, moderate, severe, destroyed
- **Generate damage heatmaps** - Visualize affected areas
- **Prioritize rescue zones** - Guide response efforts
- **Track changes over time** - Before/after damage assessment

## Architecture

### Core Components (Phase 6+)

- **Image Preprocessing** - Normalization, resizing, augmentation
- **Detection Model** - YOLOv8 for building detection
- **Classification Model** - Damage level classification
- **Post-processing** - Spatial filtering, confidence thresholding
- **Inference Pipeline** - Batch image processing
- **Visualization** - Damage heatmaps and overlays

### Current Status

**Phase 1: Initialization**
- ✅ Module structure created
- ✅ Directory layout for training and inference
- ⏳ Data preparation (Phase 6)
- ⏳ YOLOv8 integration (Phase 6)
- ⏳ Damage classification (Phase 6)
- ⏳ Heatmap generation (Phase 6)

## Technology Stack

- **Language**: Python 3.10+
- **Deep Learning**: PyTorch
- **Detection**: YOLOv8
- **Image Processing**: OpenCV
- **Data**: NumPy, Pillow
- **Visualization**: Matplotlib, Folium

## Project Structure

```
cv/
├── data/                # Image datasets
│   ├── raw/            # Original images
│   ├── annotated/      # Labeled datasets
│   ├── test/           # Test images
│   └── metadata.json   # Image metadata
├── models/             # Trained model weights
│   ├── yolo_detector.pt
│   ├── damage_classifier.pt
│   └── model_info.json
├── preprocessing/      # Image preparation
│   ├── __init__.py
│   ├── image_loader.py
│   ├── augmentation.py
│   ├── normalization.py
│   └── tiling.py
├── detection/          # YOLOv8 detection
│   ├── __init__.py
│   ├── yolo_detector.py
│   ├── building_detector.py
│   └── post_processing.py
├── training/           # Model training scripts
│   ├── __init__.py
│   ├── train_yolo.py
│   ├── train_classifier.py
│   ├── validate.py
│   └── metrics.py
├── inference/          # Prediction & deployment
│   ├── __init__.py
│   ├── detector.py
│   ├── damage_scorer.py
│   ├── batch_processor.py
│   └── heatmap_generator.py
├── requirements.txt    # CV-specific dependencies
├── README.md          # This file
└── .gitignore
```

## Planned Development

### Phase 6: Computer Vision Engine
1. Prepare xView2 dataset or similar
2. Fine-tune YOLOv8 for building detection
3. Train damage classification model
4. Implement inference pipeline
5. Generate damage heatmaps
6. Integrate with backend & dashboard

### Phase 7: Advanced Features
- Multi-temporal change detection
- Uncertainty estimation
- Real-time video processing
- 3D reconstruction
- Damage timeline analysis

## Installation

```bash
cd cv
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Dataset

### Recommended Datasets
- **xView2**: Before/after satellite images with damage labels
- **AIST Damage Mapper**: Building damage classification
- **INRIA Aerial Image Labeling**: Building detection

### Dataset Format
```
data/
├── train/
│   ├── pre_disaster/
│   │   ├── image_001.tif
│   │   └── ...
│   ├── post_disaster/
│   │   ├── image_001.tif
│   │   └── ...
│   └── annotations/
│       └── image_001.json
└── test/
    └── ...
```

## Model Architecture

### YOLOv8 Detection
- Input: RGB satellite images (256x256 or 512x512)
- Output: Bounding boxes for buildings
- Backbone: CSPDarknet
- Head: Detection head with 3 scales

### Damage Classification
- Input: Cropped building images
- Output: Damage class (0-4 scale)
- Backbone: ResNet50
- Head: FC layers with softmax

## Training

### Detection Model

```python
from cv.training.train_yolo import train_yolo

# Train YOLOv8 on building detection
train_yolo(
    data_yaml="data/dataset.yaml",
    epochs=100,
    imgsz=512,
    batch_size=16
)
```

### Classification Model

```python
from cv.training.train_classifier import train_classifier

# Train damage classifier
train_classifier(
    train_dir="data/train",
    val_dir="data/val",
    epochs=50,
    learning_rate=0.001
)
```

## Usage (Phase 6+)

### Inference

```python
from cv.inference.detector import DamageDetector

detector = DamageDetector(
    yolo_model="models/yolo_detector.pt",
    classifier_model="models/damage_classifier.pt"
)

# Process single image
results = detector.detect("satellite_image.tif")

for detection in results:
    print(f"Building: {detection['bbox']}")
    print(f"Damage: {detection['damage_class']}")
    print(f"Confidence: {detection['confidence']}")
```

### Batch Processing

```python
from cv.inference.batch_processor import BatchProcessor

processor = BatchProcessor(detector)

# Process directory of images
results = processor.process_directory(
    input_dir="images/",
    output_dir="results/",
    batch_size=32
)
```

### Generate Heatmaps

```python
from cv.inference.heatmap_generator import HeatmapGenerator

generator = HeatmapGenerator()

# Create damage heatmap
heatmap = generator.create_heatmap(
    results,
    map_extent=(-180, 180, -90, 90),
    resolution=100
)

generator.save_geotiff(heatmap, "damage_heatmap.tif")
```

## Performance Metrics

### Detection
- mAP@0.5: > 0.85
- mAP@0.5:0.95: > 0.75
- Inference time: < 100ms per image

### Classification
- Accuracy: > 80% per damage class
- Macro F1-score: > 0.75
- Inference time: < 10ms per building

## Integration with Backend

```python
# In backend/app/services/damage_service.py
from cv.inference.detector import DamageDetector

detector = DamageDetector()

async def analyze_image(image_path: str):
    results = detector.detect(image_path)
    
    return {
        "building_count": len(results),
        "damage_distribution": get_damage_stats(results),
        "heatmap_url": generate_heatmap(results),
        "confidence": compute_avg_confidence(results)
    }
```

## Data Augmentation

- Random rotation (-30° to 30°)
- Random brightness/contrast adjustment
- Random horizontal/vertical flips
- Gaussian noise addition
- Channel dropout

## Optimization Techniques

- Model quantization for inference speedup
- Batch processing for throughput
- Parallel processing with multiprocessing
- GPU acceleration with CUDA
- TensorRT for deployment

## Troubleshooting

### CUDA out of memory

```python
# Reduce batch size
processor.process_directory(
    input_dir="images/",
    batch_size=8  # Reduced from 32
)
```

### Model not converging

- Increase learning rate
- Use learning rate scheduler
- Add data augmentation
- Collect more training data

### Poor detection on certain image types

- Fine-tune on domain-specific data
- Adjust confidence thresholds
- Use test-time augmentation

## Related Documentation

- [System Architecture](../docs/architecture.md)
- [Computer Vision Design](../docs/cv.md)

## Resources

- [YOLOv8 Documentation](https://github.com/ultralytics/ultralytics)
- [PyTorch Tutorials](https://pytorch.org/tutorials/)
- [OpenCV Documentation](https://docs.opencv.org/)
- [xView2 Dataset](https://www.cosmiqworks.org/xview2/)

---

**Phase**: 1 (Initialization)  
**Status**: ✅ Ready for Phase 6 (Model Development)  
**Last Updated**: August 2026
