import json
import logging
from PIL import Image
import io
from fastapi import HTTPException
from google import genai
from google.genai import types

from typing import List, Dict, Any, Optional
from app.config import GEMINI_API_KEY, GEMINI_API_KEYS, GEMINI_ACTIVE_MODELS
from app.schemas.analysis import LabelAnalysisResult, NutrientIntegrityMatrix, ProteinAudit, IngredientItem
from app.schemas.multi_profile import MultiProfileScanResult, ProfileAuditInsight
from app.schemas.user_profile import UserProfile

logger = logging.getLogger(__name__)

FALLBACK_MODELS = GEMINI_ACTIVE_MODELS

SYSTEM_PROMPT = """You are LabelTruth - an elite Indian food regulatory compliance auditor, forensic label expert, and clinical dietary physician powered by FSSAI regulations (2020 & 2023 Labelling & Display, 2018 Advertising & Claims) and ICMR-NIN 2024 Dietary Guidelines.

AUDIT CRITERIA & FORENSIC PROTOCOLS:

1. Relevance & Label Classification:
   - Determine if this image is a genuine food product, food package, or nutritional panel.
   - If it is NOT food or food packaging (e.g. photo of room, pet, car, document), set "is_food_label": false and "label_type": "NOT_A_LABEL".
   - Check presence of packaging panels:
     * Are ingredients visible? Set "has_ingredients": true/false
     * Is nutrition facts table visible? Set "has_nutrition_table": true/false
   - If both are present, set "label_type": "FULL_PANEL".
   - If only front marketing/hero branding is present, set "label_type": "FRONT_OF_PACK".
   - If only ingredient list or nutrition table is present, set "label_type": "BACK_OF_PACK".

2. Comprehensive FSSAI Regulatory Audit (Check ALL Applicable Regulations):
   - Regulation 5(2)(b) Descending Weight Order: Ingredients must appear in exact descending order of incoming weight at time of manufacture. Expose split-sugar games (e.g. maltodextrin, invert syrup, glucose syrup listed separately to avoid sugar being #1), and refined wheat flour (Maida) disguised behind whole wheat (Atta) claims.
   - FSSAI Dairy vs. Non-Dairy Standards: Real ice cream MUST use 100% milk fat. Any substitution with vegetable oil, palm oil, or hydrogenated fat is legally a "Frozen Dessert" and must be exposed.
   - Whole Wheat (Atta) vs Maida Compliance: Flag products claiming "Brown Bread", "Atta Biscuits", or "Multigrain" where maida is the dominant flour or dyed with INS 150d (Caramel Colour).
   - Industrial Trans Fat Limits: Must comply with FSSAI limit of <= 0.2g per 100g. Flag any vanaspati, margarine, or partially hydrogenated vegetable oil.
   - Non-Veg / Veg & Allergen Declarations: Check for mandatory allergen warnings (nuts, soy, gluten, milk, sulfites) and clear declarations.
   - Advertising & Claims Regulations 2018: Expose misleading front-of-pack claims ("100% Natural", "Zero Added Sugar", "Immunity Booster", "Diet / Lite", "0% Cholesterol" hiding palm oil).

3. Comprehensive Ingredient-by-Ingredient Safety Inspection:
   - Inspect EVERY single ingredient and additive on the label for safety, toxicity, and ultra-processing, not just specific INS numbers.
   - Synthetic Food Dyes: Tartrazine (INS 102), Sunset Yellow (INS 110), Carmoisine (INS 122), Ponceau 4R (INS 124), Brilliant Blue (INS 133), Caramel Colour III/IV (INS 150c/150d with 4-MEI carcinogen concern).
   - Chemical Preservatives: Sodium Benzoate (INS 211 - benzene risk with Vitamin C), Sulfites/Sulfur Dioxide (INS 220/223 - asthma/respiratory triggers), Sodium Nitrite/Nitrate (INS 250/251 - nitrosamine risk).
   - Flavor Enhancers & Excitotoxins: Monosodium Glutamate (MSG / INS 621), Disodium Inosinate & Guanylate (INS 627/631), Hydrolyzed Vegetable Protein (HVP).
   - Artificial & Non-Nutritive Sweeteners: Sucralose (INS 955), Aspartame (INS 951), Acesulfame Potassium (INS 950), Saccharin (INS 954), Cyclamate (INS 952), High Polyol Laxative loads (Maltitol, Sorbitol).
   - Industrial Emulsifiers & Thickeners: Carboxymethylcellulose (INS 466), Polysorbate 80 (INS 433), Polyglycerol Polyricinoleate (INS 476), Carrageenan (INS 407 - gut mucosal barrier disruption).
   - Cheap Industrial Fats & Refractive Oils: Palm oil, Palmolein, Interesterified vegetable fat, Hydrogenated oils. (Never hallucinate fat or palm oil in soft drinks, sodas, juices, coffee, or teas!).

4. Universal Clinical Severity Rubric for User Health Profile:
   User Health Profile: {user_profile_json}
   - Dynamically cross-reference EVERY identified ingredient and nutritional metric against the user's active health profile (medical conditions, allergies, dietary preferences, and custom avoidance list).
   - Apply clinical point deductions on a standardized, justifiable severity scale:
     * -5 pts (Minor / Trace Friction): Ingredient is slightly suboptimal for the user's condition (e.g. minor refined starch in mild insulin resistance, trace mineral sodium in borderline blood pressure).
     * -7 to -8 pts (Mild Irritation): Mildly aggravates symptoms or causes digestive friction (e.g. mild citric acid in acid sensitivity, refined flours in sluggish digestion).
     * -10 to -12 pts (Moderate Flare-Up Risk): Known trigger likely to provoke symptoms (e.g. carbonation & phosphoric acid in GERD/acidity, >8g added sugar in diabetes, elevated sodium in hypertension, yeast extract in histamine intolerance).
     * -15 to -20 pts (Severe Clinical Escalation): High-impact contraindication that directly worsens pathology (e.g. maltodextrin [GI 110] or liquid glucose in diabetes, excessive MSG/sodium in severe hypertension, high fructose corn syrup in fatty liver/NAFLD, high purines in gout).
     * -30 pts (Direct Allergen / Autoimmune Violation): Direct conflict with user allergy or autoimmune condition (e.g. peanut, soy, gluten in celiac, dairy in cow's milk allergy). Set personalized_warning in bold: "**⚠️ TRIGGERS YOUR ALLERGY — STRICTLY AVOID**", set concern_level "HIGH", and force "personalized_verdict" to "AVOID (VIOLATES PROFILE)".
   - Dietary Restrictions (Vegan, Jain): Deduct -25 to -30 pts and set "AVOID (VIOLATES PROFILE)" if animal fats, gelatin, or root vegetables are detected.

5. Intelligent Holistic Health Scoring (0 to 100) & ICMR-NIN Whole-Food Sparing:
   - Evaluate overall nutritional reality, ingredient purity, and metabolic impact starting from 100.
   - WHOLE-FOOD MATRIX RULE (MANDATORY):
     * Pure whole foods (100% peanut butter, raw almonds, walnuts, seeds, A2 cow ghee, cold-pressed mustard/coconut/olive oils, pure natural cheese) naturally have high caloric and fat density. These are INTRINSIC, BENEFICIAL MACRONUTRIENTS.
     * You MUST NOT penalize clean whole foods for high natural fats! If the ingredient list is clean (single ingredient or minimal whole foods, zero palm oil, zero chemical additives), award scores between 88 and 98/100!
     * Only penalize cheap industrial fats (palm oil, hydrogenated vanaspati, trans fats).
   - Deduct justifiable clinical points if product violates profile conditions per the rubric in Section 4.

6. Clean Indian Alternatives & Market Availability:
   - Provide 2-3 genuine clean commercial Indian alternative products accessible on quick-commerce (Blinkit, Zepto) in the exact same category.
   - If health_score >= 85 and product is already at the peak of clean Indian options, set "cleaner_alternative_exists_in_market": false.
   - If a cleaner, less processed alternative is realistically available, set "cleaner_alternative_exists_in_market": true.

OUTPUT FORMAT:
Return ONLY valid JSON matching this schema:
{
  "is_food_label": true,
  "label_type": "FULL_PANEL",
  "has_ingredients": true,
  "has_nutrition_table": true,
  "cleaner_alternative_exists_in_market": false,
  "product_name": "string",
  "health_score": 0,
  "personalized_verdict": "SAFE FOR YOU", // or "CAUTION" or "AVOID (VIOLATES PROFILE)"
  "simple_summary": "string",
  "deceptive_claims_flagged": ["string"],
  "fssai_violations": ["string"],
  "ingredient_breakdown": [
    {
      "ingredient": "string",
      "purpose": "string",
      "concern_level": "LOW", // "LOW", "MEDIUM", or "HIGH"
      "personalized_warning": "string"
    }
  ],
  "nutrition_card": {
    "serving_size": "100g",
    "calories_kcal": 0.0,
    "total_fat_g": 0.0,
    "saturated_fat_g": 0.0,
    "trans_fat_g": 0.0,
    "total_carbs_g": 0.0,
    "added_sugars_g": 0.0,
    "sodium_mg": 0.0,
    "breakdown": [
      {
        "nutrient": "string",
        "amount_per_100g": "string",
        "daily_value_percent": "string",
        "clinical_evaluation": "string"
      }
    ]
  },
  "nutrient_integrity": {
    "protein": {
      "declared_protein_g": 0.0,
      "usable_protein_g": 0.0,
      "pdcaas_score": 0.5,
      "primary_sources": ["string"],
      "protein_to_calorie_percent": 0.0,
      "amino_spiking_risk": false
    },
    "fiber_type": "Whole Grain",
    "palm_oil_present": false,
    "hidden_sugars_flagged": ["string"],
    "sodium_and_preservatives_risk": "Low",
    "claims_matrix": [
      {
        "claim": "string",
        "status": "VERIFIED", // "VERIFIED", "MISLEADING", or "DECEPTIVE"
        "explanation": "string"
      }
    ]
  },
  "healthier_alternative": {
    "name": "string",
    "key_benefit": "string",
    "price_comparison": "string",
    "personalized_fit": "string"
  },
  "clean_alternatives": [
    {
      "name": "string",
      "key_benefit": "string",
      "price_comparison": "string",
      "personalized_fit": "string"
    }
  ]
}
"""

