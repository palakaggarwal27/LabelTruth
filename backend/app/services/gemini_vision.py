import json
import logging
from PIL import Image
import io
from google import genai
from google.genai import types

from app.config import GEMINI_API_KEY
from app.schemas.analysis import LabelAnalysisResult, NutrientIntegrityMatrix, ProteinAudit
from app.schemas.user_profile import UserProfile

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are LabelTruth - an elite Indian food regulatory compliance auditor, nutritionist, and forensic label expert powered by FSSAI 2020 standards and clinical dietary science.

AUDIT CRITERIA:
1. Relevance & Label Classification:
   - Determine if this image is a genuine food product, food package, or nutritional panel.
   - If it is NOT food or food packaging (e.g., photo of a cat, wall, car, human face, unrelated object), set "is_food_label": false and "label_type": "NOT_A_LABEL".
   - If it is only the Front-of-Pack (branding, marketing claims, hero images, no detailed ingredients), set "label_type": "FRONT_OF_PACK".
   - If it is Back-of-Pack (ingredient list, nutrition facts table, barcode), set "label_type": "BACK_OF_PACK".
   - If both or complete, set "label_type": "FULL_PANEL".

2. FSSAI 2020 Labelling and Display Regulations:
   - Regulation 5(2)(b) Descending Weight Order: Ingredients must appear in descending order of incoming weight at time of manufacture. Flag brands that split sugar across aliases (maltodextrin, liquid glucose, invert syrup, dextrose, HFCS) or place Maida ahead of Atta.
   - Regulation 2.1.7 Dairy vs Vegetable Oil: Real ice cream MUST use 100% milk fat. Any substitution with vegetable/palm oil is legally a Frozen Dessert.
   - Whole Wheat (Atta) vs Maida: Flag products marketed as Brown Bread or Atta Biscuits that use INS 150d (Caramel Colour) to dye white flour brown or have maida as the primary grain.
   - Flag harmful INS codes: INS 150d (Caramel Colour IV, 4-MEI carcinogen risk), INS 621 (MSG), INS 627/631 (flavour enhancers), INS 211 (Sodium Benzoate), INS 102 (Tartrazine), INS 320 (BHA), Maltodextrin (GI 105-110).

3. Nutrient Card Breakdown & Nutrient Integrity Audit:
   - Detailed Nutritional Panel (MANDATORY): You MUST ALWAYS construct and return the complete "nutrition_card" object with values for serving_size, calories_kcal, total_fat_g, saturated_fat_g, trans_fat_g, total_carbs_g, added_sugars_g, sodium_mg, and itemized breakdown list.
   - If the uploaded image only shows the ingredient list or front-of-pack and lacks a visible nutrition table, use the ONLINE BACK-OF-PACK SUPPLEMENTARY DATA or scientifically estimate the exact nutritional values per 100g based on the ingredient composition and product category. Do NOT return an empty or null nutrition_card!
   - Protein Reality & PDCAAS: Calculate declared protein, estimate usable bioavailable protein using PDCAAS score (e.g. Soy=0.91, Whey=1.0, Wheat/Gluten=0.25-0.4), identify protein sources, protein-to-calorie percentage, and amino spiking risk (added free Glycine/Taurine).
   - Fiber Quality: Classify fiber as Whole Grain vs. synthetic isolate (polydextrose, chicory root inulin).
   - Fat & Oil Audit: Expose Palm Oil or trans fats hidden behind "0% Cholesterol" claims ONLY IF fats/oils are present. NEVER hallucinate palm oil or fat in carbonated soft drinks, sodas, colas (e.g. Coca-Cola, Pepsi), fruit juices, or tea/coffee — they contain 0g fat and 0g palm oil!
   - Sugar Audit: Expose disguised sugars (maltodextrin, concentrated fruit juice, invert sugar).
   - Claims Matrix: Audit each front-of-pack claim and classify as "VERIFIED", "MISLEADING", or "DECEPTIVE".

4. User Health Profile Personalization:
   User Profile: {user_profile_json}
   - Flag specific contraindications for diabetes, celiac/gluten, vegan, jain, hypertension, allergies, and custom avoidance list.

5. Scoring & Clean Indian Alternatives:
   - health_score: 0 to 100.
   - Provide 2-3 clean whole-food Indian alternative products accessible on quick-commerce (Blinkit, Zepto).

