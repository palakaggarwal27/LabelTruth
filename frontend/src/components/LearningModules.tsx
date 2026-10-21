"use client";

import React, { useState } from 'react';
import { Scale, EyeOff, AlertTriangle, Globe2, ShieldAlert, HeartCrack } from 'lucide-react';
import { useHealthProfile } from '@/context/HealthProfileContext';

const MODULES = [
  {
    id: 'weight-rule',
    icon: Scale,
    title: 'FSSAI Regulation 5(2)(b): The Descending Weight Rule',
    summary: 'The first ingredient listed is always the heaviest component in the product at the time of manufacture.',
    fssaiCitation: 'FSSAI Labelling and Display Regulations 2020, Reg 5(2)(b)',
    details: [
      'If "Refined Wheat Flour (Maida)" or "Sugar" appears first, it dominates the product formulation.',
      'Industry bypass: Manufacturers frequently split sugar across 3 to 4 distinct chemical names (e.g., Maltodextrin, Invert Sugar, Liquid Glucose, Dextrose) so that no individual sugar name appears as ingredient #1, masking the massive total glycemic load.',
    ],
    exploitedLoophole: 'Sugar Splitting: Splitting 40g of total sugar into 10g Maltodextrin, 10g Invert Syrup, 10g Liquid Glucose, and 10g Sucrose so each ingredient appears lower than Whole Wheat on the label.',
    diseaseRisks: ['Type-2 Diabetes', 'Insulin Resistance', 'Fatty Liver (NAFLD)'],
  },
  {
    id: 'maltodextrin',
    icon: EyeOff,
    title: 'The Maltodextrin Mystery (GI 105 - 110)',
    summary: 'Classified as a complex carbohydrate, bypassing "Sugar" disclosures while causing worse blood sugar spikes than pure table sugar.',
    fssaiCitation: 'FSSAI Food Safety Standards (Food Products and Additives) Regulations',
    details: [
      'Table sugar (sucrose) has a Glycemic Index of 65. Maltodextrin has a GI of 105 to 110, triggering immediate insulin surges and fat storage.',
      'Commonly added to "Diabetic-Friendly" biscuits, malted powders, and low-fat snacks as an inexpensive bulking agent.',
    ],
    exploitedLoophole: 'Advertising "0g Added Sugar" on front-of-pack while putting 30% Maltodextrin as the main texturizing filler.',
    diseaseRisks: ['Type-2 Diabetes', 'PCOS', 'Obesity', 'Pre-diabetes'],
  },
  {
    id: 'dairy-vs-oil',
    icon: AlertTriangle,
    title: 'Dairy Deception & The "Frozen Dessert" Trap',
    summary: 'How cheap palm oils and hydrogenated vegetable fats masquerade as dairy ice cream and biscuit cremes.',
    fssaiCitation: 'FSSAI Reg 2.1.7 (Standards for Dairy Products)',
    details: [
      'FSSAI Regulation 2.1.7 mandates that "Ice Cream" must be made strictly from 100% milk fat. Any product using palm or vegetable oil must be labeled "Frozen Dessert".',
      'The phonetic spelling "Creme" is deliberately used on biscuits to evade dairy regulations while giving consumers the impression of real milk cream.',
    ],
    exploitedLoophole: 'Using small faint 6pt text for "Frozen Dessert" while displaying huge images of scoops and cows on packaging.',
    diseaseRisks: ['High Cholesterol', 'Hypertension (High BP)', 'Cardiovascular Disease'],
  },
  {
    id: 'caramel-dye',
    icon: ShieldAlert,
    title: 'Atta Dyeing & INS 150d (Caramel Colour IV)',
    summary: 'Dyeing refined maida brown to deceive consumers seeking whole wheat fiber.',
    fssaiCitation: 'FSSAI 2023 Bread & Cereal Standards Amendment',
    details: [
      'Commercial Brown Breads legally require only 50% whole wheat, and many use Maida as the primary grain.',
      'Brands add INS 150d (manufactured with ammonia and sulfites, creating trace 4-MEI carcinogen risk) to give white flour an earthy brown appearance.',
    ],
    exploitedLoophole: 'Naming the product "Atta Bread" on front-of-pack while the ingredients state Maida 60%, Atta 40%, and INS 150d dye.',
    diseaseRisks: ['Celiac Disease / Gluten Sensitivity', 'Carcinogen Exposure', 'Sulfite Allergies'],
  },
  {
    id: 'msg-enhancers',
    icon: AlertTriangle,
    title: 'INS 621 (MSG) & Flavour Enhancers (627 / 631)',
    summary: 'Synthetic umami boosters used to mask poor quality ingredients and drive compulsive snacking.',
    fssaiCitation: 'FSSAI Food Additives Regulations (Table 3: Flavour Enhancers)',
    details: [
      'Monosodium Glutamate (INS 621) and ribonucleotides (INS 627, INS 631) trigger neurotransmitter excitotoxicity and hyper-palatability, bypassing natural fullness cues.',
      'Under FSSAI rules, products with added MSG must declare "Contains Added MSG" on the label, but brands frequently hide it under "Natural Yeast Extract" or "Hydrolyzed Vegetable Protein (HVP)".',
    ],
    exploitedLoophole: 'Advertising "No Added MSG" while dumping 2% Hydrolyzed Soy Protein or Autolyzed Yeast, which naturally contains 20% free glutamates.',
    diseaseRisks: ['Hypertension (High BP)', 'Migraines', 'Excitotoxicity', 'High Sodium Retention'],
  },
  {
    id: 'synthetic-fiber',
    icon: EyeOff,
    title: 'Synthetic Fiber Padding: Polydextrose & Inulin',
    summary: 'Industrial synthetic fiber powders used to fabricate high-fiber claims without actual whole grains.',
    fssaiCitation: 'FSSAI Functional Foods and Fiber Labelling Guidelines',
    details: [
      'Real dietary fiber comes bound with vitamins, minerals, and polyphenols in whole oats, millets, and whole wheat.',
      'Ultra-processed products dump cheap synthetic isolated fibers (Polydextrose, Corn Dextrin, Chicory Root Inulin) to claim "High Fiber" on white maida cookies.',
    ],
    exploitedLoophole: 'Claiming "6g Fiber per serving" on cookies composed of 50% white maida and palm oil by adding 3g of industrial Polydextrose powder.',
    diseaseRisks: ['IBS & Bloating', 'Digestive Distress', 'Microbiome Dysbiosis'],
  },
  {
    id: 'double-standards',
    icon: Globe2,
    title: 'The Nutritional Divide & Double Standards',
    summary: 'Multinational brands sell higher-sugar, higher-additive formulations in India than in Western markets.',
    fssaiCitation: 'Global Food Safety Standards vs. Domestic Tolerance',
    details: [
      'A 2024 Public Eye investigation revealed that Nestlé Cerelac in India contains ~2.7g to 3.0g of added sugar per serving, while containing 0.0g added sugar in the UK, Germany, and Switzerland.',
      'Indian spices faced global recalls for carcinogenic Ethylene Oxide (EtO), yet domestic pesticide tolerance was raised tenfold to 0.1 mg/kg.',
    ],
    exploitedLoophole: 'Formulating cheaper, hyper-palatable high-sugar recipes specifically for South Asian markets due to delayed FOPL red warning regulations.',
    diseaseRisks: ['Childhood Obesity', 'Dental Caries', 'Early Metabolic Syndrome'],
  },
];

