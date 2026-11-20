import axios from 'axios';
import { LabelAnalysisResult, SurveyStatsResponse, PresetProduct, UserProfile, ConditionValidationResult, IngredientItem, CartAuditResponse, HealthierAlternative, ProductComparisonResult, MultiProfileScanResult } from '@/types';

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
  productNameOrHash: string,
  activeProfile: UserProfile,
  baseProduct?: LabelAnalysisResult
): Promise<{
  personalized_verdict: string;
  adjusted_health_score: number;
  contraindications: string[];
  ingredient_breakdown: IngredientItem[];
}> => {
  const res = await apiClient.post('/api/evaluate-profile-safety', {
    product_name: productNameOrHash,
    product_hash: productNameOrHash,
    base_product: baseProduct,
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

export const smartScanMultiProfile = async (
  input: { query?: string; imageFile?: Blob | File },
  profiles: UserProfile[],
  pincode?: string
): Promise<MultiProfileScanResult> => {
  const formData = new FormData();
  if (input.imageFile) {
    formData.append('image', input.imageFile, 'scan.jpg');
  }
  if (input.query) {
    formData.append('query', input.query);
  }
  formData.append('pincode', pincode || '110001');
  formData.append('profiles', JSON.stringify(profiles.slice(0, 3)));

  const res = await apiClient.post<MultiProfileScanResult>('/api/smart-scan-multi-profile', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return res.data;
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

export const auditCart = async (
  input: {
    images?: (Blob | File)[];
    imageFile?: Blob | File;
    itemNames?: string;
    cartUrl?: string;
    pincode?: string;
  },
  userProfile: UserProfile
): Promise<CartAuditResponse> => {
  const formData = new FormData();
  if (input.images && input.images.length > 0) {
    input.images.forEach((img, idx) => {
      formData.append('images', img, `cart_capture_${idx}.jpg`);
    });
  } else if (input.imageFile) {
    formData.append('image', input.imageFile, 'cart_capture.jpg');
    formData.append('images', input.imageFile, 'cart_capture.jpg');
  }
  if (input.itemNames) {
    formData.append('item_names', input.itemNames);
  }
  if (input.cartUrl) {
    formData.append('cart_url', input.cartUrl);
  }
  formData.append('pincode', input.pincode || '110001');
  formData.append('user_profile', JSON.stringify(userProfile));

  const res = await apiClient.post<CartAuditResponse>('/api/audit-cart', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return res.data;
};

export const discoverAlternatives = async (
  productName: string,
  currentHealthScore: number,
  category: string = '',
  pincode: string = '110001',
  userProfile?: UserProfile
): Promise<HealthierAlternative[]> => {
  try {
    const res = await apiClient.post<HealthierAlternative[]>('/api/discover-alternatives', {
      product_name: productName,
      category,
      current_health_score: currentHealthScore,
      pincode,
      user_profile: userProfile,
    });
    return res.data;
  } catch (err) {
    console.warn('Failed to asynchronously discover alternatives:', err);
    return [];
  }
};

export const reverseGeocodePincode = async (lat: number, lon: number): Promise<string | null> => {
  try {
    const res = await apiClient.get<{ pincode: string | null; formatted_address?: string }>(`/api/reverse-geocode?lat=${lat}&lon=${lon}`);
    return res.data?.pincode || null;
  } catch (e) {
    console.warn("Backend reverse geocode request failed:", e);
    return null;
  }
};

export const compareProducts = async (
  productA: LabelAnalysisResult,
  productB: LabelAnalysisResult,
  userProfile: UserProfile,
  pincode?: string
): Promise<ProductComparisonResult> => {
  const res = await apiClient.post<ProductComparisonResult>('/api/compare-products', {
    product_a: productA,
    product_b: productB,
    user_profile: userProfile,
    pincode: pincode || '110001',
  });
  return res.data;
};

export const resetBackendCache = async (): Promise<void> => {
  try {
    await apiClient.post('/api/reset-cache');
  } catch (e) {
    console.warn('Backend cache reset failed:', e);
  }
};

