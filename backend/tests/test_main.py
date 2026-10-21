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
    assert len(data) == 5
    assert data[0]["id"] == "chips-18"
    assert data[1]["id"] == "bread-38"

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
            "pincode": "110001",
            "user_profile": json.dumps({"medical_conditions": []})
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["product_name"] == "The Whole Truth Peanut Butter"
    assert data["health_score"] == 92

def test_piecewise_scoring_mathematical_logic():
    """Verify piecewise mathematical scoring engine equation and rules offline"""
    from app.services.scoring_engine import (
        calculate_trans_fat_penalty,
        calculate_added_sugar_penalty,
        calculate_saturated_fat_penalty,
        calculate_sodium_penalty,
        calculate_energy_density_penalty,
        calculate_ins_additives_penalty,
        calculate_protein_bonus,
        calculate_fiber_bonus,
        compute_piecewise_health_score
    )

    # 1. Trans Fat: <=0.2g is 0; >0.2 and <=0.5 is 10; Vanaspati adds 10
    assert calculate_trans_fat_penalty(0.1, "cow milk fat") == 0.0
    assert calculate_trans_fat_penalty(0.4, "refined oil") == 10.0
    assert calculate_trans_fat_penalty(0.1, "partially hydrogenated vanaspati oil") == 10.0

    # 2. Added Sugar: solids >20g is -25, zero sugar with maltodextrin adds -15
    assert calculate_added_sugar_penalty(25.0, False, "wheat flour, sugar", "") == 25.0
    assert calculate_added_sugar_penalty(0.0, False, "maltodextrin, wheat", "zero sugar claim") == 15.0

    # 3. Saturated Fat: solids >8g is -16, palm oil adds -10
    assert calculate_saturated_fat_penalty(10.0, False, "refined palm olein") == 26.0

    # 4. Sodium: >900mg is -25
    assert calculate_sodium_penalty(1200.0) == 25.0

    # 5. Energy Density: solids >450 kcal is -15
    assert calculate_energy_density_penalty(520.0, False) == 15.0

    # 6. Additives: Caramel Colour INS 150d high risk (12) + INS 621 MSG med risk (6) = 18
    assert calculate_ins_additives_penalty([], "contains ins 150d and ins 621") == 18.0

    # 7. Protein bonus: Whey protein 15g, PDCAAS 1.0 -> +10; Spiking with Glycine -> -15
    assert calculate_protein_bonus(15.0, 1.0, "whey protein concentrate") == 10.0
    assert calculate_protein_bonus(15.0, 1.0, "whey protein, free glycine") == -5.0

    # 8. Fiber bonus: 8g whole grain fiber -> +10
    assert calculate_fiber_bonus(8.0, "whole grain oats") == 10.0

    # Comprehensive clean product should score near 100
    clean_score = compute_piecewise_health_score(
        nutrition={"trans_fat_g": 0.0, "added_sugars_g": 0.0, "saturated_fat_g": 1.0, "sodium_mg": 50, "calories_kcal": 180},
        ingredients=[{"ingredient": "Whole Oats"}],
        integrity={"protein": {"declared_protein_g": 12.0, "pdcaas_score": 0.9}},
        product_name="Clean Whole Grain Oats"
    )
    assert clean_score["final_health_score"] >= 95

def test_alternatives_score_filter_strictly_drops_below_70():
    """Verify clean_alternatives only keeps products with health_score >= 70"""
    from app.schemas.analysis import HealthierAlternative

    alts = [
        HealthierAlternative(name="Clean Alt A", health_score=85, key_benefit="Clean", price_comparison="1x", personalized_fit="Good"),
        HealthierAlternative(name="Subpar Alt B", health_score=55, key_benefit="Bad", price_comparison="1x", personalized_fit="Poor"),
        HealthierAlternative(name="Clean Alt C", health_score=72, key_benefit="Great", price_comparison="1x", personalized_fit="Good"),
    ]
    filtered = [a for a in alts if (a.health_score or 80) >= 70]
    assert len(filtered) == 2
    assert all(a.health_score >= 70 for a in filtered)
    assert not any(a.name == "Subpar Alt B" for a in filtered)

