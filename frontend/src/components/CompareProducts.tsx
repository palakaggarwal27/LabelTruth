"use client";

import React, { useState } from 'react';
import { UploadZone } from '@/components/Scanner/UploadZone';
import { smartScan } from '@/lib/api';
import { LabelAnalysisResult, PersonalizedVerdict } from '@/types';
import { useHealthProfile } from '@/context/HealthProfileContext';
import { Trophy, CheckCircle2, AlertTriangle, XCircle, ShieldCheck, Flame, Candy, Droplet, RefreshCw } from 'lucide-react';

export const CompareProducts: React.FC = () => {
  const { activeProfile, profile } = useHealthProfile();
  const currentProfile = activeProfile || profile;

  const [productA, setProductA] = useState<LabelAnalysisResult | null>(null);
  const [productB, setProductB] = useState<LabelAnalysisResult | null>(null);

  const [loadingA, setLoadingA] = useState(false);
  const [loadingB, setLoadingB] = useState(false);

  const [errorA, setErrorA] = useState<string | null>(null);
  const [errorB, setErrorB] = useState<string | null>(null);

  const handleScanA = async (input: { query?: string; imageFile?: File | Blob }) => {
    setLoadingA(true);
    setErrorA(null);
    try {
      const data = await smartScan(input, currentProfile);
      setProductA(data);
    } catch (err: unknown) {
      const errorObj = err as { response?: { data?: { detail?: string } } };
      setErrorA(errorObj.response?.data?.detail || 'Failed to audit Product 1. Please try again.');
    } finally {
      setLoadingA(false);
    }
  };

  const handleScanB = async (input: { query?: string; imageFile?: File | Blob }) => {
    setLoadingB(true);
    setErrorB(null);
    try {
      const data = await smartScan(input, currentProfile);
      setProductB(data);
    } catch (err: unknown) {
      const errorObj = err as { response?: { data?: { detail?: string } } };
      setErrorB(errorObj.response?.data?.detail || 'Failed to audit Product 2. Please try again.');
    } finally {
      setLoadingB(false);
    }
  };

  const scoreA = productA ? productA.health_score : 0;
  const scoreB = productB ? productB.health_score : 0;
  const scoreDiff = Math.abs(scoreA - scoreB);

  // Comparison State Logic:
  // - If both are low scores (< 55): Neither is a superior choice.
  // - If scoreDiff <= 3: It's essentially a tie / comparable.
  // - Clear winner requires scoreDiff >= 4 AND a reasonable health profile.
  let comparisonType: 'CLEAR_WINNER' | 'MARGINAL_LEAD' | 'BOTH_POOR' | 'TIE' | null = null;
  let winnerProduct: 'A' | 'B' | null = null;
  let verdictText = '';

  if (productA && productB) {
    if (scoreA < 55 && scoreB < 55) {
      if (scoreDiff <= 3) {
        comparisonType = 'BOTH_POOR';
        verdictText = `Both products have compromised nutritional quality (${scoreA} vs ${scoreB} pts). Neither is recommended.`;
      } else {
        comparisonType = 'MARGINAL_LEAD';
        winnerProduct = scoreA > scoreB ? 'A' : 'B';
        const leadProd = scoreA > scoreB ? productA : productB;
        verdictText = `${leadProd.product_name} is marginally less processed (+${scoreDiff} pts), but both products have significant nutritional concerns.`;
      }
    } else if (scoreDiff <= 3) {
      comparisonType = 'TIE';
      verdictText = `Both products have comparable nutritional integrity (${scoreA} vs ${scoreB} pts).`;
    } else {
      comparisonType = 'CLEAR_WINNER';
      winnerProduct = scoreA > scoreB ? 'A' : 'B';
      const leadProd = scoreA > scoreB ? productA : productB;
      verdictText = `${leadProd.product_name} is the superior choice (+${scoreDiff} pts cleaner).`;
    }
  }

  const getScoreColor = (score: number) => {
    if (score >= 75) return 'text-emerald-700 bg-emerald-50 border-emerald-200';
    if (score >= 45) return 'text-amber-700 bg-amber-50 border-amber-200';
    return 'text-rose-700 bg-rose-50 border-rose-200';
  };

  const renderVerdictBadge = (verdict: PersonalizedVerdict | string, healthScore: number) => {
    // Medical integrity rule: A product with health score < 70 must NEVER be labeled SAFE FOR YOU
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

  const renderProductCard = (
    label: string,
    product: LabelAnalysisResult | null,
    loading: boolean,
    error: string | null,
    onScan: (input: { query?: string; imageFile?: File | Blob }) => void,
    onReset: () => void,
    isLead: boolean,
    badgeType: 'SUPERIOR' | 'MARGINAL' | null
  ) => {
    return (
      <div
        className={`p-5 rounded-lg border transition-all ${
          badgeType === 'SUPERIOR'
            ? 'border-emerald-400 bg-emerald-50/20 shadow-sm ring-1 ring-emerald-300'
            : badgeType === 'MARGINAL'
            ? 'border-amber-300 bg-amber-50/20 shadow-sm'
            : 'border-zinc-200 bg-white'
        }`}
      >
        <div className="flex items-center justify-between mb-4 border-b border-zinc-100 pb-3">
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-zinc-900 text-white">
              {label}
            </span>
            {badgeType === 'SUPERIOR' && (
              <span className="text-[11px] font-mono font-semibold px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 border border-emerald-300 flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                Superior Choice
              </span>
            )}
            {badgeType === 'MARGINAL' && (
              <span className="text-[11px] font-mono font-semibold px-2 py-0.5 rounded bg-amber-100 text-amber-900 border border-amber-300 flex items-center gap-1">
                <AlertTriangle className="w-3 h-3 text-amber-700" />
                Marginally Better (+{scoreDiff} pts)
              </span>
            )}
          </div>
          {product && (
            <button
              onClick={onReset}
              className="text-xs text-zinc-400 hover:text-zinc-700 font-medium transition-colors"
            >
              Change
            </button>
          )}
        </div>

        {!product ? (
          <div>
            <UploadZone
              onFileSelect={(file) => onScan({ imageFile: file })}
              onTextSubmit={(text) => onScan({ query: text })}
              loading={loading}
              compact
            />
            {error && (
              <div className="mt-3 p-3 bg-rose-50 border border-rose-200 rounded text-xs text-rose-700">
                {error}
              </div>
            )}
          </div>
        ) : (
          <div className="space-y-4">
            {/* Title & Score */}
            <div className="flex items-start justify-between gap-3">
              <div>
                <h3 className="text-base font-semibold text-zinc-900 leading-snug">
                  {product.product_name}
                </h3>
                <p className="text-xs text-zinc-500 font-light mt-0.5 line-clamp-2">
                  {product.simple_summary}
                </p>
              </div>
              <div
                className={`flex flex-col items-center justify-center w-14 h-14 rounded-lg border font-mono font-bold shrink-0 ${getScoreColor(
                  product.health_score
                )}`}
              >
                <span className="text-lg leading-none">{product.health_score}</span>
                <span className="text-[9px] opacity-75 mt-0.5">/100</span>
              </div>
            </div>

            {/* Verdict Badge */}
            <div className="flex items-center gap-2">
              {renderVerdictBadge(product.personalized_verdict, product.health_score)}
            </div>

            {/* Metric Comparison Table */}
            <div className="grid grid-cols-2 gap-2 text-xs font-mono pt-2 border-t border-zinc-100">
              <div className="p-2.5 rounded bg-zinc-50 border border-zinc-100">
                <div className="flex items-center gap-1 text-zinc-400 text-[10px] uppercase">
                  <Flame className="w-3 h-3 text-amber-500" />
                  <span>Calories</span>
                </div>
                <p className="text-xs font-semibold text-zinc-900 mt-1">
                  {product.nutrition_card?.calories_kcal != null ? `${product.nutrition_card.calories_kcal} kcal` : 'N/A'}
                </p>
              </div>

              <div className="p-2.5 rounded bg-zinc-50 border border-zinc-100">
                <div className="flex items-center gap-1 text-zinc-400 text-[10px] uppercase">
                  <Candy className="w-3 h-3 text-purple-500" />
                  <span>Added Sugar</span>
                </div>
                <p className="text-xs font-semibold text-zinc-900 mt-1">
                  {product.nutrition_card?.added_sugars_g != null ? `${product.nutrition_card.added_sugars_g} g` : '0 g / N/A'}
                </p>
              </div>

              <div className="p-2.5 rounded bg-zinc-50 border border-zinc-100">
                <div className="flex items-center gap-1 text-zinc-400 text-[10px] uppercase">
                  <Droplet className="w-3 h-3 text-rose-500" />
                  <span>Palm Oil / Sat Fat</span>
                </div>
                <p className="text-xs font-semibold text-zinc-900 mt-1">
                  {product.nutrient_integrity?.palm_oil_present ? 'Palm Oil Present' : product.nutrition_card?.saturated_fat_g != null ? `${product.nutrition_card.saturated_fat_g}g sat fat` : 'Clean Fat'}
                </p>
              </div>

              <div className="p-2.5 rounded bg-zinc-50 border border-zinc-100">
                <div className="flex items-center gap-1 text-zinc-400 text-[10px] uppercase">
                  <AlertTriangle className="w-3 h-3 text-amber-500" />
                  <span>Flagged Additives</span>
                </div>
                <p className="text-xs font-semibold text-zinc-900 mt-1">
                  {product.deceptive_claims_flagged.length + product.fssai_violations.length} red flags
                </p>
              </div>
            </div>

            {/* Top Red Flags */}
            {product.fssai_violations.length > 0 && (
              <div className="text-xs p-2.5 bg-rose-50/70 border border-rose-200 rounded text-rose-900 space-y-1">
                <span className="font-semibold block text-[10px] uppercase tracking-wide text-rose-700">
                  FSSAI / Health Red Flags:
                </span>
                <p className="text-[11px] leading-tight">
                  {product.fssai_violations[0]}
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="space-y-6">
      <div className="border border-zinc-200 rounded-lg p-5 bg-gradient-to-r from-zinc-50 to-white">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-xs font-mono font-bold uppercase tracking-wider text-zinc-600">
            Head-to-Head Comparison
          </span>
        </div>
        <h2 className="text-lg font-semibold text-zinc-900">Compare Two Packaged Products</h2>
        <p className="text-xs text-zinc-500 mt-1 max-w-xl font-light">
          Scan or search two snacks, beverages, or groceries. We analyze calories, added sugars, palm oil, FSSAI compliance, and clinical safety to declare the superior choice.
        </p>
      </div>

      {comparisonType && productA && productB && (
        <div className={`p-4 rounded-lg border flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-sm ${
          comparisonType === 'CLEAR_WINNER'
            ? 'border-emerald-300 bg-emerald-50/90'
            : comparisonType === 'MARGINAL_LEAD' || comparisonType === 'BOTH_POOR'
            ? 'border-amber-300 bg-amber-50/90'
            : 'border-zinc-300 bg-zinc-50/90'
        }`}>
          <div className="flex items-center gap-3">
            <div className={`w-10 h-10 rounded-full text-white flex items-center justify-center shrink-0 shadow-sm ${
              comparisonType === 'CLEAR_WINNER'
                ? 'bg-emerald-600'
                : comparisonType === 'MARGINAL_LEAD' || comparisonType === 'BOTH_POOR'
                ? 'bg-amber-600'
                : 'bg-zinc-600'
            }`}>
              {comparisonType === 'CLEAR_WINNER' ? (
                <Trophy className="w-5 h-5" />
              ) : (
                <AlertTriangle className="w-5 h-5" />
              )}
            </div>
            <div>
              <span className={`text-[10px] font-mono uppercase tracking-wider font-bold block ${
                comparisonType === 'CLEAR_WINNER'
                  ? 'text-emerald-800'
                  : comparisonType === 'MARGINAL_LEAD' || comparisonType === 'BOTH_POOR'
                  ? 'text-amber-800'
                  : 'text-zinc-600'
              }`}>
                Forensic Audit Verdict
              </span>
              <p className={`text-sm font-semibold mt-0.5 ${
                comparisonType === 'CLEAR_WINNER'
                  ? 'text-emerald-950'
                  : comparisonType === 'MARGINAL_LEAD' || comparisonType === 'BOTH_POOR'
                  ? 'text-amber-950'
                  : 'text-zinc-900'
              }`}>
                {verdictText}
              </p>
            </div>
          </div>
          <button
            onClick={() => {
              setProductA(null);
              setProductB(null);
            }}
            className="self-start sm:self-auto px-3 py-1.5 bg-zinc-900 text-white rounded text-xs font-medium hover:bg-zinc-800 transition-colors flex items-center gap-1.5"
          >
            <RefreshCw className="w-3 h-3" />
            <span>Reset Comparison</span>
          </button>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {renderProductCard(
          'PRODUCT 1',
          productA,
          loadingA,
          errorA,
          handleScanA,
          () => setProductA(null),
          winnerProduct === 'A',
          winnerProduct === 'A'
            ? (comparisonType === 'CLEAR_WINNER' ? 'SUPERIOR' : (comparisonType === 'MARGINAL_LEAD' ? 'MARGINAL' : null))
            : null
        )}
        {renderProductCard(
          'PRODUCT 2',
          productB,
          loadingB,
          errorB,
          handleScanB,
          () => setProductB(null),
          winnerProduct === 'B',
          winnerProduct === 'B'
            ? (comparisonType === 'CLEAR_WINNER' ? 'SUPERIOR' : (comparisonType === 'MARGINAL_LEAD' ? 'MARGINAL' : null))
            : null
        )}
      </div>
    </div>
  );
};
