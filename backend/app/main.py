import time
import json
import logging
import re
import asyncio
from typing import Optional, List, Dict
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from app.config import PORT, HOST
from app.schemas.analysis import LabelAnalysisResult, HealthierAlternative
from app.schemas.user_profile import UserProfile
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.cart_audit import CartAuditResponse
from app.services.cart_audit_service import cart_audit_service
from app.schemas.condition import ValidateConditionRequest, ValidateConditionResponse
from app.schemas.compare import CompareProductsRequest, ProductComparisonResult
from app.schemas.multi_profile import MultiProfileScanResult, MultiProfileScanRequest, ProfileAuditInsight
from app.services.gemini_vision import gemini_vision_service
from app.services.chat_service import chat_service
from app.services.compare_service import compare_service
from app.services.condition_service import condition_validation_service
from app.data.survey_stats import SURVEY_METRICS
from app.data.presets import PRESET_PRODUCTS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="LabelTruth Backend",
    description="LabelTruth - Transparent Food Labeling, FSSAI Regulatory Auditor & Clinical Health Engine",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import hashlib
from typing import Optional, Dict
from pydantic import BaseModel

from app.data.demo_suite import DEMO_TIER_PRODUCTS
from app.services.profile_evaluator import evaluate_profile_safety_offline, create_multi_profile_result_offline
from app.services.delta_audit import apply_delta_audit_hierarchy

# Decoupled Dual-Key Cache Layer (Photo SHA256 + Normalized Product Name)
BASE_PRODUCT_CACHE: Dict[str, LabelAnalysisResult] = {}
SAFETY_CACHE: Dict[str, dict] = {}
AUDIT_CACHE: Dict[str, tuple[float, LabelAnalysisResult]] = {}
CACHE_TTL_SECONDS = 30 * 24 * 3600  # 30 days cache validity for food reformulation updates

def normalize_name_key(name: str) -> str:
    if not name:
        return ""
    return re.sub(r'[^a-z0-9]+', ' ', name.lower()).strip()

def compute_product_base_hash(content: bytes) -> str:
    h = hashlib.sha256()
    h.update(content)
    return h.hexdigest()

def compute_audit_hash(content: bytes, profile_str: str) -> str:
    h = hashlib.sha256()
    h.update(content)
    h.update(profile_str.encode('utf-8'))
    return h.hexdigest()

def store_product_in_cache(
    base_product: LabelAnalysisResult,
    image_bytes: Optional[bytes] = None,
    query_text: Optional[str] = None,
    profile: Optional[UserProfile] = None,
    profile_result: Optional[LabelAnalysisResult] = None
):
    now = time.time()
    res_to_store = profile_result or base_product

    name_keys = []
    if getattr(base_product, "product_name", None):
        name_keys.append(normalize_name_key(base_product.product_name))
    if query_text:
        name_keys.append(normalize_name_key(query_text))

    img_hash = compute_product_base_hash(image_bytes) if image_bytes else None

    # 1. Base product cache
    if img_hash:
        BASE_PRODUCT_CACHE[img_hash] = base_product
    for nk in name_keys:
        if nk:
            BASE_PRODUCT_CACHE[nk] = base_product
            nh = hashlib.sha256(nk.encode('utf-8')).hexdigest()
            BASE_PRODUCT_CACHE[nh] = base_product

    # 2. Profile audit cache (if profile provided)
    if profile:
        pid = profile.id or "default"
        if img_hash:
            AUDIT_CACHE[f"img:{img_hash}:{pid}"] = (now, res_to_store)
        for nk in name_keys:
            if nk:
                AUDIT_CACHE[f"name:{nk}:{pid}"] = (now, res_to_store)
                nh = hashlib.sha256(nk.encode('utf-8')).hexdigest()
                AUDIT_CACHE[f"hash:{nh}:{pid}"] = (now, res_to_store)

