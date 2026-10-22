def is_whole_food_matrix(ingredients: list, ingredients_text: str, product_name: str) -> bool:
    """
    Detects if the food is a 100% clean whole food, pure cold-pressed oil,
    A2 dairy/ghee, natural nut/seed butter, or single-ingredient whole food
    as defined under ICMR-NIN 2024 Dietary Guidelines and FSSAI 2020 Schedule II.
    """
    lower_ing = ingredients_text.lower()
    lower_name = product_name.lower()

    # Disqualify any product containing industrial refined fats, sugars, or harsh chemical additives
    industrial_disqualifiers = [
        "palm oil", "palmolein", "hydrogenated", "vanaspati", "interesterified",
        "maltodextrin", "liquid glucose", "invert syrup", "high fructose", "corn syrup",
        "ins 150d", "ins 621", "msg", "ins 211", "ins 102", "artificial color", "artificial flavour"
    ]
    if any(d in lower_ing for d in industrial_disqualifiers):
        return False

    # Positive whole-food lipid/matrix indicators
    whole_food_indicators = [
        "peanut butter", "peanuts", "almonds", "walnuts", "cashews", "chia", "flax",
        "ghee", "clarified butter", "cold-pressed", "wood-pressed", "extra virgin",
        "mustard oil", "coconut oil", "olive oil", "sesame oil", "groundnut oil",
        "whole grain", "rolled oats", "millets", "ragi", "jowar", "bajra",
        "paneer", "cheese", "curd", "yogurt", "milk", "makhana", "seeds"
    ]
    has_indicator = any(w in lower_ing or w in lower_name for w in whole_food_indicators)
    few_ingredients = len(ingredients) <= 6 if ingredients else True

    return has_indicator and few_ingredients

"""
Piecewise Mathematical Scoring Engine for LabelTruth.
Based on FSSAI 2020/2023 Labelling & Display Regulations, ICMR-NIN 2024 Dietary Guidelines, and WHO SEARO Nutrient Profile Model.

Health Score Formula:
S = min(100, max(0, 100 - sum(D_i) + sum(B_j)))
"""

from typing import List, Dict, Any, Optional
import re

INS_LOW_RISK = {"330", "415", "500", "500ii", "500i", "322", "300", "440", "406", "410", "412"}
INS_MED_RISK = {"102", "110", "122", "124", "133", "211", "220", "223", "621", "627", "631", "950", "951", "955", "960"}
INS_HIGH_RISK = {"150d", "150c", "320", "321", "952", "954"}

def calculate_trans_fat_penalty(trans_fat_g: float, ingredients_text: str) -> float:
    penalty = 0.0
    if trans_fat_g <= 0.2:
        penalty = 0.0
    elif trans_fat_g <= 0.5:
        penalty = 10.0
    elif trans_fat_g <= 1.0:
        penalty = 20.0
    else:
        penalty = 30.0

    lower_text = ingredients_text.lower()
    pho_keywords = ["partially hydrogenated", "hydrogenated vegetable oil", "vanaspati", "margarine", "shortening"]
    if any(kw in lower_text for kw in pho_keywords):
        penalty += 10.0

    return penalty

def calculate_added_sugar_penalty(added_sugar_g: float, is_liquid: bool, ingredients_text: str, claims_text: str) -> float:
    penalty = 0.0
    if is_liquid:
        if added_sugar_g <= 2.0:
            penalty = 0.0
        elif added_sugar_g <= 6.0:
            penalty = 8.0
        elif added_sugar_g <= 12.0:
            penalty = 16.0
        else:
            penalty = 25.0
    else:
        if added_sugar_g <= 3.0:
            penalty = 0.0
        elif added_sugar_g <= 10.0:
            penalty = 8.0
        elif added_sugar_g <= 20.0:
            penalty = 16.0
        else:
            penalty = 25.0

    lower_claims = claims_text.lower()
    lower_ing = ingredients_text.lower()
    zero_sugar_claim = any(claim in lower_claims for claim in ["zero sugar", "no added sugar", "sugar free", "0% sugar", "without added sugar"])
    has_maltodextrin = "maltodextrin" in lower_ing
    if zero_sugar_claim and has_maltodextrin:
        penalty += 15.0

    return penalty

def calculate_saturated_fat_penalty(sat_fat_g: float, is_liquid: bool, ingredients_text: str) -> float:
    penalty = 0.0
    if is_liquid:
        if sat_fat_g <= 1.5:
            penalty = 0.0
        elif sat_fat_g <= 4.0:
            penalty = 8.0
        else:
            penalty = 16.0
    else:
        if sat_fat_g <= 3.0:
            penalty = 0.0
        elif sat_fat_g <= 8.0:
            penalty = 8.0
        else:
            penalty = 16.0

    lower_ing = ingredients_text.lower()
    tropical_oils = ["palm oil", "palmolein", "palm olein", "fractionated palm", "interesterified fat", "interesterified vegetable fat", "palm kernel"]
    if any(kw in lower_ing for kw in tropical_oils):
        penalty += 10.0

    return penalty

