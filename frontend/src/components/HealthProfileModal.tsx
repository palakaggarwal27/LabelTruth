"use client";

import React, { useState } from 'react';
import { X, Check, AlertCircle, Sparkles, Loader2 } from 'lucide-react';
import { useHealthProfile } from '@/context/HealthProfileContext';
import { UserProfile } from '@/types';
import { validateCondition } from '@/lib/api';

const DIETARY_OPTIONS = [
  'Vegan',
  'Vegetarian',
  'Jain',
  'Halal',
  'Eggless',
  'Gluten-Free',
  'Dairy-Free'
];

const MEDICAL_CONDITIONS = [
  'Type-2 Diabetes',
  'Celiac Disease / Gluten Sensitivity',
  'Hypertension (High BP)',
  'Lactose Intolerance',
  'Hyperuricemia (Gout)',
  'Chronic Kidney Disease (Low Sodium/Potassium)',
  'Phenylketonuria (PKU)',
  'High Cholesterol',
  'Fatty Liver (NAFLD)'
];

const ALLERGY_OPTIONS = [
  'Peanut Allergy',
  'Tree Nut Allergy',
  'Soy Allergy',
  'Shellfish / Seafood Allergy',
  'Sesame Allergy',
  'Gluten',
  'Dairy / Lactose',
  'Sulfites',
  'Egg'
];

const COMMON_AVOID = [
  'Palm Oil',
  'Maltodextrin',
  'INS 150d (Caramel Colour IV)',
  'Liquid Glucose',
  'High Fructose Corn Syrup (HFCS)',
  'INS 621 (MSG)',
  'INS 102 (Tartrazine)',
  'INS 211 (Sodium Benzoate)',
  'INS 320 (BHA)'
];

