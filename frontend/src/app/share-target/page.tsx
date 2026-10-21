"use client";

import React, { useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { RefreshCw, Share2 } from 'lucide-react';

function ShareTargetContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  useEffect(() => {
    const sharedUrl = searchParams.get('url') || '';
    const sharedText = searchParams.get('text') || '';
    const sharedTitle = searchParams.get('title') || '';

    // Extract quick-commerce URL or product title
    const targetQuery = sharedUrl || sharedText || sharedTitle;

    if (targetQuery) {
      // Direct immediately to /scan with query preloaded
      router.replace(`/scan?query=${encodeURIComponent(targetQuery)}`);
    } else {
      router.replace('/scan');
    }
  }, [searchParams, router]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-zinc-50 p-6">
      <div className="p-8 bg-white border border-zinc-200 rounded-md max-w-sm w-full text-center space-y-4 shadow-sm">
        <div className="w-12 h-12 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-200 flex items-center justify-center mx-auto">
          <Share2 className="w-6 h-6 text-emerald-600" />
        </div>
        <h2 className="text-base font-semibold text-zinc-900">
          Receiving Shared Product Link...
        </h2>
        <p className="text-xs text-zinc-500 font-light">
          Transferring quick-commerce product details directly to LabelTruth Forensic Scanner.
        </p>
        <div className="flex items-center justify-center gap-2 text-xs font-mono text-zinc-600 pt-2">
          <RefreshCw className="w-4 h-4 animate-spin text-zinc-900" />
          <span>Opening Audit...</span>
        </div>
      </div>
    </div>
  );
}

export default function ShareTargetPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-zinc-50" />}>
      <ShareTargetContent />
    </Suspense>
  );
}
