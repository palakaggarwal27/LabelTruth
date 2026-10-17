"use client";

import React from 'react';
import { useHealthProfile } from '@/context/HealthProfileContext';
import { Users, User } from 'lucide-react';

export const HealthProfileManager: React.FC = () => {
  const { profiles, activeProfile, switchProfile, setIsModalOpen } = useHealthProfile();

  return (
    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3 bg-zinc-50 border border-zinc-200 rounded-md">
      <div className="flex items-center gap-2">
        <Users className="w-4 h-4 text-zinc-700" />
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
                <span>{p.name}</span>
              </button>
            );
          })}
        </div>
      </div>

      <div className="flex items-center gap-2 self-end sm:self-auto">
        <span className="text-[11px] text-zinc-500 font-mono hidden md:inline">
          {activeProfile.medical_conditions.length > 0
            ? activeProfile.medical_conditions.join(', ')
            : 'General Health Focus'}
        </span>
        <button
          onClick={() => setIsModalOpen(true)}
          className="text-xs text-zinc-800 hover:text-black font-semibold underline"
        >
          Customize
        </button>
      </div>
    </div>
  );
};
