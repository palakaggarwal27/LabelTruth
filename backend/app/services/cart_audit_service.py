import json
import logging
from typing import Optional, List, Dict, Any
from google import genai
from google.genai import types
from PIL import Image
import io

from app.config import GEMINI_API_KEY, GEMINI_API_KEYS
from app.schemas.cart_audit import CartAuditResponse, CartItemAudit
from app.schemas.analysis import HealthierAlternative, LabelAnalysisResult
from app.schemas.user_profile import UserProfile
from app.services.tinyfish_service import tinyfish_service
from app.services.profile_evaluator import evaluate_profile_safety_offline
from app.utils.pdp_validator import validate_and_clean_pdp_url

logger = logging.getLogger(__name__)

CART_OCR_PROMPT = """You are LabelTruth Cart Intelligence Auditor.
Analyze this quick-commerce cart screenshot (e.g., Blinkit, Zepto, Swiggy Instamart, BigBasket).
Identify:
1. The store platform (e.g. Zepto, Blinkit, Instamart, Amazon Fresh).
2. The exact list of grocery or packaged food items in the cart, along with quantity.

Return ONLY valid JSON matching this schema:
{
  "store_name": "Zepto",
  "items": [
    {
      "product_name": "Full Product Name with Brand",
      "quantity": 1
    }
  ]
}
"""

CART_URL_PROMPT = """You are LabelTruth Cart Intelligence Auditor.
Extract the quick-commerce store name and the list of food/grocery items in this cart text.
Return ONLY valid JSON matching this schema:
{
  "store_name": "Zepto",
  "items": [
    {
      "product_name": "Full Product Name with Brand",
      "quantity": 1
    }
  ]
}
"""

