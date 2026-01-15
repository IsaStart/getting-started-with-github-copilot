"""Tests for the Mergington High School Activities API"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app, activities

# Create test client
client = TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to initial state before each test"""
    # Store original state
    original_activities = {
        name: {
            "description": activity["description"],
            "schedule": activity["schedule"],
            "max_participants": activity["max_participants"],
            "participants": activity["participants"].copy()
        }
        for name, activity in activities.items()
    }
    
    yield
    
    # Restore original state after test
    for name, activity in activities.items():
        activity["participants"] = original_activities[name]["participants"].copy()


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities_returns_all_activities(self):
        """Test that GET /activities returns all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Basketball Team" in data
    
    def test_get_activities_has_required_fields(self):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_info in data.items():
            assert "description" in activity_info
            assert "schedule" in activity_info
            assert "max_participants" in activity_info
            assert "participants" in activity_info
            assert isinstance(activity_info["participants"], list)


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_successful(self, reset_activities):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Basketball%20Team/signup?email=test@example.com"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Signed up" in data["message"]
        assert "test@example.com" in data["message"]
    
    def test_signup_adds_participant(self, reset_activities):
        """Test that signup actually adds participant to the list"""
        email = "newstudent@mergington.edu"
        response = client.post(
            "/activities/Soccer%20Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        
        # Verify participant was added
        activities_response = client.get("/activities")
        data = activities_response.json()
        assert email in data["Soccer Club"]["participants"]
    
    def test_signup_duplicate_email(self, reset_activities):
        """Test that duplicate signup is rejected"""
        # First signup
        client.post(
            "/activities/Basketball%20Team/signup?email=test@example.com"
        )
        
        # Try same signup again
        response = client.post(
            "/activities/Basketball%20Team/signup?email=test@example.com"
        )
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]
    
    def test_signup_nonexistent_activity(self):
        """Test signup for activity that doesn't exist"""
        response = client.post(
            "/activities/NonExistent%20Activity/signup?email=test@example.com"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_signup_activity_full(self, reset_activities):
        """Test signup when activity is full"""
        # Fill up Basketball Team (max 15)
        for i in range(15):
            email = f"student{i}@mergington.edu"
            client.post(
                f"/activities/Basketball%20Team/signup?email={email}"
            )
        
        # Try to signup when full
        response = client.post(
            "/activities/Basketball%20Team/signup?email=overfull@mergington.edu"
        )
        assert response.status_code == 400
        assert "full" in response.json()["detail"]


class TestUnregisterFromActivity:
    """Tests for POST /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_successful(self, reset_activities):
        """Test successful unregistration from an activity"""
        email = "michael@mergington.edu"
        response = client.post(
            f"/activities/Chess%20Club/unregister?email={email}"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]
        assert email in data["message"]
    
    def test_unregister_removes_participant(self, reset_activities):
        """Test that unregister actually removes participant"""
        email = "michael@mergington.edu"
        
        # Verify they're registered
        activities_response = client.get("/activities")
        assert email in activities_response.json()["Chess Club"]["participants"]
        
        # Unregister
        response = client.post(
            f"/activities/Chess%20Club/unregister?email={email}"
        )
        assert response.status_code == 200
        
        # Verify they're no longer registered
        activities_response = client.get("/activities")
        assert email not in activities_response.json()["Chess Club"]["participants"]
    
    def test_unregister_not_registered(self, reset_activities):
        """Test unregister for student not in activity"""
        response = client.post(
            "/activities/Chess%20Club/unregister?email=notregistered@example.com"
        )
        assert response.status_code == 400
        assert "not registered" in response.json()["detail"]
    
    def test_unregister_nonexistent_activity(self):
        """Test unregister from activity that doesn't exist"""
        response = client.post(
            "/activities/NonExistent%20Activity/unregister?email=test@example.com"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]


class TestRootEndpoint:
    """Tests for GET / endpoint"""
    
    def test_root_redirects(self):
        """Test that root endpoint redirects to static index"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]
