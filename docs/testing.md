# Testing & QA Guide - Disaster Response System

## Overview

This document outlines the testing strategy for the Disaster Response System across all phases. It covers unit testing, integration testing, system testing, and user acceptance testing (UAT).

## Testing Pyramid

```
           /\
          /  \
         /____\        E2E Tests (10%)
        /\    /\
       /  \  /  \
      /____\/____\     Integration Tests (30%)
     /\    /\    /\
    /  \  /  \  /  \
   /____\/____\/____\  Unit Tests (60%)
```

## Phase-wise Testing Strategy

### Phase 1: Initialization (Current)
- ✅ Project structure verification
- ✅ Dependency resolution
- ✅ Basic build tests
- ⏳ Health check endpoints

### Phase 2: Backend & Database
- Unit tests for models & schemas
- Database integration tests
- API endpoint tests
- Migration tests

### Phase 3: Mobile SOS Collection
- Component unit tests
- Screen navigation tests
- Form validation tests
- GPS service mocking

### Phase 4: Device-to-Device Communication
- Bluetooth message format tests
- Routing algorithm tests
- Duplicate detection tests
- Network simulation tests

### Phase 5: ML Classification
- Model accuracy tests
- Inference time tests
- Edge case tests
- Integration with backend

### Phase 6: Computer Vision
- Model accuracy tests
- Image processing tests
- Heatmap generation tests
- Performance tests

### Phase 7: Dashboard & Visualization
- React component tests
- Map rendering tests
- Real-time update tests
- Accessibility tests

### Phase 8: Integration & Deployment
- End-to-end workflow tests
- Load testing
- Stress testing
- Security testing

## Unit Testing

### Backend (Python + pytest)

```python
# tests/test_models.py
import pytest
from app.models import Emergency
from datetime import datetime

def test_emergency_creation():
    emergency = Emergency(
        victim_id="mobile_1",
        latitude=28.7041,
        longitude=77.1025,
        description="Building collapsed"
    )
    
    assert emergency.victim_id == "mobile_1"
    assert emergency.latitude == 28.7041
    assert emergency.status == "pending"
    assert emergency.created_at is not None

def test_emergency_status_update():
    emergency = Emergency(victim_id="mobile_1", latitude=0, longitude=0)
    emergency.status = "assigned"
    
    assert emergency.status == "assigned"
    assert emergency.updated_at is not None
```

### Mobile (JavaScript + Jest)

```javascript
// mobile/src/components/SOSForm.test.js
import { render, screen, fireEvent } from '@testing-library/react';
import SOSForm from './SOSForm';

describe('SOS Form Component', () => {
  test('renders form with all fields', () => {
    render(<SOSForm />);
    
    expect(screen.getByLabelText(/emergency description/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /submit/i })).toBeInTheDocument();
  });

  test('validates required fields', () => {
    render(<SOSForm />);
    const submitButton = screen.getByRole('button', { name: /submit/i });
    
    fireEvent.click(submitButton);
    
    expect(screen.getByText(/description is required/i)).toBeInTheDocument();
  });

  test('submits form with valid data', async () => {
    const onSubmit = jest.fn();
    render(<SOSForm onSubmit={onSubmit} />);
    
    fireEvent.change(screen.getByLabelText(/description/i), {
      target: { value: 'Building collapsed' }
    });
    fireEvent.click(screen.getByRole('button', { name: /submit/i }));
    
    expect(onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({ description: 'Building collapsed' })
    );
  });
});
```

### Dashboard (React + Vitest)

```javascript
// dashboard/src/components/EmergencyMap.test.jsx
import { render, screen } from '@testing-library/react';
import EmergencyMap from './EmergencyMap';

describe('Emergency Map', () => {
  test('renders map component', () => {
    render(<EmergencyMap />);
    expect(screen.getByRole('region')).toBeInTheDocument();
  });

  test('displays emergency markers', () => {
    const emergencies = [
      { id: '1', lat: 28.7, lon: 77.1, severity: 9 },
      { id: '2', lat: 28.8, lon: 77.2, severity: 7 }
    ];
    
    render(<EmergencyMap emergencies={emergencies} />);
    
    const markers = screen.getAllByTestId('marker');
    expect(markers).toHaveLength(2);
  });
});
```

