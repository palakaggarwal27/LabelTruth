"use client";

import React from 'react';
import { AlertOctagon, Scale } from 'lucide-react';

interface RedFlagsCardProps {
  deceptions: string[];
  violations: string[];
}

export const RedFlagsCard: React.FC<RedFlagsCardProps> = ({ deceptions, violations }) => {
  if (deceptions.length === 0 && violations.length === 0) return null;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {/* Front-of-Pack Deceptions */}
      {deceptions.length > 0 && (
        <div className="p-6 bg-white border border-rose-200 rounded-md">
          <div className="flex items-center gap-2 text-rose-900 text-xs font-semibold uppercase tracking-wider mb-3">
            <AlertOctagon className="w-4 h-4 text-rose-700" />
            <span>Misleading Front Claims Flagged</span>
          </div>
          <ul className="space-y-2">
            {deceptions.map((claim, idx) => (
              <li key={idx} className="flex items-start gap-2 text-xs text-zinc-700 leading-relaxed font-light">
                <span className="w-1.5 h-1.5 rounded-full bg-rose-600 mt-1.5 shrink-0"></span>
                <span>{claim}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* FSSAI Regulatory Violations / Loopholes */}
      {violations.length > 0 && (
        <div className="p-6 bg-white border border-zinc-200 rounded-md">
          <div className="flex items-center gap-2 text-zinc-900 text-xs font-semibold uppercase tracking-wider mb-3">
            <Scale className="w-4 h-4 text-zinc-700" />
            <span>FSSAI Violations & Loopholes</span>
          </div>
          <ul className="space-y-2">
            {violations.map((violation, idx) => (
              <li key={idx} className="flex items-start gap-2 text-xs text-zinc-700 leading-relaxed font-light">
                <span className="w-1.5 h-1.5 rounded-full bg-zinc-500 mt-1.5 shrink-0"></span>
                <span>{violation}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};