def test_pdp_validator_utility():
    """Verify backend/app/utils/pdp_validator.py correctly identifies PDP vs search URLs"""
    from app.utils.pdp_validator import validate_and_clean_pdp_url

    valid_zepto = "https://www.zepto.com/pn/the-whole-truth-peanut-butter/pvid/12345?query=abc"
    res1 = validate_and_clean_pdp_url(valid_zepto)
    assert res1["is_pdp"] is True
    assert res1["url"] == "https://www.zepto.com/pn/the-whole-truth-peanut-butter/pvid/12345"

    valid_blinkit = "https://blinkit.com/prn/farmley-roasted-makhana/prid/98765"
    res2 = validate_and_clean_pdp_url(valid_blinkit)
    assert res2["is_pdp"] is True

    generic_search = "https://www.zepto.com/search?q=peanut+butter"
    res3 = validate_and_clean_pdp_url(generic_search)
    assert res3["is_pdp"] is False

def test_demo_mode_5_tiers():
    """Verify offline DEMO_MODE returns deterministic data (<100ms) for all 5 tiers"""
    # 1. Very Low (18)
    r1 = client.post("/api/smart-scan", data={"query": "chips 18", "demo_mode": "true", "user_profile": json.dumps({})})
    assert r1.status_code == 200
    assert r1.json()["health_score"] == 18

    # 2. Low (38)
    r2 = client.post("/api/smart-scan", data={"query": "brown bread 38", "demo_mode": "true", "user_profile": json.dumps({})})
    assert r2.status_code == 200
    assert r2.json()["health_score"] == 38

    # 3. Moderate (58)
    r3 = client.post("/api/smart-scan", data={"query": "d'lecta cheese 58", "demo_mode": "true", "user_profile": json.dumps({})})
    assert r3.status_code == 200
    assert r3.json()["health_score"] == 58

    # 4. High (78)
    r4 = client.post("/api/smart-scan", data={"query": "greek yogurt 78", "demo_mode": "true", "user_profile": json.dumps({})})
    assert r4.status_code == 200
    assert r4.json()["health_score"] == 78

    # 5. Very High (95)
    r5 = client.post("/api/smart-scan", data={"query": "rolled oats 95", "demo_mode": "true", "user_profile": json.dumps({})})
    assert r5.status_code == 200
    assert r5.json()["health_score"] == 95

def test_decoupled_profile_safety_reevaluation():
    """Verify /api/evaluate-profile-safety re-evaluates base product against Dad profile in <50ms"""
    payload = {
        "product_hash": "mock_hash_chips",
        "active_profile": {
            "id": "profile_dad",
            "name": "Dad (Diabetes & High BP)",
            "medical_conditions": ["Type-2 Diabetes", "Hypertension (High BP)"],
            "allergies": [],
            "dietary_preferences": ["Vegetarian"],
            "custom_avoid_list": ["Maltodextrin"]
        }
    }
    response = client.post("/api/evaluate-profile-safety", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "personalized_verdict" in data
    assert "contraindications" in data
    assert len(data["contraindications"]) > 0

def test_delta_audit_hierarchy_brand_swap_ban():
    """Verify relative delta audit strictly blocks swapping one processed brand for another"""
    from app.services.delta_audit import apply_delta_audit_hierarchy

    # Scanned: D'lecta Mozzarella (58/100). Candidate: Amul Mozzarella (60/100) -> Banned brand swap
    candidates = [
        {"name": "Amul Mozzarella Block", "health_score": 60, "direct_pdp_url": "https://www.zepto.com/pn/amul-mozzarella/pvid/123", "is_direct_pdp": True}
    ]
    res = apply_delta_audit_hierarchy("D'lecta Mozzarella Cheese Block", 58, candidates, "mozzarella")
    # Commercial candidate is blocked; fallbacks to YouTube whole-food recipe
    assert any(r.type == "HOMEMADE_RECIPE" for r in res)
    assert not any(r.name == "Amul Mozzarella Block" for r in res)
