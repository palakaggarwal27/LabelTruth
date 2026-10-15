import json
import logging
from typing import Optional
from google import genai
from google.genai import types

from app.config import GEMINI_API_KEY
from app.schemas.condition import ValidateConditionResponse

logger = logging.getLogger(__name__)

VALIDATION_SYSTEM_PROMPT = """You are LabelTruth Medical and Food Science Validator.
Verify if the following string is a legitimate health condition, medical diagnosis, food allergy, dietary restriction, or chemical food ingredient/additive.
Return JSON strictly adhering to this format:
{
  "is_valid": true or false,
  "standardized_name": "Standardized Clinical/Additive Name",
  "reason": "Brief explanation of health relevance or ingredient classification."
}
If it is gibberish, spam, unrelated text, or not a recognized dietary/medical/chemical term, set is_valid to false.
"""

# Comprehensive clinical & additive dictionary for fast, token-efficient, zero-latency validation
KNOWN_STANDARDS = {
    "e102": ("Tartrazine (INS 102)", "Synthetic azo food dye linked to pediatric hyperactivity and asthma.", True),
    "tartrazine": ("Tartrazine (INS 102)", "Synthetic azo food dye linked to pediatric hyperactivity and asthma.", True),
    "ins 102": ("Tartrazine (INS 102)", "Synthetic azo food dye linked to pediatric hyperactivity and asthma.", True),
    "ins 150d": ("Caramel Colour IV (INS 150d)", "Ammonia-process colorant containing 4-MEI carcinogen risk.", True),
    "caramel colour": ("Caramel Colour IV (INS 150d)", "Ammonia-process colorant containing 4-MEI carcinogen risk.", True),
    "ins 621": ("Monosodium Glutamate (MSG)", "Flavor enhancer linked to excitotoxicity and headaches.", True),
    "msg": ("Monosodium Glutamate (MSG)", "Flavor enhancer linked to excitotoxicity and headaches.", True),
    "palm oil": ("Palm Oil / Palmitic Fat", "High saturated atherogenic fat often replacing dairy.", True),
    "maltodextrin": ("Maltodextrin", "Ultra-high Glycemic Index (105-110) bulking agent spiking blood sugar.", True),
    "maltitol": ("Maltitol", "Sugar alcohol polyol with laxative effects and moderate glycemic impact.", True),
    "histamine intolerance": ("Histamine Intolerance", "Inability to metabolize dietary histamine causing allergy-like symptoms.", True),
    "sucralose": ("Sucralose (INS 955)", "Artificial non-nutritive sweetener affecting gut microbiome.", True),
    "aspartame": ("Aspartame (INS 951)", "Artificial intense sweetener containing phenylalanine.", True),
    "sodium benzoate": ("Sodium Benzoate (INS 211)", "Chemical preservative that can synthesize benzene with Vitamin C.", True),
    "ins 211": ("Sodium Benzoate (INS 211)", "Chemical preservative that can synthesize benzene with Vitamin C.", True),
    "bha": ("BHA (INS 320)", "Synthetic antioxidant classified as possibly carcinogenic to humans.", True),
    "ins 320": ("BHA (INS 320)", "Synthetic antioxidant classified as possibly carcinogenic to humans.", True),
    "pku": ("Phenylketonuria (PKU)", "Genetic metabolic disorder requiring zero dietary phenylalanine.", True),
    "gout": ("Hyperuricemia (Gout)", "High uric acid requiring low-purine and low-fructose dietary profile.", True),
    "high uric acid": ("Hyperuricemia (Gout)", "High uric acid requiring low-purine and low-fructose dietary profile.", True),
    "ibs": ("Irritable Bowel Syndrome (IBS)", "Gastrointestinal disorder sensitive to FODMAPs and emulsifiers.", True),
    "gerd": ("Acid Reflux / GERD", "Digestive condition aggravated by high acidity and excessive spice.", True),
    "corn syrup": ("High Fructose Corn Syrup (HFCS)", "High-fructose corn sweetener linked to non-alcoholic fatty liver disease.", True),
    "hfcs": ("High Fructose Corn Syrup (HFCS)", "High-fructose corn sweetener linked to non-alcoholic fatty liver disease.", True),
    "soy lecithin": ("Soy Lecithin (INS 322)", "Emulsifier derived from soy; potential allergen for sensitive individuals.", True),
    "sesame": ("Sesame Allergy", "Severe IgE-mediated food allergy requiring complete avoidance of sesame.", True),
    "shellfish": ("Shellfish / Seafood Allergy", "Severe allergen triggering anaphylaxis in sensitive individuals.", True)
}

class ConditionValidationService:
    def __init__(self):
        if GEMINI_API_KEY:
            try:
                self.client = genai.Client(api_key=GEMINI_API_KEY)
            except Exception as e:
                logger.error(f"Failed to init Gemini client in condition validator: {e}")
                self.client = None
        else:
            self.client = None

    async def validate(self, query: str) -> ValidateConditionResponse:
        cleaned = query.strip().lower()
        if not cleaned:
            return ValidateConditionResponse(
                is_valid=False,
                standardized_name="",
                reason="Input cannot be empty."
            )

        # Check local clinical dictionary first (instant & 0 credit cost)
        if cleaned in KNOWN_STANDARDS:
            std_name, reason, valid = KNOWN_STANDARDS[cleaned]
            return ValidateConditionResponse(is_valid=valid, standardized_name=std_name, reason=reason)

        for key, (std_name, reason, valid) in KNOWN_STANDARDS.items():
            if key in cleaned or cleaned in key:
                return ValidateConditionResponse(is_valid=valid, standardized_name=std_name, reason=reason)

        # If Gemini client is active, query Gemini Flash with strict JSON schema
        if self.client:
            try:
                prompt = f"{VALIDATION_SYSTEM_PROMPT}\n\nTerm to verify: {query.strip()}"
                response = self.client.models.generate_content(
                    model="gemini-3.1-flash-lite",
                    contents=prompt,
                    config=types.GenerateContentConfig(response_mime_type="application/json")
                )
                clean_text = response.text.strip()
                if clean_text.startswith("```json"):
                    clean_text = clean_text[7:]
                if clean_text.startswith("```"):
                    clean_text = clean_text[3:]
                if clean_text.endswith("```"):
                    clean_text = clean_text[:-3]
                parsed = json.loads(clean_text.strip())
                return ValidateConditionResponse(**parsed)
            except Exception as e:
                logger.error(f"Gemini condition validation error: {e}")

        # If not in KNOWN_STANDARDS and Gemini validation could not confirm or rejected
        return ValidateConditionResponse(
            is_valid=False,
            standardized_name=query.strip(),
            reason="Please enter a recognized health condition, medical diagnosis, allergy, or food additive."
        )

condition_validation_service = ConditionValidationService()