def calculate_sodium_penalty(sodium_mg: float) -> float:
    if sodium_mg <= 150.0:
        return 0.0
    elif sodium_mg <= 350.0:
        return 6.0
    elif sodium_mg <= 600.0:
        return 12.0
    elif sodium_mg <= 900.0:
        return 18.0
    else:
        return 25.0

def calculate_energy_density_penalty(calories_kcal: float, is_liquid: bool) -> float:
    if is_liquid:
        if calories_kcal <= 20.0:
            return 0.0
        elif calories_kcal <= 50.0:
            return 5.0
        elif calories_kcal <= 80.0:
            return 10.0
        else:
            return 15.0
    else:
        if calories_kcal <= 225.0:
            return 0.0
        elif calories_kcal <= 350.0:
            return 5.0
        elif calories_kcal <= 450.0:
            return 10.0
        else:
            return 15.0

def calculate_ins_additives_penalty(ingredients: list, ingredients_text: str) -> float:
    all_codes = set()
    matches = re.findall(r'(?:ins|e)[ -]?(\d{3,4}[a-z]*)', ingredients_text.lower())
    for m in matches:
        all_codes.add(m.strip())

    for item in ingredients:
        ing_name = getattr(item, "ingredient", "") if hasattr(item, "ingredient") else str(item.get("ingredient", "")) if isinstance(item, dict) else str(item)
        ing_matches = re.findall(r'(?:ins|e)[ -]?(\d{3,4}[a-z]*)', ing_name.lower())
        for m in ing_matches:
            all_codes.add(m.strip())

    n_low = 0
    n_med = 0
    n_high = 0

    for code in all_codes:
        if code in INS_HIGH_RISK or any(code.startswith(hr) for hr in INS_HIGH_RISK):
            n_high += 1
        elif code in INS_MED_RISK or any(code.startswith(mr) for mr in INS_MED_RISK):
            n_med += 1
        elif code in INS_LOW_RISK or any(code.startswith(lr) for lr in INS_LOW_RISK):
            n_low += 1

    lower_text = ingredients_text.lower()
    if ("caramel color" in lower_text or "caramel colour" in lower_text or "150d" in lower_text) and "150d" not in all_codes:
        n_high += 1
    if ("monosodium glutamate" in lower_text or "msg" in lower_text or "tartrazine" in lower_text or "sodium benzoate" in lower_text):
        if not any(c in all_codes for c in ["621", "102", "211"]):
            n_med += 1
    if "ethylene oxide" in lower_text or "eto" in lower_text:
        n_high += 1

    total = (2 * n_low) + (6 * n_med) + (12 * n_high)
    return float(min(30, total))

def calculate_protein_bonus(declared_protein_g: float, pdcaas: float, ingredients_text: str) -> float:
    usable = declared_protein_g * max(0.0, min(1.0, pdcaas))
    bonus = 0.0
    if usable >= 10.0:
        bonus = 10.0
    elif usable >= 5.0:
        bonus = 5.0
    else:
        bonus = 0.0

    lower_ing = ingredients_text.lower()
    if "glycine" in lower_ing or "taurine" in lower_ing or "l-glycine" in lower_ing:
        bonus -= 15.0

    return bonus

def calculate_fiber_bonus(declared_fiber_g: float, ingredients_text: str) -> float:
    lower_ing = ingredients_text.lower()
    synthetic_isolated = ["polydextrose", "inulin", "chicory root fiber", "isolated soluble fiber", "resistant dextrin"]
    has_only_synthetic = any(syn in lower_ing for syn in synthetic_isolated) and not any(wg in lower_ing for wg in ["whole wheat", "whole grain", "oats", "millet", "ragi", "bajra", "jowar", "bran"])
    
    if has_only_synthetic:
        return 0.0

    if declared_fiber_g >= 6.0:
        return 10.0
    elif declared_fiber_g >= 3.0:
        return 5.0
    return 0.0

