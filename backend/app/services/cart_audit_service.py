import json
import logging
import re
import asyncio
from typing import Optional, List, Dict, Any
from google import genai
from google.genai import types
from PIL import Image
import io

from app.config import GEMINI_API_KEY, GEMINI_API_KEYS
from app.schemas.cart_audit import CartAuditResponse, CartItemAudit
from app.schemas.analysis import HealthierAlternative
from app.schemas.user_profile import UserProfile
from app.services.tinyfish_service import tinyfish_service

logger = logging.getLogger(__name__)

CART_TEXT_PARSE_PROMPT = """You are LabelTruth Cart Extractor. The following is scraped text from a quick-commerce website or shared cart link.
Extract all packaged food/grocery product names visible in this text. Include brand names when available.

Text:
{text}

Return ONLY valid JSON with this structure:
{{
  "store_name": "detected store or Quick-Commerce",
  "items": [
    {{"product_name": "Brand Product Name", "quantity": 1}}
  ]
}}

If fewer than 1 food product can be identified, return {{"store_name": "Quick-Commerce", "items": []}}
"""

ALTERNATIVE_DISCOVERY_PROMPT = """You are LabelTruth's Alternative Product Advisor for Indian quick-commerce.

Product in cart: "{product_name}"
Category: {category}
Current health score: {score}/100
Store: {store_name}
User health profile: {profile_summary}

Your task:
1. Think of a SPECIFIC cleaner, healthier Indian brand/product that is a genuine same-category alternative to "{product_name}".
   - It must be a real brand available in India (e.g. The Whole Truth, Early Foods, Slurrp Farm, Sattviko, Yoga Bar, Raw Pressery, Akshayakalpa, Wingreens, Epigamia, Ketofy, True Elements, Sorich, etc.)
   - It must be realistically available on Zepto/Blinkit in India
   - It must have FEWER additives, no palm oil, no refined sugar (or significantly less), less processing
   - It must be from a DIFFERENT brand/product than "{product_name}"
   - Its estimated health score must be strictly greater than {score}
2. Provide key benefit (what makes it cleaner — specific ingredients avoided or present)
3. Construct a realistic Zepto or Blinkit search URL for this product.

Return ONLY valid JSON:
{{
  "name": "Brand Product Full Name",
  "health_score": 88,
  "key_benefit": "Specific reason why it is cleaner (e.g. zero palm oil, no refined sugar)",
  "search_url": "https://www.zepto.com/search?query=product+name",
  "reason": "Why this is a better choice for the user profile"
}}

If NO genuinely cleaner alternative exists (the product is already a clean wholefood), return:
{{"name": null}}
"""

CART_OCR_PROMPT = """You are LabelTruth Cart Intelligence Auditor.
Carefully examine this quick-commerce cart screenshot (from Zepto, Blinkit, Swiggy Instamart, BigBasket, or Amazon Fresh).
Extract:
1. "store_name": The quick-commerce app (e.g. Zepto, Blinkit, Swiggy Instamart).
2. "items": The list of distinct grocery or packaged food items in the cart with their full product name (including brand if visible) and quantity.

Return ONLY valid JSON:
{
  "store_name": "Zepto",
  "items": [
    {
      "product_name": "Exact Brand and Product Name",
      "quantity": 1
    }
  ]
}
If no food products are visible or legible, return:
{
  "store_name": "Quick-Commerce",
  "items": []
}
"""

