"use client";

import React from 'react';
import { ToggleLeft, ToggleRight, Sparkles } from 'lucide-react';

interface DemoToggleProps {
  demoMode: boolean;
  onToggle: (val: boolean) => void;
  onSelectTier?: (tier: string) => void;
}

export const DemoToggle: React.FC<DemoToggleProps> = ({ demoMode, onToggle, onSelectTier }) => {
  const tiers = [
    { id: 'very_low', label: "Lay's Magic Masala", color: 'bg-rose-100 text-rose-800 border-rose-300' },
    { id: 'low', label: 'English Oven Bread', color: 'bg-orange-100 text-orange-800 border-orange-300' },
    { id: 'moderate', label: "D'lecta Mozzarella", color: 'bg-amber-100 text-amber-800 border-amber-300' },
    { id: 'high', label: 'Epigamia Greek Yogurt', color: 'bg-emerald-100 text-emerald-800 border-emerald-300' },
    { id: 'very_high', label: 'Organic Rolled Oats', color: 'bg-green-100 text-green-900 border-green-300' },
  ];

  return (
    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 p-3 bg-zinc-100/80 border border-zinc-200 rounded-md">
      <div className="flex items-center gap-2">
        <button
          onClick={() => onToggle(!demoMode)}
          className="flex items-center gap-1.5 text-xs font-semibold text-zinc-900 hover:text-black transition-colors"
        >
          {demoMode ? (
            <ToggleRight className="w-5 h-5 text-emerald-600" />
          ) : (
            <ToggleLeft className="w-5 h-5 text-zinc-400" />
          )}
          <span>Offline DEMO Mode (Zero Credits Used)</span>
        </button>
        {demoMode && (
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-50 text-emerald-800 border border-emerald-200 font-semibold flex items-center gap-1">
            <Sparkles className="w-3 h-3 text-emerald-600" />
            Active (&lt;100ms)
          </span>
        )}
      </div>

      {demoMode && onSelectTier && (
        <div className="flex items-center gap-1.5 flex-wrap">
          <span className="text-[11px] font-mono text-zinc-500">5 Tiers:</span>
          {tiers.map((t) => (
            <button
              key={t.id}
              onClick={() => onSelectTier(t.id)}
              className={`px-2 py-0.5 rounded text-[10px] font-mono font-medium border ${t.color} hover:opacity-80 transition-opacity`}
            >
              {t.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};
