from typing import List, Literal, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from app.schemas.analysis import LabelAnalysisResult, IngredientItem
from app.schemas.user_profile import UserProfile

class ProfileAuditInsight(BaseModel):
    profile_id: str = Field(description="Unique ID of the evaluated profile")
    profile_name: str = Field(description="Display label of the profile e.g. Self, Dad, Kid")
    health_score: int = Field(ge=0, le=100, description="Personalized health score for this profile")
    personalized_verdict: Literal['SAFE FOR YOU', 'CAUTION', 'AVOID (VIOLATES PROFILE)'] = Field(description="Personalized safety verdict")
    personalized_summary: str = Field(description="Clinical explanation tailored to this profile's conditions")
    contraindications: List[str] = Field(default_factory=list, description="Specific medical or allergen conflicts")
    ingredient_warnings: List[IngredientItem] = Field(default_factory=list, description="Ingredients with tailored warning tags")
    allergy_trigger: Optional[str] = Field(default=None, description="Allergen causing score to be rated 0")
    base_score_without_allergy: Optional[int] = Field(default=None, description="Base nutritional score if not for allergy")

class MultiProfileScanResult(BaseModel):
    product_name: str = Field(description="Identified brand and product title")
    base_product: LabelAnalysisResult = Field(description="The underlying objective food audit (nutrition card, additives, alternatives)")
    profiles_audited: List[ProfileAuditInsight] = Field(description="Personalized insights for each requested profile (max 3)")
    household_verdict: Literal['SAFE FOR HOUSEHOLD', 'PARTIALLY SAFE (CAUTION)', 'UNSAFE FOR FAMILY MEMBERS'] = Field(description="Overarching family safety decision")
    household_summary: str = Field(description="Summary advising whether this item is safe for the household")
    comparison_matrix: List[Dict[str, Any]] = Field(default_factory=list, description="Side-by-side comparison matrix for UI rendering")

class MultiProfileScanRequest(BaseModel):
    product_name: Optional[str] = None
    profiles: List[UserProfile] = Field(description="List of household profiles to evaluate (max 3)")
    pincode: Optional[str] = "110001"

    @field_validator('profiles')
    def validate_max_profiles(cls, v):
        if len(v) > 3:
            raise ValueError("Simultaneous audits are limited to a maximum of 3 profiles.")
        if len(v) == 0:
            raise ValueError("At least one profile must be provided for evaluation.")
        return v
