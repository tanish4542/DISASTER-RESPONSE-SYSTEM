# API Documentation - Disaster Response System

## Overview

This document describes the REST API for the Disaster Response System backend. The API is built with **FastAPI** and uses JSON for request/response formats.

## Base URL

**Development**: `http://localhost:8000`  
**Production**: `https://api.disaster-response.example.com`

## Authentication

To be implemented in Phase 8. Currently, all endpoints are public.

### Future: JWT Token
```
Authorization: Bearer <jwt_token>
```

## Response Format

All responses follow this format:

```json
{
  "status": "success|error|validation_error",
  "data": { /* response data */ },
  "message": "Human-readable message",
  "timestamp": 1693468200
}
```

## Error Responses

```json
{
  "status": "error",
  "error_code": "INVALID_INPUT",
  "message": "Emergency description is required",
  "timestamp": 1693468200
}
```

## Health Check Endpoints

### GET `/`
Health check and service status.

**Response:**
```json
{
  "status": "ok",
  "service": "Disaster Response System Backend",
  "version": "1.0.0",
  "message": "Backend is running successfully"
}
```

### GET `/health`
Alias for health check.

**Response:**
```json
{
  "status": "healthy",
  "service": "Disaster Response System API"
}
```

## Emergency Endpoints (Phase 2+)

### POST `/api/sos`
Submit a new emergency report.

**Request:**
```json
{
  "victim_id": "mobile_device_1",
  "latitude": 28.7041,
  "longitude": 77.1025,
  "description": "Building collapsed, people trapped",
  "emergency_type": "structural_collapse",
  "photos": ["photo_1.jpg", "photo_2.jpg"],
  "timestamp": 1693468200
}
```

**Response (201 Created):**
```json
{
  "status": "success",
  "data": {
    "emergency_id": "sos_12345",
    "received_at": 1693468200,
    "status": "pending"
  }
}
```

### GET `/api/sos/{emergency_id}`
Retrieve details of a specific emergency.

**Response (200):**
```json
{
  "status": "success",
  "data": {
    "id": "sos_12345",
    "victim_id": "mobile_device_1",
    "latitude": 28.7041,
    "longitude": 77.1025,
    "description": "Building collapsed, people trapped",
    "emergency_type": "structural_collapse",
    "severity_score": 9.2,
    "priority_rank": 1,
    "status": "assigned",
    "created_at": 1693468200,
    "assigned_team": "rescue_team_5"
  }
}
```

### GET `/api/sos/active`
List all active emergencies.

**Query Parameters:**
- `limit` (int, default=50): Maximum number of results
- `offset` (int, default=0): Pagination offset
- `status` (string): Filter by status (pending, assigned, resolved)
- `min_priority` (float): Minimum priority score

**Response (200):**
```json
{
  "status": "success",
  "data": {
    "emergencies": [
      {
        "id": "sos_12345",
        "latitude": 28.7041,
        "longitude": 77.1025,
        "description": "Building collapsed",
        "priority_rank": 1,
        "status": "assigned"
      }
    ],
    "total": 156,
    "returned": 50
  }
}
```

### PATCH `/api/sos/{emergency_id}`
Update emergency status.

**Request:**
```json
{
  "status": "in_progress",
  "assigned_team": "rescue_team_5",
  "notes": "Team arrived at location"
}
```

**Response (200):**
```json
{
  "status": "success",
  "data": {
    "emergency_id": "sos_12345",
    "updated_at": 1693468300
  }
}
```

## Message Endpoints (Phase 2+)

### POST `/api/messages`
Store a forwarded emergency message.

**Request:**
```json
{
  "emergency_id": "sos_12345",
  "source_device": "mobile_1",
  "text": "Building collapsed, people trapped",
  "media": ["photo_1.jpg"],
  "hop_count": 2,
  "timestamp": 1693468200
}
```

**Response (201 Created):**
```json
{
  "status": "success",
  "data": {
    "message_id": "msg_67890",
    "received_at": 1693468200
  }
}
```

### GET `/api/messages/{emergency_id}`
Retrieve all messages for an emergency.

**Response (200):**
```json
{
  "status": "success",
  "data": {
    "emergency_id": "sos_12345",
    "messages": [
      {
        "id": "msg_67890",
        "text": "Building collapsed",
        "source_device": "mobile_1",
        "created_at": 1693468200,
        "classification": "structural_collapse",
        "confidence": 0.94
      }
    ]
  }
}
```

## Classification Endpoints (Phase 5+)

### POST `/api/classify`
Classify an emergency message.

**Request:**
```json
{
  "text": "Building collapsed, people trapped",
  "context": "disaster_response"
}
```

**Response (200):**
```json
{
  "status": "success",
  "data": {
    "classification": "structural_collapse",
    "confidence": 0.94,
    "severity_score": 9.2,
    "keywords": ["collapsed", "trapped", "people"],
    "alternative_classifications": [
      {
        "type": "entrapment",
        "confidence": 0.82
      }
    ]
  }
}
```

## Priority Queue Endpoints (Phase 5+)

### GET `/api/priority-queue`
Get prioritized list of emergencies.

**Query Parameters:**
- `limit` (int, default=50): Number of emergencies to return
- `status` (string): Filter by status

**Response (200):**
```json
{
  "status": "success",
  "data": {
    "queue": [
      {
        "rank": 1,
        "emergency_id": "sos_12345",
        "priority_score": 95,
        "location": [28.7041, 77.1025],
        "description": "Building collapsed, people trapped",
        "team_assigned": "rescue_team_5",
        "estimated_arrival": 600
      }
    ],
    "timestamp": 1693468200
  }
}
```