MULTI_PROFILE_SYSTEM_PROMPT = """You are LabelTruth - an elite Indian food regulatory compliance auditor, forensic label expert, and clinical dietary physician powered by FSSAI regulations (2020 & 2023 Labelling & Display, 2018 Advertising & Claims) and ICMR-NIN 2024 Dietary Guidelines.

CRITICAL TASK: SIMULTANEOUS MULTI-MEMBER HOUSEHOLD AUDIT
You are auditing this food product simultaneously for {num_profiles} specific family household members:
{profiles_text}

CRITICAL CLINICAL MANDATE - INDEPENDENT & DISTINCT EVALUATIONS PER MEMBER:
1. You MUST evaluate this food product INDEPENDENTLY and SEPARATELY for EACH individual profile above based strictly on their specific physiology, medical conditions, allergies, dietary preferences, and custom avoidance list.
2. DO NOT assign the same health score or verdict to all members unless their health conditions and restrictions are 100% identical!
   - Member with Diabetes / Blood Sugar concerns: Heavily penalize added sugars (>2g), liquid glucose, maltodextrin (GI 110), high glycemic flours (-20 to -35 pts). Must receive a lower score and "AVOID (VIOLATES PROFILE)" or "CAUTION".
   - Member with Hypertension / High BP: Heavily penalize sodium (>250mg per 100g) and flavor enhancers (MSG / INS 621, INS 211) (-15 to -25 pts).
   - Member with Allergies (Peanuts, Soy, Gluten/Celiac, Dairy, etc.): If their specific allergen is detected, deduct -35 to -45 pts and force verdict to "AVOID (VIOLATES PROFILE)".
   - Member with Acidity / GERD / Gastritis: Penalize citric acid (INS 330), carbonation, phosphoric acid, and concentrated caffeine (-12 to -20 pts).
   - Member with High Cholesterol / Cardiovascular issues: Heavily penalize palm oil, palmolein, and saturated/trans fats (-15 to -25 pts).
   - Member with Fatty Liver / NAFLD: Heavily penalize high fructose corn syrup, invert sugars, and cheap fats (-15 to -25 pts).
   - Member with NO medical conditions or allergies (e.g. Fitness / General): Evaluate objectively based on the food's purity. DO NOT penalize them for conditions they do not have! If the food is wholesome, award a high score (75-95/100) and "SAFE FOR YOU".
3. For EACH profile in "profiles_audited":
   - "profile_id": Exact profile_id string from the member list above.
   - "profile_name": Exact profile_name string from the member list above.
   - "health_score": (0 to 100) Distinct personalized health score for THIS member.
   - "personalized_verdict": 'SAFE FOR YOU' | 'CAUTION' | 'AVOID (VIOLATES PROFILE)'.
   - "personalized_summary": 2-3 sentences explaining directly to THIS member why this product is safe or unsafe for their personal health profile.
   - "contraindications": Array of specific clinical risk statements for this member (empty array [] if no conflicts).
   - "ingredient_warnings": Array of ingredients where "personalized_warning" is tailored to this member's conditions (empty string if safe for this member, clear bold warning if harmful to them).
4. HOUSEHOLD OVERARCHING DECISION:
   - "household_verdict":
     * 'UNSAFE FOR FAMILY MEMBERS': if ANY evaluated member receives 'AVOID (VIOLATES PROFILE)'.
     * 'PARTIALLY SAFE (CAUTION)': if no member violates, but at least one receives 'CAUTION'.
     * 'SAFE FOR HOUSEHOLD': if all members receive 'SAFE FOR YOU'.
   - "household_summary": Clear family grocery cart advice explaining whether to buy this for the household and identifying bottleneck family members who must avoid it.
   - "comparison_matrix": Array with "profile_name", "health_score", "personalized_verdict", and "key_issue".
5. BASE PRODUCT FOOD FACTS:
   - "product_name": Brand and product name.
   - "base_health_score": Objective un-penalized food score (0-100).
   - "nutrition_card": Standard nutrition facts table per 100g.
   - "nutrient_integrity": Protein quality, fiber, palm oil presence, hidden sugars.
   - "deceptive_claims_flagged": Front-of-pack deceptive marketing claims.
   - "fssai_violations": Any FSSAI labeling/display non-compliance.
   - "healthier_alternative": Cleaner commercial Indian alternative.
   - "clean_alternatives": List of cleaner Indian alternatives.

OUTPUT FORMAT:
Return ONLY valid JSON matching this schema:
{
  "product_name": "string",
  "base_health_score": 0,
  "household_verdict": "SAFE FOR HOUSEHOLD",
  "household_summary": "string",
  "comparison_matrix": [
    {
      "profile_name": "string",
      "health_score": 0,
      "personalized_verdict": "SAFE FOR YOU",
      "key_issue": "string"
    }
  ],
  "profiles_audited": [
    {
      "profile_id": "string",
      "profile_name": "string",
      "health_score": 0,
      "personalized_verdict": "SAFE FOR YOU",
      "personalized_summary": "string",
      "contraindications": ["string"],
      "ingredient_warnings": [
        {
          "ingredient": "string",
          "purpose": "string",
          "concern_level": "LOW",
          "personalized_warning": "string"
        }
      ]
    }
  ],
  "base_product": {
    "product_name": "string",
    "health_score": 0,
    "base_health_score": 0,
    "personalized_verdict": "SAFE FOR YOU",
    "simple_summary": "string",
    "deceptive_claims_flagged": ["string"],
    "fssai_violations": ["string"],
    "ingredient_breakdown": [
      {
        "ingredient": "string",
        "purpose": "string",
        "concern_level": "LOW",
        "personalized_warning": ""
      }
    ],
    "nutrition_card": {
      "serving_size": "100g",
      "calories_kcal": 0.0,
      "total_fat_g": 0.0,
      "saturated_fat_g": 0.0,
      "trans_fat_g": 0.0,
      "total_carbs_g": 0.0,
      "added_sugars_g": 0.0,
      "sodium_mg": 0.0,
      "breakdown": []
    },
    "nutrient_integrity": {
      "protein": {
        "declared_protein_g": 0.0,
        "usable_protein_g": 0.0,
        "pdcaas_score": 0.5,
        "primary_sources": ["string"],
        "protein_to_calorie_percent": 0.0,
        "amino_spiking_risk": false
      },
      "fiber_type": "Whole Grain",
      "palm_oil_present": false,
      "hidden_sugars_flagged": ["string"],
      "sodium_and_preservatives_risk": "Low",
      "claims_matrix": []
    },
    "healthier_alternative": {
      "name": "string",
      "key_benefit": "string",
      "price_comparison": "string",
      "personalized_fit": "string"
    },
    "clean_alternatives": []
  }
}
"""