def find_in_audit_cache(
    image_bytes: Optional[bytes] = None,
    query_text: Optional[str] = None,
    profile: Optional[UserProfile] = None
) -> Optional[LabelAnalysisResult]:
    now = time.time()
    pid = profile.id or "default" if profile else "default"

    if image_bytes:
        img_hash = compute_product_base_hash(image_bytes)
        key = f"img:{img_hash}:{pid}"
        if key in AUDIT_CACHE:
            ts, item = AUDIT_CACHE[key]
            if now - ts < CACHE_TTL_SECONDS:
                return item

    if query_text:
        nk = normalize_name_key(query_text)
        if nk:
            key = f"name:{nk}:{pid}"
            if key in AUDIT_CACHE:
                ts, item = AUDIT_CACHE[key]
                if now - ts < CACHE_TTL_SECONDS:
                    return item
            nh = hashlib.sha256(nk.encode('utf-8')).hexdigest()
            hash_key = f"hash:{nh}:{pid}"
            if hash_key in AUDIT_CACHE:
                ts, item = AUDIT_CACHE[hash_key]
                if now - ts < CACHE_TTL_SECONDS:
                    return item

    return None

def find_in_base_cache(
    image_bytes: Optional[bytes] = None,
    query_text: Optional[str] = None
) -> Optional[LabelAnalysisResult]:
    if image_bytes:
        img_hash = compute_product_base_hash(image_bytes)
        if img_hash in BASE_PRODUCT_CACHE:
            return BASE_PRODUCT_CACHE[img_hash]
    if query_text:
        nk = normalize_name_key(query_text)
        if nk and nk in BASE_PRODUCT_CACHE:
            return BASE_PRODUCT_CACHE[nk]
        nh = hashlib.sha256(nk.encode('utf-8')).hexdigest()
        if nh in BASE_PRODUCT_CACHE:
            return BASE_PRODUCT_CACHE[nh]
    return None

class EvaluateProfileSafetyRequest(BaseModel):
    product_hash: Optional[str] = None
    product_name: Optional[str] = None
    base_product: Optional[LabelAnalysisResult] = None
    active_profile: UserProfile

@app.post('/api/evaluate-profile-safety')
async def evaluate_profile_safety_endpoint(payload: EvaluateProfileSafetyRequest):
    """
    Decoupled Profile Safety Re-Evaluation:
    Evaluates cached base product against active family member conditions in < 50ms
    without re-running OCR or web scraping.
    """
    prof = payload.active_profile
    prof_id = prof.id or "default"
    p_key = payload.product_name or payload.product_hash or (payload.base_product.product_name if payload.base_product else "")
    safety_key = f"safety:{p_key}:{prof_id}"

    if safety_key in SAFETY_CACHE:
        return SAFETY_CACHE[safety_key]

    base_product = payload.base_product
    if not base_product:
        base_product = find_in_base_cache(query_text=payload.product_name or payload.product_hash)

    if not base_product and payload.product_hash:
        base_product = BASE_PRODUCT_CACHE.get(payload.product_hash)

    if not base_product:
        # Default fallback to first demo product if not found
        base_product = LabelAnalysisResult(**DEMO_TIER_PRODUCTS["moderate"])

    eval_result = evaluate_profile_safety_offline(base_product, prof)
    SAFETY_CACHE[safety_key] = eval_result
    return eval_result

@app.get('/api/health')
def health_check():
    return {'status': 'healthy', 'service': 'LabelTruth'}

@app.get('/api/stats')
def get_survey_and_fssai_stats():
    return SURVEY_METRICS

@app.get('/api/presets')
def get_demo_presets():
    return PRESET_PRODUCTS

@app.post('/api/validate-condition', response_model=ValidateConditionResponse)
async def validate_condition(payload: ValidateConditionRequest):
    try:
        result = await condition_validation_service.validate(payload.condition)
        return result
    except Exception as e:
        logger.error(f'Condition validation error: {e}')
        raise HTTPException(status_code=500, detail=str(e))

