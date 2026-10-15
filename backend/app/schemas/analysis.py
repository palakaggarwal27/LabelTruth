from typing import List, Literal, Optional
from pydantic import BaseModel, Field

class IngredientItem(BaseModel):
    ingredient: str = Field(description='Identified ingredient or additive name')
    purpose: str = Field(description='Functional purpose e.g., Colorant, Preservative, Bulking agent, Flour')
    concern_level: Literal['LOW', 'MEDIUM', 'HIGH'] = Field(description='Health risk or processing concern level')
    personalized_warning: str = Field(description='Direct warning if this conflicts with user profile or medical condition')

class HealthierAlternative(BaseModel):
    name: str = Field(description='Recommended healthier brand or clean food alternative in India')
    key_benefit: str = Field(description='Primary health advantage over current product')
    price_comparison: str = Field(description='Realistic price comparison context e.g., Comparable price or ~1.2x')
    personalized_fit: str = Field(description='Why this alternative fits user dietary and medical profile')

class LabelAnalysisResult(BaseModel):
    product_name: str = Field(description='Identified brand and product title')
    health_score: int = Field(ge=0, le=100, description='Overall health score from 0 (ultra-processed/toxic) to 100 (wholesome/clean)')
    personalized_verdict: Literal['SAFE FOR YOU', 'CAUTION', 'AVOID (VIOLATES PROFILE)'] = Field(description='Personalized safety verdict')
    simple_summary: str = Field(description='Clear 2-3 sentence layperson summary of the reality of this food')
    deceptive_claims_flagged: List[str] = Field(default_factory=list, description='Front-of-pack claims that deceive or contradict back-of-pack realities')
    fssai_violations: List[str] = Field(default_factory=list, description='Violations or bypasses of FSSAI regulations e.g. descending weight rule, frozen dessert sold as ice cream, misleading Atta claims')
    ingredient_breakdown: List[IngredientItem] = Field(default_factory=list, description='Itemized breakdown of ingredients')
    healthier_alternative: HealthierAlternative = Field(description='Clean swap recommendation')
