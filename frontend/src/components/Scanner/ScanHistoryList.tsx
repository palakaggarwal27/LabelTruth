"use client";

import React from 'react';
import { ScannedHistoryItem } from '@/types';
import { Clock, Trash2, ArrowUpRight, ShieldAlert } from 'lucide-react';

interface ScanHistoryListProps {
  history: ScannedHistoryItem[];
  onSelect: (item: ScannedHistoryItem) => void;
  onClear: () => void;
}

export const ScanHistoryList: React.FC<ScanHistoryListProps> = ({
  history,
  onSelect,
  onClear,
}) => {
  if (history.length === 0) {
    return (
      <div className="bg-white border border-zinc-200 rounded-md p-10 text-center">
        <Clock className="w-8 h-8 text-zinc-300 mx-auto mb-2" />
        <h3 className="text-sm font-semibold text-zinc-900">No Scanned Products Yet</h3>
        <p className="text-xs text-zinc-500 mt-1 max-w-sm mx-auto">
          Every product label you audit is automatically saved to this device so you can revisit clinical insights and AI breakdowns anytime.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between pb-2 border-b border-zinc-200">
        <div>
          <h2 className="text-sm font-semibold text-zinc-900">
            Previously Scanned Products ({history.length})
          </h2>
          <p className="text-xs text-zinc-500">
            Stored locally on your device with complete ingredient & regulatory audit insights.
          </p>
        </div>
        <button
          onClick={onClear}
          className="text-xs text-zinc-500 hover:text-rose-700 flex items-center gap-1 transition-colors px-2 py-1 rounded border border-zinc-200 hover:border-rose-200"
          title="Clear all local scan history"
        >
          <Trash2 className="w-3.5 h-3.5" />
          <span>Clear History</span>
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {history.map((item) => {
          const dateStr = new Date(item.timestamp).toLocaleDateString(undefined, {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
          });

          const isViolated = item.result.personalized_verdict.includes('AVOID');
          const isCaution = item.result.personalized_verdict.includes('CAUTION');

          return (
            <div
              key={item.id}
              onClick={() => onSelect(item)}
              className="group bg-white border border-zinc-200 hover:border-zinc-400 rounded-md p-4 transition-all cursor-pointer flex flex-col justify-between"
            >
              <div>
                <div className="flex items-start justify-between gap-2 mb-2">
                  <div className="flex items-center gap-2">
                    {item.image_preview ? (
                      /* eslint-disable-next-line @next/next/no-img-element */
                      <img
                        src={item.image_preview}
                        alt="Label thumbnail"
                        className="w-12 h-12 object-cover rounded border border-zinc-200 shrink-0"
                      />
                    ) : (
                      <div className="w-12 h-12 bg-zinc-100 rounded border border-zinc-200 flex items-center justify-center text-[10px] font-mono text-zinc-400 shrink-0">
                        LABEL
                      </div>
                    )}
                    <div>
                      <h3 className="text-xs font-semibold text-zinc-900 group-hover:text-black line-clamp-1">
                        {item.result.product_name}
                      </h3>
                      <span className="text-[10px] text-zinc-400 flex items-center gap-1 mt-0.5">
                        <Clock className="w-3 h-3" />
                        {dateStr}
                      </span>
                    </div>
                  </div>

                  <div className="flex flex-col items-end shrink-0">
                    <span className="text-xs font-mono font-bold text-zinc-900">
                      {item.result.health_score}/100
                    </span>
                    <span
                      className={`text-[9px] px-1.5 py-0.5 rounded font-mono font-semibold uppercase mt-1 border ${
                        isViolated
                          ? 'bg-rose-50 border-rose-200 text-rose-800'
                          : isCaution
                          ? 'bg-amber-50 border-amber-200 text-amber-800'
                          : 'bg-emerald-50 border-emerald-200 text-emerald-800'
                      }`}
                    >
                      {item.result.personalized_verdict}
                    </span>
                  </div>
                </div>

                <p className="text-[11px] text-zinc-600 line-clamp-2 mt-2 font-light">
                  {item.result.simple_summary}
                </p>

                {item.result.fssai_violations.length > 0 && (
                  <div className="mt-2 text-[10px] text-rose-800 bg-rose-50/70 border border-rose-200/60 p-1.5 rounded flex items-center gap-1">
                    <ShieldAlert className="w-3 h-3 shrink-0" />
                    <span className="truncate">
                      FSSAI Flag: {item.result.fssai_violations[0]}
                    </span>
                  </div>
                )}
              </div>

              <div className="mt-3 pt-2.5 border-t border-zinc-100 flex items-center justify-between text-[11px]">
                <span className="text-zinc-500 font-mono">
                  {item.result.ingredient_breakdown.length} ingredients analyzed
                </span>
                <span className="text-zinc-900 font-medium group-hover:underline flex items-center gap-1">
                  View Full Insights
                  <ArrowUpRight className="w-3 h-3" />
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