class GeminiVisionService:
    def __init__(self):
        if GEMINI_API_KEY:
            try:
                self.client = genai.Client(api_key=GEMINI_API_KEY)
            except Exception as e:
                logger.error(f"Failed to init genai Client: {e}")
                self.client = None
        else:
            self.client = None

    async def analyze_label_image(self, image_bytes: bytes, user_profile: UserProfile, bop_supplement_text: str = "") -> LabelAnalysisResult:
        if not self.client:
            raise HTTPException(
                status_code=503,
                detail="All AI models are currently busy or unconfigured. Please try again in a few moments."
            )
            
        profile_json = user_profile.model_dump_json()
        prompt = SYSTEM_PROMPT.replace("{user_profile_json}", profile_json)
        if bop_supplement_text:
            prompt += f"\n\nONLINE BACK-OF-PACK SUPPLEMENTARY DATA:\n{bop_supplement_text}\nUse this back-of-pack data to complete the audit if the image is only Front-of-Pack."
        
        # Resize/compress image to max 1024x1024 JPEG to slash transfer and inference latency by up to 60%
        try:
            pil_img = Image.open(io.BytesIO(image_bytes))
            if pil_img.mode in ("RGBA", "P"):
                pil_img = pil_img.convert("RGB")
            pil_img.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
            buf = io.BytesIO()
            pil_img.save(buf, format="JPEG", quality=82, optimize=True)
            image_bytes = buf.getvalue()
        except Exception as img_err:
            logger.debug(f"Image optimization notice: {img_err}")

        image_part = types.Part.from_bytes(
            data=image_bytes,
            mime_type="image/jpeg",
        )

        last_error = None
        parsed = None

        # Build client pool from all configured keys (or single primary key)
        clients_to_try = [self.client] if self.client else []
        for extra_key in GEMINI_API_KEYS:
            if self.client and extra_key == GEMINI_API_KEY:
                continue
            try:
                clients_to_try.append(genai.Client(api_key=extra_key))
            except Exception:
                pass

        if not clients_to_try:
            raise HTTPException(
                status_code=503,
                detail="All AI models are currently busy or unavailable. Please try again in a few moments."
            )

        for cl in clients_to_try:
            for model_name in FALLBACK_MODELS:
                try:
                    response = cl.models.generate_content(
                        model=model_name,
                        contents=[prompt, image_part],
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            temperature=0.0
                        )
                    )
                    clean_text = response.text.strip()
                    if clean_text.startswith("```json"):
                        clean_text = clean_text[7:]
                    if clean_text.startswith("```"):
                        clean_text = clean_text[3:]
                    if clean_text.endswith("```"):
                        clean_text = clean_text[:-3]
                    parsed = json.loads(clean_text.strip())
                    break
                except Exception as e:
                    err_str = str(e)
                    last_error = e
                    logger.warning(f"Model {model_name} failed for label image ({err_str[:120]}), trying next fallback...")
                    continue
            if parsed:
                break

        # If all Gemini models/keys fail, return honest error (never hardcoded cheese fallback)
        if not parsed:
            logger.error(f"All Gemini Vision models/keys failed: {last_error}")
            raise HTTPException(
                status_code=503,
                detail="All AI models are currently busy or the label text could not be recognized. Please try again in a few moments or upload a clearer photo of the packaging."
            )

        # Normalize ingredient concern levels
        if isinstance(parsed, dict) and "ingredient_breakdown" in parsed:
            for item in parsed.get("ingredient_breakdown", []):
                lvl = str(item.get("concern_level", "LOW")).upper()
                if lvl not in ["LOW", "MEDIUM", "HIGH"]:
                    lvl = "HIGH" if "HIGH" in lvl or "WARN" in lvl else ("MEDIUM" if "MED" in lvl else "LOW")
                item["concern_level"] = lvl
        
        # Ensure healthier_alternative is also mirrored into clean_alternatives if empty
        if parsed.get("healthier_alternative") and not parsed.get("clean_alternatives"):
            parsed["clean_alternatives"] = [parsed["healthier_alternative"]]

        # Beverage Sanity Guard: Clear any accidental palm oil hallucination on liquid drinks / sodas
        prod_lower = str(parsed.get("product_name", "")).lower()
        if any(term in prod_lower for term in ["coca cola", "coke", "pepsi", "thums up", "soda", "sprite", "fanta", "carbonated"]):
            if "nutrient_integrity" in parsed and isinstance(parsed["nutrient_integrity"], dict):
                parsed["nutrient_integrity"]["palm_oil_present"] = False
            if "nutrition_card" in parsed and isinstance(parsed["nutrition_card"], dict):
                parsed["nutrition_card"]["total_fat_g"] = 0.0
                parsed["nutrition_card"]["saturated_fat_g"] = 0.0
                parsed["nutrition_card"]["trans_fat_g"] = 0.0
            # Strip any erroneous palm oil from ingredient list
            if "ingredient_breakdown" in parsed and isinstance(parsed["ingredient_breakdown"], list):
                parsed["ingredient_breakdown"] = [
                    item for item in parsed["ingredient_breakdown"]
                    if "palm" not in str(item.get("ingredient", "")).lower()
                ]

        # Blend AI holistic assessment with mathematical reference engine
        try:
            from app.services.scoring_engine import compute_piecewise_health_score
            score_data = compute_piecewise_health_score(
                nutrition=parsed.get("nutrition_card"),
                ingredients=parsed.get("ingredient_breakdown", []),
                integrity=parsed.get("nutrient_integrity"),
                deceptive_claims=parsed.get("deceptive_claims_flagged", []),
                product_name=parsed.get("product_name", "")
            )
            math_ref_score = score_data["final_health_score"]
            ai_score = int(parsed.get("health_score", 0))

            if ai_score > 0:
                # Use AI score as primary clinical judgement with mathematical reference as anchor
                # Gives 60% weight to AI holistic nuance and 40% to mathematical baseline
                blended_score = int(round(0.60 * ai_score + 0.40 * math_ref_score))
                parsed["health_score"] = max(5, min(100, blended_score))
            else:
                parsed["health_score"] = math_ref_score
        except Exception as score_err:
            logger.warning(f"Error computing piecewise health score: {score_err}")

        return LabelAnalysisResult(**parsed)

    async def analyze_text_query(self, query: str, user_profile: UserProfile, online_content: str = "") -> LabelAnalysisResult:
        """Process text search or URL without an image"""
        if not self.client and not GEMINI_API_KEYS:
            raise HTTPException(
                status_code=503,
                detail="All AI models are currently busy or unconfigured. Please try again in a few moments."
            )

        profile_json = user_profile.model_dump_json()
        prompt = SYSTEM_PROMPT.replace("{user_profile_json}", profile_json)
        prompt += f"\n\nUSER INPUT QUERY: {query}\n\nRETRIEVED PRODUCT DATA:\n{online_content}\nPerform the forensic FSSAI and nutritional audit on this product based on this data."

        last_error = None
        parsed = None

        # Build client pool
        clients_to_try = [self.client] if self.client else []
        for extra_key in GEMINI_API_KEYS:
            if self.client and extra_key == GEMINI_API_KEY:
                continue
            try:
                clients_to_try.append(genai.Client(api_key=extra_key))
            except Exception:
                pass

        if not clients_to_try:
            raise HTTPException(
                status_code=503,
                detail="All AI models are currently busy or unavailable. Please try again in a few moments."
            )

        for cl in clients_to_try:
            for model_name in FALLBACK_MODELS:
                try:
                    response = cl.models.generate_content(
                        model=model_name,
                        contents=[prompt],
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            temperature=0.0
                        )
                    )
                    clean_text = response.text.strip()
                    if clean_text.startswith("```json"):
                        clean_text = clean_text[7:]
                    if clean_text.startswith("```"):
                        clean_text = clean_text[3:]
                    if clean_text.endswith("```"):
                        clean_text = clean_text[:-3]
                    parsed = json.loads(clean_text.strip())
                    break
                except Exception as e:
                    err_str = str(e)
                    last_error = e
                    continue
            if parsed:
                break

        if parsed:
            # Blend AI holistic assessment with mathematical reference engine
            try:
                from app.services.scoring_engine import compute_piecewise_health_score
                score_data = compute_piecewise_health_score(
                    nutrition=parsed.get("nutrition_card"),
                    ingredients=parsed.get("ingredient_breakdown", []),
                    integrity=parsed.get("nutrient_integrity"),
                    deceptive_claims=parsed.get("deceptive_claims_flagged", []),
                    product_name=parsed.get("product_name", "")
                )
                math_ref_score = score_data["final_health_score"]
                ai_score = int(parsed.get("health_score", 0))

                if ai_score > 0:
                    blended_score = int(round(0.60 * ai_score + 0.40 * math_ref_score))
                    parsed["health_score"] = max(5, min(100, blended_score))
                else:
                    parsed["health_score"] = math_ref_score
            except Exception as score_err:
                logger.warning(f"Error computing piecewise health score for text query: {score_err}")

            return LabelAnalysisResult(**parsed)

        # If all Gemini models fail, return honest error (never hardcoded cheese preset)
        logger.error(f"All Gemini models failed for text query '{query}': {last_error}")
        raise HTTPException(
            status_code=503,
            detail=f"All AI models are currently busy or could not retrieve packaging details for '{query}'. Please try again in a few moments."
        )

    def _get_clients_to_try(self):
        clients = [self.client] if self.client else []
        for extra_key in GEMINI_API_KEYS:
            if self.client and extra_key == GEMINI_API_KEY:
                continue
            try:
                clients.append(genai.Client(api_key=extra_key))
            except Exception:
                pass
        return clients

    def _build_multi_profile_prompt(self, profiles: List[UserProfile]) -> str:
        profiles_formatted_lines = []
        for idx, p in enumerate(profiles, 1):
            pid = p.id or f"profile_{idx}"
            pname = p.name or f"Member {idx}"
            conds = ", ".join(p.medical_conditions) if p.medical_conditions else "None declared"
            allergies = ", ".join(p.allergies) if p.allergies else "None declared"
            dietary = ", ".join(p.dietary_preferences) if p.dietary_preferences else "Standard / Omnivore"
            avoid = ", ".join(p.custom_avoid_list) if p.custom_avoid_list else "None declared"
            profiles_formatted_lines.append(
                f"MEMBER {idx} (profile_id: '{pid}', profile_name: '{pname}'):\n"
                f"  - Medical Conditions: {conds}\n"
                f"  - Allergies: {allergies}\n"
                f"  - Dietary Preferences: {dietary}\n"
                f"  - Custom Avoidance List: {avoid}"
            )
        profiles_text = "\n\n".join(profiles_formatted_lines)
        return MULTI_PROFILE_SYSTEM_PROMPT.replace("{profiles_text}", profiles_text).replace("{num_profiles}", str(len(profiles)))

    def _parse_multi_profile_response(
        self,
        parsed: Dict[str, Any],
        profiles: List[UserProfile]
    ) -> MultiProfileScanResult:
        from app.services.profile_evaluator import create_profile_insight_from_base
        base_dict = parsed.get("base_product") or {}
        prod_name = base_dict.get("product_name") or parsed.get("product_name") or "Food Product"
        base_dict["product_name"] = prod_name

        if not base_dict.get("base_health_score"):
            base_dict["base_health_score"] = base_dict.get("health_score", 70)

        # Normalize clean_alternatives
        raw_alts = base_dict.get("clean_alternatives", [])
        clean_alts = []
        for alt in raw_alts:
            if isinstance(alt, str):
                clean_alts.append({
                    "name": alt,
                    "key_benefit": "Cleaner whole-food alternative",
                    "price_comparison": "Comparable",
                    "personalized_fit": "Better nutritional profile"
                })
            elif isinstance(alt, dict):
                clean_alts.append(alt)
        base_dict["clean_alternatives"] = clean_alts

        # Normalize healthier_alternative
        raw_healthy = base_dict.get("healthier_alternative")
        if isinstance(raw_healthy, str):
            base_dict["healthier_alternative"] = {
                "name": raw_healthy,
                "key_benefit": "Cleaner alternative",
                "price_comparison": "Comparable",
                "personalized_fit": "Healthy swap"
            }
        elif not raw_healthy and clean_alts:
            base_dict["healthier_alternative"] = clean_alts[0]
        elif not raw_healthy:
            base_dict["healthier_alternative"] = {
                "name": "Whole Food Alternative",
                "key_benefit": "Minimally processed",
                "price_comparison": "Comparable",
                "personalized_fit": "Whole food nutrition"
            }

        if base_dict.get("healthier_alternative") and not base_dict.get("clean_alternatives"):
            base_dict["clean_alternatives"] = [base_dict["healthier_alternative"]]

        # Normalize nutrition_card breakdown
        if "nutrition_card" in base_dict and isinstance(base_dict["nutrition_card"], dict):
            raw_breakdown = base_dict["nutrition_card"].get("breakdown", [])
            clean_breakdown = []
            for b in raw_breakdown:
                if isinstance(b, dict):
                    clean_breakdown.append({
                        "nutrient": str(b.get("nutrient") or b.get("label") or b.get("name") or "Nutrient"),
                        "amount_per_100g": str(b.get("amount_per_100g") or b.get("value") or b.get("amount") or "0g"),
                        "daily_value_percent": str(b.get("daily_value_percent") or b.get("dv") or "N/A"),
                        "clinical_evaluation": str(b.get("clinical_evaluation") or b.get("evaluation") or "Normal")
                    })
            base_dict["nutrition_card"]["breakdown"] = clean_breakdown

        for ing in base_dict.get("ingredient_breakdown", []):
            ing["personalized_warning"] = ""
            lvl = str(ing.get("concern_level", "LOW")).upper()
            if lvl not in ["LOW", "MEDIUM", "HIGH"]:
                lvl = "HIGH" if "HIGH" in lvl or "WARN" in lvl else ("MEDIUM" if "MED" in lvl else "LOW")
            ing["concern_level"] = lvl

        if not base_dict.get("personalized_verdict"):
            base_dict["personalized_verdict"] = "SAFE FOR YOU" if "SAFE" in parsed.get("household_verdict", "") else "CAUTION"
        elif base_dict["personalized_verdict"] not in ['SAFE FOR YOU', 'CAUTION', 'AVOID (VIOLATES PROFILE)']:
            base_dict["personalized_verdict"] = "CAUTION"
        if not base_dict.get("simple_summary"):
            base_dict["simple_summary"] = parsed.get("household_summary") or "Food evaluation complete."

        base_product = LabelAnalysisResult(**base_dict)

        audited_insights = []
        raw_insights = parsed.get("profiles_audited", [])
        for p in profiles:
            match = next(
                (item for item in raw_insights
                 if str(item.get("profile_id", "")).strip().lower() == str(p.id or "").strip().lower()
                 or str(item.get("profile_name", "")).strip().lower() == str(p.name or "").strip().lower()),
                None
            )
            if match:
                score_val = max(10, min(100, int(match.get("health_score", base_product.health_score))))
                verdict_val = match.get("personalized_verdict", "CAUTION")
                if verdict_val not in ["SAFE FOR YOU", "CAUTION", "AVOID (VIOLATES PROFILE)"]:
                    verdict_val = "AVOID (VIOLATES PROFILE)" if score_val < 45 else ("SAFE FOR YOU" if score_val >= 70 else "CAUTION")
                
                contra = match.get("contraindications", [])
                base_ings = base_product.ingredient_breakdown or []
                raw_warns = match.get("ingredient_warnings", [])
                ing_warns = []

                raw_warn_map = {}
                for w in raw_warns:
                    if isinstance(w, dict) and w.get("ingredient"):
                        raw_warn_map[str(w["ingredient"]).strip().lower()] = w
                    elif isinstance(w, IngredientItem) and w.ingredient:
                        raw_warn_map[str(w.ingredient).strip().lower()] = w.model_dump()

                if base_ings:
                    for base_ing in base_ings:
                        ing_copy = base_ing.model_copy(deep=True)
                        ing_copy.personalized_warning = ""
                        b_name = (ing_copy.ingredient or "").strip().lower()
                        matched_w = raw_warn_map.get(b_name)
                        if not matched_w:
                            for k, v in raw_warn_map.items():
                                if k in b_name or b_name in k:
                                    matched_w = v
                                    break
                        if matched_w:
                            lvl = str(matched_w.get("concern_level", ing_copy.concern_level)).upper()
                            if lvl not in ["LOW", "MEDIUM", "HIGH"]:
                                lvl = "HIGH" if ("HIGH" in lvl or "WARN" in lvl) else ("MEDIUM" if ("MED" in lvl or "MOD" in lvl) else "LOW")
                            ing_copy.concern_level = lvl
                            ing_copy.personalized_warning = str(matched_w.get("personalized_warning") or "")
                            if matched_w.get("purpose"):
                                ing_copy.purpose = str(matched_w.get("purpose"))
                        ing_warns.append(ing_copy)
                else:
                    for ing in raw_warns:
                        if isinstance(ing, dict):
                            lvl = str(ing.get("concern_level", "LOW")).upper()
                            if lvl not in ["LOW", "MEDIUM", "HIGH"]:
                                lvl = "HIGH" if ("HIGH" in lvl or "WARN" in lvl) else ("MEDIUM" if ("MED" in lvl or "MOD" in lvl) else "LOW")
                            ing["concern_level"] = lvl
                            ing_warns.append(IngredientItem(**ing))
                        elif isinstance(ing, IngredientItem):
                            ing_warns.append(ing)

                audited_insights.append(ProfileAuditInsight(
                    profile_id=p.id or match.get("profile_id", "default"),
                    profile_name=p.name or match.get("profile_name", "Member"),
                    health_score=score_val,
                    personalized_verdict=verdict_val,
                    personalized_summary=match.get("personalized_summary", "Evaluated for your dietary profile."),
                    contraindications=contra,
                    ingredient_warnings=ing_warns
                ))
            else:
                audited_insights.append(create_profile_insight_from_base(base_product, p))

        hh_verdict = parsed.get("household_verdict")
        if hh_verdict not in ['SAFE FOR HOUSEHOLD', 'PARTIALLY SAFE (CAUTION)', 'UNSAFE FOR FAMILY MEMBERS']:
            any_avoid = any(ins.personalized_verdict == "AVOID (VIOLATES PROFILE)" for ins in audited_insights)
            any_caution = any(ins.personalized_verdict == "CAUTION" for ins in audited_insights)
            hh_verdict = "UNSAFE FOR FAMILY MEMBERS" if any_avoid else ("PARTIALLY SAFE (CAUTION)" if any_caution else "SAFE FOR HOUSEHOLD")

        hh_summary = parsed.get("household_summary")
        if not hh_summary:
            if hh_verdict == "UNSAFE FOR FAMILY MEMBERS":
                violators = [ins.profile_name for ins in audited_insights if ins.personalized_verdict == "AVOID (VIOLATES PROFILE)"]
                hh_summary = f"Not recommended for family purchase: violates health profile for {', '.join(violators)}."
            elif hh_verdict == "PARTIALLY SAFE (CAUTION)":
                cautions = [ins.profile_name for ins in audited_insights if ins.personalized_verdict == "CAUTION"]
                hh_summary = f"Safe for some members, but exercise caution for {', '.join(cautions)}."
            else:
                hh_summary = "Safe for all evaluated family members with no major clinical contraindications."

        comparison_matrix = parsed.get("comparison_matrix") or [
            {
                "profile_name": ins.profile_name,
                "health_score": ins.health_score,
                "personalized_verdict": ins.personalized_verdict,
                "key_issue": ins.contraindications[0] if ins.contraindications else ("Low nutritional quality" if ins.health_score < 45 else "Clean profile fit")
            }
            for ins in audited_insights
        ]

        return MultiProfileScanResult(
            product_name=base_product.product_name,
            base_product=base_product,
            profiles_audited=audited_insights,
            household_verdict=hh_verdict,
            household_summary=hh_summary,
            comparison_matrix=comparison_matrix
        )

    async def analyze_multi_profile_image(
        self,
        image_bytes: bytes,
        profiles: List[UserProfile],
        bop_supplement_text: str = ""
    ) -> MultiProfileScanResult:
        from app.services.profile_evaluator import create_multi_profile_result_offline
        clients_to_try = self._get_clients_to_try()
        if not clients_to_try:
            logger.warning("No Gemini client available for multi-profile image audit, using offline fallback")
            base_res = await self.analyze_label_image(image_bytes, profiles[0] if profiles else UserProfile())
            return create_multi_profile_result_offline(base_res, profiles)

        prompt = self._build_multi_profile_prompt(profiles)
        if bop_supplement_text:
            prompt += f"\n\nONLINE BACK-OF-PACK SUPPLEMENTARY DATA:\n{bop_supplement_text}\nUse this back-of-pack data to complete the audit if the image is only Front-of-Pack."

        try:
            pil_img = Image.open(io.BytesIO(image_bytes))
            if pil_img.mode in ("RGBA", "P"):
                pil_img = pil_img.convert("RGB")
            pil_img.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
            buf = io.BytesIO()
            pil_img.save(buf, format="JPEG", quality=82, optimize=True)
            image_bytes = buf.getvalue()
        except Exception as img_err:
            logger.debug(f"Image optimization notice: {img_err}")

        image_part = types.Part.from_bytes(
            data=image_bytes,
            mime_type="image/jpeg",
        )

        last_error = None
        parsed = None

        for cl in clients_to_try:
            for model_name in FALLBACK_MODELS:
                try:
                    response = cl.models.generate_content(
                        model=model_name,
                        contents=[prompt, image_part],
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            temperature=0.0
                        )
                    )
                    clean_text = response.text.strip()
                    if clean_text.startswith("```json"):
                        clean_text = clean_text[7:]
                    if clean_text.startswith("```"):
                        clean_text = clean_text[3:]
                    if clean_text.endswith("```"):
                        clean_text = clean_text[:-3]
                    parsed = json.loads(clean_text.strip())
                    break
                except Exception as e:
                    last_error = e
                    continue
            if parsed:
                break

        if not parsed:
            logger.error(f"All Gemini models failed for multi-profile image: {last_error}")
            base_res = await self.analyze_label_image(image_bytes, profiles[0] if profiles else UserProfile())
            return create_multi_profile_result_offline(base_res, profiles)

        return self._parse_multi_profile_response(parsed, profiles)

    async def analyze_multi_profile_text_query(
        self,
        query: str,
        profiles: List[UserProfile],
        online_content: str = ""
    ) -> MultiProfileScanResult:
        from app.services.profile_evaluator import create_multi_profile_result_offline
        clients_to_try = self._get_clients_to_try()
        if not clients_to_try:
            logger.warning("No Gemini client available for multi-profile text query, using offline fallback")
            base_res = await self.analyze_text_query(query, profiles[0] if profiles else UserProfile(), online_content)
            return create_multi_profile_result_offline(base_res, profiles)

        prompt = self._build_multi_profile_prompt(profiles)
        prompt += f"\n\nUSER INPUT QUERY: {query}\n\nRETRIEVED PRODUCT PACKAGING DATA:\n{online_content}\nPerform the simultaneous multi-profile household audit based on this packaging data."

        last_error = None
        parsed = None

        for cl in clients_to_try:
            for model_name in FALLBACK_MODELS:
                try:
                    response = cl.models.generate_content(
                        model=model_name,
                        contents=[prompt],
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            temperature=0.0
                        )
                    )
                    clean_text = response.text.strip()
                    if clean_text.startswith("```json"):
                        clean_text = clean_text[7:]
                    if clean_text.startswith("```"):
                        clean_text = clean_text[3:]
                    if clean_text.endswith("```"):
                        clean_text = clean_text[:-3]
                    parsed = json.loads(clean_text.strip())
                    break
                except Exception as e:
                    last_error = e
                    continue
            if parsed:
                break

        if not parsed:
            logger.error(f"All Gemini models failed for multi-profile query '{query}': {last_error}")
            base_res = await self.analyze_text_query(query, profiles[0] if profiles else UserProfile(), online_content)
            return create_multi_profile_result_offline(base_res, profiles)

        return self._parse_multi_profile_response(parsed, profiles)


gemini_vision_service = GeminiVisionService()