@app.post('/api/analyze-label', response_model=LabelAnalysisResult)
async def analyze_label(
    image: UploadFile = File(..., alias="image"),
    user_profile: str = Form(...)
):
    try:
        profile_dict = json.loads(user_profile)
        profile = UserProfile(**profile_dict)
    except (json.JSONDecodeError, ValidationError) as e:
        logger.error(f'Invalid user profile: {e}')
        profile = UserProfile()

    try:
        image_bytes = await image.read()
        if not image_bytes:
            raise HTTPException(status_code=400, detail='Empty image file received.')
        
        # Check repeat audit hash cache
        cache_key = compute_audit_hash(image_bytes, user_profile)
        if cache_key in AUDIT_CACHE:
            c_time, c_result = AUDIT_CACHE[cache_key]
            if time.time() - c_time < CACHE_TTL_SECONDS:
                logger.info("Serving audit result from 30-day valid SHA-256 memory cache (zero credits used)")
                return c_result
            else:
                del AUDIT_CACHE[cache_key]

        result = await gemini_vision_service.analyze_label_image(image_bytes, profile)

        # 1. Image Validation: Reject non-food images
        is_food = result.get("is_food_label", True) if isinstance(result, dict) else getattr(result, "is_food_label", True)
        lbl_type = result.get("label_type", "") if isinstance(result, dict) else getattr(result, "label_type", "")
        if not is_food or lbl_type == "NOT_A_LABEL":
            raise HTTPException(
                status_code=400,
                detail="PRODUCT_NOT_VISIBLE: No food packaging or label detected in the image. Please upload a clear photo of the product label."
            )

        # 2. Comprehensive Partial Photo Logic:
        # If user provides only Front-of-Pack (fetch both ingredients & nutrition)
        # If user provides only Ingredients (fetch nutrition table)
        # If user provides only Nutrition card (fetch ingredients)
        has_ingredients = bool(getattr(result, "ingredient_breakdown", []))
        has_nutrition = bool(getattr(result, "nutrition_card", None) and getattr(result.nutrition_card, "breakdown", []))
        lbl_type_str = str(getattr(result, "label_type", ""))

        needs_enrichment = (
            lbl_type_str == "FRONT_OF_PACK" or
            (not has_ingredients and has_nutrition) or
            (has_ingredients and not has_nutrition)
        )

        if needs_enrichment and result.product_name:
            try:
                from app.services.tinyfish_service import tinyfish_service
                supplement_text = await tinyfish_service.search_and_fetch_bop(result.product_name)
                if supplement_text:
                    result = await gemini_vision_service.analyze_label_image(
                        image_bytes, 
                        profile, 
                        bop_supplement_text=supplement_text
                    )
            except Exception as tf_err:
                logger.warning(f"TinyFish partial photo enrichment fallback: {tf_err}")

        # Store in cache
        AUDIT_CACHE[cache_key] = (time.time(), result)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Analysis error: {e}')
        raise HTTPException(status_code=500, detail=f"Audit failed. Please verify that the label text is legible. Error: {str(e)}")

