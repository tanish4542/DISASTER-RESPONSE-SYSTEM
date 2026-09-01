# Backend - Disaster Response System

## Overview

The backend is a **FastAPI** application that serves as the central coordination hub for the Disaster Response System. It handles:
- Emergency message reception and storage
- Message classification and priority scoring
- Communication between mobile apps and rescue dashboard
- Coordination of rescue operations

## Architecture

### Core Components

- **app/main.py** - FastAPI application entry point
- **app/models/** - SQLAlchemy database models (Phase 2)
- **app/schemas/** - Pydantic request/response schemas (Phase 2)
- **app/routes/** - API route handlers (Phase 2)
- **app/services/** - Business logic layer (Phase 2)
- **app/utils/** - Utility functions

## Technology Stack

- **Framework**: FastAPI
- **Web Server**: Uvicorn
- **Database**: SQLite with SQLAlchemy ORM
- **Validation**: Pydantic
- **Language**: Python 3.10+

## Current Status

**Phase 1: Initialization**
- ✅ Project structure created
- ✅ FastAPI application skeleton
- ✅ Health check endpoints
- ⏳ Database models (Phase 2)
- ⏳ SOS API endpoints (Phase 2)
- ⏳ Message classification service (Phase 5)
- ⏳ Priority scoring (Phase 5)

## Installation

### Prerequisites
- Python 3.10+
- pip or poetry

### Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Running the Backend

### Development Mode

```bash
# From backend directory with venv activated
python -m uvicorn app.main:app --reload
```

The API will be available at: `http://localhost:8000`

### Interactive API Documentation

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Health Check

```bash
curl http://localhost:8000/
curl http://localhost:8000/health
```

## API Endpoints (Phase 1)

### Root Endpoint
- `GET /` - Health check and service status

### Health Check
- `GET /health` - Health status

## Future Endpoints (Phase 2+)

- `POST /api/sos` - Submit emergency report
- `GET /api/sos/{id}` - Retrieve emergency details
- `GET /api/sos/active` - List active emergencies
- `POST /api/messages` - Store forwarded message
- `GET /api/priority-queue` - Get prioritized emergency list
- `POST /api/classify` - Classify emergency message
- `GET /api/dashboard/stats` - Dashboard statistics

## Configuration

### Environment Variables

Create a `.env` file in the backend directory:

```env
DATABASE_URL=sqlite:///./disaster_response.db
ENVIRONMENT=development
DEBUG=true
API_PORT=8000
```

## Database

### SQLite Setup

Database file will be created automatically at `./disaster_response.db` when the application starts.

## Planned Development

### Phase 2: Database & Models
- SQLAlchemy models for SOS, messages, users
- Migration scripts
- Database schema design

### Phase 5: Classification Service
- Integration with ML module
- SVM-based emergency classification
- TF-IDF text vectorization

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app entry point
│   ├── models/              # SQLAlchemy models (Phase 2)
│   ├── schemas/             # Pydantic schemas (Phase 2)
│   ├── routes/              # API route handlers (Phase 2)
│   ├── services/            # Business logic (Phase 2)
│   └── utils/               # Utility functions
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Testing

Tests will be added in Phase 2:

```bash
pytest tests/
```

## Troubleshooting

### Port 8000 already in use
```bash
# On macOS/Linux
lsof -i :8000
kill -9 <PID>

# On Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Module not found
Ensure virtual environment is activated:
```bash
source venv/bin/activate
```

## Contributing

- Follow PEP 8 style guide
- Add type hints to functions
- Write tests for new features
- Update this README for significant changes

## Related Documentation

- [System Architecture](../docs/architecture.md)
- [API Documentation](../docs/api.md)
- [Database Schema](../docs/database.md)
- [Communication Protocol](../docs/communication.md)

---

**Phase**: 1 (Initialization)  
**Status**: ✅ Ready for Phase 2 development  
**Last Updated**: August 2026
