"use client";

import React, { useState } from 'react';
import { UploadZone } from '@/components/Scanner/UploadZone';
import { CameraCapture } from '@/components/Scanner/CameraCapture';
import { PresetBar } from '@/components/Scanner/PresetBar';
import { ScoreCard } from '@/components/Results/ScoreCard';
import { RedFlagsCard } from '@/components/Results/RedFlagsCard';
import { IngredientAccordion } from '@/components/Results/IngredientAccordion';
import { AlternativeCard } from '@/components/Results/AlternativeCard';
import { FloatingChatbot } from '@/components/FloatingChatbot';
import { useHealthProfile } from '@/context/HealthProfileContext';
import { smartScan } from '@/lib/api';
import { LabelAnalysisResult, PresetProduct, ScannedHistoryItem } from '@/types';
import { AlertCircle, RefreshCw, ScanLine, History, Trash2 } from 'lucide-react';
import { ScanHistoryList } from '@/components/Scanner/ScanHistoryList';
import { HealthProfileManager } from '@/components/HealthProfileManager';
import { NutrientMatrix } from '@/components/Results/NutrientMatrix';
import { FALLBACK_PRESET_PRODUCTS } from '@/data/presets';

import { DemoToggle } from '@/components/DemoToggle';
import { evaluateProfileSafety } from '@/lib/api';

const SCAN_HISTORY_KEY = 'labeltruth_scan_history_v1';

export default function ScanPage() {
  const { profile, activeProfile } = useHealthProfile();
  const currentProfile = activeProfile || profile;
  const [activeTab, setActiveTab] = useState<'scan' | 'history'>('scan');
  const [isCameraOpen, setIsCameraOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<LabelAnalysisResult | null>(null);
  const [history, setHistory] = useState<ScannedHistoryItem[]>([]);
  const [demoMode, setDemoMode] = useState(false);

  // Instant Profile Re-evaluation when family profile is switched
  React.useEffect(() => {
    if (result && currentProfile) {
      // Re-evaluate active result against active member in <50ms without re-running OCR
      evaluateProfileSafety(result.product_name, currentProfile)
        .then((evalData) => {
          if (evalData && evalData.personalized_verdict) {
            setResult((prev) => prev ? {
              ...prev,
              personalized_verdict: evalData.personalized_verdict as import('@/types').PersonalizedVerdict,
              ingredient_breakdown: evalData.ingredient_breakdown || prev.ingredient_breakdown
            } : null);
          }
        })
        .catch((e) => console.warn('Instant profile evaluation notice:', e));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentProfile.id, currentProfile.name]);

  // Load scan history and check for shared URL / query search params from Web Share Target
  React.useEffect(() => {
    try {
      const saved = localStorage.getItem(SCAN_HISTORY_KEY);
      if (saved) {
        setHistory(JSON.parse(saved));
      }
    } catch (e) {
      console.warn('Failed to load scan history:', e);
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
        const updated = [newItem, ...prev].slice(0, 30); // keep recent 30 scans
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
    try {
      localStorage.removeItem(SCAN_HISTORY_KEY);
    } catch (e) {
      console.warn('Failed to clear scan history:', e);
    }
  };

  const handleProcessImage = async (fileOrBlob: File | Blob) => {
    setLoading(true);
    setError(null);
    try {
      const data = await smartScan({ imageFile: fileOrBlob }, profile);
      setResult(data);
      saveToHistory(data, fileOrBlob);
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

  const handleProcessQuery = async (queryText: string, pincode?: string) => {
    setLoading(true);
    setError(null);
    const normalized = queryText.trim().toLowerCase();

    // 1. Check client-side history cache only on exact product name match
    const cachedItem = history.find(
      (h) => h.result.product_name.trim().toLowerCase() === normalized
    );
    if (cachedItem) {
      setResult(cachedItem.result);
      setLoading(false);
      return;
    }

    try {
      const data = await smartScan({ query: queryText, pincode: pincode || '110001', demoMode }, currentProfile);
      setResult(data);
      saveToHistory(data);
    } catch (err: unknown) {
      console.warn('Backend query error, checking local preset catalog:', err);
      // Check if user queried one of our exact demo products
      const matched = FALLBACK_PRESET_PRODUCTS.find((p) => 
        p.title.toLowerCase() === normalized || 
        p.sample_result.product_name.toLowerCase() === normalized
      );

      if (matched) {
        setResult(matched.sample_result);
        saveToHistory(matched.sample_result);
        return;
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

  const handleSelectPreset = (preset: PresetProduct) => {
    setResult(preset.sample_result);
    setError(null);
    saveToHistory(preset.sample_result);
  };

  const handleSelectHistoryItem = (item: ScannedHistoryItem) => {
    setResult(item.result);
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
        <HealthProfileManager />
      </div>

      {/* Offline Demo Mode Sandbox Suite */}
      <div className="mb-6">
        <DemoToggle
          demoMode={demoMode}
          onToggle={(val) => setDemoMode(val)}
          onSelectTier={(tier) => {
            setDemoMode(true);
            handleProcessQuery(tier);
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

      {activeTab === 'history' ? (
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
            <div className="mt-6 p-4 border border-zinc-200 bg-zinc-50 rounded-md text-center flex items-center justify-center gap-2 text-xs font-medium text-zinc-700">
              <RefreshCw className="w-4 h-4 animate-spin text-zinc-900" />
              <span>Auditing label with Gemini Vision against FSSAI 2020 guidelines...</span>
            </div>
          )}

          {error && (
            <div className="mt-6 p-4 border border-rose-200 bg-rose-50 rounded-md text-xs text-rose-800 flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Preset Demo Bar */}
          <PresetBar onSelectPreset={handleSelectPreset} loading={loading} />
        </div>
      ) : (
        <div className="space-y-6">
          {/* Action Bar */}
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono uppercase tracking-wider text-zinc-500">
              Audit Complete
            </span>
            <button
              onClick={() => setResult(null)}
              className="px-3.5 py-1.5 bg-zinc-900 hover:bg-zinc-800 text-white rounded-md text-xs font-semibold flex items-center gap-1.5"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              Scan Another Label
            </button>
          </div>

          {/* Results components */}
          <ScoreCard
            productName={result.product_name}
            healthScore={result.health_score}
            verdict={result.personalized_verdict}
            summary={result.simple_summary}
          />

          <RedFlagsCard
            deceptions={result.deceptive_claims_flagged}
            violations={result.fssai_violations}
          />

          <IngredientAccordion ingredients={result.ingredient_breakdown} />

          <NutrientMatrix 
            matrix={result.nutrient_integrity} 
            nutritionCard={result.nutrition_card}
          />

          <AlternativeCard 
            alternative={result.healthier_alternative} 
            cleanAlternatives={result.clean_alternatives}
          />
        </div>
      )}

      {/* Floating Chatbot grounded in current scan */}
      <FloatingChatbot activeProductContext={result} />
    </div>
  );
}
