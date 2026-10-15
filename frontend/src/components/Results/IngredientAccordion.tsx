"use client";

import React, { useState } from 'react';
import { IngredientItem } from '@/types';
import { AlertCircle } from 'lucide-react';

interface IngredientAccordionProps {
  ingredients: IngredientItem[];
}

export const IngredientAccordion: React.FC<IngredientAccordionProps> = ({ ingredients }) => {
  const [filter, setFilter] = useState<'ALL' | 'HIGH' | 'MEDIUM' | 'LOW'>('ALL');

  const filtered = ingredients.filter((item) => {
    if (filter === 'ALL') return true;
    return item.concern_level === filter;
  });

  return (
    <div className="bg-white border border-zinc-200 rounded-md p-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-zinc-100 gap-3">
        <div>
          <h3 className="text-sm font-semibold text-zinc-900">
            Forensic Ingredient Breakdown
          </h3>
          <p className="text-xs text-zinc-500 mt-0.5">
            Analyzed in accordance with FSSAI Regulation 5(2)(b) descending weight order.
          </p>
        </div>

        {/* Filter buttons */}
        <div className="flex items-center gap-1.5 text-xs flex-wrap">
          <button
            onClick={() => setFilter('ALL')}
            className={`px-2.5 py-1 rounded-md border text-xs font-medium ${
              filter === 'ALL'
                ? 'bg-zinc-900 text-white border-zinc-900'
                : 'bg-white text-zinc-600 border-zinc-200 hover:bg-zinc-50'
            }`}
          >
            All ({ingredients.length})
          </button>
          <button
            onClick={() => setFilter('HIGH')}
            className={`px-2.5 py-1 rounded-md border text-xs font-medium ${
              filter === 'HIGH'
                ? 'bg-rose-900 text-white border-rose-900'
                : 'bg-white text-zinc-600 border-zinc-200 hover:bg-zinc-50'
            }`}
          >
            High Concern ({ingredients.filter((x) => x.concern_level === 'HIGH').length})
          </button>
          <button
            onClick={() => setFilter('MEDIUM')}
            className={`px-2.5 py-1 rounded-md border text-xs font-medium ${
              filter === 'MEDIUM'
                ? 'bg-amber-800 text-white border-amber-800'
                : 'bg-white text-zinc-600 border-zinc-200 hover:bg-zinc-50'
            }`}
          >
            Medium ({ingredients.filter((x) => x.concern_level === 'MEDIUM').length})
          </button>
        </div>
      </div>

      <div className="divide-y divide-zinc-100 mt-2">
        {filtered.map((item, idx) => (
          <div key={idx} className="py-3 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div className="sm:max-w-md">
              <div className="flex items-center gap-2">
                <span className="text-xs font-semibold text-zinc-900">
                  {item.ingredient}
                </span>
                <span
                  className={`text-[10px] font-mono px-1.5 py-0.5 rounded border ${
                    item.concern_level === 'HIGH'
                      ? 'bg-rose-50 border-rose-200 text-rose-800 font-semibold'
                      : item.concern_level === 'MEDIUM'
                      ? 'bg-amber-50 border-amber-200 text-amber-800 font-semibold'
                      : 'bg-zinc-50 border-zinc-200 text-zinc-600'
                  }`}
                >
                  {item.concern_level}
                </span>
              </div>
              <div className="text-[11px] text-zinc-500 mt-0.5">
                Function: {item.purpose}
              </div>
            </div>

            {item.personalized_warning && (
              <div className="text-xs text-zinc-700 bg-zinc-50 p-2 rounded-md sm:max-w-sm flex items-start gap-1.5">
                <AlertCircle className="w-3.5 h-3.5 text-zinc-500 shrink-0 mt-0.5" />
                <span className="text-[11px] leading-snug font-light">
                  {item.personalized_warning}
                </span>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
