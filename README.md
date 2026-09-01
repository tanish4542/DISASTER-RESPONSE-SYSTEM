# Disaster Response System

## Overview

The **Disaster Response System** is an academic prototype designed to demonstrate emergency response and rescue coordination in scenarios where conventional internet infrastructure is unavailable or severely compromised.

## Problem Statement

During major disaster events (earthquakes, tsunamis, floods, wildfires), cellular and internet infrastructure often becomes damaged or overwhelmed. This system explores how emergency information can reach rescue personnel through **device-to-device communication**, **local offline storage**, and **store-and-forward message propagation**.

## Motivation

- Conventional emergency systems rely on cellular networks that may fail during disasters
- Rescue teams need actionable intelligence (victim locations, damage assessment, priorities) quickly
- Building a proof-of-concept that bridges the "last mile" of emergency communication

## Objectives

1. **Enable offline emergency reporting** from mobile victims
2. **Implement device-to-device communication** using Bluetooth/Wi-Fi Direct
3. **Provide store-and-forward messaging** to propagate SOS signals across disconnected devices
4. **Classify and prioritize emergencies** using natural language processing
5. **Visualize emergencies and damage** on a rescue dashboard
6. **Detect structural damage** in affected areas using computer vision

## Proposed Solution

### System Flow

```
Victim Mobile App
        ↓
Offline SOS Storage
        ↓
Bluetooth / Wi-Fi Direct
        ↓
Store-and-Forward Communication
        ↓
Rescue Station / Backend
        ↓
AI Emergency Classification
        ↓
Priority Scoring
        ↓
Rescue Dashboard
        ↓
Map + Emergency Response
```

## System Architecture

See [docs/architecture.md](docs/architecture.md) for detailed architecture diagrams and component descriptions.

## Major Modules

| Module | Purpose | Language | Status |
|--------|---------|----------|--------|
| **Mobile App** | Victim emergency reporting | React Native / JavaScript | Phase 1: Structure |
| **Dashboard** | Rescue personnel interface | React / Vite / JavaScript | Phase 1: Structure |
| **Backend** | API, message processing, coordination | Python / FastAPI | Phase 1: Structure |
| **ML Engine** | Emergency classification & sentiment analysis | Python / scikit-learn | Phase 2 & beyond |
| **CV Engine** | Damage detection & assessment | Python / PyTorch / YOLOv8 | Phase 3 & beyond |
| **Communication** | Offline device-to-device messaging | Bluetooth / Wi-Fi Direct | Phase 2 & beyond |
| **Database** | Persistent storage of emergencies | SQLite / SQLAlchemy | Phase 2 & beyond |

## Technology Stack

### Mobile Application
- **Framework**: React Native (Expo)
- **Language**: JavaScript
- **Storage**: Local offline SQLite
- **Networking**: Bluetooth/Wi-Fi Direct (future phases)

### Rescue Dashboard
- **Framework**: React + Vite
- **Language**: JavaScript
- **Styling**: Tailwind CSS
- **Maps**: Leaflet + OpenStreetMap
- **Build**: Vite

### Backend Server
- **Framework**: FastAPI
- **Language**: Python 3.10+
- **Database**: SQLite + SQLAlchemy
- **Validation**: Pydantic
- **Server**: Uvicorn

### Machine Learning
- **Library**: scikit-learn
- **NLP**: TF-IDF, Support Vector Machine (SVM)
- **Data Processing**: NumPy, Pandas

### Computer Vision
- **Framework**: PyTorch
- **Model**: YOLOv8 (for damage detection)
- **Dataset**: xView2 building damage classification
- **Image Processing**: OpenCV

### Maps & Visualization
- **Map Library**: Leaflet (JavaScript)
- **Base Maps**: OpenStreetMap (offline tiles)
- **Web**: Vite + React

## Planned Development Phases

### Phase 1: Project Initialization & Architecture ✅
- Initialize project structure
- Set up all module directories
- Create README and documentation skeleton
- Verify basic builds

### Phase 2: Core Backend & Database
- Implement FastAPI endpoints
- Database schema & SQLAlchemy models
- SOS message storage
- Basic API routes

