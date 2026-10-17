"use client";

import React, { createContext, useContext, useEffect, useState } from 'react';
import { UserProfile } from '@/types';

export const DEFAULT_PROFILES: UserProfile[] = [
  {
    id: 'profile_self',
    name: 'Self (Active / Fitness)',
    dietary_preferences: ['Vegetarian'],
    medical_conditions: [],
    allergies: [],
    custom_avoid_list: ['Palm Oil', 'Maltodextrin', 'INS 150d (Caramel Colour IV)'],
  },
  {
    id: 'profile_dad',
    name: 'Dad (Diabetes & High BP)',
    dietary_preferences: ['Vegetarian'],
    medical_conditions: ['Type-2 Diabetes', 'Hypertension (High BP)'],
    allergies: [],
    custom_avoid_list: ['Liquid Glucose', 'Maltodextrin', 'High Sodium', 'MSG (INS 621)'],
  },
  {
    id: 'profile_kid',
    name: 'Kid (Allergies & Clean Growth)',
    dietary_preferences: [],
    medical_conditions: [],
    allergies: ['Peanut Allergy', 'Soy Allergy'],
    custom_avoid_list: ['INS 102 (Tartrazine)', 'INS 150d (Caramel Colour IV)', 'Artificial Sweeteners'],
  }
];

const STORAGE_KEY = 'labeltruth_household_profiles_v3';
const ACTIVE_PROFILE_KEY = 'labeltruth_active_profile_id_v3';

interface HealthProfileContextType {
  profiles: UserProfile[];
  activeProfile: UserProfile;
  profile: UserProfile; // backward compatibility
  switchProfile: (profileId: string) => void;
  updateActiveProfile: (newProfile: UserProfile) => void;
  updateProfile: (newProfile: UserProfile) => void; // backward compatibility
  addProfile: (newProfile: UserProfile) => void;
  removeProfile: (profileId: string) => void;
  isModalOpen: boolean;
  setIsModalOpen: (open: boolean) => void;
}

const HealthProfileContext = createContext<HealthProfileContextType | undefined>(undefined);

export const HealthProfileProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [profiles, setProfiles] = useState<UserProfile[]>(DEFAULT_PROFILES);
  const [activeProfileId, setActiveProfileId] = useState<string>('profile_self');
  const [isModalOpen, setIsModalOpen] = useState(false);

  useEffect(() => {
    try {
      const savedProfiles = localStorage.getItem(STORAGE_KEY);
      const savedActiveId = localStorage.getItem(ACTIVE_PROFILE_KEY);
      if (savedProfiles) {
        setProfiles(JSON.parse(savedProfiles));
      } else {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(DEFAULT_PROFILES));
      }
      if (savedActiveId) {
        setActiveProfileId(savedActiveId);
      }
    } catch (e) {
      console.warn('Could not read health profiles from localStorage', e);
    }
  }, []);

  const activeProfile = profiles.find((p) => p.id === activeProfileId) || profiles[0] || DEFAULT_PROFILES[0];

  const switchProfile = (profileId: string) => {
    setActiveProfileId(profileId);
    try {
      localStorage.setItem(ACTIVE_PROFILE_KEY, profileId);
    } catch (e) {
      console.warn('Could not save active profile ID', e);
    }
  };

  const updateActiveProfile = (updated: UserProfile) => {
    const newProfiles = profiles.map((p) => 
      p.id === activeProfile.id 
        ? { ...updated, id: p.id, name: updated.name || p.name } 
        : p
    );
    setProfiles(newProfiles);
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(newProfiles));
    } catch (e) {
      console.warn('Could not save health profiles to localStorage', e);
    }
  };

  const addProfile = (newProfile: UserProfile) => {
    const id = newProfile.id || `profile_${Date.now()}`;
    const profileWithId = { ...newProfile, id };
    const newProfiles = [...profiles, profileWithId];
    setProfiles(newProfiles);
    setActiveProfileId(id);
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(newProfiles));
      localStorage.setItem(ACTIVE_PROFILE_KEY, id);
    } catch (e) {
      console.warn('Could not add profile to localStorage', e);
    }
  };

  const removeProfile = (profileId: string) => {
    if (profiles.length <= 1) return; // Keep at least one profile
    const newProfiles = profiles.filter((p) => p.id !== profileId);
    setProfiles(newProfiles);
    if (activeProfileId === profileId) {
      setActiveProfileId(newProfiles[0].id!);
      try {
        localStorage.setItem(ACTIVE_PROFILE_KEY, newProfiles[0].id!);
      } catch (e) {
        console.warn('Could not save active profile ID', e);
      }
    }
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(newProfiles));
    } catch (e) {
      console.warn('Could not save profiles after removal', e);
    }
  };

  return (
    <HealthProfileContext.Provider
      value={{
        profiles,
        activeProfile,
        profile: activeProfile,
        switchProfile,
        updateActiveProfile,
        updateProfile: updateActiveProfile,
        addProfile,
        removeProfile,
        isModalOpen,
        setIsModalOpen,
      }}
    >
      {children}
    </HealthProfileContext.Provider>
  );
};

export const useHealthProfile = () => {
  const context = useContext(HealthProfileContext);
  if (!context) {
    throw new Error('useHealthProfile must be used within a HealthProfileProvider');
  }
  return context;
};
