"use client";

import React from 'react';
import { HeroBanner } from '@/components/HeroBanner';
import { CitedStatCards } from '@/components/CitedStatCards';
import { LearningModules } from '@/components/LearningModules';
import { FloatingChatbot } from '@/components/FloatingChatbot';

export default function HomePage() {
  return (
    <div className="min-h-screen">
      <HeroBanner />
      <CitedStatCards />
      <LearningModules />
      <FloatingChatbot />
    </div>
  );
}
