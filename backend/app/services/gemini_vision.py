import json
import logging
from PIL import Image
import io
from fastapi import HTTPException
from google import genai
from google.genai import types

from app.config import GEMINI_API_KEY, GEMINI_API_KEYS
from app.schemas.analysis import LabelAnalysisResult, NutrientIntegrityMatrix, ProteinAudit
from app.schemas.user_profile import UserProfile

logger = logging.getLogger(__name__)

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

        FALLBACK_MODELS = [
            "gemini-flash-lite-latest",
            "gemini-2.5-flash-lite",
            "gemini-2.5-flash",
            "gemini-flash-latest"
        ]
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
                            response_mime_type="application/json"
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

        FALLBACK_MODELS = [
            "gemini-flash-lite-latest",
            "gemini-2.5-flash-lite",
            "gemini-2.5-flash",
            "gemini-flash-latest"
        ]
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
                            response_mime_type="application/json"
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


gemini_vision_service = GeminiVisionService()
