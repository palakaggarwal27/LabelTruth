import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.analysis import LabelAnalysisResult, NutritionCardAnalysis, IngredientItem, HealthierAlternative
from app.schemas.user_profile import UserProfile
from app.services.compare_service import compare_service, COMPARE_CACHE

client = TestClient(app)

@pytest.fixture
def sample_product_a():
    return {
        "product_name": "Organic Whole Grain Rolled Oats",
        "health_score": 88,
        "personalized_verdict": "SAFE FOR YOU",
        "simple_summary": "100% whole grain rolled oats with no added sugars or preservatives.",
        "deceptive_claims_flagged": [],
        "fssai_violations": [],
        "ingredient_breakdown": [
            {"ingredient": "Rolled Oats", "purpose": "Grain base", "concern_level": "LOW", "personalized_warning": ""}
        ],
        "nutrition_card": {
            "serving_size": "100g",
            "calories_kcal": 389.0,
            "total_fat_g": 6.9,
            "saturated_fat_g": 1.2,
            "trans_fat_g": 0.0,
            "total_carbs_g": 66.0,
            "added_sugars_g": 0.0,
            "sodium_mg": 2.0,
            "breakdown": []
        },
        "healthier_alternative": {
            "name": "Steel Cut Oats",
            "key_benefit": "Even lower glycemic index",
            "price_comparison": "Comparable",
            "personalized_fit": "Excellent for blood sugar"
        },
        "clean_alternatives": [],
        "nutrient_integrity": {},
        "is_food_label": True,
        "label_type": "FULL_PANEL"
    }

@pytest.fixture
def sample_product_b():
    return {
        "product_name": "Sugar Frosted Breakfast Flakes",
        "health_score": 35,
        "personalized_verdict": "AVOID (VIOLATES PROFILE)",
        "simple_summary": "Ultra-processed corn flakes coated in inverted sugar syrup and maltodextrin.",
        "deceptive_claims_flagged": ["Claims High Energy while concealing 38g added sugar"],
        "fssai_violations": ["Misleading wholesome grains front-of-pack claim"],
        "ingredient_breakdown": [
            {"ingredient": "Milled Corn", "purpose": "Grain base", "concern_level": "LOW", "personalized_warning": ""},
            {"ingredient": "Sugar", "purpose": "Sweetener", "concern_level": "HIGH", "personalized_warning": "Elevates glycemic spike"},
            {"ingredient": "Maltodextrin", "purpose": "Bulking agent", "concern_level": "HIGH", "personalized_warning": "Extreme GI index"}
        ],
        "nutrition_card": {
            "serving_size": "100g",
            "calories_kcal": 410.0,
            "total_fat_g": 1.5,
            "saturated_fat_g": 0.4,
            "trans_fat_g": 0.0,
            "total_carbs_g": 88.0,
            "added_sugars_g": 38.0,
            "sodium_mg": 520.0,
            "breakdown": []
        },
        "healthier_alternative": {
            "name": "Millet Muesli No Added Sugar",
            "key_benefit": "Zero refined sugar",
            "price_comparison": "Comparable",
            "personalized_fit": "Suitable for diabetics"
        },
        "clean_alternatives": [],
        "nutrient_integrity": {},
        "is_food_label": True,
        "label_type": "FULL_PANEL"
    }

@pytest.fixture
def sample_profile():
    return {
        "id": "profile_test",
        "name": "Test User",
        "medical_conditions": ["Type 2 Diabetes", "Hypertension"],
        "allergies": [],
        "dietary_preferences": ["Vegetarian"],
        "custom_avoid_list": ["Palm Oil"]
    }

def test_compare_products_endpoint_success(sample_product_a, sample_product_b, sample_profile):
    payload = {
        "product_a": sample_product_a,
        "product_b": sample_product_b,
        "user_profile": sample_profile,
        "pincode": "110001"
    }

    response = client.post("/api/compare-products", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["winner"] in ["PRODUCT_A", "PRODUCT_B", "TIE", "NEITHER_RECOMMENDED"]
    assert "verdict_title" in data
    assert "verdict_summary" in data
    assert "personalized_impact" in data
    assert isinstance(data["key_tradeoffs"], list)
    assert len(data["dimension_breakdown"]) >= 3
    assert data["score_diff"] == 53

def test_compare_caching(sample_product_a, sample_product_b, sample_profile):
    payload = {
        "product_a": sample_product_a,
        "product_b": sample_product_b,
        "user_profile": sample_profile,
        "pincode": "110001"
    }

    # Call 1
    resp1 = client.post("/api/compare-products", json=payload)
    assert resp1.status_code == 200
    data1 = resp1.json()

    # Call 2 (should hit cache)
    resp2 = client.post("/api/compare-products", json=payload)
    assert resp2.status_code == 200
    data2 = resp2.json()

    assert data1["verdict_title"] == data2["verdict_title"]
    assert data1["winner"] == data2["winner"]

def test_compare_algorithmic_fallback(sample_product_a, sample_product_b, sample_profile):
    prod_a = LabelAnalysisResult(**sample_product_a)
    prod_b = LabelAnalysisResult(**sample_product_b)
    prof = UserProfile(**sample_profile)

    res = compare_service._algorithmic_fallback(prod_a, prod_b, prof)
    assert res.winner == "PRODUCT_A"
    assert res.score_diff == 53
    assert len(res.dimension_breakdown) == 3
    assert res.dimension_breakdown[0].category == "Nutritional Density"
