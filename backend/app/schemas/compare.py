from typing import List, Literal, Optional
from pydantic import BaseModel, Field
from app.schemas.analysis import LabelAnalysisResult, HealthierAlternative
from app.schemas.user_profile import UserProfile

class DimensionComparison(BaseModel):
    category: str = Field(description="Category of comparison e.g. Nutritional Density, Ingredient Purity, Clinical Profile Fit")
    winner: Literal['PRODUCT_A', 'PRODUCT_B', 'TIE', 'NEITHER'] = Field(description="Winning product for this dimension")
    explanation: str = Field(description="Clinical or nutritional rationale for the dimension verdict")

class ProductComparisonResult(BaseModel):
    winner: Literal['PRODUCT_A', 'PRODUCT_B', 'TIE', 'NEITHER_RECOMMENDED'] = Field(description="Overall winner or neither if both harmful")
    verdict_title: str = Field(description="Concise, impactful verdict headline")
    verdict_summary: str = Field(description="2-3 sentence clinical summary comparing both products head-to-head")
    score_diff: int = Field(default=0, description="Absolute difference in audited health score points")
    personalized_impact: str = Field(description="Specific clinical impact and trade-offs tailored to the user's active diseases, allergies, and goals")
    key_tradeoffs: List[str] = Field(default_factory=list, description="Direct bulleted trade-offs between Product A and Product B")
    dimension_breakdown: List[DimensionComparison] = Field(default_factory=list, description="Dimension-by-dimension forensic assessment")
    superior_alternative: Optional[HealthierAlternative] = Field(default=None, description="A 3rd product in the same food category that beats both Product A and Product B")

class CompareProductsRequest(BaseModel):
    product_a: LabelAnalysisResult
    product_b: LabelAnalysisResult
    user_profile: UserProfile
    pincode: Optional[str] = "110001"
