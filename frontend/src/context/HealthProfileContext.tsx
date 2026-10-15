"use client";

import React, { createContext, useContext, useEffect, useState } from 'react';
import { UserProfile } from '@/types';

const DEFAULT_PROFILE: UserProfile = {
  dietary_preferences: ['Vegetarian'],
  medical_conditions: ['Type-2 Diabetes'],
  allergies: ['Gluten'],
  custom_avoid_list: ['Palm Oil', 'Maltodextrin', 'INS 150d (Caramel Colour IV)'],
};

const STORAGE_KEY = 'labeltruth_health_profile_v2';

interface HealthProfileContextType {
  profile: UserProfile;
  updateProfile: (newProfile: UserProfile) => void;
  isModalOpen: boolean;
  setIsModalOpen: (open: boolean) => void;
}

const HealthProfileContext = createContext<HealthProfileContextType | undefined>(undefined);

export const HealthProfileProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [profile, setProfile] = useState<UserProfile>(DEFAULT_PROFILE);
  const [isModalOpen, setIsModalOpen] = useState(false);
  // profile loaded via localStorage

  useEffect(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        setProfile(JSON.parse(saved));
      } else {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(DEFAULT_PROFILE));
      }
    } catch (e) {
      console.warn('Could not read health profile from localStorage', e);
    }
  }, []);

  const updateProfile = (newProfile: UserProfile) => {
    setProfile(newProfile);
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(newProfile));
    } catch (e) {
      console.warn('Could not write health profile to localStorage', e);
    }
  };

  return (
    <HealthProfileContext.Provider value={{ profile, updateProfile, isModalOpen, setIsModalOpen }}>
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
