"use client";

import React, { useEffect, useState } from 'react';
import { PresetProduct } from '@/types';
import { fetchPresets } from '@/lib/api';

interface PresetBarProps {
  onSelectPreset: (preset: PresetProduct) => void;
  loading: boolean;
}

export const PresetBar: React.FC<PresetBarProps> = ({ onSelectPreset, loading }) => {
  const [presets, setPresets] = useState<PresetProduct[]>([]);

  useEffect(() => {
    fetchPresets()
      .then((data) => setPresets(data))
      .catch((err) => console.warn('Using embedded fallback presets:', err));
  }, []);

  if (presets.length === 0) return null;

  return (
    <div className="mt-6 pt-6 border-t border-zinc-200">
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-mono uppercase tracking-wider text-zinc-500">
          Rapid Demo Testing Presets
        </span>
        <span className="text-[11px] text-zinc-400 font-mono">MSIT Report Appendix C</span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
        {presets.map((p) => (
          <button
            key={p.id}
            disabled={loading}
            onClick={() => onSelectPreset(p)}
            className="text-left p-3 border border-zinc-200 hover:border-zinc-400 bg-white rounded-md transition-colors disabled:opacity-50 flex flex-col justify-between"
          >
            <div>
              <div className="text-xs font-semibold text-zinc-900 leading-tight">
                {p.title}
              </div>
              <div className="text-[11px] text-zinc-500 mt-1 font-light line-clamp-1">
                {p.subtitle}
              </div>
            </div>
            <div className="mt-2 text-[10px] font-mono text-zinc-400 uppercase">
              Click to evaluate
            </div>
          </button>
        ))}
      </div>
    </div>
  );
};
