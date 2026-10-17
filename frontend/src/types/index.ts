export type ConcernLevel = 'LOW' | 'MEDIUM' | 'HIGH';
export type PersonalizedVerdict = 'SAFE FOR YOU' | 'CAUTION' | 'AVOID (VIOLATES PROFILE)';

export interface IngredientItem {
  ingredient: string;
  purpose: string;
  concern_level: ConcernLevel;
  personalized_warning: string;
}

export interface HealthierAlternative {
  name: string;
  key_benefit: string;
  price_comparison: string;
  personalized_fit: string;
  store_url?: string;
}

export interface ProteinAudit {
  declared_protein_g: number;
  usable_protein_g: number;
  pdcaas_score: number;
  primary_sources: string[];
  protein_to_calorie_percent: number;
  amino_spiking_risk: boolean;
}

export interface ClaimVerification {
  claim: string;
  status: 'VERIFIED' | 'MISLEADING' | 'DECEPTIVE';
  explanation: string;
}

export interface NutrientIntegrityMatrix {
  protein?: ProteinAudit;
  fiber_type?: string;
  palm_oil_present?: boolean;
  hidden_sugars_flagged?: string[];
  sodium_and_preservatives_risk?: string;
  claims_matrix?: ClaimVerification[];
}

export interface LabelAnalysisResult {
  product_name: string;
  health_score: number;
  personalized_verdict: PersonalizedVerdict;
  simple_summary: string;
  deceptive_claims_flagged: string[];
  fssai_violations: string[];
  ingredient_breakdown: IngredientItem[];
  healthier_alternative: HealthierAlternative;
  clean_alternatives?: HealthierAlternative[];
  nutrient_integrity?: NutrientIntegrityMatrix;
  is_food_label?: boolean;
  label_type?: 'FRONT_OF_PACK' | 'BACK_OF_PACK' | 'FULL_PANEL' | 'NOT_A_LABEL';
}

export interface UserProfile {
  id?: string;
  name?: string; // e.g. "Self", "Dad", "Kid"
  dietary_preferences: string[];
  medical_conditions: string[];
  allergies: string[];
  custom_avoid_list: string[];
}

export interface ConditionValidationResult {
  is_valid: boolean;
  standardized_name: string;
  reason: string;
}

export interface PresetProduct {
  id: string;
  title: string;
  subtitle: string;
  description: string;
  sample_result: LabelAnalysisResult;
}

export interface StatCardData {
  stat: string;
  title: string;
  description: string;
  source: string;
}

export interface FSSAICardData {
  regulation: string;
  name: string;
  description: string;
  impact?: string;
  loophole_exposed?: string;
}

export interface INSCardData {
  code: string;
  name: string;
  function: string;
  risk: string;
  disease_contraindications?: string[];
}

export interface SurveyStatsResponse {
  sample_size: number;
  national_sample_size?: number;
  location: string;
  key_stats: StatCardData[];
  national_stats?: StatCardData[];
  fssai_regulations: FSSAICardData[];
  harmful_ins_codes: INSCardData[];
}

export interface ScannedHistoryItem {
  id: string;
  timestamp: number;
  image_preview?: string;
  result: LabelAnalysisResult;
}
