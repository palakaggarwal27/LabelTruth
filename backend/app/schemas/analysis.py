from typing import List, Literal, Optional
from pydantic import BaseModel, Field

class IngredientItem(BaseModel):
    ingredient: str = Field(description='Identified ingredient or additive name')
    purpose: str = Field(description='Functional purpose e.g., Colorant, Preservative, Bulking agent, Flour')
    concern_level: Literal['LOW', 'MEDIUM', 'HIGH'] = Field(description='Health risk or processing concern level')
    personalized_warning: str = Field(default='', description='Direct warning if this conflicts with user profile or medical condition')

class HealthierAlternative(BaseModel):
    name: str = Field(description='Recommended healthier brand or clean food alternative in India')
    product_name: Optional[str] = Field(default=None, description='Alternative product name alias')
    health_score: Optional[int] = Field(default=80, description='Audited health score (must be >= 70)')
    key_benefit: str = Field(description='Primary health advantage over current product')
    price_comparison: str = Field(description='Realistic price comparison context e.g., Comparable price or ~1.2x')
    personalized_fit: str = Field(description='Why this alternative fits user dietary and medical profile')
    store_url: Optional[str] = Field(default=None, description='Quick-commerce or brand store link')
    direct_pdp_url: Optional[str] = Field(default=None, description='Direct Product Detail Page URL on Blinkit or Zepto')
    pincode_available: bool = Field(default=True, description='Whether available at delivery pincode')
    reason: Optional[str] = Field(default=None, description='Clinical reason for recommendation')

class ProteinAudit(BaseModel):
    declared_protein_g: float = Field(default=0.0, description='Declared protein in grams per 100g or serving')
    usable_protein_g: float = Field(default=0.0, description='Usable bioavailable protein adjusted by PDCAAS score')
    pdcaas_score: float = Field(default=0.5, description='Protein Digestibility-Corrected Amino Acid Score (0.0 to 1.0)')
    primary_sources: List[str] = Field(default_factory=list, description='Primary protein source ingredients (e.g. Wheat Gluten, Whey, Soy)')
    protein_to_calorie_percent: float = Field(default=0.0, description='Percentage of total calories derived from protein')
    amino_spiking_risk: bool = Field(default=False, description='True if non-protein nitrogen (free Glycine, Taurine) suspected')

class ClaimVerification(BaseModel):
    claim: str = Field(description='Front-of-pack claim made by brand')
    status: Literal['VERIFIED', 'MISLEADING', 'DECEPTIVE'] = Field(description='Regulatory verification status')
    explanation: str = Field(description='Clinical or regulatory explanation exposing the reality')

class NutrientIntegrityMatrix(BaseModel):
    protein: ProteinAudit = Field(default_factory=ProteinAudit)
    fiber_type: str = Field(default='Whole Grain', description='Whole grain dietary fiber vs. synthetic isolate (polydextrose/inulin)')
    palm_oil_present: bool = Field(default=False, description='Whether palm oil is present despite zero-cholesterol or health claims')
    hidden_sugars_flagged: List[str] = Field(default_factory=list, description='Disguised sugars found e.g. maltodextrin, invert syrup, liquid glucose')
    sodium_and_preservatives_risk: str = Field(default='Low', description='Risk assessment for MSG/INS 627/631/INS 211')
    claims_matrix: List[ClaimVerification] = Field(default_factory=list, description='Verification of all front-of-pack claims')

class NutritionFactItem(BaseModel):
    nutrient: str = Field(description='Nutrient name e.g. Calories, Total Fat, Saturated Fat, Added Sugar, Sodium, Carbohydrates')
    amount_per_100g: str = Field(default='', description='Amount per 100g or per serving e.g. 450 kcal, 15g, 820mg')
    daily_value_percent: Optional[str] = Field(default=None, description='% Daily Value (% RDA) if present or estimated')
    clinical_evaluation: str = Field(default='', description='Forensic clinical analysis of this nutrient amount e.g. Exceeds WHO recommended daily free sugar limit in single serving')

class NutritionCardAnalysis(BaseModel):
    serving_size: str = Field(default='100g', description='Stated serving size')
    calories_kcal: float = Field(default=0.0, description='Energy in kcal per 100g')
    total_fat_g: float = Field(default=0.0, description='Total fat in grams')
    saturated_fat_g: float = Field(default=0.0, description='Saturated fat in grams')
    trans_fat_g: float = Field(default=0.0, description='Trans fat in grams')
    total_carbs_g: float = Field(default=0.0, description='Total carbohydrates in grams')
    added_sugars_g: float = Field(default=0.0, description='Added sugars in grams')
    sodium_mg: float = Field(default=0.0, description='Sodium in milligrams')
    breakdown: List[NutritionFactItem] = Field(default_factory=list, description='Detailed clinical breakdown of every line on the nutrition table')

class LabelAnalysisResult(BaseModel):
    product_name: str = Field(description='Identified brand and product title')
    health_score: int = Field(ge=0, le=100, description='Overall health score from 0 (ultra-processed/toxic) to 100 (wholesome/clean)')
    personalized_verdict: Literal['SAFE FOR YOU', 'CAUTION', 'AVOID (VIOLATES PROFILE)'] = Field(description='Personalized safety verdict')
    simple_summary: str = Field(description='Clear 2-3 sentence layperson summary of the reality of this food')
    deceptive_claims_flagged: List[str] = Field(default_factory=list, description='Front-of-pack claims that deceive or contradict back-of-pack realities')
    fssai_violations: List[str] = Field(default_factory=list, description='Violations or bypasses of FSSAI regulations e.g. descending weight rule, frozen dessert sold as ice cream, misleading Atta claims')
    ingredient_breakdown: List[IngredientItem] = Field(default_factory=list, description='Itemized breakdown of ingredients')
    nutrition_card: Optional[NutritionCardAnalysis] = Field(default=None, description='Detailed breakdown and clinical analysis of the nutritional table facts')
    healthier_alternative: HealthierAlternative = Field(description='Clean swap recommendation')
    clean_alternatives: List[HealthierAlternative] = Field(default_factory=list, description='2-3 clean whole-food Indian alternative products available on quick-commerce')
    nutrient_integrity: NutrientIntegrityMatrix = Field(default_factory=NutrientIntegrityMatrix, description='Protein bioavailability and full nutrient integrity matrix')
    is_food_label: bool = Field(default=True, description='False if image is not a food product or label')
    label_type: Literal['FRONT_OF_PACK', 'BACK_OF_PACK', 'FULL_PANEL', 'NOT_A_LABEL'] = Field(default='FULL_PANEL')
