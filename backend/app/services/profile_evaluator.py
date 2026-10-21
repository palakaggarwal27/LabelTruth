"""
Decoupled clinical profile safety re-evaluation service.
Evaluates base food product facts against active family member health restrictions
in < 50ms without calling external LLM or vision OCR.
"""

from typing import Dict, Any, List
from app.schemas.analysis import LabelAnalysisResult
from app.schemas.user_profile import UserProfile

def evaluate_profile_safety_offline(
    base_product: LabelAnalysisResult,
    profile: UserProfile
) -> Dict[str, Any]:
    """
    Evaluates base product against medical conditions, allergies, and custom avoidance list.
    Returns:
    - personalized_verdict: 'SAFE FOR YOU' | 'CAUTION' | 'AVOID (VIOLATES PROFILE)'
    - updated_ingredient_breakdown: with tailored personalized_warnings
    - contraindications: list of specific conflicts detected
    """
    med_conditions = [c.lower() for c in (profile.medical_conditions or [])]
    allergies = [a.lower() for a in (profile.allergies or [])]
    dietary = [d.lower() for d in (profile.dietary_preferences or [])]
    avoid_list = [v.lower() for v in (profile.custom_avoid_list or [])]

    contraindications = []
    has_severe_violation = False
    has_moderate_warning = False

    # Extract all text from ingredients and nutrition
    ingredients = base_product.ingredient_breakdown or []
    all_ing_text = " ".join([i.ingredient for i in ingredients]).lower()
    
    nutr = base_product.nutrition_card
    added_sugars = float(getattr(nutr, "added_sugars_g", 0.0) or 0.0) if nutr else 0.0
    sodium = float(getattr(nutr, "sodium_mg", 0.0) or 0.0) if nutr else 0.0
    sat_fat = float(getattr(nutr, "saturated_fat_g", 0.0) or 0.0) if nutr else 0.0

    # 1. Medical Conditions Check
    if any("diabetes" in c or "blood sugar" in c for c in med_conditions):
        if added_sugars > 5.0 or "maltodextrin" in all_ing_text or "liquid glucose" in all_ing_text or "invert sugar" in all_ing_text:
            contraindications.append("Contains high glycemic sugars/maltodextrin that trigger immediate insulin resistance & glucose spikes.")
            has_severe_violation = True
        elif added_sugars > 2.0:
            contraindications.append("Contains moderate added sugars; consume with extreme caution.")
            has_moderate_warning = True

    if any("hypertension" in c or "high bp" in c or "blood pressure" in c for c in med_conditions):
        if sodium > 400.0 or "ins 621" in all_ing_text or "msg" in all_ing_text or "monosodium glutamate" in all_ing_text:
            contraindications.append(f"Elevated sodium ({sodium}mg) & flavour enhancers worsen fluid retention and arterial blood pressure.")
            has_severe_violation = True
        elif sodium > 250.0:
            contraindications.append(f"Moderate sodium ({sodium}mg); limit portion size.")
            has_moderate_warning = True

    if any("cholesterol" in c or "cardiovascular" in c or "heart" in c for c in med_conditions):
        if sat_fat > 5.0 or "palm oil" in all_ing_text or "palmolein" in all_ing_text or "partially hydrogenated" in all_ing_text:
            contraindications.append("High saturated palmitic acid / palm oil promotes LDL oxidation and arterial stiffness.")
            has_severe_violation = True

    if any("celiac" in c or "gluten" in c for c in med_conditions) or any("gluten" in a or "wheat" in a for a in allergies):
        if any(term in all_ing_text for term in ["wheat", "maida", "atta", "gluten", "barley", "malt", "spelt"]):
            contraindications.append("Contains gluten/wheat grains strictly contraindicated for celiac disease.")
            has_severe_violation = True

    # 2. Allergy Check
    for allergy in allergies:
        if allergy and allergy in all_ing_text:
            contraindications.append(f"Direct allergen detected matching profile restriction: '{allergy}'.")
            has_severe_violation = True
        if "peanut" in allergy and ("peanut" in all_ing_text or "groundnut" in all_ing_text):
            contraindications.append("Peanut allergen detected.")
            has_severe_violation = True
        if "soy" in allergy and ("soy" in all_ing_text or "soya" in all_ing_text):
            contraindications.append("Soy allergen detected.")
            has_severe_violation = True

    # 3. Dietary Preferences Check
    if any("vegan" in d for d in dietary):
        if any(dairy in all_ing_text for dairy in ["milk", "whey", "curd", "paneer", "butter", "cheese", "ghee", "casein", "gelatin"]):
            contraindications.append("Contains animal/dairy-derived ingredients violating vegan profile.")
            has_severe_violation = True

    if any("jain" in d for d in dietary):
        if any(root in all_ing_text for root in ["onion", "garlic", "potato", "carrot", "radish"]):
            contraindications.append("Contains underground root vegetables violating Jain dietary requirements.")
            has_severe_violation = True

    # 4. Custom Avoid List Check
    for item in avoid_list:
        if item and item in all_ing_text:
            contraindications.append(f"Contains '{item}' which is on your active personal avoidance list.")
            has_severe_violation = True

    # Calculate Verdict
    if has_severe_violation:
        verdict = "AVOID (VIOLATES PROFILE)"
    elif has_moderate_warning:
        verdict = "CAUTION"
    else:
        verdict = "SAFE FOR YOU"

    # Produce updated personalized warnings on ingredients
    updated_ingredients = []
    for ing in ingredients:
        ing_dict = ing.model_dump() if hasattr(ing, "model_dump") else dict(ing)
        name_lower = ing_dict.get("ingredient", "").lower()
        warns = []
        if any("diabetes" in c for c in med_conditions) and ("sugar" in name_lower or "maltodextrin" in name_lower or "glucose" in name_lower):
            warns.append("Glycemic surge risk for diabetes")
        if any("hypertension" in c for c in med_conditions) and ("salt" in name_lower or "sodium" in name_lower or "621" in name_lower):
            warns.append("Elevates blood pressure")
        if any(a in name_lower for a in allergies):
            warns.append("Allergen match")
        if warns:
            ing_dict["personalized_warning"] = " • ".join(warns)
            ing_dict["concern_level"] = "HIGH"
        updated_ingredients.append(ing_dict)

    return {
        "personalized_verdict": verdict,
        "contraindications": contraindications,
        "ingredient_breakdown": updated_ingredients
    }