@app.post('/api/smart-scan', response_model=LabelAnalysisResult)
async def smart_scan(
    query: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    pincode: Optional[str] = Form("110001"),
    demo_mode: Optional[bool] = Form(False),
    user_profile: str = Form(...)
):
    """Smart hybrid input: handles image, product text name, or online quick-commerce URL with pincode localization and demo mode"""
    try:
        profile_dict = json.loads(user_profile)
        profile = UserProfile(**profile_dict)
    except Exception:
        profile = UserProfile()

    delivery_pincode = pincode or "110001"

    is_url_input = bool(query and (query.strip().startswith("http://") or query.strip().startswith("https://")))

    # Module 4: Offline DEMO_MODE Sandbox Suite (<100ms instant deterministic data)
    # Never apply demo sandbox to live URLs
    if demo_mode and not is_url_input:
        q_lower = (query or "").lower()
        if any(w in q_lower for w in ["chip", "lays", "bingo", "masala", "18"]):
            tier_key = "very_low"
        elif any(w in q_lower for w in ["bread", "brown bread", "atta bread", "38"]):
            tier_key = "low"
        elif any(w in q_lower for w in ["mozzarella", "cheese", "d'lecta", "58"]):
            tier_key = "moderate"
        elif any(w in q_lower for w in ["yogurt", "greek yogurt", "epigamia", "dahi", "78"]):
            tier_key = "high"
        elif any(w in q_lower for w in ["oat", "rolled oats", "steel cut", "95"]):
            tier_key = "very_high"
        else:
            tier_key = "moderate"
        
        demo_res = LabelAnalysisResult(**DEMO_TIER_PRODUCTS[tier_key])
        # Run decoupled profile evaluation on demo item
        eval_res = evaluate_profile_safety_offline(demo_res, profile)
        demo_res.personalized_verdict = eval_res["personalized_verdict"]
        return demo_res


    try:
        # Scenario 1: Image provided
        if image:
            image_bytes = await image.read()
            if image_bytes and len(image_bytes) > 0:
                await image.seek(0)
                cached_res = find_in_audit_cache(image_bytes=image_bytes, profile=profile)
                if cached_res:
                    logger.info("Serving image scan from dual-key audit cache (0 credits)")
                    return cached_res

                result = await analyze_label(image=image, user_profile=user_profile)
                
                # Enrich with TinyFish live web agent pincode alternatives
                candidate_list = []
                if result.health_score < 85:
                    try:
                        from app.services.tinyfish_service import tinyfish_service
                        pincode_alts = await tinyfish_service.find_pincode_alternatives(result.product_name, delivery_pincode)
                        if pincode_alts:
                            candidate_list.extend(pincode_alts)
                    except Exception as alt_err:
                        logger.warning(f"Error enriching image pincode alternatives: {alt_err}")

                if getattr(result, "clean_alternatives", None):
                    for ca in result.clean_alternatives:
                        candidate_list.append(ca.model_dump() if hasattr(ca, "model_dump") else ca)

                # Apply delta audit hierarchy
                hierarchical_alts = apply_delta_audit_hierarchy(result.product_name, result.health_score, candidate_list)
                if hierarchical_alts:
                    result.clean_alternatives = hierarchical_alts
                    result.healthier_alternative = hierarchical_alts[0]

                store_product_in_cache(
                    base_product=result,
                    image_bytes=image_bytes,
                    query_text=result.product_name,
                    profile=profile,
                    profile_result=result
                )
                return result

        # Scenario 2: Text / Product name / Shared URL
        if query and query.strip():
            clean_query = query.strip()
            cached_res = find_in_audit_cache(query_text=clean_query, profile=profile)
            if cached_res:
                logger.info(f"Serving query audit for '{clean_query}' from dual-key audit cache (zero credits used)")
                return cached_res

            from app.services.tinyfish_service import tinyfish_service
            online_content = ""
            effective_product_name = clean_query

            if clean_query.startswith("http://") or clean_query.startswith("https://"):
                url_title, bop_content = await tinyfish_service.search_and_fetch_bop_by_url(clean_query)
                effective_product_name = url_title or clean_query
                online_content = bop_content or ""
            else:
                online_content = await tinyfish_service.search_and_fetch_bop(clean_query) or ""

            result = await gemini_vision_service.analyze_text_query(effective_product_name, profile, online_content)
            if isinstance(result, dict):
                result = LabelAnalysisResult(**result)

            # Module 2 & 1: Pin-Code Location Web Agent & Delta Audit Hierarchy
            candidate_list = []
            cleaner_hint = getattr(result, "cleaner_alternative_exists_in_market", False)
            should_search = result.health_score < 85 or cleaner_hint
            if should_search:
                try:
                    prod_name = getattr(result, "product_name", clean_query)
                    pincode_alts = await tinyfish_service.find_pincode_alternatives(prod_name, delivery_pincode)
                    if pincode_alts:
                        candidate_list.extend(pincode_alts)
                except Exception as alt_err:
                    logger.warning(f"Error enriching pincode alternatives: {alt_err}")

            if getattr(result, "clean_alternatives", None):
                for ca in result.clean_alternatives:
                    candidate_list.append(ca.model_dump() if hasattr(ca, "model_dump") else ca)

            hierarchical_alts = apply_delta_audit_hierarchy(
                result.product_name or clean_query,
                result.health_score,
                candidate_list,
                cleaner_exists_hint=cleaner_hint
            )
            if hierarchical_alts:
                result.clean_alternatives = hierarchical_alts
                result.healthier_alternative = hierarchical_alts[0]

            store_product_in_cache(
                base_product=result,
                query_text=clean_query,
                profile=profile,
                profile_result=result
            )
            return result

        raise HTTPException(status_code=400, detail="Please provide either a product label photo, product name, or quick-commerce link.")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Smart scan error: {e}")
        raise HTTPException(status_code=500, detail=f"Smart scan encountered an issue: {str(e)}. Try uploading an image directly.")


