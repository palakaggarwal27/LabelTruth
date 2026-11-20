"use client";

import { CompareProducts } from '@/components/CompareProducts';
import { CartAuditView } from '@/components/CartAudit/CartAuditView';

import React, { useState } from 'react';
import { UploadZone } from '@/components/Scanner/UploadZone';
import { CameraCapture } from '@/components/Scanner/CameraCapture';
import { ScoreCard } from '@/components/Results/ScoreCard';
import { RedFlagsCard } from '@/components/Results/RedFlagsCard';
import { IngredientAccordion } from '@/components/Results/IngredientAccordion';
import { AlternativeCard } from '@/components/Results/AlternativeCard';
import { FloatingChatbot } from '@/components/FloatingChatbot';
import { useHealthProfile } from '@/context/HealthProfileContext';
import { smartScan, discoverAlternatives, evaluateProfileSafety, smartScanMultiProfile, resetBackendCache } from '@/lib/api';
import { LabelAnalysisResult, ScannedHistoryItem, UserProfile, MultiProfileScanResult } from '@/types';
import { AlertCircle, RefreshCw, ScanLine, History, Trash2, Scale, ShoppingCart, Users, ShieldAlert, HeartPulse, CheckCircle2, ChevronRight } from 'lucide-react';
import { ScanHistoryList } from '@/components/Scanner/ScanHistoryList';
import { HealthProfileManager } from '@/components/HealthProfileManager';
import { NutrientMatrix } from '@/components/Results/NutrientMatrix';
import { FALLBACK_PRESET_PRODUCTS } from '@/data/presets';

import { DemoToggle } from '@/components/DemoToggle';
import { LOCAL_DEMO_TIER_PRODUCTS } from '@/data/demoTiers';

const SCAN_HISTORY_KEY = 'labeltruth_scan_history_v1';

