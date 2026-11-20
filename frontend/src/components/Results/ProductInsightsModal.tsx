"use client";

import React, { useEffect, useRef } from 'react';
import { LabelAnalysisResult } from '@/types';
import { ScoreCard } from '@/components/Results/ScoreCard';
import { RedFlagsCard } from '@/components/Results/RedFlagsCard';
import { IngredientAccordion } from '@/components/Results/IngredientAccordion';
import { NutrientMatrix } from '@/components/Results/NutrientMatrix';
import { X, Sparkles, ShieldCheck } from 'lucide-react';

interface ProductInsightsModalProps {
  isOpen: boolean;
  onClose: () => void;
  product: LabelAnalysisResult | null;
  productTitle?: string;
}

export const ProductInsightsModal: React.FC<ProductInsightsModalProps> = ({
  isOpen,
  onClose,
  product,
  productTitle,
}) => {
  const dialogRef = useRef<HTMLDivElement>(null);

  // Close on Escape key press
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    if (isOpen) {
      window.addEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'hidden';
    }
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, onClose]);

  if (!isOpen || !product) return null;

  const displayName = productTitle || product.product_name || 'Product Full Insights';

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="insights-modal-title"
      className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-black/60 backdrop-blur-sm animate-in fade-in duration-150"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        ref={dialogRef}
        className="bg-white rounded-xl shadow-2xl border border-zinc-200 w-full max-w-4xl max-h-[92vh] flex flex-col overflow-hidden animate-in zoom-in-95 duration-200"
      >
        {/* Modal Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-zinc-200 bg-zinc-50 shrink-0">
          <div className="flex items-center gap-2.5 min-w-0 pr-4">
            <div className="w-8 h-8 rounded-lg bg-emerald-100 text-emerald-700 flex items-center justify-center shrink-0">
              <Sparkles className="w-4 h-4" />
            </div>
            <div className="min-w-0">
              <span className="text-[10px] font-mono uppercase tracking-wider text-emerald-800 font-semibold block">
                Full Forensic Product Audit
              </span>
              <h2
                id="insights-modal-title"
                className="text-base font-semibold text-zinc-900 truncate"
              >
                {displayName}
              </h2>
            </div>
          </div>

          <div className="flex items-center gap-3 shrink-0">
            <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded font-mono text-xs font-bold ${
              product.health_score === 0 && product.allergy_trigger
                ? 'bg-rose-100 text-rose-800 border border-rose-300'
                : 'bg-zinc-200/80 text-zinc-800'
            }`}>
              <span>{product.health_score}</span>
              <span className="text-[10px] opacity-60">/100</span>
              {product.health_score === 0 && product.allergy_trigger && (
                <span className="text-[9px] uppercase tracking-wider font-sans font-bold text-rose-700 ml-1">Allergen</span>
              )}
            </div>
            <button
              type="button"
              onClick={onClose}
              aria-label="Close modal"
              className="p-1.5 rounded-md text-zinc-400 hover:text-zinc-700 hover:bg-zinc-200 transition-colors cursor-pointer"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Modal Scrollable Body */}
        <div className="overflow-y-auto p-5 sm:p-6 space-y-5 flex-1">
          {/* 1. Score Card */}
          <ScoreCard
            productName={displayName}
            healthScore={product.health_score}
            verdict={product.personalized_verdict}
            summary={product.simple_summary}
            allergyTrigger={product.allergy_trigger}
            baseScoreWithoutAllergy={product.base_score_without_allergy}
          />

          {/* 2. Red Flags & Violations */}
          <RedFlagsCard
            deceptions={product.deceptive_claims_flagged || []}
            violations={product.fssai_violations || []}
          />

          {/* 3. Ingredient Breakdown */}
          <IngredientAccordion
            ingredients={product.ingredient_breakdown || []}
          />

          {/* 4. Nutrient Integrity & Nutrition Card */}
          <NutrientMatrix
            matrix={product.nutrient_integrity}
            nutritionCard={product.nutrition_card}
          />
        </div>

        {/* Modal Footer */}
        <div className="px-5 py-3 border-t border-zinc-200 bg-zinc-50 flex items-center justify-between text-xs text-zinc-500 shrink-0">
          <span className="flex items-center gap-1.5 text-[11px]">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
            Audited against FSSAI 2020/2023 regulations &amp; ICMR-NIN guidelines
          </span>
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-1.5 bg-zinc-900 hover:bg-zinc-800 text-white font-medium rounded-md transition-colors cursor-pointer"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