@app.post('/api/smart-scan-multi-profile', response_model=MultiProfileScanResult)
async def smart_scan_multi_profile(
    query: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    pincode: Optional[str] = Form("110001"),
    demo_mode: Optional[bool] = Form(False),
    profiles: str = Form(...)
):
    """
    Simultaneous Multi-Profile Audit (Max 3 Profiles):
    Audits the food product once, and produces simultaneous clinical evaluations,
    personalized health scores, and an overarching household decision in a single pass.
    Populates dual-key cache entries for every profile for instant zero-credit repeat scans.
    """
    try:
        profiles_raw = json.loads(profiles)
        user_profiles = [UserProfile(**p) for p in profiles_raw][:3]
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid profiles format: {str(e)}")

    if not user_profiles:
        raise HTTPException(status_code=400, detail="At least 1 profile must be provided (max 3).")

    delivery_pincode = pincode or "110001"
    image_bytes = None
    if image:
        image_bytes = await image.read()
        await image.seek(0)

    # 1. Check if base product exists in dual-key cache
    base_product = find_in_base_cache(image_bytes=image_bytes, query_text=query)

    # 2. If not cached, run smart scan once with primary profile
    if not base_product:
        base_product = await smart_scan(
            query=query,
            image=image,
            pincode=delivery_pincode,
            demo_mode=demo_mode,
            user_profile=user_profiles[0].model_dump_json()
        )

    # 3. Create multi-profile evaluation
    multi_result = create_multi_profile_result_offline(base_product, user_profiles)

    # 4. Populate dual-key cache entries for all profiles audited
    for p in user_profiles:
        ins = next((i for i in multi_result.profiles_audited if i.profile_id == p.id), None)
        prof_res = base_product.model_copy(deep=True)
        if ins:
            prof_res.health_score = ins.health_score
            prof_res.personalized_verdict = ins.personalized_verdict
            prof_res.simple_summary = ins.personalized_summary
            prof_res.ingredient_breakdown = ins.ingredient_warnings

        store_product_in_cache(
            base_product=base_product,
            image_bytes=image_bytes,
            query_text=query or base_product.product_name,
            profile=p,
            profile_result=prof_res
        )

    return multi_result


class DiscoverAlternativesRequest(BaseModel):
    product_name: str
    category: Optional[str] = ""
    current_health_score: int
    pincode: Optional[str] = "110001"
    user_profile: Optional[UserProfile] = None


