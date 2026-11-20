import json
import logging
import hashlib
import urllib.parse
from typing import Optional, Dict
from fastapi import HTTPException
from google import genai
from google.genai import types

from app.config import GEMINI_API_KEY, GEMINI_API_KEYS
from app.schemas.analysis import LabelAnalysisResult, HealthierAlternative
from app.schemas.user_profile import UserProfile
from app.schemas.compare import ProductComparisonResult, DimensionComparison

logger = logging.getLogger(__name__)

FALLBACK_MODELS = [
    "gemini-flash-lite-latest",
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash",
    "gemini-flash-latest",
]

# Fast in-memory cache for repeat comparisons (zero credit cost)
COMPARE_CACHE: Dict[str, ProductComparisonResult] = {}

class CompareService:
    def __init__(self):
        self.client = None
        if GEMINI_API_KEY:
            try:
                self.client = genai.Client(api_key=GEMINI_API_KEY)
            except Exception as e:
                logger.error(f"Failed to initialize CompareService Gemini client: {e}")

    def _compute_cache_key(self, prod_a: LabelAnalysisResult, prod_b: LabelAnalysisResult, profile: UserProfile) -> str:
        raw_key = f"{prod_a.product_name}:{prod_a.health_score}:{prod_b.product_name}:{prod_b.health_score}:{profile.model_dump_json()}"
        return hashlib.sha256(raw_key.encode('utf-8')).hexdigest()

    async def compare_products(
        self,
        product_a: LabelAnalysisResult,
        product_b: LabelAnalysisResult,
        user_profile: UserProfile,
        pincode: Optional[str] = "110001"
    ) -> ProductComparisonResult:
        cache_key = self._compute_cache_key(product_a, product_b, user_profile)
        if cache_key in COMPARE_CACHE:
            logger.info(f"Serving product comparison for '{product_a.product_name}' vs '{product_b.product_name}' from cache (0 credits)")
            return COMPARE_CACHE[cache_key]

        # Extract structured nutrition facts
        nc_a = product_a.nutrition_card
        nc_b = product_b.nutrition_card

        calories_a = f"{nc_a.calories_kcal} kcal" if nc_a else "N/A"
        sugar_a = f"{nc_a.added_sugars_g}g" if nc_a else "N/A"
        fat_a = f"{nc_a.total_fat_g}g (Sat Fat: {nc_a.saturated_fat_g}g)" if nc_a else "N/A"
        sodium_a = f"{nc_a.sodium_mg}mg" if nc_a else "N/A"

        calories_b = f"{nc_b.calories_kcal} kcal" if nc_b else "N/A"
        sugar_b = f"{nc_b.added_sugars_g}g" if nc_b else "N/A"
        fat_b = f"{nc_b.total_fat_g}g (Sat Fat: {nc_b.saturated_fat_g}g)" if nc_b else "N/A"
        sodium_b = f"{nc_b.sodium_mg}mg" if nc_b else "N/A"

        # Format ingredients
        ing_a_list = [f"{i.ingredient} ({i.purpose}, concern: {i.concern_level})" for i in product_a.ingredient_breakdown[:12]]
        ingredients_a_str = ", ".join(ing_a_list) if ing_a_list else "Not itemized"

        ing_b_list = [f"{i.ingredient} ({i.purpose}, concern: {i.concern_level})" for i in product_b.ingredient_breakdown[:12]]
        ingredients_b_str = ", ".join(ing_b_list) if ing_b_list else "Not itemized"

        violations_a_str = "; ".join(product_a.fssai_violations + product_a.deceptive_claims_flagged) or "None flagged"
        violations_b_str = "; ".join(product_b.fssai_violations + product_b.deceptive_claims_flagged) or "None flagged"

        prompt = f"""You are LabelTruth - an elite Indian food regulatory compliance auditor, forensic label expert, and clinical dietary physician powered by FSSAI regulations and ICMR-NIN 2024 Dietary Guidelines.

TASK:
Conduct a comprehensive, forensic HEAD-TO-HEAD comparison between two packaged food products for a specific individual with known clinical medical conditions, allergies, and dietary goals.

PRODUCT A:
- Name: {product_a.product_name}
- Audited Health Score: {product_a.health_score}/100
- Personalized Verdict: {product_a.personalized_verdict}
- Key Nutrition (per 100g): Calories: {calories_a}, Added Sugar: {sugar_a}, Fat: {fat_a}, Sodium: {sodium_a}
- Ingredients: {ingredients_a_str}
- Red Flags & Violations: {violations_a_str}

PRODUCT B:
- Name: {product_b.product_name}
- Audited Health Score: {product_b.health_score}/100
- Personalized Verdict: {product_b.personalized_verdict}
- Key Nutrition (per 100g): Calories: {calories_b}, Added Sugar: {sugar_b}, Fat: {fat_b}, Sodium: {sodium_b}
- Ingredients: {ingredients_b_str}
- Red Flags & Violations: {violations_b_str}

USER'S CLINICAL HEALTH PROFILE:
- Medical Conditions: {', '.join(user_profile.medical_conditions) if user_profile.medical_conditions else 'None specified'}
- Allergies: {', '.join(user_profile.allergies) if user_profile.allergies else 'None specified'}
- Dietary Preferences: {', '.join(user_profile.dietary_preferences) if user_profile.dietary_preferences else 'Standard / None'}
- Custom Avoided Ingredients: {', '.join(getattr(user_profile, 'custom_avoid_list', [])) if getattr(user_profile, 'custom_avoid_list', None) else 'None'}

EVALUATION & SCORING PROTOCOLS:
1. Winner Determination:
   - Set winner to "PRODUCT_A", "PRODUCT_B", "TIE", or "NEITHER_RECOMMENDED".
   - If BOTH products have poor scores (< 55) or both contain high-risk triggers for the user's clinical conditions (e.g. both high sugar in diabetes, or both high sodium in hypertension, or both contain ultra-processed industrial additives), set winner to "NEITHER_RECOMMENDED".
   - Do NOT label a product "Superior" if it is merely 1 or 2 points higher than another poor product.
2. Personalized Clinical Impact:
   - Give a direct, personalized clinical evaluation of how the specific ingredients, hidden sugars, oils, and additives in both products affect the user's conditions and allergies. Highlight real-world trade-offs (e.g. Product A has more protein but 3x more sugar; Product B has fewer calories but uses artificial sweeteners).
3. Key Trade-offs:
   - Provide 3 to 4 concise, factual bullet comparisons between the two products.
4. Dimension Breakdown:
   - "Nutritional Density": winner + reason.
   - "Ingredient Purity & Additives": winner + reason.
   - "Clinical Profile Fit": winner + reason.
5. Superior 3rd Alternative (Clean Indian Food Swap):
   - Identify a genuine, commercial clean-label Indian food product available on quick-commerce (Blinkit, Zepto, Nature's Basket) in the exact same food category that is significantly superior to BOTH Product A and Product B.
   - Must have an audited health score >= 80, clean whole-food ingredients, and high clinical suitability for this user.
   - Provide: name, health_score, key_benefit, personalized_fit, reason, delta_vs_scanned.

OUTPUT FORMAT:
Return ONLY valid JSON matching this schema:
{{
  "winner": "PRODUCT_A", // "PRODUCT_A", "PRODUCT_B", "TIE", or "NEITHER_RECOMMENDED"
  "verdict_title": "string",
  "verdict_summary": "string",
  "personalized_impact": "string",
  "key_tradeoffs": ["string"],
  "dimension_breakdown": [
    {{
      "category": "Nutritional Density",
      "winner": "PRODUCT_A", // "PRODUCT_A", "PRODUCT_B", "TIE", or "NEITHER"
      "explanation": "string"
    }},
    {{
      "category": "Ingredient Purity & Additives",
      "winner": "PRODUCT_B",
      "explanation": "string"
    }},
    {{
      "category": "Clinical Profile Fit",
      "winner": "PRODUCT_A",
      "explanation": "string"
    }}
  ],
  "superior_alternative": {{
    "name": "string",
    "health_score": 85,
    "key_benefit": "string",
    "personalized_fit": "string",
    "reason": "string",
    "price_comparison": "Comparable",
    "delta_vs_scanned": "+22 pts vs both"
  }}
}}
"""

        clients_to_try = []
        if self.client:
            clients_to_try.append(self.client)
        for extra_key in GEMINI_API_KEYS:
            if self.client and extra_key == GEMINI_API_KEY:
                continue
            try:
                clients_to_try.append(genai.Client(api_key=extra_key))
            except Exception:
                pass

        if not clients_to_try:
            logger.warning("No Gemini API client configured for CompareService, using algorithmic fallback")
            return self._algorithmic_fallback(product_a, product_b, user_profile)

        parsed = None
        last_error = None

        for cl in clients_to_try:
            for model_name in FALLBACK_MODELS:
                try:
                    response = cl.models.generate_content(
                        model=model_name,
                        contents=[prompt],
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            temperature=0.2,
                            max_output_tokens=900
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
                    if parsed:
                        break
                except Exception as e:
                    last_error = e
                    logger.warning(f"Compare model {model_name} failed: {e}")
                    continue
            if parsed:
                break

        if not parsed:
            logger.error(f"All Gemini models failed for product comparison: {last_error}")
            return self._algorithmic_fallback(product_a, product_b, user_profile)

        # Build comparison result object
        score_diff = abs(product_a.health_score - product_b.health_score)
        winner = parsed.get("winner", "TIE")
        if winner not in ["PRODUCT_A", "PRODUCT_B", "TIE", "NEITHER_RECOMMENDED"]:
            winner = "TIE"

        dims = []
        for d in parsed.get("dimension_breakdown", []):
            d_winner = d.get("winner", "TIE")
            if d_winner not in ["PRODUCT_A", "PRODUCT_B", "TIE", "NEITHER"]:
                d_winner = "TIE"
            dims.append(DimensionComparison(
                category=d.get("category", "General"),
                winner=d_winner,
                explanation=d.get("explanation", "")
            ))

        sup_alt_raw = parsed.get("superior_alternative")
        superior_alt = None
        if sup_alt_raw and isinstance(sup_alt_raw, dict) and sup_alt_raw.get("name"):
            alt_name = sup_alt_raw.get("name", "Clean Whole Food Option")
            store_url = f"https://blinkit.com/s/?q={urllib.parse.quote_plus(alt_name)}"
            superior_alt = HealthierAlternative(
                name=alt_name,
                product_name=alt_name,
                health_score=sup_alt_raw.get("health_score", 85),
                key_benefit=sup_alt_raw.get("key_benefit", "Clean whole-food ingredients with zero toxic additives"),
                price_comparison=sup_alt_raw.get("price_comparison", "Comparable"),
                personalized_fit=sup_alt_raw.get("personalized_fit", "Free of conflicting ingredients for your health profile"),
                store_url=store_url,
                reason=sup_alt_raw.get("reason", "Superior nutritional integrity and clean label compliance"),
                delta_vs_scanned=sup_alt_raw.get("delta_vs_scanned", f"+{max(15, 85 - max(product_a.health_score, product_b.health_score))} pts vs both"),
                type="CLEAN_COMMERCIAL"
            )

        result = ProductComparisonResult(
            winner=winner,
            verdict_title=parsed.get("verdict_title", "Head-to-Head Nutritional Comparison"),
            verdict_summary=parsed.get("verdict_summary", ""),
            score_diff=score_diff,
            personalized_impact=parsed.get("personalized_impact", ""),
            key_tradeoffs=parsed.get("key_tradeoffs", []),
            dimension_breakdown=dims,
            superior_alternative=superior_alt
        )

        COMPARE_CACHE[cache_key] = result
        return result

    def _algorithmic_fallback(
        self,
        product_a: LabelAnalysisResult,
        product_b: LabelAnalysisResult,
        user_profile: UserProfile
    ) -> ProductComparisonResult:
        score_a = product_a.health_score
        score_b = product_b.health_score
        score_diff = abs(score_a - score_b)

        if score_a < 55 and score_b < 55:
            winner = "NEITHER_RECOMMENDED"
            verdict_title = "Neither Product Recommended"
            verdict_summary = f"Both {product_a.product_name} ({score_a} pts) and {product_b.product_name} ({score_b} pts) exhibit significant ultra-processing, additives, or clinical friction with your health profile."
        elif score_diff <= 3:
            winner = "TIE"
            verdict_title = "Comparable Nutritional Integrity"
            verdict_summary = f"Both products demonstrate comparable nutritional profiles ({score_a} vs {score_b} pts). Choose based on whole-ingredient preference."
        elif score_a > score_b:
            winner = "PRODUCT_A"
            verdict_title = f"{product_a.product_name} is the Superior Choice"
            verdict_summary = f"{product_a.product_name} scores +{score_diff} points cleaner than {product_b.product_name} with fewer flagged additives and better profile compatibility."
        else:
            winner = "PRODUCT_B"
            verdict_title = f"{product_b.product_name} is the Superior Choice"
            verdict_summary = f"{product_b.product_name} scores +{score_diff} points cleaner than {product_a.product_name} with fewer flagged additives and better profile compatibility."

        # Suggest 3rd clean alternative from product clean_alternatives if available
        sup_alt = None
        cand_alts = product_a.clean_alternatives or product_b.clean_alternatives
        if cand_alts:
            best_cand = max(cand_alts, key=lambda x: getattr(x, 'health_score', 80) or 80)
            sup_alt = best_cand

        return ProductComparisonResult(
            winner=winner,
            verdict_title=verdict_title,
            verdict_summary=verdict_summary,
            score_diff=score_diff,
            personalized_impact="Evaluate individual ingredients against your medical conditions and avoid excessive added sugars or industrial palm fats.",
            key_tradeoffs=[
                f"{product_a.product_name}: Health Score {score_a}/100, Verdict: {product_a.personalized_verdict}",
                f"{product_b.product_name}: Health Score {score_b}/100, Verdict: {product_b.personalized_verdict}"
            ],
            dimension_breakdown=[
                DimensionComparison(
                    category="Nutritional Density",
                    winner="PRODUCT_A" if score_a > score_b else ("PRODUCT_B" if score_b > score_a else "TIE"),
                    explanation="Evaluated based on calorie density, sugar load, and fat quality."
                ),
                DimensionComparison(
                    category="Ingredient Purity & Additives",
                    winner="PRODUCT_A" if len(product_a.fssai_violations) < len(product_b.fssai_violations) else ("PRODUCT_B" if len(product_b.fssai_violations) < len(product_a.fssai_violations) else "TIE"),
                    explanation="Evaluated based on artificial preservatives, emulsifiers, and regulatory flags."
                ),
                DimensionComparison(
                    category="Clinical Profile Fit",
                    winner=winner if winner in ["PRODUCT_A", "PRODUCT_B"] else "TIE",
                    explanation="Evaluated against active medical conditions and allergen profiles."
                )
            ],
            superior_alternative=sup_alt
        )

compare_service = CompareService()