## Integration Testing

### Backend API Tests

```python
# tests/integration/test_sos_api.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

@pytest.fixture
def sample_sos():
    return {
        "victim_id": "mobile_1",
        "latitude": 28.7041,
        "longitude": 77.1025,
        "description": "Building collapsed"
    }

def test_submit_sos(sample_sos):
    response = client.post("/api/sos", json=sample_sos)
    
    assert response.status_code == 201
    assert response.json()['status'] == 'success'
    assert 'emergency_id' in response.json()['data']

def test_retrieve_sos(sample_sos):
    # Submit
    submit_response = client.post("/api/sos", json=sample_sos)
    emergency_id = submit_response.json()['data']['emergency_id']
    
    # Retrieve
    get_response = client.get(f"/api/sos/{emergency_id}")
    
    assert get_response.status_code == 200
    assert get_response.json()['data']['victim_id'] == "mobile_1"

def test_list_active_emergencies(sample_sos):
    # Submit multiple
    for i in range(3):
        sample_sos['victim_id'] = f"mobile_{i}"
        client.post("/api/sos", json=sample_sos)
    
    # List
    response = client.get("/api/sos/active?limit=10")
    
    assert response.status_code == 200
    assert len(response.json()['data']['emergencies']) >= 3
```

### Mobile-Backend Communication Tests

```javascript
// mobile/src/services/apiService.test.js
import apiService from './apiService';
import fetchMock from 'jest-fetch-mock';

fetchMock.enableMocks();

describe('API Service', () => {
  beforeEach(() => {
    fetchMock.resetMocks();
  });

  test('submits SOS to backend', async () => {
    fetchMock.mockResponseOnce(JSON.stringify({
      status: 'success',
      data: { emergency_id: 'sos_123' }
    }));

    const sos = {
      description: 'Building collapsed',
      latitude: 28.7041,
      longitude: 77.1025
    };

    const result = await apiService.submitSOS(sos);

    expect(result.emergency_id).toBe('sos_123');
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining('/api/sos'),
      expect.any(Object)
    );
  });
});
```

## System Testing

### End-to-End Workflow

#### Scenario 1: Complete SOS Flow (Phase 3)

```
1. User launches mobile app
2. App displays home screen
3. User clicks "Report Emergency"
4. Form loads with location pre-filled
5. User enters description and selects type
6. User attaches photos
7. User submits form
8. Form validates
9. Message stored locally
10. Backend API called (if online)
11. Confirmation displayed
12. Backend stores in database
13. ML classification runs
14. Priority assigned
15. Dashboard updated
16. Rescue team notified
```

**Test Script**:
```python
def test_complete_sos_workflow():
    # Start mobile app
    app.start()
    
    # Navigate to SOS form
    app.click('report_emergency_button')
    form = app.find_element('sos_form')
    assert form.is_displayed()
    
    # Fill form
    app.fill_text('description', 'Building collapsed, people trapped')
    app.select_dropdown('emergency_type', 'structural_collapse')
    
    # Submit
    app.click('submit_button')
    
    # Verify confirmation
    assert app.find_element('confirmation_message').is_displayed()
    
    # Check backend
    response = backend_api.get('/api/sos/active')
    assert len(response['data']['emergencies']) > 0
```

## Load Testing

### Backend Stress Test

```python
# tests/load/load_test.py
import locust

class DisasterResponseTasks(locust.HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def submit_sos(self):
        self.client.post('/api/sos', json={
            'victim_id': f'mobile_{random.randint(1, 1000)}',
            'latitude': 28.7041 + random.uniform(-0.1, 0.1),
            'longitude': 77.1025 + random.uniform(-0.1, 0.1),
            'description': 'Emergency message'
        })

    @task(2)
    def list_emergencies(self):
        self.client.get('/api/sos/active')

    @task(1)
    def get_priority_queue(self):
        self.client.get('/api/priority-queue')

# Run: locust -f load_test.py --headless -u 100 -r 10
```

## Performance Testing

### Database Query Performance

