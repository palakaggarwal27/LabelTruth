"use client";

import React, { useEffect, useState } from 'react';
import { StatCardData } from '@/types';
import { fetchStats } from '@/lib/api';

const FALLBACK_STATS: StatCardData[] = [
  {
    stat: '82.4%',
    title: 'Rely on Front Claims or Legacy',
    description: '31.4% are driven by front buzzwords (No Added Sugar, High Protein) and 51.0% by legacy brand trust. Only 13.7% turn the pack over to read ingredients.',
    source: 'Primary Survey Q1 & Appendix A',
  },
  {
    stat: '47.1%',
    title: 'Completely Blind to Jargon',
    description: 'Nearly half of urban consumers cannot identify terms like Maltodextrin, INS 150d, HFCS, or RDA %, finding them akin to indecipherable laboratory jargon.',
    source: 'Primary Survey Q5 & MSIT Report Sec 3.2',
  },
  {
    stat: '52.9%',
    title: 'Unaware of Weight Order Principle',
    description: 'More than half do not know FSSAI Regulation 5(2)(b) mandates ingredients in descending order of weight. Most assume alphabetical or random placement.',
    source: 'Primary Survey Q6 & FSSAI 2020 Reg 5(2)(b)',
  },
  {
    stat: '68.6%',
    title: 'Misled by "Sugar-Free" Marketing',
    description: '23.5% believe Sugar-Free is safe for diabetics, while 21.6% believe it uses safe fruit juice, unaware of high-GI bulking agents like Maltodextrin (GI 105-110).',
    source: 'Primary Survey Q4 & MSIT Report Sec 2.3.1',
  },
  {
    stat: '70.6%',
    title: 'Frozen Dessert Mistaken for Ice Cream',
    description: 'Chose Kwality Walls as preferred ice cream despite it being legally a Frozen Dessert containing up to 10.2% edible vegetable/palm oil.',
    source: 'Primary Survey Q9 & FSSAI Reg 2.1.7',
  },
  {
    stat: '92.2%',
    title: 'Demand Front Warning Labels',
    description: '66.7% would stop buying junk food or switch to a green alternative if a Red Dot / Stop Sign was enforced, while 25.5% would exercise higher caution.',
    source: 'Primary Survey Q8 & Supreme Court / FOPL Mandate',
  },
];

export const CitedStatCards: React.FC = () => {
  const [stats, setStats] = useState<StatCardData[]>(FALLBACK_STATS);

  useEffect(() => {
    fetchStats()
      .then((data) => {
        if (data.key_stats && data.key_stats.length > 0) {
          setStats(data.key_stats);
        }
      })
      .catch((err) => {
        console.warn('Using embedded research stats:', err);
      });
  }, []);

  return (
    <section id="evidence-stats" className="py-12 sm:py-16 border-b border-zinc-200 bg-zinc-50">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">
        <div className="mb-8">
          <div className="text-xs font-mono uppercase tracking-wider text-zinc-500 mb-1">
            Empirical Findings & Data Verification
          </div>
          <h2 className="text-2xl font-semibold tracking-tight text-zinc-900">
            The Evidence Base: Consumer Perception vs. Food Industry Reality
          </h2>
          <p className="text-xs text-zinc-500 mt-1">
            Grounded in primary consumer research across 51 urban respondents (N=51) and FSSAI 2020 regulatory benchmarks.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {stats.map((item, idx) => (
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
