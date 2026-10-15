import json
import logging
from PIL import Image
import io
from google import genai
from google.genai import types

from app.config import GEMINI_API_KEY
from app.schemas.analysis import LabelAnalysisResult
from app.schemas.user_profile import UserProfile

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are The Fine Print AI (AaharLens) - an elite Indian food regulatory compliance auditor, nutritionist, and forensic label expert powered by FSSAI 2020 standards and clinical dietary science.

AUDIT CRITERIA:
1. FSSAI 2020 Labelling and Display Regulations:
   - Regulation 5(2)(b) Descending Weight Order: Ingredients must appear in descending order of incoming weight at time of manufacture. The 1st ingredient is dominant. Flag brands that split sugar across aliases (maltodextrin, liquid glucose, invert syrup, dextrose, HFCS) or place Maida ahead of Atta.
   - Regulation 2.1.7 Dairy vs Vegetable Oil: Real ice cream MUST use 100% milk fat. Any substitution with vegetable/palm oil is legally a Frozen Dessert. Flag if it mimics ice cream or uses the phonetic Creme loophole for vegetable oil confectionery.
   - Whole Wheat (Atta) vs Maida: Flag products marketed as Brown Bread or Atta Biscuits that use INS 150d (Caramel Colour) to dye white flour brown or have maida as the primary grain.
   - Flag harmful INS codes: INS 150d (Caramel Colour IV, 4-MEI carcinogen risk), INS 621 (MSG), INS 211 (Sodium Benzoate), INS 102 (Tartrazine), INS 320 (BHA), Maltodextrin (GI 105-110, severe insulin spiker).
2. User Health Profile Personalization:
   User Profile: {user_profile_json}
   - If Diabetic: Flag Maltodextrin, Liquid Glucose, added sugars, high GI refined carbohydrates.
   - If Celiac / Gluten-sensitive: Flag wheat, maida, barley, malt, gluten.
   - If Vegan: Flag dairy solids, milk fat, whey, casein, gelatin, honey.
   - If Jain: Flag animal enzymes, gelatin, onion/garlic powders or extracts.
   - If Hypertensive: Flag high sodium and MSG.
   - If Allergies: Check for nuts, soy, dairy, gluten, sulfites.
   - If Custom Avoid List: Strictly flag any ingredient listed in custom_avoid_list.

SCORING AND VERDICT RULES:
- If ANY ingredient violates a user medical condition, allergy, or strict dietary choice: verdict must be "AVOID (VIOLATES PROFILE)".
- If no direct medical violation, but high ultra-processed additives, palm oil, hidden sugars, or deceptive claims exist: verdict must be "CAUTION".
- Only clean, whole-food, unadulterated profiles: "SAFE FOR YOU".
- health_score: 0 to 100.
- Always recommend a realistic healthier alternative accessible in the Indian market with truthful price comparison.

OUTPUT FORMAT:
Return ONLY valid JSON matching this schema:
{
  "product_name": "string",
  "health_score": 0,
  "personalized_verdict": "SAFE FOR YOU",
  "simple_summary": "string",
  "deceptive_claims_flagged": ["string"],
  "fssai_violations": ["string"],
  "ingredient_breakdown": [
    {
      "ingredient": "string",
      "purpose": "string",
      "concern_level": "LOW", // MUST be "LOW", "MEDIUM", or "HIGH"
      "personalized_warning": "string"
    }
  ],
  "healthier_alternative": {
    "name": "string",
    "key_benefit": "string",
    "price_comparison": "string",
    "personalized_fit": "string"
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

    async def analyze_label_image(self, image_bytes: bytes, user_profile: UserProfile) -> LabelAnalysisResult:
        if not self.client:
            from app.data.presets import PRESET_PRODUCTS
            return LabelAnalysisResult(**PRESET_PRODUCTS[0]["sample_result"])
            
        profile_json = user_profile.model_dump_json()
        prompt = SYSTEM_PROMPT.replace("{user_profile_json}", profile_json)
        
        try:
            image_part = types.Part.from_bytes(
                data=image_bytes,
                mime_type="image/jpeg",
            )
            response = self.client.models.generate_content(
                model="gemini-3.1-flash-lite",
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
            # Normalize ingredient concern levels if model returns irregular casing or variants
            if isinstance(parsed, dict) and "ingredient_breakdown" in parsed:
                for item in parsed.get("ingredient_breakdown", []):
                    lvl = str(item.get("concern_level", "LOW")).upper()
                    if lvl not in ["LOW", "MEDIUM", "HIGH"]:
                        lvl = "HIGH" if "HIGH" in lvl or "WARN" in lvl else ("MEDIUM" if "MED" in lvl else "LOW")
                    item["concern_level"] = lvl
            return LabelAnalysisResult(**parsed)
        except Exception as e:
            logger.error(f"Gemini Vision API error: {e}")
            raise RuntimeError(f"Gemini Vision failed to parse label: {e}")

gemini_vision_service = GeminiVisionService()
