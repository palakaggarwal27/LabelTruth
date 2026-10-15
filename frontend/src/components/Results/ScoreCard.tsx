"use client";

import React from 'react';
import { PersonalizedVerdict } from '@/types';

interface ScoreCardProps {
  productName: string;
  healthScore: number;
  verdict: PersonalizedVerdict;
  summary: string;
}

export const ScoreCard: React.FC<ScoreCardProps> = ({
  productName,
  healthScore,
  verdict,
  summary,
}) => {
  // Traffic Light functional color system (Strict, muted, no neon)
  const getVerdictStyles = (v: PersonalizedVerdict) => {
    switch (v) {
      case 'SAFE FOR YOU':
        return {
          badge: 'bg-emerald-950 text-emerald-100 border-emerald-800',
          scoreText: 'text-emerald-900',
          dot: 'bg-emerald-600',
        };
      case 'CAUTION':
        return {
          badge: 'bg-amber-950 text-amber-100 border-amber-800',
          scoreText: 'text-amber-900',
          dot: 'bg-amber-500',
        };
      case 'AVOID (VIOLATES PROFILE)':
      default:
        return {
          badge: 'bg-rose-950 text-rose-100 border-rose-800',
          scoreText: 'text-rose-900',
          dot: 'bg-rose-600',
        };
    }
  };

  const styles = getVerdictStyles(verdict);

  return (
    <div className="p-6 sm:p-8 bg-white border border-zinc-200 rounded-md">
      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
        <div>
          <span className="text-[11px] font-mono uppercase tracking-wider text-zinc-500 block">
            Audited Food Product
          </span>
          <h2 className="text-xl sm:text-2xl font-semibold text-zinc-900 tracking-tight mt-0.5">
            {productName}
          </h2>
        </div>

        {/* Verdict Badge */}
        <div
          className={`self-start px-3 py-1.5 border rounded-md text-xs font-semibold tracking-wider flex items-center gap-2 ${styles.badge}`}
        >
          <span className={`w-2 h-2 rounded-full ${styles.dot}`}></span>
          {verdict}
        </div>
      </div>

      <div className="mt-6 grid grid-cols-1 sm:grid-cols-4 gap-6 pt-6 border-t border-zinc-100">
        {/* Health Score */}
        <div className="sm:col-span-1 border-r-0 sm:border-r border-zinc-100 pr-4">
          <div className="text-[11px] font-mono uppercase tracking-wider text-zinc-500">
            Health Score
          </div>
          <div className="text-4xl font-semibold font-mono tracking-tight text-zinc-900 mt-1">
            {healthScore}
            <span className="text-base text-zinc-400 font-normal">/100</span>
          </div>
          <div className="text-[11px] text-zinc-500 mt-1 font-light">
            {healthScore < 40 ? 'Ultra-processed hazard' : healthScore < 70 ? 'Moderate nutritional quality' : 'Clean / Whole food'}
          </div>
        </div>

        {/* Simple Summary */}
        <div className="sm:col-span-3">
          <div className="text-[11px] font-mono uppercase tracking-wider text-zinc-500">
            Forensic Layperson Summary
          </div>
          <p className="text-xs sm:text-sm text-zinc-700 mt-1 leading-relaxed font-light">
            {summary}
          </p>
        </div>
      </div>
    </div>
  );
};
