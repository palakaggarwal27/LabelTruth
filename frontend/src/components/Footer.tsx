"use client";

import React, { useState } from 'react';
import { FileText, Database, ShieldAlert, ExternalLink, X } from 'lucide-react';

export const Footer: React.FC = () => {
  const [modalResource, setModalResource] = useState<{
    title: string;
    description: string;
    downloadUrl: string;
    details: string[];
  } | null>(null);

  const openPdfModal = () => {
    setModalResource({
      title: 'Primary Research Report: The Fine Print of Nutrition',
      description: 'Academic research paper detailing regulatory loopholes in Indian food packaging, FSSAI 2020 compliance standards, technical jargon analysis (Maltodextrin, INS 150d), and Front-of-Pack Labelling (FOPL) reforms.',
      downloadUrl: '/resources/pm_hve_report.pdf',
      details: [
        'Title: The Fine Print of Nutrition - A Deep Dive into Label Literacy, Public Health, and the Case for Stricter Food Regulation in India',
        'Authors: Pranay Khanna, Palak Aggarwal, Niharika Popli, Saksham Chopra, Vaibhav Singh',
        'Supervisor: Dr. Rashmi Gupta (April 2026)',
        'Topics Covered: FSSAI Regulation 5(2)(b) Descending Weight Order, Hidden Sugars, Dairy vs. Vegetable Oil (Frozen Desserts), Ethylene Oxide Spice Bans, Global Nutritional Double Standards (Cerelac).'
      ]
    });
  };

  const openCsvModal = () => {
    setModalResource({
      title: 'Consumer Survey Dataset: The Indian Food Label Challenge',
      description: 'Primary empirical survey responses from 51 urban Indian consumers measuring label literacy, awareness of the descending weight rule, brand trust, and willingness to change habits under front-of-pack traffic light warning systems.',
      downloadUrl: '/resources/The_Indian_Food_Label_Challenge_Responses.csv',
      details: [
        'Sample Size: 51 Urban Respondents (N=51)',
        'Key Metric 1: 82.4% rely on front claims or legacy brand trust; only 13.7% inspect ingredient lists.',
        'Key Metric 2: 47.1% do not recognize common industrial additive terms (Maltodextrin, INS 150d, HFCS).',
        'Key Metric 3: 52.9% unaware of descending weight ingredient ordering.',
        'Key Metric 4: 92.2% express positive behavioural shift towards avoidance/caution if mandatory red warning labels are enforced.'
      ]
    });
  };

  return (
    <footer className="border-t border-zinc-200 bg-white py-12 text-zinc-600">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">
        <div className="flex flex-col md:flex-row items-start justify-between gap-8 pb-8 border-b border-zinc-100">
          {/* Brand & Badge */}
          <div className="max-w-md">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-md bg-zinc-900 text-white flex items-center justify-center font-bold text-xs tracking-tight">
                LT
              </div>
              <span className="text-sm font-semibold tracking-tight text-zinc-900">
                LabelTruth
              </span>
            </div>
            <p className="text-xs text-zinc-700 mt-2 font-medium">
              Transparent Food Labeling & Consumer Protection
            </p>
            <div className="inline-flex items-center gap-1.5 mt-3 px-2.5 py-1 rounded border border-emerald-200 bg-emerald-50 text-emerald-900 text-[11px] font-mono font-medium">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-600"></span>
              Grounded in primary consumer research across 51 respondents (N=51).
            </div>
          </div>

          {/* Research & Open Resources */}
          <div>
            <div className="text-xs font-mono uppercase tracking-wider text-zinc-500 mb-3">
              Primary Research & Datasets
            </div>
            <div className="flex flex-col gap-2.5 text-xs">
              <button
                onClick={openPdfModal}
                className="inline-flex items-center gap-2 text-zinc-700 hover:text-zinc-900 font-medium text-left transition-colors"
              >
                <FileText className="w-3.5 h-3.5 text-zinc-500" />
                <span>Primary Research Report (PDF)</span>
              </button>

              <button
                onClick={openCsvModal}
                className="inline-flex items-center gap-2 text-zinc-700 hover:text-zinc-900 font-medium text-left transition-colors"
              >
                <Database className="w-3.5 h-3.5 text-zinc-500" />
                <span>Consumer Survey Dataset (N=51 CSV)</span>
              </button>
            </div>
          </div>
        </div>

        {/* Mandatory Legal & Health Disclaimer */}
        <div className="pt-6 text-[11px] text-zinc-500 leading-relaxed font-light flex items-start gap-2.5">
          <ShieldAlert className="w-4 h-4 text-zinc-400 shrink-0 mt-0.5" />
          <div>
            <span className="font-medium text-zinc-700">Disclaimer:</span> LabelTruth is an AI-powered educational and consumer protection tool designed to decode food labels and FSSAI regulatory compliance. It does not provide clinical medical diagnosis, treatment, or medical nutrition therapy. Always consult a qualified physician or clinical dietitian for personal medical conditions.
          </div>
        </div>
      </div>

      {/* Resource Modal */}
      {modalResource && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="w-full max-w-lg bg-white border border-zinc-200 rounded-md shadow-sm p-6 text-sm flex flex-col">
            <div className="flex items-start justify-between gap-4 pb-3 border-b border-zinc-100">
              <div>
                <span className="text-[10px] font-mono uppercase tracking-wider text-zinc-500 block">
                  Open Innovation Dataset
                </span>
                <h3 className="text-sm font-semibold text-zinc-900 mt-0.5">
                  {modalResource.title}
                </h3>
              </div>
              <button
                onClick={() => setModalResource(null)}
                className="p-1 text-zinc-400 hover:text-zinc-800 rounded"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <p className="text-xs text-zinc-600 mt-3 leading-relaxed font-light">
              {modalResource.description}
            </p>

            <div className="mt-4 p-3 bg-zinc-50 border border-zinc-200 rounded-md space-y-2">
              {modalResource.details.map((item, idx) => (
                <div key={idx} className="text-[11px] text-zinc-700 flex items-start gap-2 font-light">
                  <span className="w-1 h-1 rounded-full bg-zinc-400 mt-1.5 shrink-0"></span>
                  <span>{item}</span>
                </div>
              ))}
            </div>

            <div className="mt-6 pt-4 border-t border-zinc-100 flex items-center justify-between">
              <button
                onClick={() => setModalResource(null)}
                className="px-3 py-1.5 border border-zinc-200 hover:bg-zinc-100 rounded-md text-xs text-zinc-700"
              >
                Close
              </button>
              <a
                href={modalResource.downloadUrl}
                download
                className="px-4 py-1.5 bg-zinc-900 hover:bg-zinc-800 text-white rounded-md text-xs font-semibold inline-flex items-center gap-1.5"
              >
                <span>Download Resource</span>
                <ExternalLink className="w-3 h-3" />
              </a>
            </div>
          </div>
        </div>
      )}
    </footer>
  );
};
