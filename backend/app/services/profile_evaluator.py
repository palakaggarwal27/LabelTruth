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
    Calculates:
    - personalized_verdict: 'SAFE FOR YOU' | 'CAUTION' | 'AVOID (VIOLATES PROFILE)'
    - updated_ingredient_breakdown: with tailored personalized_warnings & concern levels
    - contraindications: list of specific conflicts and clinical reasoning
    - adjusted_health_score: score reflecting user profile penalties
    """
    med_conditions = [c.lower() for c in (profile.medical_conditions or [])]
    allergies = [a.lower() for a in (profile.allergies or [])]
    dietary = [d.lower() for d in (profile.dietary_preferences or [])]
    avoid_list = [v.lower() for v in (profile.custom_avoid_list or [])]

    contraindications = []
    has_severe_violation = False
    has_moderate_warning = False
    penalty_points = 0

    # Extract all text from ingredients and nutrition
    ingredients = base_product.ingredient_breakdown or []
    all_ing_text = " ".join([getattr(i, 'ingredient', str(i)) for i in ingredients]).lower()
    p_name_lower = (getattr(base_product, 'product_name', '') or '').lower()
    
    nutr = base_product.nutrition_card
    added_sugars = float(getattr(nutr, "added_sugars_g", 0.0) or 0.0) if nutr else 0.0
    sodium = float(getattr(nutr, "sodium_mg", 0.0) or 0.0) if nutr else 0.0
    sat_fat = float(getattr(nutr, "saturated_fat_g", 0.0) or 0.0) if nutr else 0.0

    # 0. Pure baseline diagnosis from scratch using unpenalized base score or mathematical piecewise scoring engine
    pure_base_score = getattr(base_product, "base_health_score", None)
    if pure_base_score is None:
        if getattr(base_product, "nutrition_card", None):
            from app.services.scoring_engine import compute_piecewise_health_score
            try:
                math_score_data = compute_piecewise_health_score(
                    nutrition=base_product.nutrition_card,
                    ingredients=base_product.ingredient_breakdown or [],
                    integrity=getattr(base_product, "nutrient_integrity", None),
                    deceptive_claims=getattr(base_product, "deceptive_claims_flagged", []) or [],
                    product_name=getattr(base_product, "product_name", "") or ""
                )
                pure_base_score = int(math_score_data.get("final_health_score", 50))
            except Exception:
                pure_base_score = getattr(base_product, "health_score", 50)
        else:
            pure_base_score = getattr(base_product, "health_score", 50)

    # 1. Acidity / Acid Reflux / GERD / Gastritis Check
    if any(c in cond for cond in med_conditions for c in ["acidity", "acid reflux", "gerd", "gastritis", "heartburn"]):
        acidity_triggers = []
        if any(t in all_ing_text for t in ["citric acid", "ins 330", "acidity regulator (330)", "e330"]):
            acidity_triggers.append("Citric Acid (INS 330)")
        if any(t in all_ing_text for t in ["carbonated water", "carbonation", "phosphoric acid", "ins 338"]):
            acidity_triggers.append("Carbonation & Phosphoric Acid")
        if any(t in all_ing_text for t in ["caffeine", "coffee extract"]):
            acidity_triggers.append("Concentrated Caffeine")
        if any(t in all_ing_text for t in ["chili", "chilli", "capsaicin", "hot sauce", "vinegar", "acetic acid"]):
            acidity_triggers.append("Irritating Spices/Acidic Agents")
        
        if acidity_triggers:
            triggers_str = ", ".join(acidity_triggers)
            contraindications.append(f"Contains {triggers_str} which directly stimulate gastric acid secretion & esophageal reflux (~70% likelihood of acidity flare-up).")
            penalty_points += 15
            has_moderate_warning = True

    # 2. Medical Conditions Check: Diabetes & Blood Sugar
    if any("diabetes" in c or "blood sugar" in c for c in med_conditions):
        if added_sugars > 5.0 or any(t in all_ing_text for t in ["maltodextrin", "liquid glucose", "invert sugar", "dextrose", "high fructose corn syrup"]):
            contraindications.append(f"Contains high glycemic ingredients ({added_sugars}g sugar / maltodextrin GI 110) triggering acute insulin spikes.")
            penalty_points += 25
            has_severe_violation = True
        elif added_sugars > 2.0:
            contraindications.append(f"Contains moderate added sugars ({added_sugars}g); consume with caution for blood sugar.")
            penalty_points += 10
            has_moderate_warning = True

    # 3. Medical Conditions Check: Hypertension / High BP
    if any("hypertension" in c or "high bp" in c or "blood pressure" in c for c in med_conditions):
        if sodium > 400.0 or any(t in all_ing_text for t in ["ins 621", "msg", "monosodium glutamate", "sodium benzoate", "ins 211"]):
            contraindications.append(f"Elevated sodium ({sodium}mg) & preservative salts worsen arterial tension & fluid retention.")
            penalty_points += 20
            has_severe_violation = True
        elif sodium > 250.0:
            contraindications.append(f"Moderate sodium ({sodium}mg); limit portion size for blood pressure control.")
            penalty_points += 8
            has_moderate_warning = True

    # 4. Medical Conditions Check: Cholesterol / Heart
    if any("cholesterol" in c or "cardiovascular" in c or "heart" in c for c in med_conditions):
        if sat_fat > 5.0 or any(t in all_ing_text for t in ["palm oil", "palmolein", "partially hydrogenated", "vanaspati"]):
            contraindications.append("High saturated palmitic acid / palm oil promotes LDL oxidation and cardiovascular plaque risk.")
            penalty_points += 20
            has_severe_violation = True

    # 5. Fatty Liver / NAFLD
    if any("fatty liver" in c or "nafld" in c or "liver" in c for c in med_conditions):
        if any(t in all_ing_text for t in ["high fructose", "corn syrup", "invert syrup", "liquid glucose", "palm oil"]):
            contraindications.append("Concentrated fructose/industrial fats accelerate hepatic de novo lipogenesis (fatty liver risk).")
            penalty_points += 18
            has_severe_violation = True

    # 6. Celiac Disease / Gluten Sensitivity
    if any("celiac" in c or "gluten" in c for c in med_conditions) or any("gluten" in a or "wheat" in a for a in allergies):
        if any(term in all_ing_text or term in p_name_lower for term in ["wheat", "maida", "atta", "gluten", "barley", "malt", "spelt"]):
            contraindications.append("Contains gluten/wheat grains strictly contraindicated for celiac disease.")
            penalty_points += 40
            has_severe_violation = True

    # 7. Lactose Intolerance
    if any("lactose" in c for c in med_conditions) or any("lactose" in a for a in allergies):
        if any(term in all_ing_text or term in p_name_lower for term in ["milk", "whey", "lactose", "milk solids", "cheese", "paneer", "curd"]):
            contraindications.append("Contains dairy lactose triggering bloating, cramping, and gastrointestinal distress.")
            penalty_points += 15
            has_moderate_warning = True

    # 8. Severe Allergy Check (Strict Anaphylaxis/Allergy Protocol: Rates 0/100)
    matched_allergies = []
    for allergy in allergies:
        if not allergy:
            continue
        if allergy in all_ing_text or allergy in p_name_lower:
            matched_allergies.append(allergy.title())
        elif "peanut" in allergy and any(t in all_ing_text or t in p_name_lower for t in ["peanut", "groundnut", "arachis"]):
            matched_allergies.append("Peanut")
        elif "tree nut" in allergy or ("nut" in allergy and "peanut" not in allergy and "coconut" not in allergy):
            if any(t in all_ing_text or t in p_name_lower for t in ["almond", "cashew", "walnut", "pistachio", "hazelnut", "pecan"]):
                matched_allergies.append("Tree Nut")
        elif "soy" in allergy and any(t in all_ing_text or t in p_name_lower for t in ["soy", "soya", "soybean", "edamame", "tofu"]):
            matched_allergies.append("Soy")
        elif ("milk" in allergy or "dairy" in allergy) and any(t in all_ing_text or t in p_name_lower for t in ["milk", "dairy", "whey", "casein", "curd", "paneer", "cheese", "butter", "ghee", "lactose"]):
            matched_allergies.append("Milk / Dairy")
        elif ("gluten" in allergy or "wheat" in allergy) and any(t in all_ing_text or t in p_name_lower for t in ["wheat", "maida", "atta", "gluten", "barley", "spelt"]):
            matched_allergies.append("Wheat / Gluten")
        elif "egg" in allergy and any(t in all_ing_text or t in p_name_lower for t in ["egg", "albumin", "ovalbumin"]):
            matched_allergies.append("Egg")
        elif ("fish" in allergy or "seafood" in allergy or "shellfish" in allergy) and any(t in all_ing_text or t in p_name_lower for t in ["fish", "prawn", "crab", "shrimp", "gelatin"]):
            matched_allergies.append("Fish / Shellfish")
        elif "sesame" in allergy and any(t in all_ing_text or t in p_name_lower for t in ["sesame", "til", "tahini"]):
            matched_allergies.append("Sesame")

    # 9. Dietary Preferences Check
    if any("vegan" in d for d in dietary):
        if any(dairy in all_ing_text for dairy in ["milk", "whey", "curd", "paneer", "butter", "cheese", "ghee", "casein", "gelatin"]):
            contraindications.append("Contains animal/dairy-derived ingredients violating vegan profile.")
            penalty_points += 30
            has_severe_violation = True

    if any("jain" in d for d in dietary):
        if any(root in all_ing_text for root in ["onion", "garlic", "potato", "carrot", "radish"]):
            contraindications.append("Contains underground root vegetables violating Jain dietary requirements.")
            penalty_points += 30
            has_severe_violation = True

    # 10. Custom Avoid List Check
    for item in avoid_list:
        if item and (item in all_ing_text or item in p_name_lower):
            contraindications.append(f"Contains '{item}' which is on your active personal avoidance list.")
            penalty_points += 20
            has_severe_violation = True

    # 11. Weight Loss / Calorie Deficit
    if any(term in c for c in med_conditions for term in ["weight loss", "obesity", "fat loss", "calorie deficit"]):
        if added_sugars > 5.0 or sat_fat > 5.0:
            contraindications.append(f"High caloric load ({added_sugars}g sugar / {sat_fat}g saturated fat) disrupts calorie deficit.")
            penalty_points += 15
            has_moderate_warning = True

    # 12. Child / Kid Profile
    p_name_lower = (profile.name or "").lower()
    if any(k in p_name_lower for k in ["kid", "child", "toddler"]) or any("child" in c for c in med_conditions):
        if any(t in all_ing_text for t in ["ins 102", "ins 110", "ins 122", "ins 133", "tartrazine", "sunset yellow", "carmoisine", "aspartame", "sucralose", "ins 955", "caffeine"]):
            contraindications.append("Contains synthetic food dyes/sweeteners contraindicated for pediatric growth.")
            penalty_points += 25
            has_severe_violation = True
        elif added_sugars > 8.0:
            contraindications.append(f"Excessive added sugar ({added_sugars}g) exceeds pediatric thresholds.")
            penalty_points += 15
            has_moderate_warning = True

    # Severe Allergy Enforcement: Rating 0/100
    has_allergy_trigger = len(matched_allergies) > 0
    if has_allergy_trigger:
        allergen_str = ", ".join(list(dict.fromkeys(matched_allergies)))
        allergy_warning = f"Rated 0/100 (Triggers severe allergy: {allergen_str}). Base nutritional score would be {pure_base_score}/100 without allergy."
        contraindications.insert(0, allergy_warning)
        adjusted_score = 0
        verdict = "AVOID (VIOLATES PROFILE)"
    else:
        allergen_str = None
        allergy_warning = None
        adjusted_score = max(10, min(100, pure_base_score - penalty_points)) if penalty_points > 0 else pure_base_score
        if has_severe_violation:
            verdict = "AVOID (VIOLATES PROFILE)"
        elif penalty_points > 0:
            verdict = "AVOID (VIOLATES PROFILE)" if adjusted_score < 45 else "CAUTION"
        else:
            verdict = "SAFE FOR YOU" if adjusted_score >= 70 else "CAUTION"

    # Produce updated personalized warnings on ingredients
    updated_ingredients = []
    for ing in ingredients:
        ing_dict = ing.model_dump() if hasattr(ing, "model_dump") else dict(ing)
        name_lower = ing_dict.get("ingredient", "").lower()
        warns = []
        if has_allergy_trigger and (any(a.lower() in name_lower for a in matched_allergies) or any(a.lower() in p_name_lower for a in matched_allergies)):
            warns.append(f"⚠️ DIRECT ALLERGEN ({allergen_str}) — RATED 0/100 STRICTLY AVOID")
        elif any(a in name_lower for a in allergies):
            warns.append("⚠️ DIRECT ALLERGEN MATCH — RATED 0/100 STRICTLY AVOID")
        if any(c in cond for cond in med_conditions for c in ["acidity", "acid reflux", "gerd", "gastritis"]) and any(t in name_lower for t in ["citric", "330", "caffeine", "acid", "carbonat"]):
            warns.append("Triggers gastric acidity & reflux (~70% flare-up risk)")
        if any("diabetes" in c for c in med_conditions) and any(t in name_lower for t in ["sugar", "maltodextrin", "glucose", "dextrose"]):
            warns.append("Glycemic surge risk for diabetes")
        if any("hypertension" in c for c in med_conditions) and any(t in name_lower for t in ["salt", "sodium", "621", "211", "msg"]):
            warns.append("Elevates blood pressure")
        if warns:
            ing_dict["personalized_warning"] = " • ".join(warns)
            ing_dict["concern_level"] = "HIGH"
        else:
            ing_dict["personalized_warning"] = ""
            if not any(bad in name_lower for bad in ["150d", "150c", "trans fat", "hydrogenated", "benzoate", "tartrazine", "102", "110", "palm oil", "palmolein"]):
                if ing_dict.get("concern_level") == "HIGH":
                    ing_dict["concern_level"] = "LOW"
        updated_ingredients.append(ing_dict)

    return {
        "personalized_verdict": verdict,
        "contraindications": contraindications,
        "ingredient_breakdown": updated_ingredients,
        "adjusted_health_score": adjusted_score,
        "allergy_trigger": allergen_str,
        "base_score_without_allergy": pure_base_score if has_allergy_trigger else None,
        "allergy_warning": allergy_warning,
        "pure_base_score": pure_base_score
    }


def create_profile_insight_from_base(
    base_product: LabelAnalysisResult,
    profile: UserProfile
):
    from app.schemas.multi_profile import ProfileAuditInsight
    from app.schemas.analysis import IngredientItem
    res = evaluate_profile_safety_offline(base_product, profile)
    if res.get("allergy_warning"):
        summary = res["allergy_warning"]
    elif res["contraindications"]:
        summary = " • ".join(res["contraindications"][:2])
    elif res["adjusted_health_score"] >= 70:
        summary = "Safe for your dietary profile with no major clinical friction."
    elif res["adjusted_health_score"] >= 45:
        summary = "Moderate nutritional balance with no direct profile contraindications."
    else:
        summary = f"No direct profile conflicts, but product has low nutritional value (Score: {res['adjusted_health_score']}/100) — consume in moderation."

    return ProfileAuditInsight(
        profile_id=profile.id or "default",
        profile_name=profile.name or "Member",
        health_score=res["adjusted_health_score"],
        personalized_verdict=res["personalized_verdict"],
        personalized_summary=summary,
        contraindications=res["contraindications"],
        allergy_trigger=res.get("allergy_trigger"),
        base_score_without_allergy=res.get("base_score_without_allergy"),
        ingredient_warnings=[
            IngredientItem(**i) if isinstance(i, dict) else i
            for i in res["ingredient_breakdown"]
        ]
    )


def create_multi_profile_result_offline(
    base_product: LabelAnalysisResult,
    profiles: List[UserProfile]
):
    from app.schemas.multi_profile import MultiProfileScanResult
    insights = [create_profile_insight_from_base(base_product, p) for p in profiles[:3]]

    # Determine household verdict
    any_avoid = any(ins.personalized_verdict == "AVOID (VIOLATES PROFILE)" for ins in insights)
    any_caution = any(ins.personalized_verdict == "CAUTION" for ins in insights)

    if any_avoid:
        hh_verdict = "UNSAFE FOR FAMILY MEMBERS"
        violators = [ins.profile_name for ins in insights if ins.personalized_verdict == "AVOID (VIOLATES PROFILE)"]
        hh_summary = f"Not recommended for family purchase: violates health profile for {', '.join(violators)}."
    elif any_caution:
        hh_verdict = "PARTIALLY SAFE (CAUTION)"
        cautions = [ins.profile_name for ins in insights if ins.personalized_verdict == "CAUTION"]
        hh_summary = f"Safe for some members, but exercise caution for {', '.join(cautions)}."
    else:
        hh_verdict = "SAFE FOR HOUSEHOLD"
        hh_summary = "Safe for all evaluated family members with no major clinical contraindications."

    matrix = [
        {
            "profile_name": ins.profile_name,
            "health_score": ins.health_score,
            "personalized_verdict": ins.personalized_verdict,
            "key_issue": (
                ins.contraindications[0]
                if ins.contraindications
                else (
                    "Low nutritional density / ultra-processed"
                    if ins.health_score < 45
                    else "No clinical conflicts"
                )
            )
        }
        for ins in insights
    ]

    return MultiProfileScanResult(
        product_name=base_product.product_name,
        base_product=base_product,
        profiles_audited=insights,
        household_verdict=hh_verdict,
        household_summary=hh_summary,
        comparison_matrix=matrix
    )