export const HealthProfileModal: React.FC = () => {
  const { profile, updateProfile, isModalOpen, setIsModalOpen } = useHealthProfile();

  const [dietary, setDietary] = useState<string[]>(profile.dietary_preferences);
  const [medical, setMedical] = useState<string[]>(profile.medical_conditions);
  const [allergies, setAllergies] = useState<string[]>(profile.allergies);
  const [avoid, setAvoid] = useState<string[]>(profile.custom_avoid_list);
  const [customInput, setCustomInput] = useState('');
  const [validating, setValidating] = useState(false);
  const [validationWarning, setValidationWarning] = useState<string | null>(null);
  const [validationSuccess, setValidationSuccess] = useState<string | null>(null);

  // Sync state whenever modal opens or profile changes
  React.useEffect(() => {
    if (isModalOpen) {
      setDietary(profile.dietary_preferences);
      setMedical(profile.medical_conditions);
      setAllergies(profile.allergies);
      setAvoid(profile.custom_avoid_list);
      setValidationWarning(null);
      setValidationSuccess(null);
    }
  }, [isModalOpen, profile]);

  if (!isModalOpen) return null;

  const toggleItem = (list: string[], setList: (v: string[]) => void, item: string) => {
    if (list.includes(item)) {
      setList(list.filter((x) => x !== item));
    } else {
      setList([...list, item]);
    }
  };

  const removeAvoidItem = (itemToRemove: string) => {
    const updatedAvoid = avoid.filter((x) => x !== itemToRemove);
    setAvoid(updatedAvoid);
    updateProfile({
      dietary_preferences: dietary,
      medical_conditions: medical,
      allergies: allergies,
      custom_avoid_list: updatedAvoid,
    });
  };

  const handleSave = () => {
    const updated: UserProfile = {
      dietary_preferences: dietary,
      medical_conditions: medical,
      allergies: allergies,
      custom_avoid_list: avoid,
    };
    updateProfile(updated);
    setIsModalOpen(false);
  };

  const handleAddCustom = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = customInput.trim();
    if (!trimmed) return;

    setValidating(true);
    setValidationWarning(null);
    setValidationSuccess(null);

    try {
      const res = await validateCondition(trimmed);
      if (res.is_valid && res.standardized_name) {
        const itemToAdd = res.standardized_name;
        let newAvoid = avoid;
        if (!avoid.includes(itemToAdd)) {
          newAvoid = [...avoid, itemToAdd];
          setAvoid(newAvoid);
        }
        // Auto-persist immediately to profile storage
        updateProfile({
          dietary_preferences: dietary,
          medical_conditions: medical,
          allergies: allergies,
          custom_avoid_list: newAvoid,
        });
        setValidationSuccess(`Added & saved: ${itemToAdd}`);
        setCustomInput('');
      } else {
        setValidationWarning(
          res.reason || "Please enter a recognized health condition, allergy, or food additive."
        );
      }
    } catch (err) {
      console.error('Validation error:', err);
      const fallbackName = trimmed.charAt(0).toUpperCase() + trimmed.slice(1);
      let newAvoid = avoid;
      if (!avoid.includes(fallbackName)) {
        newAvoid = [...avoid, fallbackName];
        setAvoid(newAvoid);
      }
      updateProfile({
        dietary_preferences: dietary,
        medical_conditions: medical,
        allergies: allergies,
        custom_avoid_list: newAvoid,
      });
      setValidationSuccess(`Added & saved: ${fallbackName}`);
      setCustomInput('');
    } finally {
      setValidating(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="w-full max-w-xl bg-white border border-zinc-200 rounded-md shadow-sm max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-zinc-200">
          <div>
            <h2 className="text-base font-semibold text-zinc-900 tracking-tight">
              Personalized Health Memory
            </h2>
            <p className="text-xs text-zinc-500 mt-0.5">
              Stored locally on your device. Gemini Vision audits every scanned label against these parameters.
            </p>
          </div>
          <button
            onClick={() => setIsModalOpen(false)}
            className="p-1.5 text-zinc-400 hover:text-zinc-800 rounded-md transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Scrollable Body */}
        <div className="p-6 overflow-y-auto space-y-6 text-sm">
          {/* Medical Conditions */}
          <div>
            <label className="text-xs font-semibold uppercase tracking-wider text-zinc-600 block mb-2">
              Clinical & Metabolic Conditions
            </label>
            <div className="flex flex-wrap gap-2">
              {MEDICAL_CONDITIONS.map((cond) => {
                const active = medical.includes(cond);
                return (
                  <button
                    key={cond}
                    type="button"
                    onClick={() => toggleItem(medical, setMedical, cond)}
                    className={`px-3 py-1.5 rounded-md border text-xs font-medium transition-colors ${
                      active
                        ? 'border-zinc-900 bg-zinc-900 text-white'
                        : 'border-zinc-200 bg-white text-zinc-700 hover:border-zinc-300'
                    }`}
                  >
                    {cond}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Dietary Preferences */}
          <div>
            <label className="text-xs font-semibold uppercase tracking-wider text-zinc-600 block mb-2">
              Dietary Standards
            </label>
            <div className="flex flex-wrap gap-2">
              {DIETARY_OPTIONS.map((diet) => {
                const active = dietary.includes(diet);
                return (
                  <button
                    key={diet}
                    type="button"
                    onClick={() => toggleItem(dietary, setDietary, diet)}
                    className={`px-3 py-1.5 rounded-md border text-xs font-medium transition-colors ${
                      active
                        ? 'border-zinc-900 bg-zinc-900 text-white'
                        : 'border-zinc-200 bg-white text-zinc-700 hover:border-zinc-300'
                    }`}
                  >
                    {diet}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Allergies */}
          <div>
            <label className="text-xs font-semibold uppercase tracking-wider text-zinc-600 block mb-2">
              Allergies & Sensitivities
            </label>
            <div className="flex flex-wrap gap-2">
              {ALLERGY_OPTIONS.map((allergy) => {
                const active = allergies.includes(allergy);
                return (
                  <button
                    key={allergy}
                    type="button"
                    onClick={() => toggleItem(allergies, setAllergies, allergy)}
                    className={`px-3 py-1.5 rounded-md border text-xs font-medium transition-colors ${
                      active
                        ? 'border-amber-800 bg-amber-50 text-amber-900 font-semibold'
                        : 'border-zinc-200 bg-white text-zinc-700 hover:border-zinc-300'
                    }`}
                  >
                    {allergy}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Custom Avoid List */}
          <div>
            <label className="text-xs font-semibold uppercase tracking-wider text-zinc-600 block mb-2">
              Specific Additives to Strictly Flag
            </label>
            <div className="flex flex-wrap gap-2 mb-3">
              {COMMON_AVOID.map((ing) => {
                const active = avoid.includes(ing);
                return (
                  <button
                    key={ing}
                    type="button"
                    onClick={() => toggleItem(avoid, setAvoid, ing)}
                    className={`px-2.5 py-1 rounded-md border text-xs font-mono transition-colors ${
                      active
                        ? 'border-rose-800 bg-rose-50 text-rose-900 font-semibold'
                        : 'border-zinc-200 bg-white text-zinc-600 hover:border-zinc-300'
                    }`}
                  >
                    {ing}
                  </button>
                );
              })}
            </div>

            {/* Custom User Added Items Section */}
            {avoid.filter((item) => !COMMON_AVOID.includes(item)).length > 0 && (
              <div className="mb-3 p-3 bg-zinc-50 border border-zinc-200 rounded-md">
                <span className="text-[11px] font-semibold uppercase tracking-wider text-zinc-600 block mb-1.5">
                  Your Custom Avoidance Memory ({avoid.filter((item) => !COMMON_AVOID.includes(item)).length}):
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {avoid.filter((item) => !COMMON_AVOID.includes(item)).map((customItem) => (
                    <span
                      key={customItem}
                      className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-rose-100/70 border border-rose-300 text-rose-900 text-xs font-mono font-medium"
                    >
                      <span>{customItem}</span>
                      <button
                        type="button"
                        onClick={() => removeAvoidItem(customItem)}
                        className="text-rose-700 hover:text-rose-950 p-0.5 rounded hover:bg-rose-200/50"
                        title="Remove custom avoidance"
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Custom Input */}
            <form onSubmit={handleAddCustom} className="flex gap-2">
              <input
                type="text"
                placeholder="Add custom condition or ingredient (e.g., E102 Tartrazine, Histamine Intolerance, Maltitol)"
                value={customInput}
                onChange={(e) => {
                  setCustomInput(e.target.value);
                  if (validationWarning) setValidationWarning(null);
                }}
                className="flex-1 px-3 py-1.5 text-xs border border-zinc-200 rounded-md focus:outline-none focus:border-zinc-900"
              />
              <button
                type="submit"
                disabled={validating || !customInput.trim()}
                className="px-3.5 py-1.5 bg-zinc-900 hover:bg-zinc-800 text-white rounded-md text-xs font-medium flex items-center gap-1.5 disabled:opacity-50"
              >
                {validating ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    <span>Verifying...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>AI Verify & Add</span>
                  </>
                )}
              </button>
            </form>

            {validationWarning && (
              <div className="mt-2.5 p-2.5 bg-amber-50 border border-amber-200 rounded-md text-amber-900 text-xs flex items-start gap-1.5">
                <AlertCircle className="w-3.5 h-3.5 shrink-0 mt-0.5 text-amber-700" />
                <span className="font-light">{validationWarning}</span>
              </div>
            )}

            {validationSuccess && (
              <div className="mt-2.5 p-2 bg-emerald-50 border border-emerald-200 rounded-md text-emerald-900 text-xs flex items-center gap-1.5">
                <Check className="w-3.5 h-3.5 text-emerald-700 shrink-0" />
                <span>{validationSuccess}</span>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-zinc-200 bg-zinc-50 flex items-center justify-between">
          <div className="flex items-center gap-1.5 text-zinc-500 text-xs">
            <AlertCircle className="w-3.5 h-3.5" />
            <span>Saved to device memory</span>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setIsModalOpen(false)}
              className="px-4 py-2 border border-zinc-200 hover:bg-zinc-100 rounded-md text-xs font-medium text-zinc-700"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              className="px-4 py-2 bg-zinc-900 hover:bg-zinc-800 text-white rounded-md text-xs font-semibold flex items-center gap-1.5"
            >
              <Check className="w-3.5 h-3.5" />
              Save Profile
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
