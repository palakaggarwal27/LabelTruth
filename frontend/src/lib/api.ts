import axios from 'axios';
import { LabelAnalysisResult, SurveyStatsResponse, PresetProduct, UserProfile, ConditionValidationResult, IngredientItem } from '@/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
});

export const validateCondition = async (condition: string): Promise<ConditionValidationResult> => {
  const res = await apiClient.post<ConditionValidationResult>('/api/validate-condition', {
    condition,
  });
  return res.data;
};

export const fetchStats = async (): Promise<SurveyStatsResponse> => {
  const res = await apiClient.get<SurveyStatsResponse>('/api/stats');
  return res.data;
};

export const fetchPresets = async (): Promise<PresetProduct[]> => {
  const res = await apiClient.get<PresetProduct[]>('/api/presets');
  return res.data;
};

export const analyzeLabel = async (
  imageFile: Blob | File,
  userProfile: UserProfile
): Promise<LabelAnalysisResult> => {
  const formData = new FormData();
  // Provide both 'image' and 'file' field aliases for robust multipart handling
  formData.append('image', imageFile, 'label_capture.jpg');
  formData.append('file', imageFile, 'label_capture.jpg');
  formData.append('user_profile', JSON.stringify(userProfile));

  const res = await apiClient.post<LabelAnalysisResult>('/api/analyze-label', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return res.data;
};

export const evaluateProfileSafety = async (
  productHash: string,
  activeProfile: UserProfile
): Promise<{ personalized_verdict: string; contraindications: string[]; ingredient_breakdown: IngredientItem[] }> => {
  const res = await apiClient.post('/api/evaluate-profile-safety', {
    product_hash: productHash,
    active_profile: activeProfile,
  });
  return res.data;
};

export const smartScan = async (
  input: { query?: string; imageFile?: Blob | File; pincode?: string; demoMode?: boolean },
  userProfile: UserProfile
): Promise<LabelAnalysisResult> => {
  const formData = new FormData();
  if (input.imageFile) {
    formData.append('image', input.imageFile, 'label_capture.jpg');
    formData.append('file', input.imageFile, 'label_capture.jpg');
  }
  if (input.query) {
    formData.append('query', input.query);
  }
  formData.append('pincode', input.pincode || '110001');
  if (input.demoMode) {
    formData.append('demo_mode', 'true');
  }
  formData.append('user_profile', JSON.stringify(userProfile));

  try {
    const res = await apiClient.post<LabelAnalysisResult>('/api/smart-scan', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return res.data;
  } catch (err: unknown) {
    const errorObj = err as { response?: { status?: number } };
    // If backend is running an older deployed version where /api/smart-scan returns 404:
    if (errorObj.response?.status === 404) {
      if (input.imageFile) {
        // Fallback directly to the classic /api/analyze-label endpoint
        return await analyzeLabel(input.imageFile, userProfile);
      }
    }
    throw err;
  }
};

export const sendChatMessage = async (
  message: string,
  history: { role: string; content: string }[],
  userProfile?: UserProfile,
  productContext?: LabelAnalysisResult | null
): Promise<string> => {
  const res = await apiClient.post<{ reply: string }>('/api/chat', {
    message,
    history,
    user_profile: userProfile,
    product_context: productContext,
  });
  return res.data.reply;
};
