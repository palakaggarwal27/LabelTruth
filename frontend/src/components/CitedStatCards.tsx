"use client";

import React, { useEffect, useState } from 'react';
import { StatCardData } from '@/types';
import { fetchStats } from '@/lib/api';
import { Globe2, Users } from 'lucide-react';

const FALLBACK_STATS: StatCardData[] = [
  {
    stat: '82.4%',
    title: 'Rely on Front Claims or Legacy',
    description: '31.4% are driven by front buzzwords (No Added Sugar, High Protein) and 51.0% by legacy brand trust. Only 13.7% turn the pack over to read ingredients.',
    source: 'Primary Survey Q1 (N=51)',
  },
  {
    stat: '47.1%',
    title: 'Completely Blind to Jargon',
    description: 'Nearly half of urban consumers cannot identify terms like Maltodextrin, INS 150d, HFCS, or RDA %, finding them akin to indecipherable laboratory jargon.',
    source: 'Primary Survey Q5 (N=51)',
  },
  {
    stat: '52.9%',
    title: 'Unaware of Weight Order Principle',
    description: 'More than half do not know FSSAI Regulation 5(2)(b) mandates ingredients in descending order of weight. Most assume alphabetical or random placement.',
    source: 'Primary Survey Q6 (N=51)',
  },
  {
    stat: '68.6%',
    title: 'Misled by "Sugar-Free" Marketing',
    description: '23.5% believe Sugar-Free is safe for diabetics, while 21.6% believe it uses safe fruit juice, unaware of high-GI bulking agents like Maltodextrin (GI 105-110).',
    source: 'Primary Survey Q4 (N=51)',
  },
  {
    stat: '70.6%',
    title: 'Frozen Dessert Mistaken for Ice Cream',
    description: 'Chose Kwality Walls as preferred ice cream despite it being legally a Frozen Dessert containing up to 10.2% edible vegetable/palm oil.',
    source: 'Primary Survey Q9 (N=51)',
  },
  {
    stat: '92.2%',
    title: 'Demand Front Warning Labels',
    description: '66.7% would stop buying junk food or switch to a green alternative if a Red Dot / Stop Sign was enforced, while 25.5% would exercise higher caution.',
    source: 'Primary Survey Q8 (N=51)',
  },
];

const FALLBACK_NATIONAL_STATS: StatCardData[] = [
  {
    stat: '88.0%',
    title: 'Demand Front Warning Labels',
    description: '88% of 23,491+ surveyed Indian citizens demand large front warning labels displaying high salt, sugar, or saturated fat on packaged junk food.',
    source: 'National Macro Study (LocalCircles N=23,491+)',
  },
  {
    stat: '80.0%',
    title: 'Demand Single-Nutrient Alerts',
    description: '8 out of 10 consumers demand an immediate red warning if a product exceeds daily limits for even ONE negative nutrient like sodium or saturated fat.',
    source: 'National Macro Study (LocalCircles N=23,491+)',
  },
  {
    stat: '90.0%',
    title: 'Demand Total Sugar/Fat Standard',
    description: '90% of consumers demand regulators evaluate Total Sugar and Total Saturated Fat instead of loophole claims like "No Added Sugar".',
    source: 'National Macro Study (LocalCircles N=23,491+)',
  },
  {
    stat: '76.5%',
    title: 'Deceived by Negative Omission',
    description: 'Over 3 in 4 consumers are misled when brands omit high sodium and palm oil while aggressively advertising "0% Trans Fat" on front panels.',
    source: 'National Consumer Protection Report',
  },
];

export const CitedStatCards: React.FC = () => {
  const [primaryStats, setPrimaryStats] = useState<StatCardData[]>(FALLBACK_STATS);
  const [nationalStats, setNationalStats] = useState<StatCardData[]>(FALLBACK_NATIONAL_STATS);
  const [activeTab, setActiveTab] = useState<'primary' | 'national'>('primary');

  useEffect(() => {
    fetchStats()
      .then((data) => {
        if (data.key_stats && data.key_stats.length > 0) {
          setPrimaryStats(data.key_stats);
        }
        if (data.national_stats && data.national_stats.length > 0) {
          setNationalStats(data.national_stats);
        }
      })
      .catch((err) => {
        console.warn('Using embedded research stats:', err);
      });
  }, []);

  const activeStats = activeTab === 'primary' ? primaryStats : nationalStats;

  return (
    <section id="evidence-stats" className="py-12 sm:py-16 border-b border-zinc-200 bg-zinc-50">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">
        <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 mb-8">
          <div>
            <div className="text-xs font-mono uppercase tracking-wider text-zinc-500 mb-1">
              Dual-Study Empirical Findings
            </div>
            <h2 className="text-2xl font-semibold tracking-tight text-zinc-900">
              The Evidence Base: Consumer Perception vs. Food Industry Reality
            </h2>
            <p className="text-xs text-zinc-500 mt-1">
              Grounded in primary research (N=51) and the Pan-India Macro Study (N=23,491+ LocalCircles / FSSAI data).
            </p>
          </div>

          {/* Toggle buttons */}
          <div className="flex items-center gap-1.5 p-1 bg-white border border-zinc-200 rounded-md self-start sm:self-auto">
            <button
              onClick={() => setActiveTab('primary')}
              className={`px-3 py-1.5 rounded text-xs font-medium flex items-center gap-1.5 transition-all ${
                activeTab === 'primary'
                  ? 'bg-zinc-900 text-white font-semibold'
                  : 'text-zinc-600 hover:text-zinc-900'
              }`}
            >
              <Users className="w-3.5 h-3.5" />
              <span>Primary Study (N=51)</span>
            </button>
            <button
              onClick={() => setActiveTab('national')}
              className={`px-3 py-1.5 rounded text-xs font-medium flex items-center gap-1.5 transition-all ${
                activeTab === 'national'
                  ? 'bg-zinc-900 text-white font-semibold'
                  : 'text-zinc-600 hover:text-zinc-900'
              }`}
            >
              <Globe2 className="w-3.5 h-3.5" />
              <span>National Study (N=23,491+)</span>
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {activeStats.map((item, idx) => (
            <div
              key={idx}
              className="p-6 bg-white border border-zinc-200 rounded-md flex flex-col justify-between"
            >
              <div>
                <div className="text-3xl sm:text-4xl font-semibold tracking-tight text-zinc-900 font-mono">
                  {item.stat}
                </div>
                <h3 className="text-sm font-semibold text-zinc-800 mt-2">
                  {item.title}
                </h3>
                <p className="text-xs text-zinc-600 mt-2 leading-relaxed font-light">
                  {item.description}
                </p>
              </div>

              <div className="mt-4 pt-3 border-t border-zinc-100 flex items-center justify-between text-[11px] font-mono text-zinc-500">
                <span>CITED EVIDENCE</span>
                <span className="truncate ml-2 text-zinc-700 font-medium">{item.source}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};
