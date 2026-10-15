"use client";

import React from 'react';
import Link from 'next/link';
import { ArrowRight, ScanLine } from 'lucide-react';

export const HeroBanner: React.FC = () => {
  return (
    <section className="border-b border-zinc-200 bg-white py-12 sm:py-16">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">
        <div className="max-w-3xl">
          <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-md border border-zinc-200 bg-zinc-50 text-zinc-700 text-xs font-mono mb-4">
            <span className="w-2 h-2 rounded-full bg-emerald-600 inline-block"></span>
            LabelTruth — FSSAI Regulatory Audit & Consumer Protection (N=51)
          </div>

          <h1 className="text-3xl sm:text-5xl font-semibold text-zinc-900 tracking-tight leading-[1.15]">
            Transparent Food Labeling. <br />
            Empowering Consumer Truth.
          </h1>

          <p className="mt-4 text-base sm:text-lg text-zinc-600 leading-relaxed font-light">
            In our primary research study across 51 Indian consumers, 82.4% relied on misleading front-of-pack claims
            or legacy brand trust. LabelTruth integrates clinical dietary science, FSSAI 2020 regulatory standards,
            and multimodal AI to decode what is truly inside your food.
          </p>

          <div className="mt-8 flex flex-wrap gap-3">
            <Link
              href="/scan"
              className="px-5 py-2.5 bg-zinc-900 hover:bg-zinc-800 text-white rounded-md text-sm font-semibold flex items-center gap-2 transition-colors"
            >
              <ScanLine className="w-4 h-4" />
              <span>Launch Label Scanner</span>
              <ArrowRight className="w-4 h-4 ml-1" />
            </Link>

            <a
              href="#evidence-stats"
              className="px-5 py-2.5 bg-zinc-50 hover:bg-zinc-100 border border-zinc-200 text-zinc-800 rounded-md text-sm font-medium transition-colors"
            >
              View Research Evidence
            </a>
          </div>
        </div>
      </div>
    </section>
  );
};
