import json
import logging
from typing import Optional
from google import genai
from google.genai import types

from app.config import GEMINI_API_KEY, GEMINI_API_KEYS
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
    "acidity": ("Acidity / Acid Reflux (GERD)", "Gastric sensitivity triggered by citric acid, excessive caffeine, artificial souring agents, or chili.", True),
    "acid reflux": ("Acid Reflux / GERD", "Digestive condition aggravated by high acidity, carbonation, and excessive spice.", True),
    "gastritis": ("Gastritis", "Inflammation of the stomach lining triggered by acidic additives, artificial preservatives, and spicy irritants.", True),
    "fatty liver": ("Non-Alcoholic Fatty Liver Disease (NAFLD)", "Metabolic liver condition aggravated by high fructose corn syrup, invert sugars, and trans fats.", True),
    "nafld": ("Non-Alcoholic Fatty Liver Disease (NAFLD)", "Metabolic liver condition aggravated by high fructose corn syrup, invert sugars, and trans fats.", True),
    "pcos": ("Polycystic Ovary Syndrome (PCOS)", "Endocrine/insulin condition sensitive to high-GI refined carbs, added sugars, and inflammatory fats.", True),
    "lactose": ("Lactose Intolerance", "Inability to digest milk sugar (lactose) causing digestive distress.", True),
    "lactose intolerance": ("Lactose Intolerance", "Inability to digest milk sugar (lactose) causing digestive distress.", True),
    "dairy allergy": ("Dairy / Milk Protein Allergy", "Allergic reaction to casein or whey proteins requiring strict dairy exclusion.", True),
    "celiac": ("Celiac Disease", "Autoimmune enteropathy triggered by gluten in wheat, rye, and barley.", True),
    "celiac disease": ("Celiac Disease", "Autoimmune enteropathy triggered by gluten in wheat, rye, and barley.", True),
    "diabetes": ("Type 2 Diabetes / Pre-diabetes", "Metabolic disorder requiring strict avoidance of high-GI sugars, maltodextrin, and liquid glucose.", True),
    "hypertension": ("Hypertension (High Blood Pressure)", "Cardiovascular condition aggravated by excess sodium, MSG, and sodium benzoate.", True),
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

        # If client is active, query active Gemini models with strict JSON schema
        ACTIVE_MODELS = [
            "gemini-flash-lite-latest",
            "gemini-3.5-flash-lite",
            "gemini-3.1-flash-lite",
            "gemini-3.8-flash",
            "gemini-flash-latest"
        ]

        clients_to_try = [self.client] if self.client else []
        for extra_key in GEMINI_API_KEYS:
            if self.client and extra_key == GEMINI_API_KEY:
                continue
            try:
                clients_to_try.append(genai.Client(api_key=extra_key))
            except Exception:
                pass

        prompt = f"{VALIDATION_SYSTEM_PROMPT}\n\nTerm to verify: {query.strip()}"
        for cl in (clients_to_try or [self.client]):
            if not cl:
                continue
            for model_name in ACTIVE_MODELS:
                try:
                    response = cl.models.generate_content(
                        model=model_name,
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
                    logger.warning(f"Condition validation model {model_name} failed: {e}")
                    continue

        # If not in KNOWN_STANDARDS and Gemini validation could not confirm or rejected
        return ValidateConditionResponse(
            is_valid=False,
            standardized_name=query.strip(),
            reason="Please enter a recognized health condition, medical diagnosis, allergy, or food additive."
        )

condition_validation_service = ConditionValidationService()
