"""
Functional tests for the application
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app
from app.database import Base, get_db
from app.models import Sample, Tasting

# Setup test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_teardown():
    """Setup and teardown for each test"""
    # Create tables before test
    Base.metadata.create_all(bind=engine)
    yield
    # Clear all data after test
    Base.metadata.drop_all(bind=engine)


class TestHealth:
    """Health check tests"""
    
    def test_health_check(self):
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


class TestDashboard:
    """Dashboard tests"""
    
    def test_dashboard_loads(self):
        response = client.get("/")
        assert response.status_code == 200
        assert "Dashboard" in response.text or "dashboard" in response.text


class TestSamples:
    """Sample management tests"""
    
    def test_list_samples(self):
        response = client.get("/samples")
        assert response.status_code == 200
    
    def test_create_sample(self):
        response = client.post("/samples", data={
            "code": "TEST-001",
            "country_code": "CO",
            "origin": "Huila",
            "producer": "Test Producer",
            "harvest_date": "2025-11",
            "variety": "Geisha",
            "altitude": 1800,
            "processing": "Washed",
            "initial_quantity": 100.0,
            "notes": "Test sample"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "TEST-001"
    
    def test_create_duplicate_sample(self):
        # Create first sample
        client.post("/samples", data={
            "code": "TEST-002",
            "country_code": "CO",
            "origin": "Huila",
            "producer": "Test Producer",
            "harvest_date": "2025-11",
            "variety": "Geisha",
            "altitude": 1800,
            "processing": "Washed",
            "initial_quantity": 100.0,
        })
        
        # Try to create duplicate
        response = client.post("/samples", data={
            "code": "TEST-002",
            "country_code": "CO",
            "origin": "Huila",
            "producer": "Test Producer",
            "harvest_date": "2025-11",
            "variety": "Geisha",
            "altitude": 1800,
            "processing": "Washed",
            "initial_quantity": 100.0,
        })
        assert response.status_code == 400
    
    def test_sample_detail(self):
        # Create sample
        response = client.post("/samples", data={
            "code": "TEST-003",
            "country_code": "CO",
            "origin": "Huila",
            "producer": "Test Producer",
            "harvest_date": "2025-11",
            "variety": "Geisha",
            "altitude": 1800,
            "processing": "Washed",
            "initial_quantity": 100.0,
        })
        sample_id = response.json()["id"]
        
        # Get detail
        response = client.get(f"/samples/{sample_id}")
        assert response.status_code == 200
        assert "TEST-003" in response.text


class TestTastings:
    """Tasting/cupping tests"""
    
    def test_create_tasting(self):
        # Create sample
        response = client.post("/samples", data={
            "code": "TEST-TASTE-001",
            "country_code": "CO",
            "origin": "Huila",
            "producer": "Test Producer",
            "harvest_date": "2025-11",
            "variety": "Geisha",
            "altitude": 1800,
            "processing": "Washed",
            "initial_quantity": 100.0,
        })
        sample_id = response.json()["id"]
        
        # Create tasting
        response = client.post(f"/samples/{sample_id}/tastings", data={
            "evaluator": "Juan García",
            "sieve_18": 65.0,
            "sieve_16": 25.0,
            "sieve_14": 10.0,
            "humidity": 11.5,
            "defects_primary": 2,
            "defects_secondary": 1,
            "aroma": 8,
            "acidity": 8,
            "body": 8,
            "flavor": 8,
            "aftertaste": 8,
            "cleanliness": 9,
            "balance": 8,
            "tasting_notes": "Excellent balance",
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "indian_score" in data


class TestShipments:
    """Shipment tests"""
    
    def test_create_shipment(self):
        # Create sample
        response = client.post("/samples", data={
            "code": "TEST-SHIP-001",
            "country_code": "CO",
            "origin": "Huila",
            "producer": "Test Producer",
            "harvest_date": "2025-11",
            "variety": "Geisha",
            "altitude": 1800,
            "processing": "Washed",
            "initial_quantity": 100.0,
        })
        sample_id = response.json()["id"]
        
        # Create shipment
        response = client.post(f"/samples/{sample_id}/shipments", data={
            "quantity": 50.0,
            "destination": "Madrid, Spain",
            "reference": "SHIP-001",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["quantity"] == 50.0
    
    def test_shipment_exceeds_available(self):
        # Create sample
        response = client.post("/samples", data={
            "code": "TEST-SHIP-002",
            "country_code": "CO",
            "origin": "Huila",
            "producer": "Test Producer",
            "harvest_date": "2025-11",
            "variety": "Geisha",
            "altitude": 1800,
            "processing": "Washed",
            "initial_quantity": 100.0,
        })
        sample_id = response.json()["id"]
        
        # Try to shipment more than available
        response = client.post(f"/samples/{sample_id}/shipments", data={
            "quantity": 150.0,
            "destination": "Madrid, Spain",
            "reference": "SHIP-002",
        })
        assert response.status_code == 400


class TestAPI:
    """API endpoint tests"""
    
    def test_api_samples(self):
        response = client.get("/api/samples")
        assert response.status_code == 200
        data = response.json()
        assert "samples" in data
    
    def test_api_sample_detail(self):
        # Create sample
        response = client.post("/samples", data={
            "code": "API-TEST-001",
            "country_code": "CO",
            "origin": "Huila",
            "producer": "Test Producer",
            "harvest_date": "2025-11",
            "variety": "Geisha",
            "altitude": 1800,
            "processing": "Washed",
            "initial_quantity": 100.0,
        })
        sample_id = response.json()["id"]
        
        # Get API detail
        response = client.get(f"/api/samples/{sample_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_id
        assert data["code"] == "API-TEST-001"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
