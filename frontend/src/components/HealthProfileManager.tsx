"use client";

import React from 'react';
import { useHealthProfile } from '@/context/HealthProfileContext';
import { Users, User } from 'lucide-react';

export const HealthProfileManager: React.FC = () => {
  const { profiles, activeProfile, switchProfile, setIsModalOpen } = useHealthProfile();

  // Helper to dynamically extract the short summary tags for any profile
  const getProfileSummary = (p: typeof activeProfile) => {
    const tags: string[] = [];
    if (p.medical_conditions && p.medical_conditions.length > 0) {
      tags.push(...p.medical_conditions);
    }
    if (p.allergies && p.allergies.length > 0) {
      tags.push(...p.allergies);
    }
    if (p.dietary_preferences && p.dietary_preferences.length > 0) {
      tags.push(...p.dietary_preferences);
    }
    if (tags.length === 0 && p.custom_avoid_list && p.custom_avoid_list.length > 0) {
      tags.push(`Avoid: ${p.custom_avoid_list.slice(0, 2).join(', ')}`);
    }
    return tags.length > 0 ? tags.slice(0, 3).join(' • ') : 'General Wellness';
  };

  return (
    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3.5 bg-zinc-50 border border-zinc-200 rounded-md">
      <div className="flex items-center gap-2 flex-wrap">
        <Users className="w-4 h-4 text-zinc-700 shrink-0" />
        <span className="text-xs font-semibold text-zinc-900">Evaluating For:</span>
        <div className="flex items-center gap-1.5 flex-wrap">
          {profiles.map((p) => {
            const isSelected = p.id === activeProfile.id;
            return (
              <button
                key={p.id}
                onClick={() => switchProfile(p.id!)}
                className={`px-2.5 py-1 rounded text-xs font-medium transition-all flex items-center gap-1.5 border ${
                  isSelected
                    ? 'bg-zinc-900 text-white border-zinc-900 shadow-sm'
                    : 'bg-white text-zinc-600 border-zinc-200 hover:border-zinc-300'
                }`}
              >
                <User className="w-3 h-3" />
                <span>{p.name || 'Member'}</span>
              </button>
            );
          })}
        </div>
      </div>

      <div className="flex items-center gap-3 self-end sm:self-auto">
        <span className="text-[11px] text-zinc-600 font-mono bg-zinc-100 px-2 py-0.5 rounded border border-zinc-200">
          {getProfileSummary(activeProfile)}
        </span>
        <button
          onClick={() => setIsModalOpen(true)}
          className="text-xs text-zinc-900 hover:text-black font-semibold underline flex items-center gap-1"
        >
          <span>Manage Profiles</span>
        </button>
      </div>
    </div>
  );
};
