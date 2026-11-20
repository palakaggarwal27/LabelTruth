import pytest
import json
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app, BASE_PRODUCT_CACHE, AUDIT_CACHE, normalize_name_key
from app.schemas.analysis import LabelAnalysisResult, NutritionCardAnalysis, IngredientItem
from app.schemas.user_profile import UserProfile

client = TestClient(app)

@pytest.fixture
def mock_product():
    return LabelAnalysisResult(
        product_name="Chocolate Malt Energy Drink",
        health_score=68,
        personalized_verdict="SAFE FOR YOU",
        simple_summary="Malt beverage mix with added vitamins.",
        deceptive_claims_flagged=[],
        fssai_violations=[],
        ingredient_breakdown=[
            IngredientItem(ingredient="Sugar", purpose="Sweetener", concern_level="HIGH", personalized_warning=""),
            IngredientItem(ingredient="Maltodextrin", purpose="Carbohydrate", concern_level="HIGH", personalized_warning=""),
            IngredientItem(ingredient="Soy Lecithin", purpose="Emulsifier", concern_level="MEDIUM", personalized_warning="")
        ],
        nutrition_card=NutritionCardAnalysis(
            serving_size="100g",
            calories_kcal=380.0,
            total_fat_g=2.5,
            saturated_fat_g=1.1,
            trans_fat_g=0.0,
            total_carbs_g=82.0,
            added_sugars_g=42.0,
            sodium_mg=310.0,
            breakdown=[]
        ),
        healthier_alternative={
            "name": "Organic Sprouted Ragi Mix",
            "key_benefit": "Zero refined sugar",
            "price_comparison": "Comparable",
            "personalized_fit": "Suitable for blood sugar control"
        },
        clean_alternatives=[],
        nutrient_integrity={},
        is_food_label=True,
        label_type="FULL_PANEL"
    )

@pytest.fixture
def household_profiles():
    return [
        {
            "id": "profile_self",
            "name": "Self",
            "dietary_preferences": ["Vegetarian"],
            "medical_conditions": [],
            "allergies": [],
            "custom_avoid_list": ["Palm Oil"]
        },
        {
            "id": "profile_dad",
            "name": "Dad",
            "dietary_preferences": ["Vegetarian"],
            "medical_conditions": ["Type 2 Diabetes", "Hypertension"],
            "allergies": [],
            "custom_avoid_list": ["Liquid Glucose"]
        },
        {
            "id": "profile_kid",
            "name": "Kid",
            "dietary_preferences": [],
            "medical_conditions": [],
            "allergies": ["Soy Allergy"],
            "custom_avoid_list": []
        }
    ]

def test_multi_profile_scan_success(mock_product, household_profiles):
    # Prime the base cache so no external Gemini call is needed
    BASE_PRODUCT_CACHE[normalize_name_key(mock_product.product_name)] = mock_product

    payload = {
        "query": mock_product.product_name,
        "profiles": json.dumps(household_profiles),
        "pincode": "110001"
    }

    response = client.post("/api/smart-scan-multi-profile", data=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["product_name"] == mock_product.product_name
    assert len(data["profiles_audited"]) == 3

    # Dad (Diabetes + High Added Sugar 42g) must receive penalty and AVOID verdict
    dad_insight = next(p for p in data["profiles_audited"] if p["profile_id"] == "profile_dad")
    assert dad_insight["personalized_verdict"] == "AVOID (VIOLATES PROFILE)"
    assert dad_insight["health_score"] < mock_product.health_score

    # Kid (Soy Allergy + Soy Lecithin present) must receive AVOID
    kid_insight = next(p for p in data["profiles_audited"] if p["profile_id"] == "profile_kid")
    assert kid_insight["personalized_verdict"] == "AVOID (VIOLATES PROFILE)"

    # Household verdict must be UNSAFE
    assert data["household_verdict"] == "UNSAFE FOR FAMILY MEMBERS"
    assert "Dad" in data["household_summary"] or "Kid" in data["household_summary"]

def test_multi_profile_max_limit_enforced():
    four_profiles = [
        {"id": f"p{i}", "name": f"Member {i}", "dietary_preferences": [], "medical_conditions": [], "allergies": [], "custom_avoid_list": []}
        for i in range(4)
    ]
    payload = {
        "query": "Rolled Oats",
        "profiles": json.dumps(four_profiles),
        "pincode": "110001"
    }
    response = client.post("/api/smart-scan-multi-profile", data=payload)
    # Backend slices to max 3
    assert response.status_code == 200
    data = response.json()
    assert len(data["profiles_audited"]) == 3

def test_dual_key_caching_after_multi_scan(mock_product, household_profiles):
    BASE_PRODUCT_CACHE[normalize_name_key(mock_product.product_name)] = mock_product

    # Run multi-profile audit
    payload = {
        "query": mock_product.product_name,
        "profiles": json.dumps(household_profiles),
        "pincode": "110001"
    }
    client.post("/api/smart-scan-multi-profile", data=payload)

    # Now verify Dad's query in single scan endpoint hits cache directly with Dad's specific score
    dad_prof = household_profiles[1]
    single_res = client.post(
        "/api/smart-scan",
        data={
            "query": mock_product.product_name,
            "user_profile": json.dumps(dad_prof),
            "pincode": "110001"
        }
    )
    assert single_res.status_code == 200
    single_data = single_res.json()
    assert single_data["personalized_verdict"] == "AVOID (VIOLATES PROFILE)"

def test_evaluate_profile_safety_recalculates_score(mock_product, household_profiles):
    dad_prof = household_profiles[1]
    response = client.post(
        "/api/evaluate-profile-safety",
        json={
            "product_name": mock_product.product_name,
            "base_product": mock_product.model_dump(),
            "active_profile": dad_prof
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "adjusted_health_score" in data
    assert data["adjusted_health_score"] < mock_product.health_score
    assert data["personalized_verdict"] == "AVOID (VIOLATES PROFILE)"