@app.post('/api/discover-alternatives', response_model=List[HealthierAlternative])
async def discover_alternatives_endpoint(payload: DiscoverAlternativesRequest):
    """
    Asynchronous Alternative Product Discovery & Forensic Verification:
    Finds real Indian cleaner brand alternatives, audits their authentic packaging
    via TinySearch + TinyFetch + Scoring Engine, verifies audited_score > current_health_score,
    and returns verified cleaner products with Google Shopping / direct commerce links.
    """
    from app.services.tinyfish_service import tinyfish_service
    from app.services.delta_audit import apply_delta_audit_hierarchy

    user_profile = payload.user_profile or UserProfile()
    p_name = payload.product_name
    category = payload.category or ""
    current_score = payload.current_health_score
    pincode = payload.pincode or "110001"

    CATEGORY_CANDIDATES = {
        "namkeen": ["Slurrp Farm Ragi Puffs", "Open Secret Roasted Makhana", "Sattviko Makhana Pudina"],
        "snack": ["Slurrp Farm Ragi Puffs", "True Elements Multigrain Snacks", "Open Secret Makhana"],
        "chips": ["The Whole Truth Baked Potato Chips", "TagZ Popped Chips", "BRB Popped Chips"],
        "biscuit": ["The Whole Truth 100% Sourdough Crackers", "Early Foods Organic Ragi Cookies", "Slurrp Farm Millet Cookies"],
        "cookies": ["Early Foods Multi-Grain Jaggery Cookies", "Slurrp Farm Millet Choco Chip Cookies"],
        "cola": ["Atmosphere Brew Sparkling Kombucha", "Wild Drum Craft Seltzer", "Raw Pressery Cold Pressed Juice"],
        "drink": ["Paper Boat Coconut Water", "Raw Pressery Cold Pressed Valencia Orange", "Epigamia Greek Yogurt Smoothie"],
        "health drink": ["Early Foods Sprouted Ragi & Almond Cocoa Mix", "Little Joys Nutrition Mix"],
        "malt": ["Early Foods Sprouted Ragi Almond Cocoa", "Slurrp Farm Superfoods Chocolate Powder"],
        "noodles": ["Slurrp Farm Foxtail Millet Noodles", "Masterchow Hakka Whole Wheat Noodles", "WickedGud Multigrain Noodles"],
        "cereal": ["The Whole Truth 100% Rolled Oats", "True Elements Rolled Oats", "Slurrp Farm Millet Muesli"],
        "oats": ["The Whole Truth Rolled Oats", "True Elements Rolled Oats"],
        "chocolate": ["The Whole Truth 71% Dark Chocolate", "Paul and Mike Dark Chocolate"],
        "cheese": ["Akshayakalpa Organic Artisan Mozzarella", "Country Delight Pure Cheese"],
        "butter": ["Country Delight Fresh Butter", "Akshayakalpa Organic Butter"],
        "yogurt": ["Epigamia Natural Greek Yogurt", "Milky Mist Greek Yogurt Plain"],
        "jam": ["The Whole Truth 100% Fruit Spread", "Bhuira Jam Homemade Apple & Cinnamon"],
        "ketchup": ["The Whole Truth No-Refined-Sugar Tomato Ketchup", "Naagin Original Hot Sauce"],
        "peanut butter": ["Pintola 100% Pure Natural Peanut Butter", "The Whole Truth 100% Peanut Butter Dark Chocolate"]
    }

    candidates_to_try = []
    cat_lower = (category or "").lower()
    name_lower = p_name.lower()

    for key, cands in CATEGORY_CANDIDATES.items():
        if key in cat_lower or key in name_lower:
            candidates_to_try.extend(cands)
            break

    if not candidates_to_try:
        candidates_to_try = ["The Whole Truth Snack", "Slurrp Farm Healthy Snack", "True Elements Rolled Oats"]

    unique_cands = list(dict.fromkeys(candidates_to_try))[:3]

    audit_tasks = [
        tinyfish_service.audit_alternative_candidate(cand, user_profile, current_score)
        for cand in unique_cands
    ]
    audited_results = await asyncio.gather(*audit_tasks, return_exceptions=True)

    verified_alts = []
    for res in audited_results:
        if isinstance(res, HealthierAlternative):
            verified_alts.append(res)
        elif isinstance(res, dict):
            try:
                verified_alts.append(HealthierAlternative(**res))
            except Exception:
                pass

    candidate_dicts = [a.model_dump() for a in verified_alts]
    hierarchical = apply_delta_audit_hierarchy(p_name, current_score, candidate_dicts)
    return hierarchical or verified_alts

@app.post('/api/chat', response_model=ChatResponse)
async def chat_endpoint(payload: ChatRequest):
    try:
        reply = await chat_service.chat(
            message=payload.message,
            history=payload.history,
            user_profile=payload.user_profile,
            product_context=payload.product_context
        )
        return ChatResponse(reply=reply)
    except Exception as e:
        logger.error(f'Chat error: {e}')
        raise HTTPException(status_code=500, detail=str(e))


@app.post('/api/compare-products', response_model=ProductComparisonResult)
async def compare_products_endpoint(payload: CompareProductsRequest):
    try:
        result = await compare_service.compare_products(
            product_a=payload.product_a,
            product_b=payload.product_b,
            user_profile=payload.user_profile,
            pincode=payload.pincode
        )
        return result
    except Exception as e:
        logger.error(f"Compare products error: {e}")
        raise HTTPException(status_code=500, detail=f"Comparison failed: {str(e)}")