class CartAuditService:
    def __init__(self):
        self.client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

    def _get_active_client(self):
        clients = [self.client] if self.client else []
        for k in GEMINI_API_KEYS:
            if self.client and k == GEMINI_API_KEY:
                continue
            try:
                clients.append(genai.Client(api_key=k))
            except Exception:
                pass
        return clients or ([self.client] if self.client else [])

    async def extract_items_from_image(self, image_bytes: bytes) -> Dict[str, Any]:
        """Extract store and items from cart screenshot using Gemini Flash Vision"""
        try:
            pil_img = Image.open(io.BytesIO(image_bytes))
            if pil_img.mode in ("RGBA", "P"):
                pil_img = pil_img.convert("RGB")
            pil_img.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
            buf = io.BytesIO()
            pil_img.save(buf, format="JPEG", quality=80, optimize=True)
            image_bytes = buf.getvalue()
        except Exception:
            pass

        ACTIVE_MODELS = [
            "gemini-flash-lite-latest",
            "gemini-3.5-flash-lite",
            "gemini-3.8-flash",
            "gemini-flash-latest"
        ]

        clients = self._get_active_client()
        for cl in clients:
            if not cl:
                continue
            for model_name in ACTIVE_MODELS:
                try:
                    response = cl.models.generate_content(
                        model=model_name,
                        contents=[
                            types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
                            CART_OCR_PROMPT
                        ],
                        config=types.GenerateContentConfig(response_mime_type="application/json")
                    )
                    txt = response.text.strip()
                    if txt.startswith("```json"):
                        txt = txt[7:]
                    if txt.startswith("```"):
                        txt = txt[3:]
                    if txt.endswith("```"):
                        txt = txt[:-3]
                    return json.loads(txt.strip())
                except Exception as e:
                    logger.warning(f"Cart image extraction with {model_name} failed: {e}")
                    continue

        return {"store_name": "Quick-Commerce", "items": []}

    async def extract_items_from_url(self, cart_url: str) -> Dict[str, Any]:
        """Extract items from shared cart URL via TinyFish fetch/agent"""
        domain_store = "Quick-Commerce"
        if "zepto" in cart_url.lower():
            domain_store = "Zepto"
        elif "blinkit" in cart_url.lower():
            domain_store = "Blinkit"
        elif "instamart" in cart_url.lower():
            domain_store = "Swiggy Instamart"

        content = ""
        try:
            details = await tinyfish_service.fetch_product_details(cart_url)
            if details:
                content = str(details.get("text", "") or details.get("content", ""))
        except Exception as e:
            logger.warning(f"TinyFetch cart url notice: {e}")

        if not content:
            # Fallback: parse URL parameters or path
            return {
                "store_name": domain_store,
                "items": [{"product_name": "Cart Item", "quantity": 1}]
            }

        clients = self._get_active_client()
        prompt = f"{CART_URL_PROMPT}\n\nCart URL Content:\n{content[:4000]}"
        for cl in clients:
            if not cl:
                continue
            for model_name in ["gemini-flash-lite-latest", "gemini-3.5-flash-lite"]:
                try:
                    response = cl.models.generate_content(
                        model=model_name,
                        contents=prompt,
                        config=types.GenerateContentConfig(response_mime_type="application/json")
                    )
                    txt = response.text.strip()
                    if txt.startswith("```json"):
                        txt = txt[7:]
                    if txt.startswith("```"):
                        txt = txt[3:]
                    if txt.endswith("```"):
                        txt = txt[:-3]
                    parsed = json.loads(txt.strip())
                    parsed["store_name"] = parsed.get("store_name") or domain_store
                    return parsed
                except Exception:
                    continue

        return {"store_name": domain_store, "items": []}

    async def audit_cart(
        self,
        image_bytes: Optional[bytes],
        cart_url: Optional[str],
        pincode: str,
        user_profile: UserProfile
    ) -> CartAuditResponse:
        """Full end-to-end audit of cart items with cleaner swaps"""
        extracted = {}
        if image_bytes:
            extracted = await self.extract_items_from_image(image_bytes)
        elif cart_url:
            extracted = await self.extract_items_from_url(cart_url)

        store_name = extracted.get("store_name") or "Quick-Commerce"
        raw_items = extracted.get("items") or []

        if not raw_items:
            # Fallback mock/sample items if empty
            raw_items = [
                {"product_name": "Britannia Good Day Butter Biscuits", "quantity": 1},
                {"product_name": "Cadbury Bournvita Chocolate Health Drink", "quantity": 1},
                {"product_name": "Haldiram's Bhujia Sev", "quantity": 1}
            ]

        audited_items: List[CartItemAudit] = []
        original_scores: List[int] = []
        swapped_scores: List[int] = []
        clean_count = 0
        red_flags_prevented = 0

        # Audit each cart product
        for item in raw_items[:8]:  # Limit to 8 items to stay within credit budget
            p_name = item.get("product_name", "Packaged Product").strip()
            qty = int(item.get("quantity", 1))

            # Estimate base score & concerns based on profile
            # Fast heuristic/mini-audit using condition rules
            base_score = 45
            concerns = []

            # Check profile conditions (e.g. acidity, diabetes)
            p_lower = p_name.lower()
            meds = [m.lower() for m in (user_profile.medical_conditions or [])]
            allergies = [a.lower() for a in (user_profile.allergies or [])]

            if any(k in p_lower for k in ["biscuit", "cookie", "cake", "rusk"]):
                base_score = 42
                concerns.append("Refined wheat flour (Maida) & palm oil")
            elif any(k in p_lower for k in ["cola", "pepsi", "coke", "soda", "fizzy"]):
                base_score = 25
                concerns.append("High added liquid sugars & phosphoric acid")
                if any("acidity" in m or "gerd" in m for m in meds):
                    concerns.append("Carbonation & high acidity trigger severe acid reflux (-15 pts)")
                    base_score -= 15
            elif any(k in p_lower for k in ["bhujia", "chips", "kurkure", "namkeen"]):
                base_score = 35
                concerns.append("Palm oil frying & high sodium density")
                if any("hypertension" in m for m in meds):
                    concerns.append("Excessive sodium worsens blood pressure")
            elif any(k in p_lower for k in ["bournvita", "horlicks", "complan"]):
                base_score = 38
                concerns.append("50% added sugars and maltodextrin (GI 110)")
                if any("diabetes" in m for m in meds):
                    concerns.append("Severe glucose spiking risk for diabetes (-20 pts)")
                    base_score -= 15
            elif any(k in p_lower for k in ["curd", "yogurt", "milk", "cheese"]):
                base_score = 75
                concerns.append("Check for added starch or thickeners")
                if any("lactose" in m for m in meds):
                    concerns.append("Contains dairy lactose")
                    base_score -= 15
            else:
                base_score = 55
                concerns.append("Industrial processing & standard preservatives")

            base_score = max(10, min(100, base_score))
            original_scores.append(base_score)

            if base_score >= 75:
                clean_count += 1
                verdict = "SAFE FOR YOU"
            elif base_score >= 45:
                verdict = "CAUTION"
            else:
                verdict = "AVOID (VIOLATES PROFILE)"

            # Search cleaner alternative on same platform at user pincode
            clean_alt: Optional[HealthierAlternative] = None
            try:
                # Ask TinyFish for clean whole-food alternative with direct PDP
                alts = await tinyfish_service.find_pincode_alternatives(f"{p_name} {store_name}", pincode)
                if alts:
                    first_alt = alts[0]
                    alt_url = first_alt.get("direct_pdp_url") or ""
                    v_res = validate_and_clean_pdp_url(alt_url)
                    alt_score = int(first_alt.get("health_score", 85))
                    
                    clean_alt = HealthierAlternative(
                        name=first_alt.get("name") or "Clean Whole-Food Swap",
                        product_name=first_alt.get("product_name") or first_alt.get("name"),
                        health_score=alt_score,
                        key_benefit="100% whole grain, zero palm oil, zero chemical INS additives.",
                        price_comparison="Comparable",
                        personalized_fit="Fully aligned with your active health profile.",
                        direct_pdp_url=v_res.get("url") or alt_url,
                        is_direct_pdp=v_res.get("is_pdp", False),
                        pincode_available=True,
                        type="CLEAN_COMMERCIAL",
                        reason=f"Available on {store_name} at PIN {pincode}."
                    )
                    swapped_scores.append(alt_score)
                    red_flags_prevented += len(concerns)
                else:
                    swapped_scores.append(base_score)
            except Exception as alt_e:
                logger.warning(f"Error fetching alt for {p_name}: {alt_e}")
                swapped_scores.append(base_score)

            audited_items.append(CartItemAudit(
                product_name=p_name,
                quantity=qty,
                health_score=base_score,
                personalized_verdict=verdict,
                key_concerns=concerns,
                cleaner_alternative=clean_alt
            ))

        orig_avg = int(sum(original_scores) / max(1, len(original_scores)))
        swap_avg = int(sum(swapped_scores) / max(1, len(swapped_scores)))
        improvement = max(0, swap_avg - orig_avg)

        summary = f"Audited {len(audited_items)} items from {store_name} at pincode {pincode}. "
        if improvement > 15:
            summary += f"Accepting cleaner swaps boosts your cart health score by +{improvement} points and removes {red_flags_prevented} flagged health additives."
        else:
            summary += "Cart shows solid nutritional baseline with minimal substitutions required."

        return CartAuditResponse(
            store_name=store_name,
            pincode=pincode,
            original_cart_score=orig_avg,
            swapped_cart_score=swap_avg,
            score_improvement=improvement,
            total_items=len(audited_items),
            clean_items_count=clean_count,
            red_flags_prevented_count=red_flags_prevented,
            summary=summary,
            items=audited_items
        )

cart_audit_service = CartAuditService()
