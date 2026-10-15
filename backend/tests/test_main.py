import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "LabelTruth"

def test_get_survey_and_fssai_stats():
    response = client.get("/api/stats")
    assert response.status_code == 200
    data = response.json()
    assert "key_stats" in data
    assert "fssai_regulations" in data
    assert "harmful_ins_codes" in data
    assert data["sample_size"] == 51

def test_get_demo_presets():
    response = client.get("/api/presets")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 3
    assert data[0]["id"] == "brown-bread"

@patch("app.services.condition_service.condition_validation_service.validate")
def test_validate_condition(mock_validate):
    # Mock offline Gemini response for condition validation
    mock_validate.return_value = {
        "is_valid": True,
        "standardized_name": "Maltitol",
        "reason": "Sugar alcohol polyol with moderate glycemic impact."
    }
    
    response = client.post("/api/validate-condition", json={"condition": "maltitol"})
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] is True
    assert data["standardized_name"] == "Maltitol"

@patch("app.services.chat_service.chat_service.chat")
def test_chat_endpoint(mock_chat):
    # Mock offline Gemini chat response
    mock_chat.return_value = (
        "**Direct Clinical Takeaway**: Maltodextrin causes rapid glycemic spikes.\n"
        "**Key Facts & Regulatory Reality**:\n"
        "• High GI of 105-110.\n"
        "• Used to mask sugar content under FSSAI rules.\n"
        "**Actionable Recommendation**: Choose whole-food alternatives."
    )
    
    payload = {
        "message": "Why avoid maltodextrin?",
        "history": [],
        "user_profile": {"medical_conditions": ["Type-2 Diabetes"]},
        "product_context": None
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert "Direct Clinical Takeaway" in data["reply"]

@patch("app.services.gemini_vision.gemini_vision_service.analyze_label_image")
def test_analyze_label_endpoint(mock_analyze):
    # Mock offline Gemini Vision response
    mock_analyze.return_value = {
        "product_name": "Test Healthy Whole Grain Bread",
        "health_score": 85,
        "personalized_verdict": "SAFE FOR YOU",
        "simple_summary": "Clean whole wheat bread with no added sugars or palm oil.",
        "deceptive_claims_flagged": [],
        "fssai_violations": [],
        "ingredient_breakdown": [
            {
                "ingredient": "Whole Wheat Flour (Atta)",
                "purpose": "Primary Grain",
                "concern_level": "LOW",
                "personalized_warning": "Safe whole grain source"
            }
        ],
        "healthier_alternative": {
            "name": "Local Sourdough Bakery",
            "key_benefit": "Zero emulsifiers",
            "price_comparison": "Comparable",
            "personalized_fit": "100% whole grain"
        }
    }

    dummy_image = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xff\xdb\x00C\x00\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xbf\x00\xff\xd9"
    files = {"image": ("test_label.jpg", dummy_image, "image/jpeg")}
    data = {"user_profile": json.dumps({"medical_conditions": ["Type-2 Diabetes"]})}

    response = client.post("/api/analyze-label", files=files, data=data)
    assert response.status_code == 200
    data = response.json()
    assert data["product_name"] == "Test Healthy Whole Grain Bread"
    assert data["health_score"] == 85
    assert data["personalized_verdict"] == "SAFE FOR YOU"
