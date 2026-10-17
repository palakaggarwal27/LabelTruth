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

AUDIT_CACHE: Dict[str, LabelAnalysisResult] = {}

def compute_audit_hash(content: bytes, profile_str: str) -> str:
    h = hashlib.sha256()
    h.update(content)
    h.update(profile_str.encode('utf-8'))
    return h.hexdigest()

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
    user_profile: str = Form(...)
):
    """Smart hybrid input: handles image, product text name, or online quick-commerce URL"""
    try:
        profile_dict = json.loads(user_profile)
        profile = UserProfile(**profile_dict)
    except Exception:
        profile = UserProfile()

    try:
        # Scenario 1: Image provided
        if image:
            image_bytes = await image.read()
            if image_bytes and len(image_bytes) > 0:
                await image.seek(0)
                return await analyze_label(image=image, user_profile=user_profile)

        # Scenario 2: Text / Product name / Shared URL
        if query and query.strip():
            clean_query = query.strip()
            query_cache_key = compute_audit_hash(clean_query.lower().encode('utf-8'), user_profile)
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