@app.post('/api/audit-cart', response_model=CartAuditResponse)
async def audit_cart_endpoint(
    images: Optional[List[UploadFile]] = File(None),
    image: Optional[UploadFile] = File(None),
    item_names: Optional[str] = Form(None),
    cart_url: Optional[str] = Form(None),
    pincode: str = Form("110001"),
    user_profile: str = Form("{}")
):
    try:
        profile_dict = json.loads(user_profile)
        profile = UserProfile(**profile_dict)
    except Exception:
        profile = UserProfile()

    images_bytes_list: List[bytes] = []
    if images:
        for img in images:
            if img and img.filename:
                try:
                    b = await img.read()
                    if b:
                        images_bytes_list.append(b)
                except Exception:
                    pass
    if image and image.filename:
        try:
            b = await image.read()
            if b and b not in images_bytes_list:
                images_bytes_list.append(b)
        except Exception:
            pass

    # Backwards compatibility: If cart_url passed in tests or legacy clients, extract item names
    effective_item_names = item_names
    if not effective_item_names and cart_url:
        from app.services.tinyfish_service import extract_product_name_from_url
        if "items=" in cart_url:
            raw = cart_url.split("items=")[-1].split("&")[0]
            effective_item_names = ", ".join([part.replace("-", " ") for part in raw.split(",")])
        else:
            extracted_name = extract_product_name_from_url(cart_url)
            if extracted_name:
                effective_item_names = extracted_name

    try:
        response = await cart_audit_service.audit_cart(
            images_bytes_list=images_bytes_list if len(images_bytes_list) > 0 else None,
            item_names_text=effective_item_names,
            pincode=pincode.strip() or "110001",
            user_profile=profile
        )
        return response
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Cart audit error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to audit cart: {str(e)}")

@app.get('/api/reverse-geocode')
async def reverse_geocode_endpoint(lat: float, lon: float):
    """
    High-precision server-side reverse geocode via Nominatim with proper User-Agent header.
    Extracts authentic 6-digit Indian postal code (PIN) directly from latitude & longitude coordinates.
    """
    import httpx
    headers = {
        "User-Agent": "LabelTruthClinicalApp/1.0 (https://labeltruth.org; contact@labeltruth.org)",
        "Accept": "application/json"
    }
    url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&zoom=18&format=json&addressdetails=1"
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            res = await client.get(url, headers=headers)
            if res.status_code == 200:
                data = res.json()
                addr = data.get("address", {})
                pin = addr.get("postcode") or addr.get("postal_code") or ""
                match = re.search(r'\b([1-9][0-9]{5})\b', str(pin))
                locality = addr.get("suburb") or addr.get("neighbourhood") or addr.get("city") or addr.get("town") or addr.get("county") or ""
                if match:
                    return {
                        "pincode": match.group(1),
                        "locality": locality,
                        "state": addr.get("state", ""),
                        "display_name": data.get("display_name", "")
                    }
    except Exception as e:
        logger.warning(f"Nominatim server reverse geocode notice: {e}")

    # Fallback to BigDataCloud
    try:
        bdc_url = f"https://api.bigdatacloud.net/data/reverse-geocode-client?latitude={lat}&longitude={lon}&localityLanguage=en"
        async with httpx.AsyncClient(timeout=6.0) as client:
            res = await client.get(bdc_url)
            if res.status_code == 200:
                data = res.json()
                pin = data.get("postcode") or data.get("postCode") or ""
                match = re.search(r'\b([1-9][0-9]{5})\b', str(pin))
                if match:
                    return {
                        "pincode": match.group(1),
                        "locality": data.get("locality") or data.get("city") or "",
                        "state": data.get("principalSubdivision", ""),
                        "display_name": data.get("locality", "")
                    }
    except Exception as bdc_err:
        logger.warning(f"BigDataCloud server reverse geocode notice: {bdc_err}")

    return {"pincode": None, "locality": None, "state": None}

