"use client";

import React from 'react';
import { HealthierAlternative } from '@/types';
import { Sparkles, ShoppingBag, ExternalLink } from 'lucide-react';
import { buildProductLink } from '@/utils/affiliate';

interface AlternativeCardProps {
  alternative: HealthierAlternative;
  cleanAlternatives?: HealthierAlternative[];
}

export const AlternativeCard: React.FC<AlternativeCardProps> = ({ alternative, cleanAlternatives }) => {
  const allAlternatives = cleanAlternatives && cleanAlternatives.length > 0 
    ? cleanAlternatives 
    : [alternative];

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 text-xs font-mono uppercase tracking-wider text-emerald-800">
        <Sparkles className="w-4 h-4 text-emerald-600" />
        <span className="font-semibold">Clean Whole-Food Alternatives (Quick-Commerce Available)</span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {allAlternatives.map((alt, idx) => {
          const buyUrl = buildProductLink(alt.name, alt.store_url);
          return (
            <div
              key={idx}
              className="p-5 bg-white border border-zinc-200 hover:border-zinc-400 rounded-md transition-all flex flex-col justify-between"
            >
              <div>
                <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-emerald-50 text-emerald-800 border border-emerald-200 font-semibold">
                  Clean Swap #{idx + 1}
                </span>
                <h4 className="text-sm font-semibold text-zinc-900 mt-2">
                  {alt.name}
                </h4>
                <p className="text-xs text-zinc-600 mt-1 font-light leading-relaxed">
                  {alt.key_benefit}
                </p>
                <div className="mt-3 pt-3 border-t border-zinc-100 text-[11px] space-y-1">
                  <div className="text-zinc-500">
                    <span className="font-medium text-zinc-700">Price:</span> {alt.price_comparison}
                  </div>
                  <div className="text-zinc-500">
                    <span className="font-medium text-zinc-700">Profile Fit:</span> {alt.personalized_fit}
                  </div>
                </div>
              </div>

              <a
                href={buyUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="mt-4 w-full py-2 px-3 bg-zinc-900 hover:bg-zinc-800 text-white rounded text-xs font-semibold flex items-center justify-center gap-1.5 transition-colors"
              >
                <ShoppingBag className="w-3.5 h-3.5" />
                <span>Find on Quick-Commerce</span>
                <ExternalLink className="w-3 h-3 text-zinc-400 ml-0.5" />
              </a>
            </div>
          );
        })}
      </div>
    </div>
  );
};
