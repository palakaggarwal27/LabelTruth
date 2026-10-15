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
}

export interface UserProfile {
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
}

export interface INSCardData {
  code: string;
  name: string;
  function: string;
  risk: string;
}

export interface SurveyStatsResponse {
  sample_size: number;
  location: string;
  key_stats: StatCardData[];
  fssai_regulations: FSSAICardData[];
  harmful_ins_codes: INSCardData[];
}

export interface ScannedHistoryItem {
  id: string;
  timestamp: number;
  image_preview?: string;
  result: LabelAnalysisResult;
}