```python
def test_priority_queue_performance():
    # Insert 10,000 emergencies
    emergencies = create_test_emergencies(10000)
    db.insert_many(emergencies)
    
    # Time query
    import time
    start = time.time()
    
    response = client.get('/api/priority-queue?limit=50')
    
    elapsed = time.time() - start
    
    assert elapsed < 0.5  # Must complete in 500ms
    assert response.status_code == 200
```

### ML Inference Performance

```python
def test_classification_inference_speed():
    classifier = load_classifier('models/classifier.joblib')
    
    test_messages = load_test_messages(1000)
    
    import time
    start = time.time()
    
    for msg in test_messages:
        classifier.classify(msg)
    
    elapsed = time.time() - start
    avg_time = elapsed / len(test_messages)
    
    assert avg_time < 0.1  # < 100ms per message
```

## Security Testing

### Input Validation

```python
def test_sos_input_validation():
    # Missing required field
    response = client.post('/api/sos', json={
        'victim_id': 'mobile_1',
        'latitude': 28.7041
        # Missing longitude
    })
    assert response.status_code == 400

    # Invalid latitude
    response = client.post('/api/sos', json={
        'victim_id': 'mobile_1',
        'latitude': 'not_a_number',
        'longitude': 77.1025,
        'description': 'Building collapsed'
    })
    assert response.status_code == 400

    # SQL injection attempt
    response = client.post('/api/sos', json={
        'victim_id': "mobile_1'; DROP TABLE emergencies; --",
        'latitude': 28.7041,
        'longitude': 77.1025,
        'description': 'Building collapsed'
    })
    assert response.status_code == 400
```

### Authentication Tests (Phase 8)

```python
def test_dashboard_requires_authentication():
    response = client.get('/dashboard')
    assert response.status_code == 401
    
    response = client.get(
        '/dashboard',
        headers={'Authorization': 'Bearer invalid_token'}
    )
    assert response.status_code == 401
```

## Testing Tools & Frameworks

### Backend Testing
- **pytest**: Python testing framework
- **pytest-asyncio**: For async tests
- **TestClient**: FastAPI test client
- **unittest.mock**: Mocking library

### Mobile Testing
- **Jest**: JavaScript testing
- **React Native Testing Library**: Component testing
- **Detox**: E2E testing for React Native

### API Testing
- **Postman**: Manual API testing
- **Insomnia**: Alternative API client
- **pytest-httpserver**: Mock HTTP server

### Load Testing
- **Locust**: Load/stress testing
- **Apache JMeter**: Performance testing

### Code Quality
- **Pylint**: Python linting
- **ESLint**: JavaScript linting
- **pytest-cov**: Coverage reports

## CI/CD Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.10
      
      - name: Install backend dependencies
        run: |
          pip install -r backend/requirements.txt
      
      - name: Run backend tests
        run: |
          pytest backend/tests/ --cov=backend/app
      
      - name: Set up Node
        uses: actions/setup-node@v2
        with:
          node-version: 18
      
      - name: Install mobile dependencies
        run: |
          cd mobile && npm install
      
      - name: Run mobile tests
        run: |
          cd mobile && npm test -- --coverage
      
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

## Test Data Management

### Seed Database for Testing

```python
def seed_test_data():
    emergencies = [
        {
            'victim_id': 'mobile_1',
            'latitude': 28.7041,
            'longitude': 77.1025,
            'description': 'Building collapsed',
            'emergency_type': 'structural_collapse',
            'severity_score': 9.0
        },
        # ... more test data
    ]
    
    for sos in emergencies:
        db.insert_emergency(sos)
```

## Known Issues & Limitations

### Phase 1
- ML/CV models not yet trained
- Communication not yet implemented
- Dashboard UI not yet built

### Testing Constraints
- Mobile testing requires emulator/device
- CV testing requires GPU
- Load testing requires resources

## Continuous Improvement

- Monthly review of test coverage
- Quarterly update of test data
- Feedback integration from UAT
- Performance baseline monitoring

---

**Version**: 1.0  
**Phase**: 1 (Test Planning)  
**Last Updated**: August 2026  
**Status**: ✅ Ready for Phase 2 (Automated Testing)
