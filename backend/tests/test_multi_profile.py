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

def test_multi_profile_max_limit_enforced(mock_product):
    BASE_PRODUCT_CACHE[normalize_name_key(mock_product.product_name)] = mock_product
    four_profiles = [
        {"id": f"p{i}", "name": f"Member {i}", "dietary_preferences": [], "medical_conditions": [], "allergies": [], "custom_avoid_list": []}
        for i in range(4)
    ]
    payload = {
        "query": mock_product.product_name,
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

def test_distinct_evaluations_and_no_self_contamination(mock_product, household_profiles):
    """
    Ensures:
    1. Single scan for Dad/Self does NOT contaminate base cache or copy verdicts to other profiles.
    2. Profiles with no matching contraindications receive distinct, non-penalized scores and verdicts.
    """
    clean_item = mock_product.model_copy(deep=True)
    clean_item.product_name = "Whole Grain Multi Crisp"
    clean_item.health_score = 75
    clean_item.base_health_score = 75
    clean_item.personalized_verdict = "SAFE FOR YOU"
    clean_item.ingredient_breakdown = [
        IngredientItem(ingredient="Whole Wheat", purpose="Grain", concern_level="LOW", personalized_warning=""),
        IngredientItem(ingredient="Sugar", purpose="Sweetener", concern_level="HIGH", personalized_warning=""),
        IngredientItem(ingredient="Salt", purpose="Flavor", concern_level="LOW", personalized_warning="")
    ]
    clean_item.nutrition_card.added_sugars_g = 8.0
    clean_item.nutrition_card.sodium_mg = 450.0

    # Step 1: Prime cache with an audit
    dad_prof = household_profiles[1]
    BASE_PRODUCT_CACHE[normalize_name_key(clean_item.product_name)] = clean_item

    # Step 2: Run multi-profile scan for [Self, Dad, Kid]
    # Self: Vegetarian, avoid Palm Oil (0 violations in this product)
    # Dad: Diabetes + Hypertension (8g sugar > 5g -> Diabetes violation, 450mg sodium > 400 -> High BP violation)
    # Kid: Soy allergy (0 violations in this product, no soy present)
    response = client.post(
        "/api/smart-scan-multi-profile",
        data={
            "query": clean_item.product_name,
            "profiles": json.dumps(household_profiles),
            "pincode": "110001"
        }
    )
    assert response.status_code == 200
    data = response.json()

    dad_res = next(p for p in data["profiles_audited"] if p["profile_id"] == "profile_dad")
    self_res = next(p for p in data["profiles_audited"] if p["profile_id"] == "profile_self")
    kid_res = next(p for p in data["profiles_audited"] if p["profile_id"] == "profile_kid")

    # Dad must have AVOID or CAUTION and reduced score compared to base (75)
    assert dad_res["personalized_verdict"] in ["AVOID (VIOLATES PROFILE)", "CAUTION"]
    assert dad_res["health_score"] < 75
    assert len(dad_res["contraindications"]) > 0

    # Self must have SAFE FOR YOU and healthy score (un-penalized, NO Dad violation copying)
    assert self_res["personalized_verdict"] == "SAFE FOR YOU"
    assert self_res["health_score"] >= 70
    assert len(self_res["contraindications"]) == 0

    # Kid must have SAFE FOR YOU and healthy score (un-penalized, NO Dad violation copying)
    assert kid_res["personalized_verdict"] == "SAFE FOR YOU"
    assert kid_res["health_score"] >= 70
    assert len(kid_res["contraindications"]) == 0

    # Ingredients for Kid and Self must NOT carry Dad's personalized warnings
    kid_sugar = next(i for i in kid_res["ingredient_warnings"] if i["ingredient"] == "Sugar")
    assert kid_sugar["personalized_warning"] == ""

    self_sugar = next(i for i in self_res["ingredient_warnings"] if i["ingredient"] == "Sugar")
    assert self_sugar["personalized_warning"] == ""

    dad_sugar = next(i for i in dad_res["ingredient_warnings"] if i["ingredient"] == "Sugar")
    assert any(term in dad_sugar["personalized_warning"].lower() for term in ["diabet", "glycemic", "sugar", "insulin", "spike", "glucose"])


def test_severe_allergy_rates_zero_with_base_score_context(mock_product):
    """
    Food allergies are life-threatening:
    1. If an ingredient matches an allergy, product MUST be rated 0/100.
    2. Must explicitly state that it is rated 0 due to allergy, and what base nutritional score would be without allergy.
    3. Offending ingredient must be flagged with HIGH concern and DIRECT ALLERGEN warning.
    """
    from app.services.profile_evaluator import evaluate_profile_safety_offline

    allergy_product = mock_product.model_copy(deep=True)
    allergy_product.product_name = "Crunchy Peanut Granola Bar"
    allergy_product.health_score = 72
    allergy_product.base_health_score = 72
    allergy_product.ingredient_breakdown = [
        IngredientItem(ingredient="Rolled Oats", purpose="Whole grain", concern_level="LOW"),
        IngredientItem(ingredient="Roasted Peanuts", purpose="Nut protein", concern_level="LOW"),
        IngredientItem(ingredient="Honey", purpose="Sweetener", concern_level="MEDIUM")
    ]

    peanut_allergy_profile = UserProfile(
        id="profile_allergy_user",
        name="Allergy User",
        allergies=["Peanut Allergy"],
        medical_conditions=[],
        dietary_preferences=[]
    )

    eval_res = evaluate_profile_safety_offline(allergy_product, peanut_allergy_profile)

    assert eval_res["adjusted_health_score"] == 0, f"Expected 0 for severe allergy, got {eval_res['adjusted_health_score']}"
    assert eval_res["personalized_verdict"] == "AVOID (VIOLATES PROFILE)"
    assert "Peanut" in eval_res["allergy_trigger"]
    assert eval_res["base_score_without_allergy"] == 72

    # Check explicit contraindication text
    allergy_contra = [c for c in eval_res["contraindications"] if "severe allergy" in c.lower()]
    assert len(allergy_contra) > 0
    assert "Rated 0/100" in allergy_contra[0]
    assert "Peanut" in allergy_contra[0]
    assert "72/100" in allergy_contra[0]

    # Check ingredient warning
    peanut_ing = next(i for i in eval_res["ingredient_breakdown"] if "Peanut" in i["ingredient"])
    assert peanut_ing["concern_level"] == "HIGH"
    assert "DIRECT ALLERGEN" in peanut_ing["personalized_warning"]
    assert "RATED 0/100" in peanut_ing["personalized_warning"]


def test_profile_editing_invalidates_cache_and_forces_fresh_scan(mock_product):
    """
    When a user edits their profile (e.g. adds an allergy), the cache fingerprint must change,
    old cache entries must be evicted, and a fresh audit must be run rather than returning stale results.
    """
    from app.main import (
        compute_profile_fingerprint,
        store_product_in_cache,
        find_in_audit_cache,
        AUDIT_CACHE,
        SAFETY_CACHE
    )

    # Initial profile: healthy with no allergies
    prof_v1 = UserProfile(
        id="prof_editing_test",
        name="Alex",
        allergies=[],
        medical_conditions=["Mild Acidity"],
        dietary_preferences=["Vegetarian"]
    )
    fp_v1 = compute_profile_fingerprint(prof_v1)

    # Store product audit for prof_v1
    prod_v1 = mock_product.model_copy(deep=True)
    prod_v1.product_name = "Cashew Almond Milk"
    prod_v1.health_score = 65
    prod_v1.personalized_verdict = "SAFE FOR YOU"
    store_product_in_cache(prod_v1, query_text="Cashew Almond Milk", profile=prof_v1)

    # Assert cache hit for prof_v1
    hit_v1 = find_in_audit_cache(query_text="Cashew Almond Milk", profile=prof_v1)
    assert hit_v1 is not None
    assert hit_v1.health_score == 65

    # User edits profile: adds Nut Allergy
    prof_v2 = UserProfile(
        id="prof_editing_test",
        name="Alex",
        allergies=["Nut Allergy"],
        medical_conditions=["Mild Acidity"],
        dietary_preferences=["Vegetarian"]
    )
    fp_v2 = compute_profile_fingerprint(prof_v2)

    # Fingerprints must be completely different
    assert fp_v1 != fp_v2

    # Querying cache with edited profile MUST NOT return stale v1 results!
    stale_check = find_in_audit_cache(query_text="Cashew Almond Milk", profile=prof_v2)
    assert stale_check is None, "Cache should MISS when profile has been edited!"

    # Now store audit for prof_v2 (rated 0 due to nut allergy)
    prod_v2 = mock_product.model_copy(deep=True)
    prod_v2.product_name = "Cashew Almond Milk"
    prod_v2.health_score = 0
    prod_v2.personalized_verdict = "AVOID (VIOLATES PROFILE)"
    prod_v2.allergy_trigger = "Nut Allergy"
    store_product_in_cache(prod_v2, query_text="Cashew Almond Milk", profile=prof_v2)

    # Verify old v1 cache entries were evicted
    v1_keys = [k for k in AUDIT_CACHE.keys() if f":prof_editing_test_{fp_v1}" in k]
    assert len(v1_keys) == 0, "Old cache entries for edited profile should be evicted!"

    # New cache hit for v2
    hit_v2 = find_in_audit_cache(query_text="Cashew Almond Milk", profile=prof_v2)
    assert hit_v2 is not None
    assert hit_v2.health_score == 0
    assert hit_v2.allergy_trigger == "Nut Allergy"


def test_reevaluation_starts_from_pure_base_no_compounding(mock_product):
    """
    Re-evaluating a product against different profiles must diagnose from the product's authentic facts,
    and never compound deductions from a previous profile's evaluation.
    """
    from app.services.profile_evaluator import evaluate_profile_safety_offline

    base = mock_product.model_copy(deep=True)
    base.product_name = "Oat & Chia Energy Bar"
    base.health_score = 75
    base.base_health_score = 75
    base.ingredient_breakdown = [
        IngredientItem(ingredient="Rolled Oats", purpose="Grain", concern_level="LOW"),
        IngredientItem(ingredient="Chia Seeds", purpose="Superfood", concern_level="LOW"),
        IngredientItem(ingredient="Sugar", purpose="Sweetener", concern_level="HIGH")
    ]
    base.nutrition_card.added_sugars_g = 15.0

    # Profile A: Severe Diabetes (deduction for 15g added sugar)
    prof_diabetic = UserProfile(
        id="p_diabetic",
        name="Diabetic User",
        medical_conditions=["Type 2 Diabetes"],
        allergies=[]
    )
    res_a = evaluate_profile_safety_offline(base, prof_diabetic)
    assert res_a["adjusted_health_score"] < 75
    penalized_score = res_a["adjusted_health_score"]

    # Now create an already-evaluated product from res_a (simulate what client sends back)
    evaluated_product = base.model_copy(deep=True)
    evaluated_product.health_score = penalized_score  # lower score e.g. 50
    evaluated_product.base_health_score = 75  # original base remains 75

    # Profile B: Clean user with no restrictions
    prof_clean = UserProfile(
        id="p_clean",
        name="Clean User",
        medical_conditions=[],
        allergies=[],
        dietary_preferences=[]
    )
    res_b = evaluate_profile_safety_offline(evaluated_product, prof_clean)

    # Profile B must receive the pure base score (75), NOT the penalized score (50)!
    assert res_b["adjusted_health_score"] == 75, f"Expected 75 but got {res_b['adjusted_health_score']} (compounding bug!)"
    assert res_b["personalized_verdict"] == "SAFE FOR YOU"