## Damage Report Endpoints (Phase 6+)

### POST `/api/damage-report`
Submit a damage detection report.

**Request:**
```json
{
  "image_url": "satellite_001.tif",
  "latitude": 28.7041,
  "longitude": 77.1025,
  "damage_class": 3,
  "confidence": 0.87,
  "model_version": "yolov8_v1.0"
}
```

**Response (201 Created):**
```json
{
  "status": "success",
  "data": {
    "report_id": "dmg_11111",
    "created_at": 1693468300
  }
}
```

### GET `/api/damage/heatmap`
Get damage heatmap for visualization.

**Query Parameters:**
- `bbox` (string, required): Bounding box "lat1,lon1,lat2,lon2"
- `zoom` (int): Zoom level for aggregation

**Response (200):**
```json
{
  "status": "success",
  "data": {
    "heatmap_url": "https://api.example.com/tiles/heatmap/{z}/{x}/{y}.png",
    "damage_distribution": {
      "no_damage": 1200,
      "minor": 450,
      "moderate": 280,
      "severe": 150,
      "destroyed": 45
    },
    "generated_at": 1693468300
  }
}
```

## Team Management Endpoints (Phase 7+)

### GET `/api/teams`
List all rescue teams.

**Response (200):**
```json
{
  "status": "success",
  "data": {
    "teams": [
      {
        "id": "rescue_team_5",
        "name": "Alpha Team",
        "location": [28.7041, 77.1025],
        "status": "in_progress",
        "current_assignment": "sos_12345",
        "capacity": 15,
        "current_load": 12
      }
    ]
  }
}
```

### POST `/api/assign`
Assign a rescue team to an emergency.

**Request:**
```json
{
  "emergency_id": "sos_12345",
  "team_id": "rescue_team_5",
  "priority": 1,
  "estimated_time": 600
}
```

**Response (200):**
```json
{
  "status": "success",
  "data": {
    "assignment_id": "assign_001",
    "created_at": 1693468300
  }
}
```

## Dashboard Analytics Endpoints (Phase 7+)

### GET `/api/dashboard/stats`
Get system statistics for dashboard.

**Response (200):**
```json
{
  "status": "success",
  "data": {
    "total_emergencies": 1234,
    "active_emergencies": 156,
    "resolved": 1078,
    "average_response_time": 420,
    "total_teams": 25,
    "teams_available": 8,
    "teams_in_progress": 17,
    "damage_area_sq_km": 450,
    "buildings_damaged": 2845,
    "coverage_percentage": 78
  }
}
```

## Rate Limiting

To be implemented in Phase 8:
- **Mobile clients**: 100 requests/minute per device
- **Dashboard**: 1000 requests/minute per user
- **Backend services**: Unlimited (trusted)

## Error Codes

| Code | HTTP | Description |
|------|------|-------------|
| INVALID_INPUT | 400 | Missing or invalid request parameters |
| NOT_FOUND | 404 | Emergency/message not found |
| DUPLICATE_SUBMISSION | 409 | Message ID already exists |
| SERVICE_ERROR | 500 | Internal server error |
| DATABASE_ERROR | 500 | Database operation failed |
| CLASSIFICATION_ERROR | 500 | ML classification failed |

## Pagination

All list endpoints support pagination:

```
GET /api/sos/active?limit=50&offset=100
```

**Response:**
```json
{
  "data": { /* items */ },
  "pagination": {
    "limit": 50,
    "offset": 100,
    "total": 1234,
    "pages": 25
  }
}
```

## Filtering

Emergency list endpoints support filtering:

```
GET /api/sos/active?status=pending&min_priority=7.0&emergency_type=structural_collapse
```

## Sorting

```
GET /api/sos/active?sort_by=priority_rank&order=desc
```

## Versioning

API versioning via URL path:

```
/api/v1/sos        # Version 1
/api/v2/sos        # Version 2 (future)
```

## Testing

### cURL Examples

```bash
# Health check
curl http://localhost:8000/

# Submit emergency
curl -X POST http://localhost:8000/api/sos \
  -H "Content-Type: application/json" \
  -d '{
    "victim_id": "mobile_1",
    "latitude": 28.7041,
    "longitude": 77.1025,
    "description": "Building collapsed"
  }'

# List active emergencies
curl http://localhost:8000/api/sos/active?limit=10
```

## WebSocket Endpoints (Phase 7+)

### WS `/ws/dashboard/{user_id}`
Real-time updates for dashboard.

**Connection:**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/dashboard/user123');

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  // {
  //   "type": "new_emergency",
  //   "data": { emergency object }
  // }
};
```

## SDK Examples

### Python
```python
import requests

response = requests.post(
    'http://localhost:8000/api/sos',
    json={
        'victim_id': 'mobile_1',
        'latitude': 28.7041,
        'longitude': 77.1025,
        'description': 'Building collapsed'
    }
)
print(response.json())
```

### JavaScript
```javascript
const response = await fetch('http://localhost:8000/api/sos', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    victim_id: 'mobile_1',
    latitude: 28.7041,
    longitude: 77.1025,
    description: 'Building collapsed'
  })
});
const data = await response.json();
```

---

**Version**: 1.0  
**Phase**: 1 (Health Check Endpoints)  
**Last Updated**: August 2026  
**Status**: ✅ Ready for Phase 2 (Full API Implementation)
