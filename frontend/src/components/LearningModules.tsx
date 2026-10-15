"use client";

import React, { useState } from 'react';
import { Scale, EyeOff, AlertTriangle, Globe2 } from 'lucide-react';

const MODULES = [
  {
    id: 'weight-rule',
    icon: Scale,
    title: 'FSSAI Regulation 5(2)(b): The Descending Weight Rule',
    summary: 'The first ingredient listed is always the heaviest component in the product at the time of manufacture.',
    details: [
      'If "Refined Wheat Flour (Maida)" or "Sugar" appears first, it dominates the product formulation.',
      'Industry bypass: Manufacturers frequently split sugar across 3 to 4 distinct chemical names (e.g., Maltodextrin, Invert Sugar, Liquid Glucose, Dextrose) so that no individual sugar name appears as ingredient #1, masking the massive total glycemic load.',
    ],
  },
  {
    id: 'maltodextrin',
    icon: EyeOff,
    title: 'The Maltodextrin Mystery (GI 105 - 110)',
    summary: 'Classified as a complex carbohydrate, bypassing "Sugar" disclosures while causing worse blood sugar spikes than pure table sugar.',
    details: [
      'Table sugar (sucrose) has a Glycemic Index of 65. Maltodextrin has a GI of 105 to 110, triggering immediate insulin surges and fat storage.',
      'Commonly added to "Diabetic-Friendly" biscuits, malted powders, and low-fat snacks as an inexpensive bulking agent.',
    ],
  },
  {
    id: 'dairy-vs-oil',
    icon: AlertTriangle,
    title: 'Dairy Deception & The "Creme" Loophole',
    summary: 'How vegetable oils and palm fats masquerade as dairy in frozen desserts and sandwich biscuits.',
    details: [
      'FSSAI Regulation 2.1.7 mandates that "Ice Cream" must be made strictly from milk fat. Any product using palm or vegetable oil must be labeled "Frozen Dessert".',
      'The phonetic spelling "Creme" is deliberately used on biscuits to evade dairy regulations while giving consumers the impression of real milk cream.',
    ],
  },
  {
    id: 'double-standards',
    icon: Globe2,
    title: 'The Nutritional Divide & Double Standards',
    summary: 'Multinational brands sell higher-sugar, higher-additive formulations in India than in Western markets.',
    details: [
      'A 2024 Public Eye investigation revealed that Nestlé Cerelac in India contains ~2.7g to 3.0g of added sugar per serving, while containing 0.0g added sugar in the UK, Germany, and Switzerland.',
      'Indian spices faced global bans for carcinogenic Ethylene Oxide (ETO), yet domestic pesticide tolerance was raised tenfold to 0.1 mg/kg.',
    ],
  },
];

export const LearningModules: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>(MODULES[0].id);

  const current = MODULES.find((m) => m.id === activeTab) || MODULES[0];
  const Icon = current.icon;

  return (
    <section className="py-12 sm:py-16 bg-white border-b border-zinc-200">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">
        <div className="mb-8">
          <div className="text-xs font-mono uppercase tracking-wider text-zinc-500 mb-1">
            FSSAI Regulatory Curriculum
          </div>
          <h2 className="text-2xl font-semibold tracking-tight text-zinc-900">
            Interactive Food Label Literacy Modules
          </h2>
          <p className="text-xs text-zinc-500 mt-1">
            Understand the loopholes, disguised additives, and regulatory definitions protecting or misleading consumers.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
          {/* Module Selector (Left) */}
          <div className="md:col-span-5 space-y-2">
            {MODULES.map((mod) => {
              const active = mod.id === activeTab;
              const ModIcon = mod.icon;
              return (
                <button
                  key={mod.id}
                  onClick={() => setActiveTab(mod.id)}
                  className={`w-full text-left p-4 rounded-md border transition-all flex items-start gap-3.5 ${
                    active
                      ? 'border-zinc-900 bg-zinc-900 text-white'
                      : 'border-zinc-200 bg-zinc-50/50 hover:bg-zinc-100/80 text-zinc-800'
                  }`}
                >
                  <ModIcon className={`w-5 h-5 shrink-0 mt-0.5 ${active ? 'text-zinc-200' : 'text-zinc-600'}`} />
                  <div>
                    <div className="text-xs font-semibold leading-snug">{mod.title}</div>
                    <div className={`text-[11px] mt-1 line-clamp-1 font-light ${active ? 'text-zinc-300' : 'text-zinc-500'}`}>
                      {mod.summary}
                    </div>
                  </div>
                </button>
              );
            })}
          </div>

          {/* Module Detail Card (Right) */}
          <div className="md:col-span-7 bg-zinc-50 border border-zinc-200 rounded-md p-6 sm:p-8 flex flex-col justify-between">
            <div>
              <div className="flex items-center gap-2 text-xs font-mono text-zinc-600 uppercase mb-3">
                <Icon className="w-4 h-4 text-zinc-800" />
                <span>Forensic Deep-Dive</span>
              </div>
              <h3 className="text-lg font-semibold text-zinc-900 tracking-tight">
                {current.title}
              </h3>
              <p className="text-xs text-zinc-600 mt-2 font-medium leading-relaxed">
                {current.summary}
              </p>

              <div className="mt-6 space-y-3">
                {current.details.map((point, i) => (
                  <div key={i} className="flex items-start gap-2.5 text-xs text-zinc-700 leading-relaxed font-light">
                    <span className="w-1.5 h-1.5 rounded-full bg-zinc-400 mt-1.5 shrink-0"></span>
                    <span>{point}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="mt-8 pt-4 border-t border-zinc-200 flex items-center justify-between text-[11px] font-mono text-zinc-500">
              <span>FSSAI 2020 Display & Labelling Norms</span>
              <span className="text-zinc-800 font-semibold">Standard Reference</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
