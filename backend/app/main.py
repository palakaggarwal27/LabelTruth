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
        
        result = await gemini_vision_service.analyze_label_image(image_bytes, profile)

        # 1. Image Validation: Reject non-food images
        if not getattr(result, "is_food_label", True) or getattr(result, "label_type", "") == "NOT_A_LABEL":
            raise HTTPException(
                status_code=400,
                detail="PRODUCT_NOT_VISIBLE: No food packaging or label detected in the image. Please upload a clear photo of the product label."
            )

        # 2. Partial Photo Logic (Scenario A: Only Front-of-Pack): Enrich with TinyFish
        if getattr(result, "label_type", "") == "FRONT_OF_PACK" and result.product_name:
            try:
                from app.services.tinyfish_service import tinyfish_service
                bop_text = await tinyfish_service.search_and_fetch_bop(result.product_name)
                if bop_text:
                    result = await gemini_vision_service.analyze_label_image(image_bytes, profile, bop_supplement_text=bop_text)
            except Exception as tf_err:
                logger.warning(f"TinyFish BOP enrichment fallback failed: {tf_err}")

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
            if image_bytes:
                return await analyze_label(image=image, user_profile=user_profile)

        # Scenario 2: Text / Product name / Shared URL
        if query and query.strip():
            from app.services.tinyfish_service import tinyfish_service
            online_content = ""
            if query.startswith("http://") or query.startswith("https://"):
                data = await tinyfish_service.fetch_product_details(query.strip())
                if data:
                    online_content = str(data)
            else:
                online_content = await tinyfish_service.search_and_fetch_bop(query.strip()) or ""

            result = await gemini_vision_service.analyze_text_query(query.strip(), profile, online_content)
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
