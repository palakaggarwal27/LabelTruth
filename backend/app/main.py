import json
import logging
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from app.config import PORT, HOST
from app.schemas.analysis import LabelAnalysisResult
from app.schemas.user_profile import UserProfile
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.condition import ValidateConditionRequest, ValidateConditionResponse
from app.services.gemini_vision import gemini_vision_service
from app.services.chat_service import chat_service
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
from app.services.profile_evaluator import evaluate_profile_safety_offline
from app.services.delta_audit import apply_delta_audit_hierarchy

# Decoupled Cache Layer
# 1. Base product data keyed by SHA256(raw_text_or_url)
BASE_PRODUCT_CACHE: Dict[str, LabelAnalysisResult] = {}
# 2. Profile warnings keyed by safety:{product_hash}:{profile_id}
SAFETY_CACHE: Dict[str, dict] = {}

AUDIT_CACHE: Dict[str, LabelAnalysisResult] = {}

def compute_product_base_hash(content: bytes) -> str:
    h = hashlib.sha256()
    h.update(content)
    return h.hexdigest()

def compute_audit_hash(content: bytes, profile_str: str) -> str:
    h = hashlib.sha256()
    h.update(content)
    h.update(profile_str.encode('utf-8'))
    return h.hexdigest()

class EvaluateProfileSafetyRequest(BaseModel):
    product_hash: str
    active_profile: UserProfile

@app.post('/api/evaluate-profile-safety')
async def evaluate_profile_safety_endpoint(payload: EvaluateProfileSafetyRequest):
    """
    Decoupled Profile Safety Re-Evaluation:
    Evaluates cached base product against active family member conditions in < 50ms
    without re-running OCR or web scraping.
    """
    p_hash = payload.product_hash
    prof = payload.active_profile
    prof_id = prof.id or "default"
    safety_key = f"safety:{p_hash}:{prof_id}"

    if safety_key in SAFETY_CACHE:
        return SAFETY_CACHE[safety_key]

    base_product = BASE_PRODUCT_CACHE.get(p_hash)
    if not base_product:
        # Check in AUDIT_CACHE fallback
        for k, v in AUDIT_CACHE.items():
            if p_hash in k:
                base_product = v
                break

    if not base_product:
        # Default fallback to first demo product if hash not found
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
            logger.info("Serving audit result from SHA-256 memory cache (zero credits used)")
            return AUDIT_CACHE[cache_key]

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
        AUDIT_CACHE[cache_key] = result
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

    # Module 4: Offline DEMO_MODE Sandbox Suite (<100ms instant deterministic data)
    if demo_mode:
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
                return result

        # Scenario 2: Text / Product name / Shared URL
        if query and query.strip():
            clean_query = query.strip()
            base_hash = compute_product_base_hash(clean_query.lower().encode('utf-8'))
            query_cache_key = compute_audit_hash(f"{clean_query.lower()}:{delivery_pincode}".encode('utf-8'), user_profile)
            if query_cache_key in AUDIT_CACHE:
                logger.info(f"Serving query audit for '{clean_query}' from SHA-256 cache (zero credits used)")
                return AUDIT_CACHE[query_cache_key]

            from app.services.tinyfish_service import tinyfish_service
            online_content = ""
            if clean_query.startswith("http://") or clean_query.startswith("https://"):
                data = await tinyfish_service.fetch_product_details(clean_query)
                if data:
                    online_content = str(data.get("text", "") or data.get("content", "") or data)
            else:
                online_content = await tinyfish_service.search_and_fetch_bop(clean_query) or ""

            result = await gemini_vision_service.analyze_text_query(clean_query, profile, online_content)
            if isinstance(result, dict):
                result = LabelAnalysisResult(**result)

            # Save in decoupled base product cache
            BASE_PRODUCT_CACHE[base_hash] = result

            # Module 2 & 1: Pin-Code Location Web Agent & Delta Audit Hierarchy
            candidate_list = []
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
                candidate_list
            )
            if hierarchical_alts:
                result.clean_alternatives = hierarchical_alts
                result.healthier_alternative = hierarchical_alts[0]

            AUDIT_CACHE[query_cache_key] = result
            return result

        raise HTTPException(status_code=400, detail="Please provide either a product label photo, product name, or quick-commerce link.")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Smart scan error: {e}")
        raise HTTPException(status_code=500, detail=f"Smart scan encountered an issue: {str(e)}. Try uploading an image directly.")

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