export default function ScanPage() {
  const { profile, activeProfile } = useHealthProfile();
  const currentProfile = activeProfile || profile;
  const [activeTab, setActiveTab] = useState<'scan' | 'compare' | 'cart' | 'history'>('scan');
  const [isCameraOpen, setIsCameraOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [isLoadingAlternatives, setIsLoadingAlternatives] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<LabelAnalysisResult | null>(null);
  const [multiProfileResult, setMultiProfileResult] = useState<MultiProfileScanResult | null>(null);
  const [activeProfileTab, setActiveProfileTab] = useState<string>('household');
  const [history, setHistory] = useState<ScannedHistoryItem[]>([]);
  const [demoMode, setDemoMode] = useState(false);

  // Instant Profile Re-evaluation when family profile is switched
  React.useEffect(() => {
    if (result && currentProfile && !multiProfileResult) {
      // Re-evaluate active result against active member in <50ms without re-running OCR
      evaluateProfileSafety(result.product_name, currentProfile, result)
        .then((evalData) => {
          if (evalData && evalData.personalized_verdict) {
            setResult((prev) => prev ? {
              ...prev,
              health_score: evalData.adjusted_health_score ?? prev.health_score,
              personalized_verdict: evalData.personalized_verdict as import('@/types').PersonalizedVerdict,
              ingredient_breakdown: evalData.ingredient_breakdown || prev.ingredient_breakdown,
              allergy_trigger: evalData.allergy_trigger ?? undefined,
              base_score_without_allergy: evalData.base_score_without_allergy ?? undefined
            } : null);
          }
        })
        .catch((e) => console.warn('Instant profile evaluation notice:', e));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    currentProfile.id, 
    currentProfile.name, 
    JSON.stringify(currentProfile.medical_conditions), 
    JSON.stringify(currentProfile.allergies), 
    JSON.stringify(currentProfile.custom_avoid_list),
    JSON.stringify(currentProfile.dietary_preferences)
  ]);

  // Load scan history and check for shared URL / query search params from Web Share Target
  React.useEffect(() => {
    try {
      const saved = localStorage.getItem(SCAN_HISTORY_KEY);
      if (saved) {
        setHistory(JSON.parse(saved));
      }
      localStorage.setItem('labeltruth_demo_presets', JSON.stringify(LOCAL_DEMO_TIER_PRODUCTS));
    } catch (e) {
      console.warn('Failed to load scan history or save presets:', e);
    }

    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search);
      const initialQuery = params.get('query');
      if (initialQuery) {
        handleProcessQuery(initialQuery);
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const saveToHistory = (res: LabelAnalysisResult, imageBlob?: Blob | File) => {
    const createItem = (previewUrl?: string) => {
      const newItem: ScannedHistoryItem = {
        id: 'scan_' + Date.now() + '_' + Math.random().toString(36).substr(2, 5),
        timestamp: Date.now(),
        image_preview: previewUrl,
        result: res,
      };
      setHistory((prev) => {
        // Prevent duplicate consecutive or repeated additions of the same product
        const filtered = prev.filter(
          (item) => item.result.product_name.trim().toLowerCase() !== res.product_name.trim().toLowerCase()
        );
        const updated = [newItem, ...filtered].slice(0, 30); // keep recent 30 scans
        try {
          localStorage.setItem(SCAN_HISTORY_KEY, JSON.stringify(updated));
        } catch (e) {
          console.warn('Failed to persist scan history:', e);
        }
        return updated;
      });
    };

    if (imageBlob) {
      const reader = new FileReader();
      reader.onload = () => {
        createItem(reader.result as string);
      };
      reader.onerror = () => createItem(undefined);
      reader.readAsDataURL(imageBlob);
    } else {
      createItem(undefined);
    }
  };

  const clearHistory = () => {
    setHistory([]);
    resetBackendCache();
    try {
      localStorage.removeItem(SCAN_HISTORY_KEY);
    } catch (e) {
      console.warn('Failed to clear scan history:', e);
    }
  };

  const triggerAlternativeDiscovery = (productData: LabelAnalysisResult, pin?: string) => {
    if (productData.health_score < 90) {
      setIsLoadingAlternatives(true);
      discoverAlternatives(
        productData.product_name,
        productData.health_score,
        productData.category || '',
        pin || '110001',
        currentProfile
      )
        .then((alts) => {
          if (alts && alts.length > 0) {
            setResult((prev) => {
              if (!prev) return null;
              return {
                ...prev,
                clean_alternatives: alts,
                healthier_alternative: alts[0],
              };
            });
          }
        })
        .catch((e) => console.warn('Async alternative discovery error:', e))
        .finally(() => {
          setIsLoadingAlternatives(false);
        });
    }
  };

  const handleProcessImage = async (fileOrBlob: File | Blob, selectedProfiles?: UserProfile[]) => {
    setLoading(true);
    setError(null);
    try {
      if (selectedProfiles && selectedProfiles.length > 1) {
        const data = await smartScanMultiProfile({ imageFile: fileOrBlob }, selectedProfiles);
        setMultiProfileResult(data);
        setResult(data.base_product);
        setActiveProfileTab('household');
        saveToHistory(data.base_product, fileOrBlob);
        triggerAlternativeDiscovery(data.base_product);
      } else {
        setMultiProfileResult(null);
        const data = await smartScan({ imageFile: fileOrBlob }, currentProfile);
        setResult(data);
        saveToHistory(data, fileOrBlob);
        triggerAlternativeDiscovery(data);
      }
    } catch (err: unknown) {
      const errorObj = err as { response?: { data?: { detail?: string } } };
      console.error('Analysis failed:', err);
      setError(
        errorObj.response?.data?.detail ||
          'Failed to audit label image. Ensure the backend is reachable or test using a preset.'
      );
    } finally {
      setLoading(false);
      setIsCameraOpen(false);
    }
  };

  const handleProcessQuery = async (queryText: string, pincode?: string, selectedProfiles?: UserProfile[]) => {
    setLoading(true);
    setError(null);
    const normalized = queryText.trim().toLowerCase();
    const isUrl = normalized.startsWith('http://') || normalized.startsWith('https://');

    // 1. Multi-profile simultaneous scan if >1 profile selected
    if (selectedProfiles && selectedProfiles.length > 1) {
      try {
        const data = await smartScanMultiProfile({ query: queryText }, selectedProfiles, pincode);
        setMultiProfileResult(data);
        setResult(data.base_product);
        setActiveProfileTab('household');
        saveToHistory(data.base_product);
        triggerAlternativeDiscovery(data.base_product, pincode);
      } catch (err: unknown) {
        const errorObj = err as { response?: { data?: { detail?: string } } };
        setError(
          errorObj.response?.data?.detail ||
            `Multi-profile audit failed for "${queryText}". Try again or upload an image directly.`
        );
      } finally {
        setLoading(false);
      }
      return;
    }

    setMultiProfileResult(null);

    // 2. Check offline demo suite if demo mode is enabled (never for live URLs)
    if (!isUrl && demoMode) {
      let matchedKey: string | null = null;

      // Exact tier key match first
      if (LOCAL_DEMO_TIER_PRODUCTS[queryText as keyof typeof LOCAL_DEMO_TIER_PRODUCTS]) {
        matchedKey = queryText;
      } else if (normalized.includes('lays') || normalized.includes('lay')) {
        matchedKey = 'very_low';
      } else if (normalized.includes('english oven') || normalized.includes('white bread')) {
        matchedKey = 'low';
      } else if (normalized.includes('dlecta') || normalized.includes("d'lecta")) {
        matchedKey = 'moderate';
      } else if (normalized.includes('epigamia')) {
        matchedKey = 'high';
      } else if (normalized.includes('rolled oats') || normalized.includes('true elements')) {
        matchedKey = 'very_high';
      }

      if (matchedKey && LOCAL_DEMO_TIER_PRODUCTS[matchedKey as keyof typeof LOCAL_DEMO_TIER_PRODUCTS]) {
        const demoItem = LOCAL_DEMO_TIER_PRODUCTS[matchedKey as keyof typeof LOCAL_DEMO_TIER_PRODUCTS];
        setResult(demoItem);
        saveToHistory(demoItem);
        setLoading(false);
        return;
      }
    }

    // 3. Check client-side history cache only on exact product name match if NOT older than 30 days
    const THIRTY_DAYS_MS = 30 * 24 * 60 * 60 * 1000;
    const cachedItem = history.find(
      (h) => h.result.product_name.trim().toLowerCase() === normalized
    );
    if (cachedItem && !isUrl) {
      const scanTime = Number(cachedItem.timestamp || 0);
      const isExpired = isNaN(scanTime) || scanTime <= 0 || (Date.now() - scanTime > THIRTY_DAYS_MS);
      if (!isExpired) {
        setResult(cachedItem.result);
        setLoading(false);
        return;
      }
    }

    try {
      const data = await smartScan({ query: queryText, pincode: pincode || '110001', demoMode: isUrl ? false : demoMode }, currentProfile);
      setResult(data);
      saveToHistory(data);
      triggerAlternativeDiscovery(data, pincode);
    } catch (err: unknown) {
      console.warn('Backend query error, checking local preset catalog:', err);
      // Check if user queried one of our exact demo products by exact name (never for URLs)
      if (!isUrl) {
        const matched = FALLBACK_PRESET_PRODUCTS.find((p) => {
          const pTitle = p.title.toLowerCase();
          const pProd = p.sample_result.product_name.toLowerCase();
          return pTitle === normalized || pProd === normalized;
        });

        if (matched) {
          setResult(matched.sample_result);
          saveToHistory(matched.sample_result);
          return;
        }
      }

      const errorObj = err as { response?: { data?: { detail?: string } } };
      setError(
        errorObj.response?.data?.detail ||
          `No live packaging data found online for "${queryText}". Try including the brand name (e.g., "Cadbury Bournvita" or "Nestle Maggi") or upload a packaging photo directly.`
      );
    } finally {
      setLoading(false);
    }
  };

  const handleSelectHistoryItem = (item: ScannedHistoryItem) => {
    setResult(item.result);
    setMultiProfileResult(null);
    setActiveProfileTab('household');
    setActiveTab('scan');
  };

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8 sm:py-12">
      {/* Header */}
      <div className="mb-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <span className="text-xs font-mono uppercase tracking-wider text-zinc-500">
            Forensic Dual-Input Scanner
          </span>
          <h1 className="text-2xl sm:text-3xl font-semibold text-zinc-900 tracking-tight mt-0.5">
            Audit Packaging Ingredients
          </h1>
          <p className="text-xs text-zinc-500 mt-1 font-light">
            Capture live back-of-pack or upload quick-commerce screenshot (Blinkit, Zepto, Amazon).
          </p>
        </div>
      </div>

      {/* Active Household Profile Switcher */}
      <div className="mb-4">
        <HealthProfileManager activeProductName={result ? result.product_name : null} />
      </div>

      {/* Offline Demo Mode Sandbox Suite */}
      <div className="mb-6">
        <DemoToggle
          demoMode={demoMode}
          onToggle={(val) => setDemoMode(val)}
          onSelectTier={(tier) => {
            setDemoMode(true);
            const demoItem = LOCAL_DEMO_TIER_PRODUCTS[tier as keyof typeof LOCAL_DEMO_TIER_PRODUCTS];
            if (demoItem) {
              setResult(demoItem);
              saveToHistory(demoItem);
              setError(null);
            } else {
              handleProcessQuery(tier);
            }
          }}
        />
      </div>

      {/* Tab Switcher */}
      <div className="flex items-center gap-2 mb-6 border-b border-zinc-200">
        <button
          onClick={() => setActiveTab('scan')}
          className={`pb-3 px-3 text-xs font-semibold flex items-center gap-2 border-b-2 transition-all ${
            activeTab === 'scan'
              ? 'border-zinc-900 text-zinc-900'
              : 'border-transparent text-zinc-500 hover:text-zinc-800'
          }`}
        >
          <ScanLine className="w-4 h-4" />
          <span>Scanner & Audit</span>
        </button>

        <button
          onClick={() => setActiveTab('compare')}
          className={`pb-3 px-3 text-xs font-semibold flex items-center gap-2 border-b-2 transition-all ${
            activeTab === 'compare'
              ? 'border-zinc-900 text-zinc-900'
              : 'border-transparent text-zinc-500 hover:text-zinc-800'
          }`}
        >
          <Scale className="w-4 h-4" />
          <span>Compare Products</span>
        </button>

        <button
          onClick={() => setActiveTab('cart')}
          className={`pb-3 px-3 text-xs font-semibold flex items-center gap-2 border-b-2 transition-all ${
            activeTab === 'cart'
              ? 'border-zinc-900 text-zinc-900'
              : 'border-transparent text-zinc-500 hover:text-zinc-800'
          }`}
        >
          <ShoppingCart className="w-4 h-4" />
          <span>Cart Audit (Zepto / Blinkit)</span>
        </button>

        <button
          onClick={() => setActiveTab('history')}
          className={`pb-3 px-3 text-xs font-semibold flex items-center gap-2 border-b-2 transition-all ${
            activeTab === 'history'
              ? 'border-zinc-900 text-zinc-900'
              : 'border-transparent text-zinc-500 hover:text-zinc-800'
          }`}
        >
          <History className="w-4 h-4" />
          <span>Previously Scanned Products</span>
          {history.length > 0 && (
            <span className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-zinc-100 text-zinc-700">
              {history.length}
            </span>
          )}
        </button>

        {history.length > 0 && (
          <button
            onClick={() => {
              if (window.confirm("Are you sure you want to reset and clear all previous scan history?")) {
                clearHistory();
                setResult(null);
              }
            }}
            className="ml-auto pb-2 text-xs text-zinc-500 hover:text-rose-600 flex items-center gap-1.5 px-2.5 py-1 rounded border border-zinc-200 hover:border-rose-200 transition-colors"
            title="Reset and clear all saved scans"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span>Reset Scans ({history.length})</span>
          </button>
        )}
      </div>

      {activeTab === 'compare' ? (
        <CompareProducts />
      ) : activeTab === 'cart' ? (
        <CartAuditView />
      ) : activeTab === 'history' ? (
        <ScanHistoryList
          history={history}
          onSelect={handleSelectHistoryItem}
          onClear={clearHistory}
        />
      ) : !result ? (
        <div className="bg-white border border-zinc-200 rounded-md p-6 sm:p-8">
          {isCameraOpen ? (
            <CameraCapture
              onCapture={handleProcessImage}
              onCancel={() => setIsCameraOpen(false)}
            />
          ) : (
            <UploadZone
              onFileSelect={handleProcessImage}
              onOpenLiveCamera={() => setIsCameraOpen(true)}
              onTextSubmit={handleProcessQuery}
              loading={loading}
            />
          )}

          {loading && (
            <div className="mt-6 p-6 border border-zinc-200 bg-zinc-50/80 rounded-md text-center flex flex-col items-center justify-center gap-2.5 shadow-sm">
              <div className="flex items-center gap-2 text-xs font-semibold text-zinc-900">
                <RefreshCw className="w-4 h-4 animate-spin text-emerald-600" />
                <span>Forensic Nutritional Audit in Progress</span>
              </div>
              <p className="text-[11px] font-mono text-zinc-600">
                Auditing label ingredients against FSSAI 2020 standards &amp; ICMR-NIN thresholds...
              </p>
              <div className="w-full max-w-sm h-1.5 bg-zinc-200 rounded-full overflow-hidden mt-1">
                <div className="w-full h-full animate-shimmer-bar rounded-full" />
              </div>
            </div>
          )}

          {error && (
            <div className="mt-6 p-4 border border-rose-200 bg-rose-50 rounded-md text-xs text-rose-800 flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
              <span>{error}</span>
            </div>
          )}

        </div>
      ) : (() => {
        const activeInsight = multiProfileResult && activeProfileTab !== 'household'
          ? multiProfileResult.profiles_audited.find(
              (p) => p.profile_id === activeProfileTab || p.profile_name === activeProfileTab
            )
          : null;

        return (
          <div className="space-y-6 animate-fade-in-up">
            {/* Action Bar */}
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono uppercase tracking-wider text-zinc-500">
                Audit Complete
              </span>
              <button
                onClick={() => {
                  setResult(null);
                  setMultiProfileResult(null);
                  setActiveProfileTab('household');
                }}
                className="px-3.5 py-1.5 bg-zinc-900 hover:bg-zinc-800 text-white rounded-md text-xs font-semibold flex items-center gap-1.5"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                Scan Another Label
              </button>
            </div>

            {/* Household Multi-Profile Tab Switcher */}
            {multiProfileResult && (
              <div className="bg-zinc-100 p-1.5 rounded-lg border border-zinc-200 flex flex-wrap items-center gap-1.5">
                <button
                  onClick={() => setActiveProfileTab('household')}
                  className={`px-3 py-1.5 rounded-md text-xs font-semibold flex items-center gap-1.5 transition-all ${
                    activeProfileTab === 'household'
                      ? 'bg-white text-zinc-900 shadow-sm border border-zinc-200'
                      : 'text-zinc-600 hover:text-zinc-900 hover:bg-zinc-200/60'
                  }`}
                >
                  <Users className="w-3.5 h-3.5" />
                  <span>Family Overview</span>
                  <span className={`text-[10px] px-1.5 py-0.5 rounded font-mono font-bold ${
                    multiProfileResult.household_verdict === 'SAFE FOR HOUSEHOLD'
                      ? 'bg-emerald-100 text-emerald-800'
                      : multiProfileResult.household_verdict === 'PARTIALLY SAFE (CAUTION)'
                      ? 'bg-amber-100 text-amber-800'
                      : 'bg-rose-100 text-rose-800'
                  }`}>
                    {multiProfileResult.household_verdict === 'SAFE FOR HOUSEHOLD' ? 'SAFE' : multiProfileResult.household_verdict === 'PARTIALLY SAFE (CAUTION)' ? 'CAUTION' : 'UNSAFE'}
                  </span>
                </button>

                {multiProfileResult.profiles_audited.map((insight) => (
                  <button
                    key={insight.profile_id}
                    onClick={() => setActiveProfileTab(insight.profile_id)}
                    className={`px-3 py-1.5 rounded-md text-xs font-semibold flex items-center gap-2 transition-all ${
                      activeProfileTab === insight.profile_id
                        ? 'bg-white text-zinc-900 shadow-sm border border-zinc-200'
                        : 'text-zinc-600 hover:text-zinc-900 hover:bg-zinc-200/60'
                    }`}
                  >
                    <span className={`w-2 h-2 rounded-full ${
                      insight.health_score >= 70 ? 'bg-emerald-500' : insight.health_score >= 40 ? 'bg-amber-500' : 'bg-rose-500'
                    }`} />
                    <span>{insight.profile_name}</span>
                    <span className="font-mono text-[11px] font-bold text-zinc-700 bg-zinc-200/80 px-1.5 py-0.5 rounded">
                      {insight.health_score}
                    </span>
                  </button>
                ))}
              </div>
            )}

            {/* Household Decision Matrix Overview */}
            {multiProfileResult && activeProfileTab === 'household' && (
              <div className="bg-white border border-zinc-200 rounded-lg p-5 sm:p-6 shadow-sm space-y-5">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-zinc-100 pb-4">
                  <div>
                    <span className="text-[10px] font-mono uppercase tracking-wider text-zinc-500">
                      Simultaneous Household Evaluation ({multiProfileResult.profiles_audited.length} Profiles)
                    </span>
                    <h3 className="text-base sm:text-lg font-semibold text-zinc-900 mt-0.5">
                      Family Purchase Decision Matrix
                    </h3>
                  </div>
                  <div>
                    <span className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-bold border ${
                      multiProfileResult.household_verdict === 'SAFE FOR HOUSEHOLD'
                        ? 'bg-emerald-50 text-emerald-800 border-emerald-300'
                        : multiProfileResult.household_verdict === 'PARTIALLY SAFE (CAUTION)'
                        ? 'bg-amber-50 text-amber-800 border-amber-300'
                        : 'bg-rose-50 text-rose-800 border-rose-300'
                    }`}>
                      {multiProfileResult.household_verdict === 'SAFE FOR HOUSEHOLD' ? (
                        <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                      ) : (
                        <ShieldAlert className="w-4 h-4 text-rose-600" />
                      )}
                      {multiProfileResult.household_verdict}
                    </span>
                  </div>
                </div>

                <div className="bg-zinc-50 border border-zinc-200 rounded-md p-3.5 text-xs text-zinc-700 leading-relaxed">
                  <span className="font-semibold text-zinc-900">Household Summary: </span>
                  {multiProfileResult.household_summary}
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
                  {multiProfileResult.comparison_matrix.map((item, idx) => {
                    const matchingInsight = multiProfileResult.profiles_audited.find(
                      (p) => p.profile_name.toLowerCase() === item.profile_name.toLowerCase()
                    );
                    return (
                      <div
                        key={idx}
                        className="border border-zinc-200 rounded-md p-4 bg-white flex flex-col justify-between hover:border-zinc-400 transition-colors"
                      >
                        <div>
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-xs font-bold text-zinc-900">{item.profile_name}</span>
                            <span className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold ${
                              item.health_score >= 70
                                ? 'bg-emerald-100 text-emerald-800'
                                : item.health_score >= 40
                                ? 'bg-amber-100 text-amber-800'
                                : 'bg-rose-100 text-rose-800'
                            }`}>
                              Score: {item.health_score}/100
                            </span>
                          </div>
                          {matchingInsight?.allergy_trigger && (
                            <div className="mb-2 px-2 py-1 bg-rose-50 border border-rose-200 rounded text-[10px] text-rose-700 font-mono">
                              ⚠️ Allergen: <strong>{matchingInsight.allergy_trigger}</strong> (Rated 0/100)
                              {matchingInsight.base_score_without_allergy !== undefined && (
                                <span className="block text-[9px] text-zinc-500 font-sans">
                                  Base nutritional score: {matchingInsight.base_score_without_allergy}/100
                                </span>
                              )}
                            </div>
                          )}
                          <div className="text-[11px] font-semibold text-zinc-600 mb-2">
                            Verdict: <span className="font-mono text-zinc-900">{item.personalized_verdict}</span>
                          </div>
                          <p className="text-xs text-zinc-600 leading-normal line-clamp-3">
                            {item.key_issue}
                          </p>
                        </div>

                        {matchingInsight && (
                          <button
                            onClick={() => setActiveProfileTab(matchingInsight.profile_id)}
                            className="mt-4 pt-2 border-t border-zinc-100 text-[11px] font-semibold text-zinc-900 hover:text-emerald-700 flex items-center justify-between w-full"
                          >
                            <span>View {item.profile_name}&apos;s Audit</span>
                            <ChevronRight className="w-3.5 h-3.5" />
                          </button>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Individual Tailored Profile Notice */}
            {activeInsight && (
              <div className="bg-zinc-900 text-white rounded-md px-4 py-3 text-xs flex flex-col sm:flex-row sm:items-center justify-between gap-2 shadow-sm">
                <div className="flex items-center gap-2">
                  <HeartPulse className="w-4 h-4 text-emerald-400 shrink-0" />
                  <span>
                    Showing tailored clinical evaluation for <strong className="text-white">{activeInsight.profile_name}</strong>
                  </span>
                </div>
                {activeInsight.contraindications && activeInsight.contraindications.length > 0 && (
                  <span className="text-[11px] bg-rose-950/80 text-rose-200 border border-rose-800 px-2 py-0.5 rounded font-mono">
                    {activeInsight.contraindications.length} Contraindication(s) Flagged
                  </span>
                )}
              </div>
            )}

            {/* Results components */}
            <ScoreCard
              productName={result.product_name}
              healthScore={
                activeInsight
                  ? activeInsight.health_score
                  : multiProfileResult
                  ? (result.base_health_score ?? result.health_score)
                  : result.health_score
              }
              verdict={
                activeInsight
                  ? activeInsight.personalized_verdict
                  : multiProfileResult
                  ? (multiProfileResult.household_verdict === 'SAFE FOR HOUSEHOLD'
                      ? 'SAFE FOR YOU'
                      : multiProfileResult.household_verdict === 'PARTIALLY SAFE (CAUTION)'
                      ? 'CAUTION'
                      : 'AVOID (VIOLATES PROFILE)')
                  : result.personalized_verdict
              }
              summary={
                activeInsight
                  ? activeInsight.personalized_summary
                  : multiProfileResult
                  ? multiProfileResult.household_summary
                  : result.simple_summary
              }
              allergyTrigger={
                activeInsight
                  ? activeInsight.allergy_trigger
                  : !multiProfileResult
                  ? result.allergy_trigger
                  : undefined
              }
              baseScoreWithoutAllergy={
                activeInsight
                  ? activeInsight.base_score_without_allergy
                  : !multiProfileResult
                  ? result.base_score_without_allergy
                  : undefined
              }
            />

            <RedFlagsCard
              deceptions={result.deceptive_claims_flagged}
              violations={result.fssai_violations}
            />

            <IngredientAccordion
              ingredients={
                activeInsight && activeInsight.ingredient_warnings && activeInsight.ingredient_warnings.length > 0
                  ? activeInsight.ingredient_warnings
                  : result.ingredient_breakdown
              }
            />

            <NutrientMatrix 
              matrix={result.nutrient_integrity} 
              nutritionCard={result.nutrition_card}
            />

            <AlternativeCard 
              alternative={result.healthier_alternative} 
              cleanAlternatives={result.clean_alternatives}
              isLoadingAlternatives={isLoadingAlternatives}
            />
          </div>
        );
      })()}

      {/* Floating Chatbot grounded in current scan */}
      <FloatingChatbot activeProductContext={result} />
    </div>
  );
}
