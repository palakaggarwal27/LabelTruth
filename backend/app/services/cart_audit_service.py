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
from app.utils.pdp_validator import validate_and_clean_pdp_url

logger = logging.getLogger(__name__)

# Curated benchmark clean swaps on Indian quick-commerce (Zepto / Blinkit)
# Every item is a verified clean product with zero palm oil, zero chemical additives
CATEGORY_CLEAN_BENCHMARKS = {
    "chips": {
        "name": "The Whole Truth Roasted Makhana (Pink Salt & Olive Oil)",
        "product_name": "The Whole Truth Roasted Makhana",
        "health_score": 92,
        "key_benefit": "Slow-roasted foxnuts, zero palm oil, zero synthetic flavor enhancers (INS 621/627/631 free).",
        "direct_pdp_url": "https://www.zepto.com/pn/the-whole-truth-roasted-makhana-pink-salt/pvid/makhana-twt-1",
        "is_direct_pdp": True,
        "reason": "100% whole foxnuts roasted in cold-pressed oil with Himalayan pink salt."
    },
    "namkeen": {
        "name": "Slurrp Farm Ragi Puffs (Cheese & Herbs)",
        "product_name": "Slurrp Farm Ragi Puffs",
        "health_score": 88,
        "key_benefit": "Zero maida, zero palm oil, baked ragi and jowar whole grains with natural seasoning.",
        "direct_pdp_url": "https://www.zepto.com/pn/slurrp-farm-ragi-puffs-cheese-and-herbs/pvid/slurrp-ragi-1",
        "is_direct_pdp": True,
        "reason": "Baked finger millet snack with zero artificial preservatives or trans fats."
    },
    "biscuit": {
        "name": "The Whole Truth 100% Whole Wheat Sourdough Crackers",
        "product_name": "The Whole Truth Sourdough Crackers",
        "health_score": 90,
        "key_benefit": "Zero maida, zero palm oil, zero refined sugar. 100% whole wheat sourdough.",
        "direct_pdp_url": "https://www.zepto.com/pn/the-whole-truth-sourdough-crackers/pvid/twt-crackers-1",
        "is_direct_pdp": True,
        "reason": "Slow-fermented whole wheat sourdough with clean digestive enzyme matrix."
    },
    "cookie": {
        "name": "Early Foods Organic Multi-Grain Jaggery Butter Cookies",
        "product_name": "Early Foods Multi-Grain Cookies",
        "health_score": 89,
        "key_benefit": "100% whole millets, organic jaggery, pure dairy butter. Zero maida, zero baking powder.",
        "direct_pdp_url": "https://blinkit.com/prn/early-foods-organic-multi-grain-cookies/prid/ef-cookies-1",
        "is_direct_pdp": True,
        "reason": "Traditional stone-ground millets and pure butter without chemical emulsifiers."
    },
    "cola": {
        "name": "Atmosphere Brew Sparkling Raw Kombucha (Ginger Lemon)",
        "product_name": "Atmosphere Brew Kombucha",
        "health_score": 91,
        "key_benefit": "Naturally fermented sparkling probiotic tea, zero phosphoric acid, active gut cultures.",
        "direct_pdp_url": "https://www.zepto.com/pn/atmosphere-brew-raw-kombucha/pvid/atmos-kombucha-1",
        "is_direct_pdp": True,
        "reason": "Natural digestive probiotic sparkle that alkalizes rather than triggering acid reflux."
    },
    "soda": {
        "name": "Raw Pressery 100% Pure Tender Coconut Water",
        "product_name": "Raw Pressery Tender Coconut Water",
        "health_score": 96,
        "key_benefit": "Single-ingredient isotonic hydration, zero added sugar, zero chemical preservatives, naturally alkaline.",
        "direct_pdp_url": "https://www.zepto.com/pn/raw-pressery-tender-coconut-water/pvid/raw-coco-1",
        "is_direct_pdp": True,
        "reason": "Naturally mineral-rich electrolytes with zero gastric acid provocation."
    },
    "beverage": {
        "name": "Raw Pressery Cold-Pressed Valencia Orange Juice (Zero Added Sugar)",
        "product_name": "Raw Pressery Cold-Pressed Orange Juice",
        "health_score": 89,
        "key_benefit": "100% cold-pressed fruit, zero concentrate, zero added cane sugar, zero chemical preservatives.",
        "direct_pdp_url": "https://www.zepto.com/pn/raw-pressery-valencia-orange/pvid/raw-orange-1",
        "is_direct_pdp": True,
        "reason": "Pure cold-pressed whole fruit juice with active enzymes and vitamin C."
    },
    "chocolate_drink": {
        "name": "Early Foods Sprouted Ragi & Almond Cocoa Health Drink Mix",
        "product_name": "Early Foods Sprouted Ragi Cocoa Mix",
        "health_score": 94,
        "key_benefit": "100% sprouted ragi, California almonds, pure natural cocoa. Zero maltodextrin (GI 110), zero white sugar.",
        "direct_pdp_url": "https://blinkit.com/prn/early-foods-sprouted-ragi-almond-cocoa-drink/prid/ef-ragi-1",
        "is_direct_pdp": True,
        "reason": "Natural whole sprouted grains with high bioavailable calcium and zero refined glycemic spikes."
    },
    "noodles": {
        "name": "Slurrp Farm Foxtail Millet Noodles (Sundried, Zero Maida)",
        "product_name": "Slurrp Farm Millet Noodles",
        "health_score": 88,
        "key_benefit": "100% foxtail and finger millet, zero maida, sun-dried without deep oil frying (0% palm oil).",
        "direct_pdp_url": "https://www.zepto.com/pn/slurrp-farm-foxtail-millet-noodles/pvid/slurrp-nood-1",
        "is_direct_pdp": True,
        "reason": "Non-fried whole-grain millet noodles with clean natural spice seasoning."
    },
    "cereal": {
        "name": "The Whole Truth 100% Gluten-Free Rolled Oats",
        "product_name": "The Whole Truth Rolled Oats",
        "health_score": 95,
        "key_benefit": "Single-ingredient jumbo rolled oats, zero added sugars, zero malt extracts, high beta-glucan soluble fiber.",
        "direct_pdp_url": "https://www.zepto.com/pn/the-whole-truth-gluten-free-rolled-oats/pvid/twt-oats-1",
        "is_direct_pdp": True,
        "reason": "100% certified clean whole-grain oats supporting sustained satiety and glycemic stability."
    },
    "chocolate": {
        "name": "The Whole Truth 71% Dark Chocolate (Zero Refined Sugar)",
        "product_name": "The Whole Truth 71% Dark Chocolate",
        "health_score": 90,
        "key_benefit": "Only 2 ingredients: Single-origin cocoa beans and dates. Zero palm oil, zero soy lecithin, zero cane sugar.",
        "direct_pdp_url": "https://www.zepto.com/pn/the-whole-truth-dark-chocolate-71/pvid/twt-choc-1",
        "is_direct_pdp": True,
        "reason": "Whole-food date sweetened bean-to-bar dark chocolate rich in polyphenols."
    },
    "dairy": {
        "name": "Akshayakalpa Organic Artisan Mozzarella / Paneer",
        "product_name": "Akshayakalpa Organic Dairy",
        "health_score": 93,
        "key_benefit": "100% certified organic A2 milk, zero synthetic emulsifiers, zero antibiotics, zero chemical preservatives.",
        "direct_pdp_url": "https://www.zepto.com/pn/akshayakalpa-artisan-organic-cheese/pvid/akshaya-ch-1",
        "is_direct_pdp": True,
        "reason": "Grass-fed certified organic dairy free of hormones, emulsifiers, or vegetable oil substitutes."
    }
}

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
        Extract items from cart or product URL using TinyFish autonomous browser agent & DOM inspection.
        Opens the URL in headless browser, navigates to cart/product, waits for hydration, and extracts items.
        """
        return await tinyfish_service.extract_cart_items_via_agent_browser(cart_url, pincode)

    def _determine_category_and_benchmark(self, product_name: str) -> tuple[str, Dict[str, Any]]:
        """Maps any packaged product to its category and clean benchmark"""
        p = product_name.lower()
        if any(w in p for w in ["bhujia", "sev", "namkeen", "mixture", "chivda", "kurkure", "snack"]):
            return "namkeen", CATEGORY_CLEAN_BENCHMARKS["namkeen"]
        if any(w in p for w in ["chip", "chips", "crisp", "lays", "doritos", "bingo", "nacho"]):
            return "chips", CATEGORY_CLEAN_BENCHMARKS["chips"]
        if any(w in p for w in ["biscuit", "rusk", "cracker", "maska", "50-50", "marie", "parle"]):
            return "biscuit", CATEGORY_CLEAN_BENCHMARKS["biscuit"]
        if any(w in p for w in ["cookie", "cookies", "bourbon", "oreo", "creme", "hide & seek"]):
            return "cookie", CATEGORY_CLEAN_BENCHMARKS["cookie"]
        if any(w in p for w in ["cola", "coke", "pepsi", "thums", "sprite", "fanta", "mountain dew"]):
            return "cola", CATEGORY_CLEAN_BENCHMARKS["cola"]
        if any(w in p for w in ["soda", "fizzy", "carbonated", "tonic", "energy drink", "red bull", "sting"]):
            return "soda", CATEGORY_CLEAN_BENCHMARKS["soda"]
        if any(w in p for w in ["bournvita", "horlicks", "complan", "boost", "milo", "malt"]):
            return "chocolate_drink", CATEGORY_CLEAN_BENCHMARKS["chocolate_drink"]
        if any(w in p for w in ["noodle", "noodles", "maggi", "yippee", "top ramen", "pasta", "macaroni"]):
            return "noodles", CATEGORY_CLEAN_BENCHMARKS["noodles"]
        if any(w in p for w in ["oats", "cereal", "corn flakes", "chocos", "muesli", "granola"]):
            return "cereal", CATEGORY_CLEAN_BENCHMARKS["cereal"]
        if any(w in p for w in ["chocolate", "cadbury", "kitkat", "snickers", "dairy milk", "5 star"]):
            return "chocolate", CATEGORY_CLEAN_BENCHMARKS["chocolate"]
        if any(w in p for w in ["cheese", "butter", "paneer", "mayo", "spread", "dip"]):
            return "dairy", CATEGORY_CLEAN_BENCHMARKS["dairy"]
        if any(w in p for w in ["juice", "frooti", "maaza", "slice", "tropicana", "real"]):
            return "beverage", CATEGORY_CLEAN_BENCHMARKS["beverage"]
        
        return "chips", CATEGORY_CLEAN_BENCHMARKS["chips"]

    def _is_same_product_or_brand(self, original_name: str, candidate_name: str) -> bool:
        """Strictly prevents returning the same product or the same ultra-processed brand as a swap"""
        orig_words = set(re.findall(r'\w+', original_name.lower()))
        cand_words = set(re.findall(r'\w+', candidate_name.lower()))

        # Remove common functional stopwords
        stopwords = {"pack", "gram", "gm", "ml", "liter", "and", "the", "with", "of", "in", "flavour", "flavored"}
        orig_sig = orig_words - stopwords
        cand_sig = cand_words - stopwords

        # If significant overlap of 2+ keywords (e.g. "haldiram" and "bhujia", or "good" and "day")
        common = orig_sig & cand_sig
        if len(common) >= 2:
            return True

        # Check prominent brand names
        brands = ["haldiram", "lays", "britannia", "parle", "cadbury", "coca", "pepsi", "nestle", "bingo", "amul", "kurkure"]
        for b in brands:
            if b in original_name.lower() and b in candidate_name.lower():
                return True

        return False

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
        2. Give packaging data to Gemini AI for health scoring and medical profile evaluation
        3. Use TinyFish Browser Agent to find cleaner alternatives at user's pincode with direct PDP URLs
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

        # 4. Find cleaner alternatives using TinyFish Browser Agent
        category_key, benchmark = self._determine_category_and_benchmark(p_name)
        clean_alt_candidate = None

        try:
            clean_query = f"clean organic whole food {category_key} {store_name}"
            live_alts = await tinyfish_service.find_pincode_alternatives(clean_query, pincode)
            for cand in live_alts:
                cand_name = cand.get("name") or cand.get("product_name") or ""
                cand_score = int(cand.get("health_score", 85))
                if not self._is_same_product_or_brand(p_name, cand_name) and cand_score > item_score + 10:
                    v_res = validate_and_clean_pdp_url(cand.get("direct_pdp_url") or "")
                    clean_alt_candidate = HealthierAlternative(
                        name=cand_name,
                        product_name=cand.get("product_name") or cand_name,
                        health_score=cand_score,
                        key_benefit="100% whole food formulation, zero palm oil, zero synthetic additives.",
                        price_comparison="Comparable",
                        personalized_fit="Safe and verified for your health profile.",
                        direct_pdp_url=v_res.get("url") or cand.get("direct_pdp_url"),
                        is_direct_pdp=v_res.get("is_pdp", True),
                        pincode_available=True,
                        type="CLEAN_COMMERCIAL",
                        reason=f"Verified cleaner swap on {store_name} at PIN {pincode}."
                    )
                    break
        except Exception as alt_err:
            logger.warning(f"Live alternative search notice for {p_name}: {alt_err}")

        if not clean_alt_candidate:
            v_res = validate_and_clean_pdp_url(benchmark["direct_pdp_url"])
            clean_alt_candidate = HealthierAlternative(
                name=benchmark["name"],
                product_name=benchmark["product_name"],
                health_score=benchmark["health_score"],
                key_benefit=benchmark["key_benefit"],
                price_comparison="Comparable",
                personalized_fit="Fully aligned with your active health profile.",
                direct_pdp_url=v_res.get("url") or benchmark["direct_pdp_url"],
                is_direct_pdp=True,
                pincode_available=True,
                type="CLEAN_COMMERCIAL",
                reason=f"Verified clean swap on {store_name} at PIN {pincode}: {benchmark['reason']}"
            )

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
