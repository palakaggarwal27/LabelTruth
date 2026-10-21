"use client";

import React from 'react';
import { CitedStatCards } from '@/components/CitedStatCards';
import { LearningModules } from '@/components/LearningModules';
import { BookOpen } from 'lucide-react';
import Link from 'next/link';

export default function LiteracyHubPage() {
  return (
    <div className="min-h-screen bg-white">
      {/* Literacy Hub Header */}
      <div className="max-w-6xl mx-auto px-4 sm:px-6 pt-10 pb-6 border-b border-zinc-200">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-xs font-mono uppercase tracking-wider text-emerald-800 mb-1">
              <BookOpen className="w-4 h-4 text-emerald-600" />
              <span>National Consumer Intelligence & Forensic Directory</span>
            </div>
            <h1 className="text-3xl font-bold tracking-tight text-zinc-900">
              Food Literacy Hub & FSSAI Directory
            </h1>
            <p className="text-xs text-zinc-500 mt-1 max-w-2xl font-light">
              Grounded in primary research (N=51) and the National Macro Study (N=23,491+ LocalCircles / FSSAI). 
              Learn the exact regulatory rules, chemical aliases, and deceptive industrial tactics used on Indian packaging.
            </p>
          </div>
          <Link
            href="/scan"
            className="self-start sm:self-auto px-4 py-2 bg-zinc-900 hover:bg-zinc-800 text-white rounded text-xs font-semibold shadow-sm transition-colors"
          >
            Go to Scanner & Audit
          </Link>
        </div>
      </div>

      {/* Dual Survey Data Section */}
      <CitedStatCards />

      {/* Interactive Curriculum & Additive Directory */}
      <LearningModules />
    </div>
  );
}
