"use client";

import React, { useState } from 'react';
import { useHealthProfile } from '@/context/HealthProfileContext';
import { Users, User, AlertTriangle, ArrowRight, X } from 'lucide-react';
import { UserProfile } from '@/types';

interface HealthProfileManagerProps {
  activeProductName?: string | null;
}

export const HealthProfileManager: React.FC<HealthProfileManagerProps> = ({ activeProductName }) => {
  const { profiles, activeProfile, switchProfile, setIsModalOpen } = useHealthProfile();

  const [pendingProfile, setPendingProfile] = useState<UserProfile | null>(null);

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

  const handleProfileClick = (p: UserProfile) => {
    if (p.id === activeProfile.id) return;

    // If an active scan is already displayed, warn the user that switching will re-evaluate
    if (activeProductName) {
      setPendingProfile(p);
    } else {
      switchProfile(p.id!);
    }
  };

  const confirmSwitch = () => {
    if (pendingProfile) {
      switchProfile(pendingProfile.id!);
      setPendingProfile(null);
    }
  };

  return (
    <>
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
                  onClick={() => handleProfileClick(p)}
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

      {/* Confirmation Modal when switching profiles during active scan */}
      {pendingProfile && (
        <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg max-w-md w-full p-5 border border-zinc-200 shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-zinc-100 pb-3">
              <div className="flex items-center gap-2 text-amber-700">
                <AlertTriangle className="w-5 h-5 text-amber-600" />
                <h3 className="text-sm font-bold text-zinc-900">Switch Active Health Profile?</h3>
              </div>
              <button
                onClick={() => setPendingProfile(null)}
                className="text-zinc-400 hover:text-zinc-700"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-2 text-xs text-zinc-600">
              <p>
                You are currently viewing analysis for <strong className="text-zinc-900">{activeProductName}</strong> under{' '}
                <strong className="text-zinc-900">{activeProfile.name || 'Current Profile'}</strong>.
              </p>
              <p className="bg-amber-50 p-2.5 rounded border border-amber-200 text-amber-900 leading-relaxed">
                Switching to <strong className="font-bold">{pendingProfile.name}</strong> will re-evaluate this product&apos;s health score, clinical contraindications, and ingredient warnings for their specific health conditions.
              </p>
            </div>

            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setPendingProfile(null)}
                className="px-3 py-1.5 text-xs font-medium text-zinc-600 hover:text-zinc-900 rounded border border-zinc-200 hover:bg-zinc-50"
              >
                Keep Current
              </button>
              <button
                type="button"
                onClick={confirmSwitch}
                className="px-3.5 py-1.5 text-xs font-semibold bg-zinc-900 text-white rounded hover:bg-zinc-800 flex items-center gap-1.5 shadow-xs"
              >
                <span>Re-evaluate for {pendingProfile.name}</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};