export const LearningModules: React.FC = () => {
  const { profile } = useHealthProfile();
  const [activeTab, setActiveTab] = useState<string>(MODULES[0].id);

  const current = MODULES.find((m) => m.id === activeTab) || MODULES[0];
  const Icon = current.icon;

  // Check if current module flags a disease that matches active profile
  const userConditions = profile.medical_conditions || [];
  const relevantToUser = current.diseaseRisks.some((d) => 
    userConditions.some((uc) => uc.toLowerCase().includes(d.toLowerCase()) || d.toLowerCase().includes(uc.toLowerCase()))
  );

  return (
    <section className="py-12 sm:py-16 bg-white border-b border-zinc-200">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">
        <div className="mb-8">
          <div className="text-xs font-mono uppercase tracking-wider text-zinc-500 mb-1">
            FSSAI Regulatory Curriculum & Additive Directory
          </div>
          <h2 className="text-2xl font-semibold tracking-tight text-zinc-900">
            Interactive Food Label Literacy & Loopholes
          </h2>
          <p className="text-xs text-zinc-500 mt-1">
            Forensic analysis of regulatory loopholes, industrial additives, and customized risk profiles.
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
              <div className="flex items-center justify-between gap-2 mb-3">
                <div className="flex items-center gap-2 text-xs font-mono text-zinc-600 uppercase">
                  <Icon className="w-4 h-4 text-zinc-800" />
                  <span>Forensic Analysis</span>
                </div>
                {relevantToUser && (
                  <span className="px-2 py-0.5 rounded bg-rose-100 text-rose-800 border border-rose-300 text-[10px] font-mono font-bold flex items-center gap-1">
                    <HeartCrack className="w-3 h-3" />
                    High Conflict with Active Profile
                  </span>
                )}
              </div>

              <h3 className="text-lg font-semibold text-zinc-900 tracking-tight">
                {current.title}
              </h3>
              <p className="text-xs text-zinc-600 mt-2 font-medium leading-relaxed">
                {current.summary}
              </p>

              {/* Core Details */}
              <div className="mt-5 space-y-2.5">
                {current.details.map((point, i) => (
                  <div key={i} className="flex items-start gap-2 text-xs text-zinc-700 leading-relaxed font-light">
                    <span className="w-1.5 h-1.5 rounded-full bg-zinc-400 mt-1.5 shrink-0"></span>
                    <span>{point}</span>
                  </div>
                ))}
              </div>

              {/* Exploited Loophole Box */}
              <div className="mt-5 p-3.5 bg-rose-50/70 border border-rose-200 rounded-md">
                <div className="text-[10px] font-mono uppercase tracking-wider text-rose-800 font-semibold mb-1 flex items-center gap-1">
                  <AlertTriangle className="w-3.5 h-3.5" />
                  Exploited Industry Loophole
                </div>
                <p className="text-xs text-rose-900 font-light leading-relaxed">
                  {current.exploitedLoophole}
                </p>
              </div>

              {/* Disease contraindications */}
              <div className="mt-4 flex items-center gap-2 flex-wrap">
                <span className="text-[11px] font-mono text-zinc-500 uppercase">Contraindicated For:</span>
                {current.diseaseRisks.map((d, idx) => (
                  <span key={idx} className="px-2 py-0.5 rounded text-[10px] font-mono bg-white border border-zinc-200 text-zinc-700">
                    {d}
                  </span>
                ))}
              </div>
            </div>

            <div className="mt-8 pt-4 border-t border-zinc-200 flex items-center justify-between text-[11px] font-mono text-zinc-500">
              <span className="truncate max-w-[280px]">{current.fssaiCitation}</span>
              <span className="text-zinc-800 font-semibold shrink-0">Regulatory Benchmark</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
