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
    assert "national_stats" in data
    assert "fssai_regulations" in data
    assert "harmful_ins_codes" in data
    assert data["sample_size"] == 51
    assert data["national_sample_size"] == 23491

def test_get_demo_presets():
    response = client.get("/api/presets")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 3
    assert data[0]["id"] == "brown-bread"

@patch("app.services.condition_service.condition_validation_service.validate")
def test_validate_condition(mock_validate):
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
def test_chat_endpoint_with_household_profile(mock_chat):
    mock_chat.return_value = (
        "**Direct Clinical Takeaway**: For Dad with Type-2 Diabetes and High BP, avoid this product.\n"
        "**Key Facts & Regulatory Reality**:\n"
        "• High Sodium and Palm Oil elevate hypertension risks.\n"
        "• Maltodextrin causes glycemic surges.\n"
        "**Actionable Recommendation**: Replace with unsalted roasted nuts."
    )
    
    payload = {
        "message": "Is this safe for Dad?",
        "history": [],
        "user_profile": {
            "name": "Dad",
            "medical_conditions": ["Type-2 Diabetes", "Hypertension (High BP)"],
            "allergies": [],
            "dietary_preferences": ["Vegetarian"],
            "custom_avoid_list": ["Maltodextrin"]
        },
        "product_context": {
            "product_name": "Commercial Snack Mix",
            "health_score": 30,
            "personalized_verdict": "AVOID (VIOLATES PROFILE)",
            "simple_summary": "High sodium, fried in palm oil.",
            "deceptive_claims_flagged": ["0% Cholesterol claim disguises 35% palm oil"],
            "fssai_violations": [],
            "ingredient_breakdown": [],
            "healthier_alternative": {
                "name": "Roasted Makhana",
                "key_benefit": "Zero palm oil",
                "price_comparison": "Comparable",
                "personalized_fit": "Low glycemic and sodium"
            }
        }
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert "Direct Clinical Takeaway" in data["reply"]

@patch("app.services.gemini_vision.gemini_vision_service.analyze_label_image")
def test_analyze_label_endpoint_success(mock_analyze):
    mock_analyze.return_value = {
        "product_name": "Test Healthy Whole Grain Bread",
        "health_score": 85,
        "personalized_verdict": "SAFE FOR YOU",
        "simple_summary": "Clean whole wheat bread with no added sugars or palm oil.",
        "deceptive_claims_flagged": [],
        "fssai_violations": [],
        "is_food_label": True,
        "label_type": "FULL_PANEL",
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
        },
        "clean_alternatives": [],
        "nutrient_integrity": {
            "protein": {
                "declared_protein_g": 9.0,
                "usable_protein_g": 4.5,
                "pdcaas_score": 0.5,
                "primary_sources": ["Whole Wheat"],
                "protein_to_calorie_percent": 15.0,
                "amino_spiking_risk": False
            },
            "fiber_type": "Whole Grain",
            "palm_oil_present": False,
            "hidden_sugars_flagged": [],
            "sodium_and_preservatives_risk": "Low",
            "claims_matrix": []
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

@patch("app.services.gemini_vision.gemini_vision_service.analyze_label_image")
def test_analyze_label_rejects_irrelevant_image(mock_analyze):
    mock_analyze.return_value = {
        "product_name": "Unknown",
        "health_score": 0,
        "personalized_verdict": "CAUTION",
        "simple_summary": "Not a food item.",
        "deceptive_claims_flagged": [],
        "fssai_violations": [],
        "is_food_label": False,
        "label_type": "NOT_A_LABEL",
        "ingredient_breakdown": [],
        "healthier_alternative": {
            "name": "N/A",
            "key_benefit": "N/A",
            "price_comparison": "N/A",
            "personalized_fit": "N/A"
        }
    }

    dummy_image = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00"
    files = {"image": ("cat.jpg", dummy_image, "image/jpeg")}
    data = {"user_profile": json.dumps({})}

    response = client.post("/api/analyze-label", files=files, data=data)
    assert response.status_code == 400
    detail = response.json().get("detail", "")
    assert "PRODUCT_NOT_VISIBLE" in detail

@patch("app.services.tinyfish_service.tinyfish_service.search_and_fetch_bop")
@patch("app.services.gemini_vision.gemini_vision_service.analyze_text_query")
def test_smart_scan_text_fallback(mock_text_query, mock_tinyfish):
    mock_tinyfish.return_value = "Ingredients: 100% Roasted Peanuts, Sea Salt."
    mock_text_query.return_value = {
        "product_name": "The Whole Truth Peanut Butter",
        "health_score": 92,
        "personalized_verdict": "SAFE FOR YOU",
        "simple_summary": "Clean 1-ingredient peanut butter without palm oil or hydrogenated fats.",
        "deceptive_claims_flagged": [],
        "fssai_violations": [],
        "is_food_label": True,
        "label_type": "FULL_PANEL",
        "ingredient_breakdown": [
            {
                "ingredient": "Roasted Peanuts",
                "purpose": "Primary Nut",
                "concern_level": "LOW",
                "personalized_warning": "High protein natural source"
            }
        ],
        "healthier_alternative": {
            "name": "Pintola All Natural",
            "key_benefit": "Zero sugar",
            "price_comparison": "Comparable",
            "personalized_fit": "Clean fit"
        }
    }

    response = client.post(
        "/api/smart-scan",
        data={
            "query": "The Whole Truth Peanut Butter",
            "user_profile": json.dumps({"medical_conditions": []})
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["product_name"] == "The Whole Truth Peanut Butter"
    assert data["health_score"] == 92
