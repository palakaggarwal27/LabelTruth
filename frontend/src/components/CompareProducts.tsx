"use client";

import React, { useState, useRef } from 'react';
import { smartScan, compareProducts } from '@/lib/api';
import { LabelAnalysisResult, PersonalizedVerdict, ProductComparisonResult } from '@/types';
import { useHealthProfile } from '@/context/HealthProfileContext';
import { 
  Trophy, CheckCircle2, AlertTriangle, XCircle, ShieldCheck, 
  Flame, Candy, Droplet, RefreshCw, Sparkles, ExternalLink, 
  Loader2, Search, Camera, UploadCloud, HeartPulse, ShieldAlert
} from 'lucide-react';

interface ProductSlotInput {
  mode: 'text' | 'image';
  query: string;
  file: File | null;
  previewUrl: string | null;
  result: LabelAnalysisResult | null;
  loading: boolean;
  error: string | null;
}

export const CompareProducts: React.FC = () => {
  const { activeProfile, profile } = useHealthProfile();
  const currentProfile = activeProfile || profile;

  // Slot A State
  const [slotA, setSlotA] = useState<ProductSlotInput>({
    mode: 'text',
    query: '',
    file: null,
    previewUrl: null,
    result: null,
    loading: false,
    error: null,
  });

  // Slot B State
  const [slotB, setSlotB] = useState<ProductSlotInput>({
    mode: 'text',
    query: '',
    file: null,
    previewUrl: null,
    result: null,
    loading: false,
    error: null,
  });

  const fileInputRefA = useRef<HTMLInputElement>(null);
  const fileInputRefB = useRef<HTMLInputElement>(null);

  // Overall Comparison State
  const [isComparing, setIsComparing] = useState(false);
  const [compareStep, setCompareStep] = useState<string>('');
  const [comparisonResult, setComparisonResult] = useState<ProductComparisonResult | null>(null);
  const [globalError, setGlobalError] = useState<string | null>(null);

  // Check if both products have inputs ready
  const hasInputA = slotA.result !== null || (slotA.mode === 'text' ? slotA.query.trim().length > 1 : slotA.file !== null);
  const hasInputB = slotB.result !== null || (slotB.mode === 'text' ? slotB.query.trim().length > 1 : slotB.file !== null);
  const canStartComparison = hasInputA && hasInputB && !isComparing;

  const handleFileChangeA = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const f = e.target.files[0];
      setSlotA(prev => ({
        ...prev,
        file: f,
        previewUrl: URL.createObjectURL(f),
        result: null,
        error: null,
      }));
      setComparisonResult(null);
    }
  };

  const handleFileChangeB = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const f = e.target.files[0];
      setSlotB(prev => ({
        ...prev,
        file: f,
        previewUrl: URL.createObjectURL(f),
        result: null,
        error: null,
      }));
      setComparisonResult(null);
    }
  };

  const setPresetComparison = (nameA: string, nameB: string) => {
    setSlotA({
      mode: 'text',
      query: nameA,
      file: null,
      previewUrl: null,
      result: null,
      loading: false,
      error: null,
    });
    setSlotB({
      mode: 'text',
      query: nameB,
      file: null,
      previewUrl: null,
      result: null,
      loading: false,
      error: null,
    });
    setComparisonResult(null);
    setGlobalError(null);
  };

  const handleRunComparison = async () => {
    if (!canStartComparison) return;

    setIsComparing(true);
    setGlobalError(null);
    setComparisonResult(null);

    let auditedA = slotA.result;
    let auditedB = slotB.result;

    try {
      // Step 1: Audit Product A if not yet audited
      if (!auditedA) {
        setCompareStep(`Auditing Product 1: ${slotA.mode === 'text' ? slotA.query : slotA.file?.name}...`);
        setSlotA(prev => ({ ...prev, loading: true, error: null }));
        const inputA = slotA.mode === 'text' ? { query: slotA.query } : { imageFile: slotA.file! };
        auditedA = await smartScan(inputA, currentProfile);
        setSlotA(prev => ({ ...prev, result: auditedA, loading: false }));
      }

      // Step 2: Audit Product B if not yet audited
      if (!auditedB) {
        setCompareStep(`Auditing Product 2: ${slotB.mode === 'text' ? slotB.query : slotB.file?.name}...`);
        setSlotB(prev => ({ ...prev, loading: true, error: null }));
        const inputB = slotB.mode === 'text' ? { query: slotB.query } : { imageFile: slotB.file! };
        auditedB = await smartScan(inputB, currentProfile);
        setSlotB(prev => ({ ...prev, result: auditedB, loading: false }));
      }

      // Step 3: Run Joint Gemini Head-to-Head Comparison
      setCompareStep('Running Gemini Head-to-Head Clinical Evaluation...');
      const pincode = typeof window !== 'undefined' ? (sessionStorage.getItem('labeltruth_user_pincode') || '110001') : '110001';
      const compRes = await compareProducts(auditedA, auditedB, currentProfile, pincode);
      setComparisonResult(compRes);
    } catch (err: unknown) {
      const errorObj = err as { response?: { data?: { detail?: string } }; message?: string };
      const msg = errorObj.response?.data?.detail || errorObj.message || 'Comparison failed. Please verify product inputs.';
      setGlobalError(msg);
    } finally {
      setIsComparing(false);
      setCompareStep('');
      setSlotA(prev => ({ ...prev, loading: false }));
      setSlotB(prev => ({ ...prev, loading: false }));
    }
  };

  const resetAll = () => {
    setSlotA({
      mode: 'text',
      query: '',
      file: null,
      previewUrl: null,
      result: null,
      loading: false,
      error: null,
    });
    setSlotB({
      mode: 'text',
      query: '',
      file: null,
      previewUrl: null,
      result: null,
      loading: false,
      error: null,
    });
    setComparisonResult(null);
    setGlobalError(null);
  };

  const getScoreColor = (score: number) => {
    if (score >= 75) return 'text-emerald-700 bg-emerald-50 border-emerald-200';
    if (score >= 45) return 'text-amber-700 bg-amber-50 border-amber-200';
    return 'text-rose-700 bg-rose-50 border-rose-200';
  };

  const renderVerdictBadge = (verdict: PersonalizedVerdict | string, healthScore: number) => {
    let effectiveVerdict = verdict;
    if (healthScore < 45) {
      effectiveVerdict = 'AVOID (VIOLATES PROFILE)';
    } else if (healthScore < 70 && effectiveVerdict === 'SAFE FOR YOU') {
      effectiveVerdict = 'CAUTION';
    }

    if (effectiveVerdict === 'SAFE FOR YOU') {
      return (
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-emerald-50 text-emerald-700 border border-emerald-200 text-xs font-semibold">
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>SAFE FOR YOU</span>
        </div>
      );
    }
    if (effectiveVerdict === 'CAUTION') {
      return (
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-amber-50 text-amber-700 border border-amber-200 text-xs font-semibold">
          <AlertTriangle className="w-3.5 h-3.5" />
          <span>CAUTION</span>
        </div>
      );
    }
    return (
      <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-rose-50 text-rose-700 border border-rose-200 text-xs font-semibold">
        <XCircle className="w-3.5 h-3.5" />
        <span>VIOLATES PROFILE</span>
      </div>
    );
  };

  const renderSlotCard = (
    label: string,
    slot: ProductSlotInput,
    setSlot: React.Dispatch<React.SetStateAction<ProductSlotInput>>,
    fileInputRef: React.RefObject<HTMLInputElement>,
    isWinner: boolean,
    isLoser: boolean,
    isNeither: boolean
  ) => {
    return (
      <div
        className={`p-5 rounded-lg border transition-all ${
          isWinner
            ? 'border-emerald-400 bg-emerald-50/20 shadow-sm ring-1 ring-emerald-300'
            : isNeither
            ? 'border-rose-300 bg-rose-50/20 shadow-sm'
            : isLoser
            ? 'border-zinc-200 bg-zinc-50/50 opacity-90'
            : 'border-zinc-200 bg-white'
        }`}
      >
        {/* Header */}
        <div className="flex items-center justify-between mb-4 border-b border-zinc-100 pb-3">
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-zinc-900 text-white">
              {label}
            </span>
            {isWinner && (
              <span className="text-[11px] font-mono font-semibold px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 border border-emerald-300 flex items-center gap-1">
                <Trophy className="w-3 h-3 text-emerald-600" />
                Superior Choice
              </span>
            )}
            {isNeither && (
              <span className="text-[11px] font-mono font-semibold px-2 py-0.5 rounded bg-rose-100 text-rose-800 border border-rose-300 flex items-center gap-1">
                <ShieldAlert className="w-3 h-3 text-rose-600" />
                Health Concern
              </span>
            )}
          </div>
          {slot.result && (
            <button
              onClick={() => {
                setSlot(prev => ({ ...prev, result: null }));
                setComparisonResult(null);
              }}
              className="text-xs text-zinc-400 hover:text-zinc-700 font-medium transition-colors"
            >
              Change
            </button>
          )}
        </div>

        {/* Input Selector if not yet audited */}
        {!slot.result ? (
          <div className="space-y-3">
            {/* Mode Toggle Buttons */}
            <div className="flex rounded-lg border border-zinc-200 p-0.5 bg-zinc-50 text-xs font-medium">
              <button
                type="button"
                onClick={() => setSlot(prev => ({ ...prev, mode: 'text' }))}
                className={`flex-1 py-1.5 rounded flex items-center justify-center gap-1.5 transition-all ${
                  slot.mode === 'text'
                    ? 'bg-white text-zinc-900 shadow-xs font-semibold'
                    : 'text-zinc-500 hover:text-zinc-800'
                }`}
              >
                <Search className="w-3.5 h-3.5" />
                <span>Product Name</span>
              </button>
              <button
                type="button"
                onClick={() => setSlot(prev => ({ ...prev, mode: 'image' }))}
                className={`flex-1 py-1.5 rounded flex items-center justify-center gap-1.5 transition-all ${
                  slot.mode === 'image'
                    ? 'bg-white text-zinc-900 shadow-xs font-semibold'
                    : 'text-zinc-500 hover:text-zinc-800'
                }`}
              >
                <Camera className="w-3.5 h-3.5" />
                <span>Photo / Screenshot</span>
              </button>
            </div>

            {/* Product Name Input */}
            {slot.mode === 'text' ? (
              <div className="space-y-2">
                <label className="block text-xs font-medium text-zinc-600">
                  Enter Brand or Food Name:
                </label>
                <div className="relative">
                  <input
                    type="text"
                    value={slot.query}
                    onChange={(e) => {
                      setSlot(prev => ({ ...prev, query: e.target.value }));
                      setComparisonResult(null);
                    }}
                    placeholder="e.g. Amul Butter, Complan Chocolate, Maggi Atta"
                    className="w-full text-xs font-sans px-3 py-2.5 rounded-lg border border-zinc-200 focus:outline-none focus:ring-1 focus:ring-zinc-900 bg-white"
                  />
                  {slot.query && (
                    <span className="absolute right-2.5 top-2.5 text-emerald-600">
                      <CheckCircle2 className="w-4 h-4" />
                    </span>
                  )}
                </div>
              </div>
            ) : (
              /* Photo Upload Zone */
              <div className="space-y-2">
                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={label === 'PRODUCT 1' ? handleFileChangeA : handleFileChangeB}
                  accept="image/*"
                  className="hidden"
                />
                {!slot.file ? (
                  <button
                    type="button"
                    onClick={() => fileInputRef.current?.click()}
                    className="w-full border-2 border-dashed border-zinc-200 rounded-lg p-5 flex flex-col items-center justify-center text-center hover:border-zinc-400 transition-colors bg-zinc-50/50"
                  >
                    <UploadCloud className="w-7 h-7 text-zinc-400 mb-1.5" />
                    <span className="text-xs font-medium text-zinc-800">
                      Upload Packaging Screenshot or Photo
                    </span>
                    <span className="text-[11px] text-zinc-400 mt-0.5">
                      Back-of-pack ingredients or front label
                    </span>
                  </button>
                ) : (
                  <div className="relative border border-zinc-200 rounded-lg p-2 bg-zinc-50 flex items-center justify-between gap-3">
                    <div className="flex items-center gap-2.5 min-w-0">
                      {slot.previewUrl && (
                        // eslint-disable-next-line @next/next/no-img-element
                        <img
                          src={slot.previewUrl}
                          alt="Packaging preview"
                          className="w-12 h-12 object-cover rounded border border-zinc-200 shrink-0"
                        />
                      )}
                      <div className="min-w-0">
                        <p className="text-xs font-medium text-zinc-800 truncate">
                          {slot.file.name}
                        </p>
                        <p className="text-[10px] text-zinc-400">
                          {(slot.file.size / 1024).toFixed(0)} KB • Photo ready
                        </p>
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={() => setSlot(prev => ({ ...prev, file: null, previewUrl: null }))}
                      className="text-xs text-rose-500 hover:text-rose-700 font-medium px-2 py-1"
                    >
                      Remove
                    </button>
                  </div>
                )}
              </div>
            )}

            {slot.error && (
              <div className="p-2.5 bg-rose-50 border border-rose-200 rounded text-xs text-rose-700">
                {slot.error}
              </div>
            )}
          </div>
        ) : (
          /* Audited Product Facts Card */
          <div className="space-y-4">
            <div className="flex items-start justify-between gap-3">
              <div>
                <h3 className="text-base font-semibold text-zinc-900 leading-snug">
                  {slot.result.product_name}
                </h3>
                <p className="text-xs text-zinc-500 font-light mt-0.5 line-clamp-2">
                  {slot.result.simple_summary}
                </p>
              </div>
              <div
                className={`flex flex-col items-center justify-center w-14 h-14 rounded-lg border font-mono font-bold shrink-0 ${getScoreColor(
                  slot.result.health_score
                )}`}
              >
                <span className="text-lg leading-none">{slot.result.health_score}</span>
                <span className="text-[9px] opacity-75 mt-0.5">/100</span>
              </div>
            </div>

            <div className="flex items-center gap-2">
              {renderVerdictBadge(slot.result.personalized_verdict, slot.result.health_score)}
            </div>

            {/* Nutrition Matrix */}
            <div className="grid grid-cols-2 gap-2 text-xs font-mono pt-2 border-t border-zinc-100">
              <div className="p-2.5 rounded bg-zinc-50 border border-zinc-100">
                <div className="flex items-center gap-1 text-zinc-400 text-[10px] uppercase">
                  <Flame className="w-3 h-3 text-amber-500" />
                  <span>Calories</span>
                </div>
                <p className="text-xs font-semibold text-zinc-900 mt-1">
                  {slot.result.nutrition_card?.calories_kcal != null ? `${slot.result.nutrition_card.calories_kcal} kcal` : 'N/A'}
                </p>
              </div>

              <div className="p-2.5 rounded bg-zinc-50 border border-zinc-100">
                <div className="flex items-center gap-1 text-zinc-400 text-[10px] uppercase">
                  <Candy className="w-3 h-3 text-purple-500" />
                  <span>Added Sugar</span>
                </div>
                <p className="text-xs font-semibold text-zinc-900 mt-1">
                  {slot.result.nutrition_card?.added_sugars_g != null ? `${slot.result.nutrition_card.added_sugars_g}g` : '0g / N/A'}
                </p>
              </div>

              <div className="p-2.5 rounded bg-zinc-50 border border-zinc-100">
                <div className="flex items-center gap-1 text-zinc-400 text-[10px] uppercase">
                  <Droplet className="w-3 h-3 text-rose-500" />
                  <span>Palm Oil / Sat Fat</span>
                </div>
                <p className="text-xs font-semibold text-zinc-900 mt-1">
                  {slot.result.nutrient_integrity?.palm_oil_present
                    ? 'Palm Oil Present'
                    : slot.result.nutrition_card?.saturated_fat_g != null
                    ? `${slot.result.nutrition_card.saturated_fat_g}g sat fat`
                    : 'Clean Fat'}
                </p>
              </div>

              <div className="p-2.5 rounded bg-zinc-50 border border-zinc-100">
                <div className="flex items-center gap-1 text-zinc-400 text-[10px] uppercase">
                  <AlertTriangle className="w-3 h-3 text-amber-500" />
                  <span>Flagged Additives</span>
                </div>
                <p className="text-xs font-semibold text-zinc-900 mt-1">
                  {slot.result.deceptive_claims_flagged.length + slot.result.fssai_violations.length} flags
                </p>
              </div>
            </div>

            {/* FSSAI Red Flags */}
            {slot.result.fssai_violations.length > 0 && (
              <div className="text-xs p-2.5 bg-rose-50/70 border border-rose-200 rounded text-rose-900 space-y-1">
                <span className="font-semibold block text-[10px] uppercase tracking-wide text-rose-700">
                  FSSAI Regulatory Red Flags:
                </span>
                <p className="text-[11px] leading-tight">
                  {slot.result.fssai_violations[0]}
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    );
  };

  const isWinnerA = comparisonResult?.winner === 'PRODUCT_A';
  const isWinnerB = comparisonResult?.winner === 'PRODUCT_B';
  const isNeither = comparisonResult?.winner === 'NEITHER_RECOMMENDED';

  return (
    <div className="space-y-6">
      {/* Intro Header */}
      <div className="border border-zinc-200 rounded-lg p-5 bg-gradient-to-r from-zinc-50 to-white">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-mono font-bold uppercase tracking-wider text-zinc-600">
                Head-to-Head Forensic Audit
              </span>
              {currentProfile && (
                <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 border border-emerald-200 flex items-center gap-1">
                  <HeartPulse className="w-3 h-3 text-emerald-600" />
                  Profile: {currentProfile.name || 'Active Member'}
                </span>
              )}
            </div>
            <h2 className="text-lg font-semibold text-zinc-900">Compare Two Packaged Products</h2>
            <p className="text-xs text-zinc-500 mt-1 max-w-xl font-light">
              Enter product names or upload photos for both. Gemini analyzes both products together in a single call, evaluates clinical trade-offs for your health conditions, and finds a superior 3rd alternative.
            </p>
          </div>

          {/* Quick Presets */}
          <div className="flex flex-wrap sm:flex-col items-start gap-1.5 shrink-0">
            <span className="text-[10px] font-mono uppercase text-zinc-400 font-semibold">
              Quick Comparisons:
            </span>
            <div className="flex flex-wrap gap-1.5">
              <button
                type="button"
                onClick={() => setPresetComparison('Amul Butter', 'Nutralite Fat Spread')}
                className="text-[11px] px-2 py-1 rounded bg-zinc-100 hover:bg-zinc-200 text-zinc-700 transition-colors font-medium"
              >
                Butter vs Margarine
              </button>
              <button
                type="button"
                onClick={() => setPresetComparison('Complan Chocolate', 'Bournvita')}
                className="text-[11px] px-2 py-1 rounded bg-zinc-100 hover:bg-zinc-200 text-zinc-700 transition-colors font-medium"
              >
                Complan vs Bournvita
              </button>
              <button
                type="button"
                onClick={() => setPresetComparison('Maggi 2-Minute Noodles', 'Yippee Power Up Noodles')}
                className="text-[11px] px-2 py-1 rounded bg-zinc-100 hover:bg-zinc-200 text-zinc-700 transition-colors font-medium"
              >
                Maggi vs Yippee
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Global Error Banner */}
      {globalError && (
        <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg text-xs text-rose-800 flex items-center justify-between">
          <span>{globalError}</span>
          <button
            onClick={() => setGlobalError(null)}
            className="text-xs text-rose-600 hover:text-rose-900 font-bold ml-2"
          >
            ✕
          </button>
        </div>
      )}

      {/* Synchronized Trigger Button */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 p-4 rounded-lg border border-zinc-200 bg-white shadow-xs">
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 text-xs text-zinc-600 font-medium">
            <span className={`w-2 h-2 rounded-full ${hasInputA ? 'bg-emerald-500' : 'bg-zinc-300'}`} />
            <span>Product 1: {slotA.result ? slotA.result.product_name : (slotA.query || slotA.file?.name || 'Pending input')}</span>
          </div>
          <span className="text-zinc-300 font-mono">|</span>
          <div className="flex items-center gap-1.5 text-xs text-zinc-600 font-medium">
            <span className={`w-2 h-2 rounded-full ${hasInputB ? 'bg-emerald-500' : 'bg-zinc-300'}`} />
            <span>Product 2: {slotB.result ? slotB.result.product_name : (slotB.query || slotB.file?.name || 'Pending input')}</span>
          </div>
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          {comparisonResult && (
            <button
              type="button"
              onClick={resetAll}
              className="px-3 py-2 rounded-lg border border-zinc-200 hover:bg-zinc-50 text-xs font-medium text-zinc-600 transition-colors flex items-center gap-1.5"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Reset</span>
            </button>
          )}

          <button
            type="button"
            onClick={handleRunComparison}
            disabled={!canStartComparison}
            className={`flex-1 sm:flex-initial px-5 py-2.5 rounded-lg text-xs font-semibold flex items-center justify-center gap-2 transition-all ${
              canStartComparison
                ? 'bg-zinc-900 text-white hover:bg-zinc-800 shadow-sm cursor-pointer'
                : 'bg-zinc-100 text-zinc-400 cursor-not-allowed'
            }`}
          >
            {isComparing ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin text-white" />
                <span>{compareStep || 'Comparing...'}</span>
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4 text-emerald-400" />
                <span>Run Head-to-Head Audit</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Comparison Verdict Banner */}
      {comparisonResult && (
        <div className="space-y-4">
          <div
            className={`p-5 rounded-lg border shadow-sm ${
              isWinnerA || isWinnerB
                ? 'border-emerald-300 bg-emerald-50/90'
                : isNeither
                ? 'border-rose-300 bg-rose-50/90'
                : 'border-zinc-300 bg-zinc-50/90'
            }`}
          >
            <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
              <div className="flex items-start gap-3.5">
                <div
                  className={`w-11 h-11 rounded-full text-white flex items-center justify-center shrink-0 shadow-sm mt-0.5 ${
                    isWinnerA || isWinnerB
                      ? 'bg-emerald-600'
                      : isNeither
                      ? 'bg-rose-600'
                      : 'bg-zinc-700'
                  }`}
                >
                  {isWinnerA || isWinnerB ? (
                    <Trophy className="w-5 h-5" />
                  ) : isNeither ? (
                    <ShieldAlert className="w-5 h-5" />
                  ) : (
                    <AlertTriangle className="w-5 h-5" />
                  )}
                </div>

                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span
                      className={`text-[10px] font-mono uppercase tracking-wider font-bold ${
                        isWinnerA || isWinnerB
                          ? 'text-emerald-800'
                          : isNeither
                          ? 'text-rose-800'
                          : 'text-zinc-600'
                      }`}
                    >
                      AI Forensic Verdict
                    </span>
                    {comparisonResult.score_diff > 0 && (
                      <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded bg-white/80 border border-zinc-200 text-zinc-700">
                        Δ {comparisonResult.score_diff} pts difference
                      </span>
                    )}
                  </div>
                  <h3
                    className={`text-base font-bold leading-tight ${
                      isWinnerA || isWinnerB
                        ? 'text-emerald-950'
                        : isNeither
                        ? 'text-rose-950'
                        : 'text-zinc-900'
                    }`}
                  >
                    {comparisonResult.verdict_title}
                  </h3>
                  <p
                    className={`text-xs leading-relaxed mt-1 ${
                      isWinnerA || isWinnerB
                        ? 'text-emerald-900'
                        : isNeither
                        ? 'text-rose-900'
                        : 'text-zinc-700'
                    }`}
                  >
                    {comparisonResult.verdict_summary}
                  </p>
                </div>
              </div>
            </div>

            {/* Personalized Impact tailored to conditions */}
            {comparisonResult.personalized_impact && (
              <div className="mt-4 pt-3.5 border-t border-black/10">
                <div className="flex items-center gap-1.5 text-xs font-semibold text-zinc-800 mb-1">
                  <HeartPulse className="w-4 h-4 text-rose-500" />
                  <span>Clinical Impact for Your Health Profile:</span>
                </div>
                <p className="text-xs text-zinc-700 leading-relaxed font-light">
                  {comparisonResult.personalized_impact}
                </p>
              </div>
            )}
          </div>

          {/* Dimension Breakdown (3 Cards) */}
          {comparisonResult.dimension_breakdown && comparisonResult.dimension_breakdown.length > 0 && (
            <div className="space-y-2">
              <span className="text-xs font-mono font-bold uppercase tracking-wider text-zinc-500 block">
                Dimension-by-Dimension Breakdown
              </span>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {comparisonResult.dimension_breakdown.map((dim, idx) => {
                  const dimWinnerLabel =
                    dim.winner === 'PRODUCT_A'
                      ? 'Product 1 Wins'
                      : dim.winner === 'PRODUCT_B'
                      ? 'Product 2 Wins'
                      : dim.winner === 'TIE'
                      ? 'Equal / Tie'
                      : 'Neither Recommended';

                  const dimWinnerColor =
                    dim.winner === 'PRODUCT_A' || dim.winner === 'PRODUCT_B'
                      ? 'text-emerald-700 bg-emerald-50 border-emerald-200'
                      : dim.winner === 'NEITHER'
                      ? 'text-rose-700 bg-rose-50 border-rose-200'
                      : 'text-zinc-700 bg-zinc-50 border-zinc-200';

                  return (
                    <div key={idx} className="p-3.5 rounded-lg border border-zinc-200 bg-white space-y-1.5 shadow-xs">
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-xs font-semibold text-zinc-900">
                          {dim.category}
                        </span>
                        <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded border ${dimWinnerColor}`}>
                          {dimWinnerLabel}
                        </span>
                      </div>
                      <p className="text-[11px] text-zinc-600 leading-relaxed font-light">
                        {dim.explanation}
                      </p>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Key Trade-offs Matrix */}
          {comparisonResult.key_tradeoffs && comparisonResult.key_tradeoffs.length > 0 && (
            <div className="p-4 rounded-lg border border-zinc-200 bg-white space-y-2 shadow-xs">
              <span className="text-xs font-mono font-bold uppercase tracking-wider text-zinc-600 block">
                Key Head-to-Head Trade-offs
              </span>
              <ul className="space-y-1.5 text-xs text-zinc-700">
                {comparisonResult.key_tradeoffs.map((bullet, idx) => (
                  <li key={idx} className="flex items-start gap-2">
                    <span className="text-emerald-600 font-bold mt-0.5">•</span>
                    <span>{bullet}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Superior 3rd Product Alternative Card */}
          {comparisonResult.superior_alternative && (
            <div className="p-5 rounded-lg border-2 border-emerald-400 bg-gradient-to-r from-emerald-50/80 via-white to-emerald-50/40 shadow-sm space-y-3">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-emerald-200 pb-3">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-full bg-emerald-600 text-white flex items-center justify-center shrink-0">
                    <Sparkles className="w-4 h-4 text-emerald-200" />
                  </div>
                  <div>
                    <span className="text-[10px] font-mono uppercase tracking-wider text-emerald-700 font-bold block">
                      Clean Swap Recommendation
                    </span>
                    <h4 className="text-sm font-bold text-zinc-900">
                      Superior 3rd Product (Beats Both Scanned Items)
                    </h4>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono font-bold px-2.5 py-1 rounded bg-emerald-600 text-white">
                    Health Score {comparisonResult.superior_alternative.health_score || 85}/100
                  </span>
                  {comparisonResult.superior_alternative.delta_vs_scanned && (
                    <span className="text-xs font-mono font-semibold px-2.5 py-1 rounded bg-emerald-100 text-emerald-900 border border-emerald-300">
                      {comparisonResult.superior_alternative.delta_vs_scanned}
                    </span>
                  )}
                </div>
              </div>

              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div className="space-y-1 max-w-xl">
                  <h5 className="text-base font-bold text-zinc-900">
                    {comparisonResult.superior_alternative.name}
                  </h5>
                  <p className="text-xs text-zinc-700 leading-relaxed">
                    <strong className="text-zinc-900 font-semibold">Why it wins: </strong>
                    {comparisonResult.superior_alternative.key_benefit || comparisonResult.superior_alternative.reason}
                  </p>
                  {comparisonResult.superior_alternative.personalized_fit && (
                    <p className="text-xs text-emerald-800 font-light mt-0.5">
                      ✓ {comparisonResult.superior_alternative.personalized_fit}
                    </p>
                  )}
                </div>

                {comparisonResult.superior_alternative.store_url && (
                  <a
                    href={comparisonResult.superior_alternative.store_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center justify-center gap-1.5 px-4 py-2.5 rounded-lg bg-emerald-700 hover:bg-emerald-800 text-white text-xs font-semibold shadow-xs transition-colors shrink-0"
                  >
                    <span>Order on Quick Commerce</span>
                    <ExternalLink className="w-3.5 h-3.5" />
                  </a>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Side-by-Side Product Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {renderSlotCard(
          'PRODUCT 1',
          slotA,
          setSlotA,
          fileInputRefA,
          isWinnerA,
          isWinnerB,
          isNeither
        )}
        {renderSlotCard(
          'PRODUCT 2',
          slotB,
          setSlotB,
          fileInputRefB,
          isWinnerB,
          isWinnerA,
          isNeither
        )}
      </div>
    </div>
  );
};
