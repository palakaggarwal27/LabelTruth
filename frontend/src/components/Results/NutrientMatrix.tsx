"use client";

import React from 'react';
import { NutrientIntegrityMatrix } from '@/types';
import { Activity, AlertTriangle, XCircle, CheckCircle2 } from 'lucide-react';

interface NutrientMatrixProps {
  matrix?: NutrientIntegrityMatrix;
}

export const NutrientMatrix: React.FC<NutrientMatrixProps> = ({ matrix }) => {
  if (!matrix) return null;

  const protein = matrix.protein;
  const claims = matrix.claims_matrix || [];

  return (
    <div className="bg-white border border-zinc-200 rounded-md p-6 space-y-6">
      <div>
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-zinc-900" />
          <h3 className="text-sm font-semibold text-zinc-900">
            Nutrient Integrity & Bioavailability Audit
          </h3>
        </div>
        <p className="text-xs text-zinc-500 mt-0.5">
          Calculates actual usable bioavailable protein (PDCAAS), fiber authenticity, and uncovers hidden sugars & fats.
        </p>
      </div>

      {/* Protein reality */}
      {protein && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 p-4 bg-zinc-50 rounded-md border border-zinc-200">
          <div>
            <div className="text-[10px] uppercase font-mono text-zinc-500">Declared Protein</div>
            <div className="text-base font-bold text-zinc-900 mt-0.5">{protein.declared_protein_g}g</div>
          </div>
          <div>
            <div className="text-[10px] uppercase font-mono text-zinc-500">Usable Protein (PDCAAS)</div>
            <div className="text-base font-bold text-emerald-700 mt-0.5">{protein.usable_protein_g}g</div>
            <span className="text-[10px] text-zinc-400">Score: {protein.pdcaas_score}</span>
          </div>
          <div>
            <div className="text-[10px] uppercase font-mono text-zinc-500">Protein Calorie %</div>
            <div className="text-base font-bold text-zinc-900 mt-0.5">{protein.protein_to_calorie_percent}%</div>
          </div>
          <div>
            <div className="text-[10px] uppercase font-mono text-zinc-500">Amino Spiking Risk</div>
            <div className={`text-xs font-bold mt-1.5 ${protein.amino_spiking_risk ? 'text-rose-700' : 'text-emerald-700'}`}>
              {protein.amino_spiking_risk ? 'HIGH RISK (Spiked)' : 'LOW (Clean)'}
            </div>
          </div>
        </div>
      )}

      {/* Fiber, Palm Oil, and Hidden Sugar Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
        <div className="p-3 border border-zinc-200 rounded-md bg-white">
          <span className="text-[10px] uppercase font-mono text-zinc-400 block mb-1">Fiber Quality</span>
          <span className="font-semibold text-zinc-900">{matrix.fiber_type || 'Whole Grain'}</span>
        </div>
        <div className="p-3 border border-zinc-200 rounded-md bg-white">
          <span className="text-[10px] uppercase font-mono text-zinc-400 block mb-1">Palm Oil Detection</span>
          <span className={`font-semibold ${matrix.palm_oil_present ? 'text-rose-700' : 'text-emerald-700'}`}>
            {matrix.palm_oil_present ? 'Present (Palmitic Acid Risk)' : 'None Detected'}
          </span>
        </div>
        <div className="p-3 border border-zinc-200 rounded-md bg-white">
          <span className="text-[10px] uppercase font-mono text-zinc-400 block mb-1">Hidden Sugars</span>
          <span className="font-medium text-zinc-800">
            {matrix.hidden_sugars_flagged && matrix.hidden_sugars_flagged.length > 0
              ? matrix.hidden_sugars_flagged.join(', ')
              : 'No Disguised Sugars'}
          </span>
        </div>
      </div>

      {/* Claim Verification Matrix */}
      {claims.length > 0 && (
        <div className="pt-4 border-t border-zinc-100">
          <span className="text-xs font-semibold uppercase tracking-wider text-zinc-700 block mb-3">
            Front-of-Pack Claim Reality Check
          </span>
          <div className="space-y-2">
            {claims.map((c, i) => {
              const isVerified = c.status === 'VERIFIED';
              const isMisleading = c.status === 'MISLEADING';
              return (
                <div key={i} className="p-3 rounded border border-zinc-200 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs">
                  <div className="flex items-center gap-2">
                    {isVerified ? (
                      <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                    ) : isMisleading ? (
                      <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
                    ) : (
                      <XCircle className="w-4 h-4 text-rose-600 shrink-0" />
                    )}
                    <div>
                      <span className="font-semibold text-zinc-900">&quot;{c.claim}&quot;</span>
                      <p className="text-[11px] text-zinc-600 font-light mt-0.5">{c.explanation}</p>
                    </div>
                  </div>
                  <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase self-start sm:self-auto border ${
                    isVerified ? 'bg-emerald-50 border-emerald-200 text-emerald-800' : isMisleading ? 'bg-amber-50 border-amber-200 text-amber-800' : 'bg-rose-50 border-rose-200 text-rose-800'
                  }`}>
                    {c.status}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
