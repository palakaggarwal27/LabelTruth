import React from 'react';
import { NutrientIntegrityMatrix, NutritionCardAnalysis } from '@/types';
import { Activity, AlertTriangle, XCircle, CheckCircle2, TableProperties, ShieldAlert } from 'lucide-react';

interface NutrientMatrixProps {
  matrix?: NutrientIntegrityMatrix;
  nutritionCard?: NutritionCardAnalysis;
}

export const NutrientMatrix: React.FC<NutrientMatrixProps> = ({ matrix, nutritionCard }) => {
  if (!matrix && !nutritionCard) return null;

  const protein = matrix?.protein;
  const claims = matrix?.claims_matrix || [];

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

      {/* Detailed Nutrition Card Table Breakdown */}
      {nutritionCard && (
        <div className="p-4 bg-zinc-50 rounded-md border border-zinc-200 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-xs font-semibold text-zinc-900">
              <TableProperties className="w-4 h-4 text-zinc-700" />
              <span>Decoded Nutrition Facts Panel</span>
            </div>
            <span className="text-[11px] font-mono text-zinc-500">
              Serving: {nutritionCard.serving_size || '100g'}
            </span>
          </div>

          {/* Quick macro highlights */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
            <div className="p-2.5 bg-white border border-zinc-200 rounded">
              <span className="text-[10px] text-zinc-400 font-mono block">Energy</span>
              <span className="font-bold text-zinc-900">{nutritionCard.calories_kcal || 0} kcal</span>
            </div>
            <div className="p-2.5 bg-white border border-zinc-200 rounded">
              <span className="text-[10px] text-zinc-400 font-mono block">Total Fat</span>
              <span className="font-bold text-zinc-900">{nutritionCard.total_fat_g || 0}g</span>
            </div>
            <div className="p-2.5 bg-white border border-zinc-200 rounded">
              <span className="text-[10px] text-zinc-400 font-mono block">Added Sugar</span>
              <span className={`font-bold ${nutritionCard.added_sugars_g > 10 ? 'text-rose-700' : 'text-zinc-900'}`}>
                {nutritionCard.added_sugars_g || 0}g
              </span>
            </div>
            <div className="p-2.5 bg-white border border-zinc-200 rounded">
              <span className="text-[10px] text-zinc-400 font-mono block">Sodium</span>
              <span className={`font-bold ${nutritionCard.sodium_mg > 400 ? 'text-amber-700' : 'text-zinc-900'}`}>
                {nutritionCard.sodium_mg || 0}mg
              </span>
            </div>
          </div>

          {/* Line by line breakdown table */}
          {nutritionCard.breakdown && nutritionCard.breakdown.length > 0 && (
            <div className="mt-2 overflow-x-auto">
              <table className="w-full text-left text-xs border border-zinc-200 bg-white rounded">
                <thead>
                  <tr className="bg-zinc-100/70 border-b border-zinc-200 text-[10px] uppercase font-mono text-zinc-600">
                    <th className="py-2 px-3">Nutrient</th>
                    <th className="py-2 px-3">Amount (100g)</th>
                    <th className="py-2 px-3">% RDA / DV</th>
                    <th className="py-2 px-3">Clinical Evaluation</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-100">
                  {nutritionCard.breakdown.map((row, idx) => {
                    const text = row.clinical_evaluation || '';
                    const lower = text.toLowerCase();
                    const isDanger = lower.includes('exceed') || lower.includes('very high') || lower.includes('dramatically') || lower.includes('hyper') || lower.includes('extreme') || lower.includes('excessive') || lower.includes('stripped') || lower.includes('cheap');
                    const isPositive = !isDanger && (lower.includes('zero') || lower.includes('clean') || lower.includes('wholesome') || lower.includes('bioavailable') || lower.includes('protective') || lower.includes('pure') || lower.includes('natural') || lower.includes('rich in') || lower.includes('balanced') || lower.includes('safe') || lower.includes('optimal') || lower.includes('within normal') || lower.includes('standard range') || (!lower.includes('high') && !lower.includes('elevated') && !lower.includes('moderate')));

                    return (
                      <tr key={idx} className="hover:bg-zinc-50/60">
                        <td className="py-2 px-3 font-medium text-zinc-900">{row.nutrient}</td>
                        <td className="py-2 px-3 font-mono text-zinc-700">{row.amount_per_100g}</td>
                        <td className="py-2 px-3 font-mono text-zinc-500">{row.daily_value_percent || '—'}</td>
                        <td className="py-2 px-3 text-[11px] font-light flex items-center gap-1.5">
                          {text ? (
                            isPositive ? (
                              <>
                                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                                <span className="text-emerald-800 font-medium">{text}</span>
                              </>
                            ) : isDanger ? (
                              <>
                                <AlertTriangle className="w-3.5 h-3.5 text-rose-600 shrink-0" />
                                <span className="text-rose-800 font-medium">{text}</span>
                              </>
                            ) : (
                              <>
                                <ShieldAlert className="w-3.5 h-3.5 text-amber-600 shrink-0" />
                                <span className="text-amber-800 font-medium">{text}</span>
                              </>
                            )
                          ) : (
                            <>
                              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                              <span className="text-emerald-700">Within normal standard range</span>
                            </>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

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
      {matrix && (
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
      )}

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
