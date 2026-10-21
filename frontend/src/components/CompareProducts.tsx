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

  let winnerText = '';
  let winnerProduct: 'A' | 'B' | 'TIE' | null = null;
  if (productA && productB) {
    if (scoreA > scoreB) {
      winnerProduct = 'A';
      winnerText = `${productA.product_name} is cleaner (+${scoreA - scoreB} pts better)`;
    } else if (scoreB > scoreA) {
      winnerProduct = 'B';
      winnerText = `${productB.product_name} is cleaner (+${scoreB - scoreA} pts better)`;
    } else {
      winnerProduct = 'TIE';
      winnerText = 'Both products have equivalent nutritional integrity.';
    }
  }

  const getScoreColor = (score: number) => {
    if (score >= 75) return 'text-emerald-700 bg-emerald-50 border-emerald-200';
    if (score >= 45) return 'text-amber-700 bg-amber-50 border-amber-200';
    return 'text-rose-700 bg-rose-50 border-rose-200';
  };

  const renderVerdictBadge = (verdict: PersonalizedVerdict | string) => {
    if (verdict === 'SAFE FOR YOU') {
      return (
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-emerald-50 text-emerald-700 border border-emerald-200 text-xs font-semibold">
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>SAFE FOR YOU</span>
        </div>
      );
    }
    if (verdict === 'CAUTION') {
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
    isWinner: boolean
  ) => {
    return (
      <div
        className={`p-5 rounded-lg border transition-all ${
          isWinner
            ? 'border-emerald-400 bg-emerald-50/20 shadow-sm ring-1 ring-emerald-300'
            : 'border-zinc-200 bg-white'
        }`}
      >
        <div className="flex items-center justify-between mb-4 border-b border-zinc-100 pb-3">
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-zinc-900 text-white">
              {label}
            </span>
            {isWinner && (
              <span className="text-[11px] font-mono font-semibold px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 border border-emerald-300 flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                Superior Choice
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
              {renderVerdictBadge(product.personalized_verdict)}
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

      {winnerProduct && productA && productB && (
        <div className="p-4 rounded-lg border border-emerald-300 bg-emerald-50/90 flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-emerald-600 text-white flex items-center justify-center shrink-0 shadow-sm">
              <Trophy className="w-5 h-5" />
            </div>
            <div>
              <span className="text-[10px] font-mono uppercase tracking-wider text-emerald-800 font-bold block">
                Forensic Audit Verdict
              </span>
              <p className="text-sm font-semibold text-emerald-950 mt-0.5">
                {winnerText}
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
          winnerProduct === 'A'
        )}
        {renderProductCard(
          'PRODUCT 2',
          productB,
          loadingB,
          errorB,
          handleScanB,
          () => setProductB(null),
          winnerProduct === 'B'
        )}
      </div>
    </div>
  );
};
