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

3. Nutrient Integrity & Bioavailability Audit:
   - Protein Reality & PDCAAS: Calculate declared protein, estimate usable bioavailable protein using PDCAAS score (e.g. Soy=0.91, Whey=1.0, Wheat/Gluten=0.25-0.4), identify protein sources, protein-to-calorie percentage, and amino spiking risk (added free Glycine/Taurine).
   - Fiber Quality: Classify fiber as Whole Grain vs. synthetic isolate (polydextrose, chicory root inulin).
   - Fat Audit: Expose Palm Oil or trans fats hidden behind "0% Cholesterol" or "Light" claims.
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

            return LabelAnalysisResult(**parsed)
        except Exception as e:
            logger.error(f"Gemini Vision API error: {e}")
            raise RuntimeError(f"Gemini Vision failed to parse label: {e}")

    async def analyze_text_query(self, query: str, user_profile: UserProfile, online_content: str = "") -> LabelAnalysisResult:
        """Process text search or URL without an image"""
        if not self.client:
            from app.data.presets import PRESET_PRODUCTS
            return LabelAnalysisResult(**PRESET_PRODUCTS[0]["sample_result"])

        profile_json = user_profile.model_dump_json()
        prompt = SYSTEM_PROMPT.replace("{user_profile_json}", profile_json)
        prompt += f"\n\nUSER INPUT QUERY: {query}\n\nRETRIEVED PRODUCT DATA:\n{online_content}\nPerform the forensic FSSAI and nutritional audit on this product based on this data."

        try:
            response = self.client.models.generate_content(
                model="gemini-3.1-flash-lite",
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
            return LabelAnalysisResult(**parsed)
        except Exception as e:
            logger.error(f"Gemini Text Query API error: {e}")
            raise RuntimeError(f"Failed to audit product text: {e}")

gemini_vision_service = GeminiVisionService()