### Phase 3: Mobile SOS Collection
- SOS form and submission
- Local offline storage
- GPS integration
- Photo capture

### Phase 4: Offline Communication
- Bluetooth/Wi-Fi Direct integration
- Message synchronization protocol
- Store-and-forward logic
- Device discovery

### Phase 5: Emergency Classification
- TF-IDF vectorization
- SVM training
- Inference pipeline
- Priority scoring

### Phase 6: Computer Vision
- YOLO model integration
- Damage detection
- Image preprocessing
- Batch inference

### Phase 7: Rescue Dashboard
- Emergency visualization
- Real-time map updates
- Priority queue display
- Damage heatmaps

### Phase 8: Integration & Deployment
- End-to-end testing
- Docker containerization
- Performance optimization
- Documentation

## Project Structure

```
disaster-response-system/
│
├── mobile/                  # React Native app
│   ├── src/
│   ├── app.json
│   ├── package.json
│   └── README.md
│
├── dashboard/              # React/Vite rescue dashboard
│   ├── src/
│   ├── package.json
│   └── README.md
│
├── backend/                # FastAPI backend
│   ├── app/
│   ├── main.py
│   ├── requirements.txt
│   └── README.md
│
├── ml/                     # ML pipeline for classification
│   ├── data/
│   ├── models/
│   ├── preprocessing/
│   ├── training/
│   ├── inference/
│   └── README.md
│
├── cv/                     # CV pipeline for damage detection
│   ├── data/
│   ├── models/
│   ├── preprocessing/
│   ├── detection/
│   ├── training/
│   ├── inference/
│   └── README.md
│
├── communication/          # Device-to-device messaging
│   ├── protocol/
│   ├── storage/
│   ├── discovery/
│   ├── synchronization/
│   └── README.md
│
├── database/               # Database schema & migrations
│   └── README.md
│
├── docs/                   # Documentation
│   ├── architecture.md
│   ├── api.md
│   ├── communication.md
│   ├── database.md
│   ├── ml.md
│   ├── cv.md
│   └── testing.md
│
├── scripts/                # Utility scripts
│   └── README.md
│
├── .gitignore
├── README.md               # This file
├── docker-compose.yml      # Container orchestration
└── requirements-root.txt   # System-wide dependencies
```

## How to Run the Project

### Prerequisites

- **Node.js** (v18+) and npm
- **Python** (3.10+)
- **Git**
- For mobile: Android SDK or iOS development tools

### Quick Start

#### 1. Clone the Repository

```bash
git clone <repository-url>
cd disaster-response-system
```

#### 2. Install & Run Dashboard

```bash
cd dashboard
npm install
npm run dev
```

The dashboard will be available at `http://localhost:5173/`

#### 3. Install & Run Mobile App

```bash
cd ../mobile
npm install
npm run android    # or npm run ios
```

#### 4. Install & Run Backend

```bash
cd ../backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

The backend API will be available at `http://localhost:8000/`

Health check: `curl http://localhost:8000/`

### Docker Compose (Future)

Once all services are ready, start all services:

```bash
docker-compose up
```

## Future Features & Roadmap

- ✅ **Phase 1**: Project structure & initialization
- 🔄 **Phase 2**: Backend & database design
- 🔄 **Phase 3**: Mobile SOS collection
- 🔄 **Phase 4**: Offline mesh communication
- 🔄 **Phase 5**: NLP-based emergency classification
- 🔄 **Phase 6**: Computer vision damage detection
- 🔄 **Phase 7**: Rescue dashboard UI
- 🔄 **Phase 8**: Integration & deployment

## Contributing

This is an academic project. Changes should:
- Follow the planned phase structure
- Include tests for new features
- Maintain the architecture defined in Phase 1
- Be documented in the appropriate docs/ files

## License

[Specify License - Academic Use]

## Support & Contact

For questions or issues, please contact [Project Lead / Team Email]

---

**Last Updated**: August 2026  
**Current Phase**: 1 - Initialization  
**Status**: 🟢 Ready for Phase 2