OUTPUT FORMAT:
Return ONLY valid JSON matching this schema:
{
  "is_food_label": true,
  "label_type": "FULL_PANEL",
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
            from app.data.presets import PRESET_PRODUCTS
            return LabelAnalysisResult(**PRESET_PRODUCTS[0]["sample_result"])
            
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

        FALLBACK_MODELS = ["gemini-3.1-flash-lite", "gemini-2.5-flash", "gemini-2.0-flash"]
        last_error = None
        parsed = None

        for model_name in FALLBACK_MODELS:
            try:
                response = self.client.models.generate_content(
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
                if "503" not in err_str and "429" not in err_str and "UNAVAILABLE" not in err_str:
                    break

        if not parsed:
            raise RuntimeError(
                f"Gemini Vision API is currently experiencing high global demand (503). "
                f"Please test with our preset products or switch on DEMO MODE (zero credits) to explore instant deterministic audits."
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

        # Apply Piecewise Mathematical Scoring Engine (FSSAI 2020/2023, ICMR-NIN 2024, WHO SEARO)
        try:
            from app.services.scoring_engine import compute_piecewise_health_score
            score_data = compute_piecewise_health_score(
                nutrition=parsed.get("nutrition_card"),
                ingredients=parsed.get("ingredient_breakdown", []),
                integrity=parsed.get("nutrient_integrity"),
                deceptive_claims=parsed.get("deceptive_claims_flagged", []),
                product_name=parsed.get("product_name", "")
            )
            parsed["health_score"] = score_data["final_health_score"]
        except Exception as score_err:
            logger.warning(f"Error computing piecewise health score: {score_err}")

        return LabelAnalysisResult(**parsed)

    async def analyze_text_query(self, query: str, user_profile: UserProfile, online_content: str = "") -> LabelAnalysisResult:
        """Process text search or URL without an image"""
        if not self.client:
            from app.data.presets import PRESET_PRODUCTS
            return LabelAnalysisResult(**PRESET_PRODUCTS[0]["sample_result"])

        profile_json = user_profile.model_dump_json()
        prompt = SYSTEM_PROMPT.replace("{user_profile_json}", profile_json)
        prompt += f"\n\nUSER INPUT QUERY: {query}\n\nRETRIEVED PRODUCT DATA:\n{online_content}\nPerform the forensic FSSAI and nutritional audit on this product based on this data."

        FALLBACK_MODELS = ["gemini-3.1-flash-lite", "gemini-2.5-flash", "gemini-2.0-flash"]
        last_error = None

        for model_name in FALLBACK_MODELS:
            try:
                response = self.client.models.generate_content(
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
                # Apply Piecewise Mathematical Scoring Engine (FSSAI 2020/2023, ICMR-NIN 2024, WHO SEARO)
                try:
                    from app.services.scoring_engine import compute_piecewise_health_score
                    score_data = compute_piecewise_health_score(
                        nutrition=parsed.get("nutrition_card"),
                        ingredients=parsed.get("ingredient_breakdown", []),
                        integrity=parsed.get("nutrient_integrity"),
                        deceptive_claims=parsed.get("deceptive_claims_flagged", []),
                        product_name=parsed.get("product_name", "")
                    )
                    parsed["health_score"] = score_data["final_health_score"]
                except Exception as score_err:
                    logger.warning(f"Error computing piecewise health score for text query: {score_err}")

                return LabelAnalysisResult(**parsed)
            except Exception as e:
                err_str = str(e)
                last_error = e
                logger.warning(f"Model {model_name} failed for text query ({err_str[:120]}), trying next fallback...")
                if "503" not in err_str and "429" not in err_str and "UNAVAILABLE" not in err_str:
                    break

        # If all Gemini models are experiencing high demand / 503, try TinyFish Agentic Web Audit
        logger.warning(f"All Gemini models busy ({last_error}). Invoking TinyFish Web Agent fallback for '{query}'...")
        try:
            from app.services.tinyfish_service import tinyfish_service
            tf_result = await tinyfish_service.audit_product_via_agent(query, user_profile)
            if tf_result:
                from app.services.profile_evaluator import evaluate_profile_safety_offline
                res = LabelAnalysisResult(**tf_result)
                eval_res = evaluate_profile_safety_offline(res, user_profile)
                res.personalized_verdict = eval_res["personalized_verdict"]
                return res
        except Exception as tf_agent_err:
            logger.warning(f"TinyFish agent fallback attempt error: {tf_agent_err}")

        # If TinyFish not applicable, match with our rich local product catalog
        from app.data.presets import PRESET_PRODUCTS
        q_low = query.lower()
        matched_preset = None
        for p in PRESET_PRODUCTS:
            p_name = p.get("title", "").lower() + " " + p.get("subtitle", "").lower() + " " + p.get("sample_result", {}).get("product_name", "").lower()
            if any(term in q_low for term in p_name.split()):
                matched_preset = p["sample_result"]
                break
        
        if matched_preset:
            from app.services.profile_evaluator import evaluate_profile_safety_offline
            res = LabelAnalysisResult(**matched_preset)
            eval_res = evaluate_profile_safety_offline(res, user_profile)
            res.personalized_verdict = eval_res["personalized_verdict"]
            return res

        raise RuntimeError(
            "Gemini AI is currently experiencing high global demand (503). "
            "Please switch on DEMO MODE (zero credits) to explore instant deterministic audits, or retry in a few moments."
        )

gemini_vision_service = GeminiVisionService()
