"use client";

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { UserCheck, ScanLine, BookOpen } from 'lucide-react';
import { useHealthProfile } from '@/context/HealthProfileContext';

export const Navbar: React.FC = () => {
  const pathname = usePathname();
  const { profile, setIsModalOpen } = useHealthProfile();

  const totalRestrictions =
    profile.dietary_preferences.length +
    profile.medical_conditions.length +
    profile.allergies.length +
    profile.custom_avoid_list.length;

  return (
    <header className="sticky top-0 z-40 w-full bg-white/95 backdrop-blur-none border-b border-zinc-200">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
        {/* Brand */}
        <Link href="/" className="flex items-center gap-2 group">
          <div className="w-8 h-8 rounded-md bg-zinc-900 text-white flex items-center justify-center font-bold text-sm tracking-tight">
            LT
          </div>
          <div className="flex flex-col">
            <span className="text-sm font-semibold tracking-tight text-zinc-900">
              LabelTruth
            </span>
            <span className="text-[10px] uppercase tracking-wider text-zinc-500 font-medium">
              Transparent Food Labeling & Consumer Protection
            </span>
          </div>
        </Link>

        {/* Navigation links */}
        <nav className="flex items-center gap-1 sm:gap-4 text-xs font-medium">
          <Link
            href="/"
            className={`px-3 py-1.5 rounded-md transition-colors flex items-center gap-1.5 ${
              pathname === '/'
                ? 'bg-zinc-100 text-zinc-900 font-semibold'
                : 'text-zinc-600 hover:text-zinc-900'
            }`}
          >
            <BookOpen className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Literacy Hub</span>
          </Link>

          <Link
            href="/scan"
            className={`px-3 py-1.5 rounded-md transition-colors flex items-center gap-1.5 ${
              pathname === '/scan'
                ? 'bg-zinc-900 text-white font-semibold'
                : 'bg-zinc-100 text-zinc-900 hover:bg-zinc-200'
            }`}
          >
            <ScanLine className="w-3.5 h-3.5" />
            <span>Scan Label</span>
          </Link>

          {/* Health Profile Pill Button */}
          <button
            onClick={() => setIsModalOpen(true)}
            className="ml-1 sm:ml-2 pl-2.5 pr-3 py-1.5 border border-zinc-200 hover:border-zinc-400 bg-white rounded-md text-zinc-800 flex items-center gap-1.5 transition-all"
            title="Configure Personal Health Profile"
          >
            <UserCheck className="w-3.5 h-3.5 text-zinc-700" />
            <span className="hidden sm:inline text-xs font-medium">Profile</span>
            <span className="text-[10px] bg-zinc-100 px-1.5 py-0.5 rounded text-zinc-600 font-mono font-semibold">
              {totalRestrictions}
            </span>
          </button>
        </nav>
      </div>
    </header>
  );
};
