import json
import logging
import re
import asyncio
from typing import Optional, List, Dict, Any
from google import genai
from google.genai import types
from PIL import Image
import io

import urllib.parse
from app.config import GEMINI_API_KEY, GEMINI_API_KEYS, GEMINI_ACTIVE_MODELS
from app.schemas.cart_audit import CartAuditResponse, CartItemAudit
from app.schemas.analysis import HealthierAlternative, LabelAnalysisResult, IngredientItem, NutrientIntegrityMatrix
from app.schemas.user_profile import UserProfile
from app.services.tinyfish_service import tinyfish_service
from app.services.delta_audit import get_realistic_homemade_recipe_score

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

CART_OR_BILL_OCR_PROMPT = """You are LabelTruth Cart & Grocery Bill Forensic Auditor.
Examine this image, which is either:
1. A digital quick-commerce cart screenshot (from Zepto, Blinkit, Swiggy Instamart, BigBasket, Amazon Fresh, etc.) OR
2. A photo of a printed supermarket / shopping mall store receipt or bill (e.g. DMart, Reliance Smart / Fresh, Nature's Basket, More, Spencer's, or local supermarket).

YOUR FORENSIC TASK:
1. Detect "store_name": The quick-commerce app or supermarket name (e.g. Zepto, Blinkit, DMart, Reliance Smart, Swiggy Instamart, BigBasket, Amazon Fresh, or "Store").
2. Extract ALL packaged foods, beverages, grocery items, dairy, snacks, cooking essentials, breads, and produce in "items":
   - Include brand name and product title as displayed (e.g. "Maggi 2-Minute Masala Noodles", "Amul Pasteurized Butter 500g", "Britannia 100% Whole Wheat Bread", "Fortune Sunflower Oil 1L", "Aashirvaad Shudh Chakki Atta 5kg", "Lay's Classic Salted", "Coca-Cola 750ml").
   - Extract "quantity": integer count (default 1).
   - Only exclude non-food household cleaning chemicals or bags: detergents, dishwash bars, floor cleaners, soaps, shampoos, garbage bags, toilet paper, batteries. All edible foods, drinks, and grocery staples MUST be included.

Return ONLY valid JSON:
{
  "store_name": "Zepto",
  "items": [
    {
      "product_name": "Full Brand Product Name",
      "quantity": 1
    }
  ]
}
If no food or grocery items are visible, return {"store_name": "Store", "items": []}
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

    async def extract_items_from_single_image(self, image_bytes: bytes) -> Dict[str, Any]:
        """Extract store and packaged food items from a single cart screenshot or store bill"""
        try:
            pil_img = Image.open(io.BytesIO(image_bytes))
            if pil_img.mode in ("RGBA", "P"):
                pil_img = pil_img.convert("RGB")
            # Preserve high resolution for tall phone screenshots (do not crush width to 540px)
            w, h = pil_img.size
            if max(w, h) > 2048:
                pil_img.thumbnail((2048, 2048), Image.Resampling.LANCZOS)
            buf = io.BytesIO()
            pil_img.save(buf, format="JPEG", quality=90, optimize=True)
            image_bytes = buf.getvalue()
        except Exception:
            pass

        for cl in self._get_active_clients():
            if not cl:
                continue
            for model_name in GEMINI_ACTIVE_MODELS:
                try:
                    response = cl.models.generate_content(
                        model=model_name,
                        contents=[
                            types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
                            CART_OR_BILL_OCR_PROMPT
                        ],
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            temperature=0.0
                        )
                    )
                    txt = response.text.strip()
                    if txt.startswith("```json"):
                        txt = txt[7:]
                    if txt.startswith("```"):
                        txt = txt[3:]
                    if txt.endswith("```"):
                        txt = txt[:-3]
                    parsed = json.loads(txt.strip())
                    if parsed and isinstance(parsed, dict) and parsed.get("items") and len(parsed["items"]) > 0:
                        return parsed
                except Exception as e:
                    logger.warning(f"Cart/bill OCR with {model_name} failed: {e}")
                    continue

        # Fallback: Plain text transcription if structured JSON OCR returned 0 items
        for cl in self._get_active_clients():
            if not cl:
                continue
            for model_name in GEMINI_ACTIVE_MODELS[:2]:
                try:
                    fallback_prompt = (
                        "Transcribe all visible food products, beverages, groceries, and packaged items in this cart screenshot or supermarket receipt. "
                        "List one product per line without prices or quantities."
                    )
                    res = cl.models.generate_content(
                        model=model_name,
                        contents=[
                            types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
                            fallback_prompt
                        ]
                    )
                    raw_text = res.text.strip() if res.text else ""
                    if raw_text:
                        parsed_items = self.parse_items_from_text_list(raw_text)
                        if parsed_items:
                            return {"store_name": "Store", "items": parsed_items}
                except Exception as e:
                    logger.warning(f"Fallback text OCR with {model_name} failed: {e}")

        return {"store_name": "Store", "items": []}

    async def extract_items_from_images(self, images_bytes_list: List[bytes]) -> Dict[str, Any]:
        """Extract and merge deduplicated packaged food items across multiple screenshots or bill photos"""
        if not images_bytes_list:
            return {"store_name": "Store", "items": []}

        tasks = [self.extract_items_from_single_image(img_b) for img_b in images_bytes_list[:8]]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        merged_items: Dict[str, int] = {}
        detected_store = "Store"

        for res in results:
            if isinstance(res, dict):
                st = res.get("store_name", "")
                if st and st not in ("Store", "Quick-Commerce"):
                    detected_store = st
                for it in res.get("items", []):
                    p_name = it.get("product_name", "").strip()
                    if p_name and len(p_name) > 2:
                        qty = int(it.get("quantity", 1))
                        # Match existing item case-insensitively
                        existing_key = next((k for k in merged_items if k.lower() == p_name.lower()), None)
                        if existing_key:
                            merged_items[existing_key] += qty
                        else:
                            merged_items[p_name] = qty

        final_items = [{"product_name": name, "quantity": qty} for name, qty in merged_items.items()]
        return {"store_name": detected_store, "items": final_items}

    def parse_items_from_text_list(self, text: str) -> List[Dict[str, Any]]:
        """Parses user-entered comma-separated or newline-separated product list"""
        if not text:
            return []
        items = []
        raw_lines = re.split(r'[\n,]+', text)
        seen = set()
        for raw in raw_lines:
            cleaned = raw.strip()
            if not cleaned:
                continue
            qty = 1
            qty_match = re.search(r'^(?:(\d+)\s*[xX*]\s*|\s*(\d+)\s+)', cleaned)
            if qty_match:
                qty = int(qty_match.group(1) or qty_match.group(2) or 1)
                cleaned = cleaned[qty_match.end():].strip()
            if len(cleaned) > 2 and cleaned.lower() not in seen:
                seen.add(cleaned.lower())
                items.append({"product_name": cleaned.title(), "quantity": max(1, qty)})
        return items

    def _call_gemini_text(self, prompt: str, max_output: int = 512) -> Optional[str]:
        """Synchronous Gemini text call for JSON extraction"""
        for cl in self._get_active_clients():
            if not cl:
                continue
            for model_name in GEMINI_ACTIVE_MODELS:
                try:
                    response = cl.models.generate_content(
                        model=model_name,
                        contents=[prompt],
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            max_output_tokens=max_output,
                            temperature=0.0
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

            # Try authentic packaging research via TinySearch + scoring engine
            audited_alt = await tinyfish_service.audit_alternative_candidate(alt_name, user_profile, item_score)
            if audited_alt and audited_alt.get("health_score", 0) > item_score:
                return HealthierAlternative(
                    name=audited_alt["name"],
                    product_name=audited_alt["name"],
                    health_score=audited_alt["health_score"],
                    key_benefit=audited_alt.get("key_benefit", "Cleaner formulation with fewer industrial additives."),
                    price_comparison="Comparable",
                    personalized_fit=audited_alt.get("personalized_fit", "Meets strict clinical health profile."),
                    store_url=audited_alt.get("store_url"),
                    direct_pdp_url=audited_alt.get("direct_pdp_url"),
                    pincode_available=True,
                    type="CLEAN_COMMERCIAL",
                    reason=audited_alt.get("reason", "Verified cleaner ingredient profile.")
                )

            alt_score = int(data.get("health_score", item_score + 12))
            key_benefit = data.get("key_benefit", "Cleaner ingredient profile with fewer additives.")
            search_url = data.get("search_url", "")
            reason = data.get("reason", "Verified cleaner formulation.")

            if alt_score <= item_score:
                return None

            from urllib.parse import quote_plus
            encoded = quote_plus(alt_name)
            google_shop = f"https://www.google.com/search?tbm=shop&q={encoded}"
            zepto_shop = f"https://www.zepto.com/search?query={encoded}"

            return HealthierAlternative(
                name=alt_name,
                product_name=alt_name,
                health_score=alt_score,
                key_benefit=key_benefit,
                price_comparison="Comparable",
                personalized_fit=reason,
                store_url=zepto_shop,
                direct_pdp_url=google_shop,
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

        # Deterministic category-specific commercial product swaps
        if not clean_alt_candidate and item_score < 75:
            OFFLINE_CATEGORY_ALTS = {
                "fruit juice/drink": ("Raw Pressery Cold Pressed Valencia Orange Juice", 86, "100% cold-pressed fruit, zero added cane sugar, zero preservatives."),
                "namkeen/savory snack": ("Slurrp Farm Ragi Puffs (Cheese & Herbs)", 88, "Baked finger millet & jowar, zero palm oil, zero synthetic MSG."),
                "chips/crisps": ("The Whole Truth Baked Potato Chips", 82, "Baked, cold-pressed oil, zero palmolein, zero artificial preservatives."),
                "biscuit/cracker": ("The Whole Truth 100% Whole Wheat Sourdough Crackers", 89, "100% whole wheat sourdough, zero maida, zero palm oil."),
                "cookies": ("Early Foods Organic Multi-Grain Jaggery Cookies", 87, "Organic jaggery and stone-ground millets, zero refined sugar."),
                "cola/carbonated drink": ("Atmosphere Brew Sparkling Raw Kombucha", 91, "Fermented probiotic tea, zero phosphoric acid."),
                "soda/carbonated water": ("Wild Drum Craft Sparkling Seltzer", 89, "Naturally flavored sparkling spring water, zero sugar, zero calories."),
                "energy drink": ("Raw Pressery Tender Coconut Water", 92, "Natural isotonic electrolyte beverage, zero synthetic taurine/caffeine."),
                "malt health drink": ("Early Foods Sprouted Ragi & Almond Cocoa Mix", 93, "100% sprouted ragi and almond, zero maltodextrin, zero refined sugar."),
                "instant noodles": ("Slurrp Farm Foxtail Millet Noodles", 88, "Sun-dried non-fried millet noodles, zero maida, clean seasoning."),
                "pasta": ("Slurrp Farm Multigrain Pasta", 86, "Millet & durum wheat semolina, zero artificial additives."),
                "breakfast cereal": ("The Whole Truth 100% Gluten-Free Rolled Oats", 94, "Single-ingredient rolled oats, high soluble fiber."),
                "chocolate/candy": ("The Whole Truth 71% Dark Chocolate", 90, "Cocoa beans and dates only, zero refined cane sugar, zero palm oil."),
                "cheese": ("Akshayakalpa Organic Artisan Mozzarella", 92, "100% certified organic A2 milk, zero synthetic emulsifying salts."),
                "butter/spread": ("Country Delight Fresh Churned White Butter", 88, "Traditional churned butter, zero synthetic coloring, zero artificial emulsifiers."),
                "bread/bakery": ("The Whole Truth 100% Whole Wheat Bread", 88, "Zero maida, zero palm oil, zero chemical dough conditioners."),
                "cooking oil": ("Two Brothers Organic Cold-Pressed Groundnut/Mustard Oil", 90, "Wood-pressed, zero chemical solvents, unrefined natural lipids."),
                "paneer": ("Akshayakalpa Organic Malai Paneer", 92, "Organic certified cow milk, zero synthetic acidifiers."),
                "milk": ("Country Delight Pure Cow Milk", 89, "Unadulterated fresh milk, tested daily, zero chemical neutralizers."),
                "yogurt/curd": ("Epigamia Natural Greek Yogurt Plain", 91, "High protein, zero added sugars, live active cultures."),
                "ghee": ("Two Brothers Organic A2 Cultured Ghee", 93, "Bilona method A2 cow milk ghee, rich in butyric acid."),
                "sauce/condiment": ("The Whole Truth No-Refined-Sugar Tomato Ketchup", 87, "Sweetened with dates and organic tomatoes, zero refined cane sugar."),
                "foxnuts/makhana": ("Open Secret Roasted Makhana (Foxnuts)", 88, "Roasted superfood, zero palm oil, rich in plant antioxidants."),
                "nuts/dry fruits": ("True Elements Raw Almonds & Walnuts", 93, "100% unroasted raw nuts, zero added sodium or preservatives.")
            }

            matched_cat = category
            if matched_cat not in OFFLINE_CATEGORY_ALTS:
                p_low = p_name.lower()
                for cat_k in OFFLINE_CATEGORY_ALTS.keys():
                    keywords = cat_k.replace('/', ' ').split()
                    if any(kw in p_low for kw in keywords if len(kw) > 3):
                        matched_cat = cat_k
                        break

            if matched_cat in OFFLINE_CATEGORY_ALTS:
                fb_name, fb_score, fb_benefit = OFFLINE_CATEGORY_ALTS[matched_cat]
                if fb_score > item_score:
                    clean_alt_candidate = HealthierAlternative(
                        name=fb_name,
                        product_name=fb_name,
                        health_score=fb_score,
                        key_benefit=fb_benefit,
                        price_comparison="Comparable",
                        personalized_fit="Verified cleaner formulation for your health profile.",
                        direct_pdp_url=f"https://www.zepto.com/search?query={urllib.parse.quote_plus(fb_name)}",
                        is_direct_pdp=False,
                        pincode_available=True,
                        type="CLEAN_COMMERCIAL",
                        reason=fb_benefit
                    )

        # Fallback to fresh whole-food YouTube recipe ONLY if no cleaner commercial product is available
        if not clean_alt_candidate and item_score < 75:
            topic = category if category and category != "packaged food" else p_name
            encoded_query = urllib.parse.quote_plus(f"how to make fresh {topic} at home healthy recipe")
            youtube_url = f"https://www.youtube.com/results?search_query={encoded_query}"
            recipe_name = f"Fresh Homemade {topic.title()} Recipe"
            recipe_score = get_realistic_homemade_recipe_score(topic, item_score)
            clean_alt_candidate = HealthierAlternative(
                name=recipe_name,
                product_name=recipe_name,
                health_score=recipe_score,
                key_benefit="100% whole unprocessed ingredients, zero industrial additives, zero palm oil.",
                price_comparison="Inexpensive",
                personalized_fit="Optimal natural nutrition without synthetic preservatives.",
                recipe_url=youtube_url,
                direct_pdp_url=youtube_url,
                is_direct_pdp=False,
                pincode_available=True,
                type="HOMEMADE_RECIPE",
                reason="No cleaner packaged swap exists in dark-store inventory. Prepare fresh with pure whole ingredients."
            )

        full_analysis_obj = analysis_res or LabelAnalysisResult(
            product_name=p_name,
            health_score=item_score,
            personalized_verdict=verdict,
            simple_summary=concerns[0] if concerns else f"Audited {p_name} for health profile.",
            deceptive_claims_flagged=[],
            fssai_violations=[],
            ingredient_breakdown=[
                IngredientItem(ingredient=c.split(':')[0], purpose="Flagged Factor", concern_level="HIGH" if item_score < 45 else "MEDIUM")
                for c in concerns
            ] if concerns else [],
            nutrition_card=None,
            healthier_alternative=clean_alt_candidate,
            clean_alternatives=[clean_alt_candidate] if clean_alt_candidate else [],
            nutrient_integrity=NutrientIntegrityMatrix()
        )

        return CartItemAudit(
            product_name=p_name,
            quantity=qty,
            health_score=item_score,
            personalized_verdict=verdict,
            key_concerns=concerns,
            cleaner_alternative=clean_alt_candidate,
            full_analysis=full_analysis_obj
        )

    async def audit_cart(
        self,
        images_bytes_list: Optional[List[bytes]] = None,
        item_names_text: Optional[str] = None,
        pincode: str = "110001",
        user_profile: UserProfile = None
    ) -> CartAuditResponse:
        """
        Full end-to-end cart & grocery bill audit.
        Accepts multiple cart screenshots / store bills or a text item list.
        """
        user_profile = user_profile or UserProfile()
        store_name = "Store"
        raw_items = []

        if images_bytes_list and len(images_bytes_list) > 0:
            extracted = await self.extract_items_from_images(images_bytes_list)
            store_name = extracted.get("store_name") or "Store"
            raw_items = extracted.get("items") or []

        # Seamless fallback: If images produced no items or user also provided text items
        if not raw_items and item_names_text and item_names_text.strip():
            raw_items = self.parse_items_from_text_list(item_names_text)
            store_name = "Custom Grocery List"

        if not raw_items:
            raise ValueError(
                "No packaged food products or cart items were detected. "
                "Please ensure the cart screenshot or store receipt clearly shows product titles, "
                "or switch to the 'Enter Product Names List' tab to type or paste the items directly."
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
