"use client";

import React, { useState, useEffect } from 'react';
import { Sparkles, CheckCircle2, Loader2, ShieldCheck, FileSearch, Dna, AlertTriangle } from 'lucide-react';

interface LiveInspectionStreamProps {
  title?: string;
  subtitle?: string;
  isCart?: boolean;
}

export const LiveInspectionStream: React.FC<LiveInspectionStreamProps> = ({
  title = "Forensic Nutritional Audit in Progress",
  subtitle = "Evaluating ingredients against FSSAI 2020 regulations and ICMR-NIN guidelines",
  isCart = false
}) => {
  const [elapsed, setElapsed] = useState(0.0);
  const [activeStep, setActiveStep] = useState(0);

  // Timer running every 100ms
  useEffect(() => {
    const start = Date.now();
    const interval = setInterval(() => {
      const sec = (Date.now() - start) / 1000;
      setElapsed(Number(sec.toFixed(1)));
      if (sec >= 4.2) setActiveStep(4);
      else if (sec >= 3.0) setActiveStep(3);
      else if (sec >= 1.8) setActiveStep(2);
      else if (sec >= 0.7) setActiveStep(1);
      else setActiveStep(0);
    }, 100);

    return () => clearInterval(interval);
  }, []);

  const singleScanSteps = [
    {
      label: "Visual and Packaging Panel Isolation",
      desc: "Detecting Front-of-Pack hero claims and Back-of-Pack ingredient panels",
      icon: FileSearch,
      log: "Detected packaging orientation. Isolate text matrix."
    },
    {
      label: "Descending Weight Order Audit (FSSAI 5(2)(b))",
      desc: "Verifying true ingredient hierarchy and exposing disguised split sugars",
      icon: ShieldCheck,
      log: "Scanning sequence: sugar, palm oil, refined flour weights parsed."
    },
    {
      label: "Chemical Additive and INS Code Screening",
      desc: "Cross-referencing synthetic dyes, preservatives and excitotoxin numbers",
      icon: AlertTriangle,
      log: "Auditing INS 150d, INS 621, INS 211, artificial sweeteners."
    },
    {
      label: "Regulatory Matrix and Nutrition Score Calculation",
      desc: "Computing piecewise mathematical score via ICMR-NIN 2024 thresholds",
      icon: Sparkles,
      log: "Calculating energy density, saturated fat, and sodium deductions."
    },
    {
      label: "Personalized Metabolic Profile Cross-Check",
      desc: "Tailoring verdict against your active health profile and contraindications",
      icon: Dna,
      log: "Cross-referencing contraindications and allergy triggers."
    }
  ];

  const cartScanSteps = [
    {
      label: "Store and Quick-Commerce Receipt Extraction",
      desc: "Parsing grocery screenshot text and isolating all food item titles",
      icon: FileSearch,
      log: "Isolating product catalog titles and quantities..."
    },
    {
      label: "Live Back-of-Pack Label Retrieval",
      desc: "Fetching authentic packaging panels via TinyFish Search and Fetch",
      icon: ShieldCheck,
      log: "Retrieved packaging ingredients for cart items."
    },
    {
      label: "Simultaneous FSSAI and Ultra-Processing Screening",
      desc: "Screening each cart item for palm oil, maltodextrin and chemical additives",
      icon: AlertTriangle,
      log: "Calculating individual item health scores..."
    },
    {
      label: "Clean Brand Alternative Discovery",
      desc: "Auditing cleaner Indian challenger brand swaps in your pincode",
      icon: Sparkles,
      log: "Finding zero-palm-oil, whole-food alternatives with higher scores..."
    },
    {
      label: "Synthesizing Cart Transformation Matrix",
      desc: "Projecting total cart score boost and red-flag additives eliminated",
      icon: Dna,
      log: "Finalizing cart health score upgrade..."
    }
  ];

  const steps = isCart ? cartScanSteps : singleScanSteps;

  return (
    <div className="mt-6 border border-zinc-200 bg-white rounded-lg shadow-sm overflow-hidden animate-in fade-in duration-300">
      {/* Stream Header */}
      <div className="bg-zinc-900 text-white px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <span className="relative flex h-2.5 w-2.5">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
          </span>
          <div>
            <h4 className="text-xs font-semibold tracking-wide flex items-center gap-1.5">
              <span>{title}</span>
            </h4>
            <p className="text-[10px] text-zinc-400 font-mono hidden sm:block mt-0.5">
              {subtitle}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 bg-zinc-800 border border-zinc-700/60 px-2.5 py-1 rounded text-xs font-mono text-emerald-400">
          <Loader2 className="w-3.5 h-3.5 animate-spin text-emerald-400" />
          <span>{elapsed.toFixed(1)}s</span>
        </div>
      </div>

      {/* Progressive Step Progress */}
      <div className="p-4 sm:p-5 space-y-3.5 bg-zinc-50/50">
        {steps.map((st, idx) => {
          const StepIcon = st.icon;
          const isDone = activeStep > idx;
          const isCurrent = activeStep === idx;

          return (
            <div
              key={idx}
              className={`flex items-start gap-3 p-2.5 rounded-md transition-all duration-300 ${
                isCurrent
                  ? 'bg-white border border-emerald-300 shadow-sm'
                  : isDone
                  ? 'bg-zinc-100/60 border border-zinc-200/60 opacity-90'
                  : 'opacity-40'
              }`}
            >
              <div className="mt-0.5 shrink-0">
                {isDone ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                ) : isCurrent ? (
                  <Loader2 className="w-4 h-4 text-emerald-600 animate-spin" />
                ) : (
                  <StepIcon className="w-4 h-4 text-zinc-400" />
                )}
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-2">
                  <span className={`text-xs font-semibold ${isCurrent ? 'text-zinc-900 font-bold' : isDone ? 'text-zinc-700' : 'text-zinc-500'}`}>
                    {st.label}
                  </span>
                  {isDone && (
                    <span className="text-[10px] font-mono text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded font-semibold border border-emerald-200">
                      COMPLETE
                    </span>
                  )}
                  {isCurrent && (
                    <span className="text-[10px] font-mono text-emerald-700 bg-emerald-100/80 px-1.5 py-0.5 rounded font-semibold animate-pulse">
                      PROCESSING
                    </span>
                  )}
                </div>
                <p className="text-[11px] text-zinc-500 mt-0.5 line-clamp-1">
                  {st.desc}
                </p>
              </div>
            </div>
          );
        })}
      </div>

      {/* Simulated Live Telemetry Stream (ChatGPT/Gemini Style) */}
      <div className="bg-zinc-950 px-4 py-2.5 text-[11px] font-mono text-zinc-400 border-t border-zinc-800 flex items-center gap-2">
        <span className="text-emerald-400 font-bold">&gt;</span>
        <span className="truncate text-zinc-300 animate-pulse">
          {steps[Math.min(activeStep, steps.length - 1)].log}
        </span>
      </div>

      {/* Shimmer Result Skeleton Preview */}
      <div className="p-4 bg-white border-t border-zinc-200/80 space-y-3">
        <div className="text-[10px] font-mono uppercase tracking-wider text-zinc-400 font-medium">
          Forensic Report Structure Materializing:
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div className="h-16 rounded bg-gradient-to-r from-zinc-100 via-zinc-200 to-zinc-100 animate-pulse border border-zinc-200" />
          <div className="h-16 rounded bg-gradient-to-r from-zinc-100 via-zinc-200 to-zinc-100 animate-pulse border border-zinc-200" />
          <div className="h-16 rounded bg-gradient-to-r from-zinc-100 via-zinc-200 to-zinc-100 animate-pulse border border-zinc-200" />
        </div>
      </div>
    </div>
  );
};
