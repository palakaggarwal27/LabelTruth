"use client";

import React from 'react';
import { HealthierAlternative } from '@/types';
import { Sparkles } from 'lucide-react';

interface AlternativeCardProps {
  alternative: HealthierAlternative;
}

export const AlternativeCard: React.FC<AlternativeCardProps> = ({ alternative }) => {
  return (
    <div className="p-6 sm:p-8 bg-zinc-900 text-white rounded-md border border-zinc-800">
      <div className="flex items-center gap-2 text-xs font-mono uppercase tracking-wider text-emerald-400 mb-2">
        <Sparkles className="w-4 h-4" />
        <span>Personalized Clean Swap Recommendation</span>
      </div>

      <h3 className="text-lg sm:text-xl font-semibold tracking-tight text-white">
        {alternative.name}
      </h3>

      <div className="mt-4 grid grid-cols-1 sm:grid-cols-3 gap-4 pt-4 border-t border-zinc-800">
        <div>
          <div className="text-[11px] font-mono text-zinc-400 uppercase tracking-wider">
            Key Health Benefit
          </div>
          <p className="text-xs text-zinc-200 mt-1 font-light leading-relaxed">
            {alternative.key_benefit}
          </p>
        </div>

        <div>
          <div className="text-[11px] font-mono text-zinc-400 uppercase tracking-wider">
            Price Comparison
          </div>
          <p className="text-xs text-zinc-200 mt-1 font-light leading-relaxed">
            {alternative.price_comparison}
          </p>
        </div>

        <div>
          <div className="text-[11px] font-mono text-zinc-400 uppercase tracking-wider">
            Why It Fits Your Profile
          </div>
          <p className="text-xs text-zinc-200 mt-1 font-light leading-relaxed">
            {alternative.personalized_fit}
          </p>
        </div>
      </div>
    </div>
  );
};