def compute_piecewise_health_score(
    nutrition=None,
    ingredients=None,
    integrity=None,
    deceptive_claims=None,
    product_name: str = ""
) -> Dict[str, Any]:
    ingredients = ingredients or []
    all_ing_text = " ".join([getattr(i, "ingredient", "") if hasattr(i, "ingredient") else str(i.get("ingredient", "")) if isinstance(i, dict) else str(i) for i in ingredients]).lower()
    claims_text = " ".join(deceptive_claims or []).lower()
    is_liquid = any(term in product_name.lower() or term in all_ing_text for term in ["juice", "drink", "beverage", "soda", "syrup", "liquid", "milk", "tea", "coffee", "cola"])

    trans_fat = 0.0
    added_sugars = 0.0
    sat_fat = 0.0
    sodium = 0.0
    calories = 0.0
    declared_protein = 0.0
    pdcaas = 0.5
    declared_fiber = 0.0

    if nutrition:
        trans_fat = float(getattr(nutrition, "trans_fat_g", 0.0) or (nutrition.get("trans_fat_g", 0.0) if isinstance(nutrition, dict) else 0.0) or 0.0)
        added_sugars = float(getattr(nutrition, "added_sugars_g", 0.0) or (nutrition.get("added_sugars_g", 0.0) if isinstance(nutrition, dict) else 0.0) or 0.0)
        sat_fat = float(getattr(nutrition, "saturated_fat_g", 0.0) or (nutrition.get("saturated_fat_g", 0.0) if isinstance(nutrition, dict) else 0.0) or 0.0)
        sodium = float(getattr(nutrition, "sodium_mg", 0.0) or (nutrition.get("sodium_mg", 0.0) if isinstance(nutrition, dict) else 0.0) or 0.0)
        calories = float(getattr(nutrition, "calories_kcal", 0.0) or (nutrition.get("calories_kcal", 0.0) if isinstance(nutrition, dict) else 0.0) or 0.0)

        breakdown = getattr(nutrition, "breakdown", []) or (nutrition.get("breakdown", []) if isinstance(nutrition, dict) else [])
        for b in breakdown:
            n_name = getattr(b, "nutrient", "") if hasattr(b, "nutrient") else str(b.get("nutrient", ""))
            amount_str = getattr(b, "amount_per_100g", "") if hasattr(b, "amount_per_100g") else str(b.get("amount_per_100g", ""))
            if "fiber" in n_name.lower() or "fibre" in n_name.lower():
                val = re.findall(r'(\d+(?:\.\d+)?)', amount_str)
                if val:
                    declared_fiber = float(val[0])
            if "protein" in n_name.lower() and declared_protein == 0:
                val = re.findall(r'(\d+(?:\.\d+)?)', amount_str)
                if val:
                    declared_protein = float(val[0])

    if integrity:
        prot_obj = getattr(integrity, "protein", None) or (integrity.get("protein", {}) if isinstance(integrity, dict) else None)
        if prot_obj:
            d_p = getattr(prot_obj, "declared_protein_g", 0.0) if hasattr(prot_obj, "declared_protein_g") else prot_obj.get("declared_protein_g", 0.0)
            if d_p > 0:
                declared_protein = float(d_p)
            pd_s = getattr(prot_obj, "pdcaas_score", 0.5) if hasattr(prot_obj, "pdcaas_score") else prot_obj.get("pdcaas_score", 0.5)
            pdcaas = float(pd_s or 0.5)

    d_tf = calculate_trans_fat_penalty(trans_fat, all_ing_text)
    d_as = calculate_added_sugar_penalty(added_sugars, is_liquid, all_ing_text, claims_text)
    d_sf = calculate_saturated_fat_penalty(sat_fat, is_liquid, all_ing_text)
    d_na = calculate_sodium_penalty(sodium)
    d_ed = calculate_energy_density_penalty(calories, is_liquid)
    d_ins = calculate_ins_additives_penalty(ingredients, all_ing_text)

    b_protein = calculate_protein_bonus(declared_protein, pdcaas, all_ing_text)
    b_fiber = calculate_fiber_bonus(declared_fiber, all_ing_text)

    # Apply ICMR-NIN 2024 & FSSAI 2020 Whole Food Matrix Sparing Rule:
    # Intrinsic fats (in whole nuts, seeds, pure oils, A2 ghee, natural cheese) are not penalized like industrial palm oil.
    is_whole_food = is_whole_food_matrix(ingredients, all_ing_text, product_name)
    b_whole_food = 0.0
    if is_whole_food:
        # 1. Natural caloric density in whole nuts/seeds comes with cellular fiber and minerals; waive empty calorie penalty
        d_ed = 0.0
        # 2. Intrinsic healthy lipids (dairy fat, oleic/linoleic plant fats): cap saturated fat deduction to max 3 points if zero palm oil
        if "palm" not in all_ing_text and "hydrogenated" not in all_ing_text:
            d_sf = min(3.0, d_sf * 0.25)
        # 3. Natural mineral sodium (e.g. pink salt, naturally cured whole foods): do not excessively penalize
        if sodium <= 650.0:
            d_na = min(4.0, d_na * 0.35)
        # 4. Award clean whole-food formulation bonus
        b_whole_food = 8.0

    total_deductions = d_tf + d_as + d_sf + d_na + d_ed + d_ins
    total_bonuses = b_protein + b_fiber + b_whole_food

    raw_score = 100.0 - total_deductions + total_bonuses
    final_score = int(round(min(100.0, max(0.0, raw_score))))

    return {
        "final_health_score": final_score,
        "deductions": {
            "trans_fat_penalty": d_tf,
            "added_sugar_penalty": d_as,
            "saturated_fat_penalty": d_sf,
            "sodium_penalty": d_na,
            "energy_density_penalty": d_ed,
            "ins_additives_penalty": d_ins,
            "total_deductions": total_deductions
        },
        "bonuses": {
            "usable_protein_bonus": b_protein,
            "whole_food_fiber_bonus": b_fiber,
            "total_bonuses": total_bonuses
        }
    }