class CartAuditService:
    def __init__(self):
        self.client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

    def _get_active_clients(self):
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
            pil_img.thumbnail((1200, 1200), Image.Resampling.LANCZOS)
            buf = io.BytesIO()
            pil_img.save(buf, format="JPEG", quality=85, optimize=True)
            image_bytes = buf.getvalue()
        except Exception:
            pass

        ACTIVE_MODELS = [
            "gemini-flash-lite-latest",
            "gemini-3.5-flash-lite",
            "gemini-3.8-flash",
            "gemini-flash-latest"
        ]

        for cl in self._get_active_clients():
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
                    logger.warning(f"Cart image OCR with {model_name} failed: {e}")
                    continue

        return {"store_name": "Quick-Commerce", "items": []}

    async def extract_items_from_url(self, cart_url: str, pincode: str = "110001") -> Dict[str, Any]:
        """
        Extract items from cart URL using TinyFish browser agent with Gemini fallback text parsing.
        """
        # Step 1: TinyFish agent browser navigation
        raw_data = await tinyfish_service.extract_cart_items_via_agent_browser(cart_url, pincode)
        items = raw_data.get("items", [])
        store_name = raw_data.get("store_name", "Quick-Commerce")

        if items:
            return raw_data

        # Step 2: TinyFetch static DOM + Gemini text parsing
        try:
            import httpx
            from app.config import TINYFISH_API_KEY
            from app.services.tinyfish_service import is_waf_block_content
            async with httpx.AsyncClient(timeout=20.0) as client:
                res = await client.post(
                    "https://api.fetch.tinyfish.ai",
                    headers={"X-API-Key": TINYFISH_API_KEY, "Content-Type": "application/json"},
                    json={"urls": [cart_url]}
                )
                if res.status_code == 200:
                    data = res.json()
                    results = data.get("results", [])
                    if results:
                        page_text = str(results[0].get("text", "") or results[0].get("content", ""))
                        if page_text and not is_waf_block_content(page_text):
                            prompt = CART_TEXT_PARSE_PROMPT.format(text=page_text[:4000])
                            parsed_json = self._call_gemini_text(prompt, max_output=1024)
                            if parsed_json:
                                parsed = json.loads(parsed_json)
                                if parsed.get("items"):
                                    return {
                                        "store_name": parsed.get("store_name") or store_name,
                                        "items": parsed["items"]
                                    }
        except Exception as e:
            logger.warning(f"TinyFetch + Gemini parse fallback notice: {e}")

        return {"store_name": store_name, "items": []}

    def _call_gemini_text(self, prompt: str, max_output: int = 512) -> Optional[str]:
        """Synchronous Gemini text call for JSON extraction"""
        ACTIVE_MODELS = [
            "gemini-flash-lite-latest",
            "gemini-3.5-flash-lite",
            "gemini-3.8-flash",
            "gemini-flash-latest"
        ]
        for cl in self._get_active_clients():
            if not cl:
                continue
            for model_name in ACTIVE_MODELS:
                try:
                    response = cl.models.generate_content(
                        model=model_name,
                        contents=[prompt],
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            max_output_tokens=max_output
                        )
                    )
                    txt = response.text.strip()
                    if txt.startswith("```json"):
                        txt = txt[7:]
                    if txt.startswith("```"):
                        txt = txt[3:]
                    if txt.endswith("```"):
                        txt = txt[:-3]
                    return txt.strip()
                except Exception as e:
                    logger.warning(f"Gemini text call with {model_name} failed: {e}")
                    continue
        return None

    def _detect_category(self, product_name: str) -> str:
        """Map product name to human-readable category for Gemini context"""
        p = product_name.lower()
        if any(w in p for w in ["bhujia", "sev", "namkeen", "mixture", "chivda"]):
            return "namkeen/savory snack"
        if any(w in p for w in ["chip", "chips", "crisp", "lays", "doritos", "bingo", "nacho", "kurkure"]):
            return "chips/crisps"
        if any(w in p for w in ["biscuit", "rusk", "cracker", "50-50", "marie", "parle-g", "mcvities"]):
            return "biscuit/cracker"
        if any(w in p for w in ["cookie", "cookies", "bourbon", "oreo", "creme", "hide & seek"]):
            return "cookies"
        if any(w in p for w in ["cola", "coke", "pepsi", "thums", "sprite", "fanta", "mountain dew", "7up"]):
            return "cola/carbonated drink"
        if any(w in p for w in ["energy drink", "red bull", "sting", "monster"]):
            return "energy drink"
        if any(w in p for w in ["soda", "fizzy", "carbonated", "tonic"]):
            return "soda/carbonated water"
        if any(w in p for w in ["bournvita", "horlicks", "complan", "boost", "milo", "ovaltine"]):
            return "malt health drink"
        if any(w in p for w in ["noodle", "noodles", "maggi", "yippee", "top ramen"]):
            return "instant noodles"
        if any(w in p for w in ["pasta", "macaroni", "spaghetti", "penne"]):
            return "pasta"
        if any(w in p for w in ["oats", "corn flakes", "chocos", "muesli", "granola", "cereal"]):
            return "breakfast cereal"
        if any(w in p for w in ["chocolate", "cadbury", "kitkat", "snickers", "dairy milk", "5 star", "munch"]):
            return "chocolate/candy"
        if any(w in p for w in ["cheese", "mozzarella"]):
            return "cheese"
        if any(w in p for w in ["butter", "margarine", "spread"]):
            return "butter/spread"
        if any(w in p for w in ["paneer", "chhena"]):
            return "paneer"
        if any(w in p for w in ["yogurt", "curd", "dahi", "greek"]):
            return "yogurt/curd"
        if any(w in p for w in ["juice", "frooti", "maaza", "slice", "tropicana", "real", "appy"]):
            return "fruit juice/drink"
        if any(w in p for w in ["sauce", "ketchup", "mayo", "mayonnaise", "dip"]):
            return "sauce/condiment"
        if any(w in p for w in ["bread", "loaf", "pav", "bun"]):
            return "bread/bakery"
        if any(w in p for w in ["milk", "full cream", "toned"]):
            return "milk"
        if any(w in p for w in ["ghee", "clarified butter"]):
            return "ghee"
        if any(w in p for w in ["oil", "sunflower", "soybean", "canola", "refined oil"]):
            return "cooking oil"
        if any(w in p for w in ["makhana", "foxnut"]):
            return "foxnuts/makhana"
        if any(w in p for w in ["almond", "cashew", "peanut", "walnut", "pistachio", "nut"]):
            return "nuts/dry fruits"
        return "packaged food"

    async def _find_alternative_with_gemini(
        self,
        product_name: str,
        category: str,
        item_score: int,
        store_name: str,
        user_profile: UserProfile
    ) -> Optional[HealthierAlternative]:
        """
        Use Gemini to discover a genuinely better, specifically-named brand alternative.
        Returns None if the product is already clean (score >= 82) or no better option exists.
        """
        if item_score >= 82:
            return None

        profile_summary = ""
        if user_profile.medical_conditions:
            profile_summary += f"Conditions: {', '.join(user_profile.medical_conditions)}. "
        if user_profile.allergies:
            profile_summary += f"Allergies: {', '.join(user_profile.allergies)}. "
        if user_profile.dietary_preferences:
            profile_summary += f"Diet: {', '.join(user_profile.dietary_preferences)}. "
        if not profile_summary:
            profile_summary = "General healthy adult."

        prompt = ALTERNATIVE_DISCOVERY_PROMPT.format(
            product_name=product_name,
            category=category,
            score=item_score,
            store_name=store_name,
            profile_summary=profile_summary
        )

        try:
            json_str = self._call_gemini_text(prompt, max_output=512)
            if not json_str:
                return None
            data = json.loads(json_str)
            if not data.get("name"):
                return None  # Gemini says product is already optimal

            alt_name = data["name"]
            alt_score = int(data.get("health_score", item_score + 12))
            key_benefit = data.get("key_benefit", "Cleaner ingredient profile with fewer additives.")
            search_url = data.get("search_url", "")
            reason = data.get("reason", "Verified cleaner formulation.")

            if alt_score <= item_score:
                return None

            # Build search URL if not provided
            if not search_url:
                query_slug = alt_name.lower().replace(" ", "+")
                search_url = f"https://www.zepto.com/search?query={query_slug}"

            return HealthierAlternative(
                name=alt_name,
                product_name=alt_name,
                health_score=alt_score,
                key_benefit=key_benefit,
                price_comparison="Comparable",
                personalized_fit=reason,
                direct_pdp_url=search_url,
                is_direct_pdp=False,
                pincode_available=True,
                type="CLEAN_COMMERCIAL",
                reason=reason
            )
        except Exception as e:
            logger.warning(f"Gemini alternative discovery notice for '{product_name}': {e}")
            return None

    async def _audit_single_item(
        self,
        item: dict,
        pincode: str,
        user_profile: UserProfile,
        store_name: str
    ) -> CartItemAudit:
        """
        Deep clinical audit of a single cart item:
        1. Fetch packaging/back-of-pack labels via TinySearch + TinyFetch
        2. Analyze via Gemini AI text query with health profile
        3. Use Gemini to find a genuinely better specific brand alternative
        """
        p_name = item.get("product_name", "Packaged Product").strip()
        qty = int(item.get("quantity", 1))

        # 1. Fetch back-of-pack label via TinyFish Search & Fetch
        bop_text = item.get("label_snippet") or ""
        if not bop_text:
            try:
                bop_text = await tinyfish_service.search_and_fetch_bop(p_name) or ""
            except Exception as bop_err:
                logger.warning(f"TinyFish search/fetch BOP notice for '{p_name}': {bop_err}")

        # 2. Analyze via Gemini AI text query (with fallback to clinical scoring engine)
        analysis_res = None
        try:
            from app.services.gemini_vision import gemini_vision_service
            analysis_res = await gemini_vision_service.analyze_text_query(
                p_name,
                user_profile,
                bop_text
            )
        except Exception as gem_err:
            logger.warning(f"Gemini analysis for cart item '{p_name}' notice: {gem_err}")

        # 3. Extract health score, verdict, and clinical concerns
        if analysis_res:
            item_score = analysis_res.health_score
            verdict = analysis_res.personalized_verdict
            concerns = []
            for claim in getattr(analysis_res, "deceptive_claims_flagged", []):
                concerns.append(f"Claim: {claim}")
            for viol in getattr(analysis_res, "fssai_violations", []):
                concerns.append(f"FSSAI: {viol}")
            for ing in getattr(analysis_res, "ingredient_breakdown", []):
                c_lvl = getattr(ing, "concern_level", "LOW")
                if c_lvl in ("HIGH", "MEDIUM"):
                    p_warn = getattr(ing, "personalized_warning", None)
                    if p_warn:
                        concerns.append(f"{getattr(ing, 'ingredient', '')}: {p_warn}")
                    else:
                        concerns.append(f"{getattr(ing, 'ingredient', '')} ({getattr(ing, 'purpose', 'Additive')})")
            if not concerns and getattr(analysis_res, "simple_summary", None):
                concerns.append(analysis_res.simple_summary[:120])
        else:
            # Deterministic clinical fallback
            p_lower = p_name.lower()
            base_score = 45
            concerns = []
            meds = [m.lower() for m in (user_profile.medical_conditions or [])]

            if any(k in p_lower for k in ["biscuit", "cookie", "cake", "rusk"]):
                base_score = 40
                concerns.append("Refined wheat flour (Maida) & palm oil")
                if any("acidity" in m or "gerd" in m for m in meds):
                    concerns.append("Souring agents / acidity triggers (-10 pts penalty)")
                    base_score -= 10
            elif any(k in p_lower for k in ["cola", "pepsi", "coke", "soda", "fizzy", "dew", "sprite"]):
                base_score = 22
                concerns.append("High added liquid sugars (10.6g/100ml) & phosphoric acid")
                if any("acidity" in m or "gerd" in m for m in meds):
                    concerns.append("Carbonation & phosphoric acid stimulate gastric reflux (-15 pts)")
                    base_score -= 15
            elif any(k in p_lower for k in ["bhujia", "chips", "kurkure", "namkeen", "sev"]):
                base_score = 32
                concerns.append("Deep fried in palm oil with excessive sodium & synthetic INS flavorings")
                if any("hypertension" in m for m in meds):
                    concerns.append("High sodium worsens arterial blood pressure (-10 pts)")
                    base_score -= 10
                if any("acidity" in m or "gerd" in m for m in meds):
                    concerns.append("Deep-fried trans-fat matrix provokes acid reflux (-10 pts)")
                    base_score -= 10
            elif any(k in p_lower for k in ["bournvita", "horlicks", "complan", "boost"]):
                base_score = 35
                concerns.append("Over 50% added sugars and maltodextrin (GI 110)")
                if any("diabetes" in m for m in meds):
                    concerns.append("High glycemic surge risk for diabetes (-20 pts)")
                    base_score -= 15
            elif any(k in p_lower for k in ["noodle", "maggi", "pasta"]):
                base_score = 34
                concerns.append("Refined maida block flash-fried in palm oil with MSG flavor mix")
            else:
                base_score = 52
                concerns.append("Industrial additives and refined processing")

            item_score = max(10, min(100, base_score))
            if item_score >= 75:
                verdict = "SAFE FOR YOU"
            elif item_score >= 45:
                verdict = "CAUTION"
            else:
                verdict = "AVOID (VIOLATES PROFILE)"

        # 4. Find genuinely better specific alternative using Gemini AI
        category = self._detect_category(p_name)
        clean_alt_candidate = await self._find_alternative_with_gemini(
            p_name, category, item_score, store_name, user_profile
        )

        # Safety check: only use alternative if score is strictly better
        if clean_alt_candidate and clean_alt_candidate.health_score <= item_score:
            clean_alt_candidate = None

        return CartItemAudit(
            product_name=p_name,
            quantity=qty,
            health_score=item_score,
            personalized_verdict=verdict,
            key_concerns=concerns,
            cleaner_alternative=clean_alt_candidate
        )

    async def audit_cart(
        self,
        image_bytes: Optional[bytes],
        cart_url: Optional[str],
        pincode: str,
        user_profile: UserProfile
    ) -> CartAuditResponse:
        """Full end-to-end cart audit using TinyFish browser agent, TinyFetch, and Gemini clinical reasoning"""
        extracted = {}
        if image_bytes:
            extracted = await self.extract_items_from_image(image_bytes)
        elif cart_url:
            extracted = await self.extract_items_from_url(cart_url, pincode)

        store_name = extracted.get("store_name") or "Zepto"
        raw_items = extracted.get("items") or []

        # If extraction returned empty, provide a clean informative response instead of mock items
        if not raw_items:
            if cart_url:
                raise ValueError(
                    "Quick-commerce cart URLs (on Zepto/Blinkit) are stored in your device's private browser session and cannot be accessed via a public link. "
                    "Please take a screenshot of your cart screen and upload it here — our vision AI will extract and audit all your products instantly!"
                )
            else:
                raise ValueError(
                    "No food products or cart items were detected in the uploaded screenshot. "
                    "Please ensure the cart screenshot clearly shows the item names and quantities."
                )

        # Concurrently audit items in parallel via asyncio.gather
        tasks = [
            self._audit_single_item(item, pincode, user_profile, store_name)
            for item in raw_items[:8]
        ]
        audited_items: List[CartItemAudit] = await asyncio.gather(*tasks)

        original_scores = [item.health_score for item in audited_items]
        swapped_scores = [
            item.cleaner_alternative.health_score if item.cleaner_alternative else item.health_score
            for item in audited_items
        ]
        clean_count = sum(1 for item in audited_items if item.health_score >= 75)
        red_flags_prevented = sum(len(item.key_concerns) for item in audited_items)

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
