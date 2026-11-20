"use client";

import React, { useState } from 'react';
import { auditCart } from '@/lib/api';
import { CartAuditResponse, CartItemAudit, LabelAnalysisResult, PersonalizedVerdict, ConcernLevel } from '@/types';
import { useHealthProfile } from '@/context/HealthProfileContext';
import { ProductInsightsModal } from '@/components/Results/ProductInsightsModal';
import { LiveInspectionStream } from '@/components/Scanner/LiveInspectionStream';
import { 
  ShoppingCart, 
  UploadCloud, 
  ListPlus, 
  Sparkles, 
  RefreshCw, 
  ArrowRight, 
  ExternalLink, 
  XCircle, 
  Trophy, 
  CheckCircle2, 
  AlertCircle,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  X,
  Image as ImageIcon,
  Eye
} from 'lucide-react';

export const CartAuditView: React.FC = () => {
  const { activeProfile, profile } = useHealthProfile();
  const currentProfile = activeProfile || profile;

  const [inputMode, setInputMode] = useState<'screenshots' | 'item_list'>('screenshots');
  const [cartImages, setCartImages] = useState<File[]>([]);
  const [itemNamesText, setItemNamesText] = useState('');
  const [pincode, setPincode] = useState('110001');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<CartAuditResponse | null>(null);
  const [inspectItem, setInspectItem] = useState<CartItemAudit | null>(null);
  const [auditStep, setAuditStep] = useState<string>("Extracting items from cart screenshots / store receipts...");

  const savePincode = (pin: string) => {
    setPincode(pin);
    try {
      sessionStorage.setItem('labeltruth_user_pincode', pin);
      localStorage.setItem('labeltruth_user_pincode', pin);
    } catch {
      // ignore
    }
  };

  // Load saved delivery pincode on mount
  React.useEffect(() => {
    try {
      const cached = sessionStorage.getItem('labeltruth_user_pincode') || localStorage.getItem('labeltruth_user_pincode');
      if (cached && /^\d{6}$/.test(cached)) {
        setPincode(cached);
      }
    } catch {
      // ignore
    }
  }, []);

  // Progressive audit stage timer for cart inspection
  React.useEffect(() => {
    if (!loading) {
      setAuditStep("Extracting items from cart screenshots / store receipts...");
      return;
    }
    const timer1 = setTimeout(() => {
      setAuditStep("Auditing packaging, ingredients, and nutrition tables against FSSAI standards...");
    }, 1500);
    const timer2 = setTimeout(() => {
      setAuditStep("Screening clinical contraindications against your personal health profile...");
    }, 4000);
    const timer3 = setTimeout(() => {
      setAuditStep("Researching verified cleaner Indian brand alternatives & checking dark-store availability...");
    }, 7500);

    return () => {
      clearTimeout(timer1);
      clearTimeout(timer2);
      clearTimeout(timer3);
    };
  }, [loading]);

  const handleAddFiles = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const newFiles = Array.from(e.target.files);
      setCartImages(prev => {
        const combined = [...prev, ...newFiles];
        return combined.slice(0, 8); // max 8 screenshots / bill photos
      });
    }
  };

  const handleRemoveFile = (idx: number) => {
    setCartImages(prev => prev.filter((_, i) => i !== idx));
  };

  const handleAudit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (inputMode === 'screenshots' && cartImages.length === 0) {
      setError('Please upload at least one screenshot of your quick-commerce cart or supermarket receipt.');
      return;
    }
    if (inputMode === 'item_list' && !itemNamesText.trim()) {
      setError('Please enter at least one product name in the list.');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const data = await auditCart(
        {
          images: inputMode === 'screenshots' ? cartImages : undefined,
          itemNames: inputMode === 'item_list' ? itemNamesText.trim() : undefined,
          pincode: pincode.trim() || '110001',
        },
        currentProfile
      );
      setResult(data);
    } catch (err: unknown) {
      const errorObj = err as { response?: { data?: { detail?: string } } };
      setError(errorObj.response?.data?.detail || 'Failed to audit cart. Please check your photos or item names.');
    } finally {
      setLoading(false);
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 75) return 'text-emerald-700 bg-emerald-50 border-emerald-200';
    if (score >= 45) return 'text-amber-700 bg-amber-50 border-amber-200';
    return 'text-rose-700 bg-rose-50 border-rose-200';
  };

  const getVerdictBadge = (verdict: string) => {
    if (verdict === 'SAFE FOR YOU') return 'bg-emerald-100 text-emerald-800 border border-emerald-300';
    if (verdict === 'CAUTION') return 'bg-amber-100 text-amber-800 border border-amber-300';
    return 'bg-rose-100 text-rose-800 border border-rose-300';
  };

  const [expandedItems, setExpandedItems] = useState<Set<number>>(new Set());
  const toggleExpanded = (idx: number) => {
    setExpandedItems(prev => {
      const next = new Set(prev);
      if (next.has(idx)) next.delete(idx);
      else next.add(idx);
      return next;
    });
  };

  return (
    <div className="space-y-6">
      {/* Intro Header */}
      <div className="border border-zinc-200 rounded-lg p-5 bg-gradient-to-r from-zinc-50 via-white to-zinc-50">
        <div className="flex items-center gap-2 mb-1">
          <ShoppingCart className="w-4 h-4 text-zinc-900" />
          <span className="text-xs font-mono font-bold uppercase tracking-wider text-zinc-600">
            Quick-Commerce & Supermarket Cart Audit
          </span>
        </div>
        <h2 className="text-lg font-semibold text-zinc-900">Forensic Audit for Your Entire Grocery Cart</h2>
        <p className="text-xs text-zinc-500 mt-1 max-w-2xl font-light leading-relaxed">
          Upload screenshots from Zepto, Blinkit, Instamart, or physical supermarket receipts (DMart, Reliance). LabelTruth automatically filters out non-food items, checks every food product for clinical contraindications and FSSAI violations, and discovers verified clean swaps.
        </p>
      </div>

      {!result ? (
        <div className="bg-white border border-zinc-200 rounded-lg p-6 sm:p-8">
          {/* Mode Switcher Tabs */}
          <div className="flex items-center gap-2 mb-6 border-b border-zinc-100 pb-3">
            <button
              type="button"
              onClick={() => setInputMode('screenshots')}
              className={`px-3.5 py-1.5 rounded-md text-xs font-semibold flex items-center gap-1.5 transition-colors ${
                inputMode === 'screenshots'
                  ? 'bg-zinc-900 text-white'
                  : 'bg-zinc-100 text-zinc-600 hover:text-zinc-900'
              }`}
            >
              <UploadCloud className="w-3.5 h-3.5" />
              <span>Screenshots or Supermarket Bill</span>
              {cartImages.length > 0 && (
                <span className="ml-1 px-1.5 py-0.2 bg-emerald-600 text-white text-[10px] rounded-full">
                  {cartImages.length}
                </span>
              )}
            </button>
            <button
              type="button"
              onClick={() => setInputMode('item_list')}
              className={`px-3.5 py-1.5 rounded-md text-xs font-semibold flex items-center gap-1.5 transition-colors ${
                inputMode === 'item_list'
                  ? 'bg-zinc-900 text-white'
                  : 'bg-zinc-100 text-zinc-600 hover:text-zinc-900'
              }`}
            >
              <ListPlus className="w-3.5 h-3.5" />
              <span>Enter Product Names List</span>
            </button>
          </div>

          <form onSubmit={handleAudit} className="space-y-4">
            {/* Delivery Pincode */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 p-3 bg-zinc-50 border border-zinc-200 rounded-md">
              <div>
                <label className="text-xs font-semibold text-zinc-900 block">
                  Delivery Pincode
                </label>
                <p className="text-[11px] text-zinc-500 font-light">
                  Ensures recommended swaps are in stock at your local dark store
                </p>
              </div>
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  maxLength={6}
                  value={pincode}
                  onChange={(e) => savePincode(e.target.value)}
                  placeholder="110001"
                  className="w-24 px-2.5 py-1 text-xs font-mono border border-zinc-200 rounded focus:outline-none focus:border-zinc-900 bg-white"
                />
              </div>
            </div>

            {/* Screenshots / Bills Form */}
            {inputMode === 'screenshots' && (
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <label className="text-xs font-semibold text-zinc-900 block">
                    Upload Quick-Commerce Screenshots or Store Receipts
                  </label>
                  <span className="text-[11px] font-mono text-zinc-500">
                    {cartImages.length} / 8 photos selected
                  </span>
                </div>
                
                <div className="border-2 border-dashed border-zinc-200 rounded-lg p-6 text-center hover:bg-zinc-50 transition-colors">
                  <input
                    type="file"
                    id="cart-screenshot-input"
                    accept="image/*"
                    multiple
                    onChange={handleAddFiles}
                    className="hidden"
                  />
                  <div className="flex flex-col items-center">
                    <UploadCloud className="w-8 h-8 text-zinc-400 mb-2" />
                    <p className="text-xs text-zinc-700 font-medium">
                      Upload screenshots from Zepto, Blinkit, Instamart, or physical supermarket receipts
                    </p>
                    <p className="text-[11px] text-zinc-400 mt-0.5">
                      Select multiple images to capture all items. Non-food products are automatically filtered out.
                    </p>
                    <button
                      type="button"
                      onClick={() => document.getElementById('cart-screenshot-input')?.click()}
                      className="mt-3 px-4 py-2 bg-zinc-900 hover:bg-zinc-800 text-white rounded text-xs font-medium transition-colors"
                    >
                      {cartImages.length > 0 ? '+ Add More Screenshots / Photos' : 'Browse Screenshots or Photos'}
                    </button>
                  </div>
                </div>

                {/* Selected Image Chips */}
                {cartImages.length > 0 && (
                  <div className="space-y-1.5 pt-1">
                    <span className="text-[11px] font-mono uppercase text-zinc-500 font-medium">
                      Selected Images to Audit:
                    </span>
                    <div className="flex flex-wrap gap-2">
                      {cartImages.map((file, idx) => (
                        <div
                          key={idx}
                          className="flex items-center gap-1.5 px-2.5 py-1 bg-zinc-100 border border-zinc-200 rounded text-xs text-zinc-800"
                        >
                          <ImageIcon className="w-3.5 h-3.5 text-zinc-500 shrink-0" />
                          <span className="max-w-[160px] truncate">{file.name}</span>
                          <span className="text-[10px] text-zinc-400 font-mono">
                            ({(file.size / 1024).toFixed(0)} KB)
                          </span>
                          <button
                            type="button"
                            onClick={() => handleRemoveFile(idx)}
                            className="ml-1 text-zinc-400 hover:text-rose-600 transition-colors"
                            title="Remove image"
                          >
                            <X className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Item List Form */}
            {inputMode === 'item_list' && (
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <label className="text-xs font-semibold text-zinc-900 block">
                    Enter or Paste Product Names
                  </label>
                  <span className="text-[11px] text-zinc-400">
                    One product per line or comma-separated
                  </span>
                </div>
                <textarea
                  rows={5}
                  value={itemNamesText}
                  onChange={(e) => setItemNamesText(e.target.value)}
                  placeholder={`Haldirams Nagpur Bhujia Sev\nBritannia Bourbon Biscuits\nAmul Salted Butter\nCoca-Cola 750ml\nLay's India's Magic Masala\nMaggi 2-Minute Noodles`}
                  className="w-full px-3 py-2 text-xs border border-zinc-200 rounded focus:outline-none focus:border-zinc-900 bg-white font-mono leading-relaxed"
                  disabled={loading}
                />
                <p className="text-[11px] text-zinc-500 font-light">
                  Enter grocery items from your cart. LabelTruth audits each product against authentic packaging, checks for clinical contraindications, and recommends cleaner swaps.
                </p>
              </div>
            )}

            {error && (
              <div className="p-3 bg-rose-50 border border-rose-200 rounded text-xs text-rose-700 flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 bg-zinc-900 hover:bg-zinc-800 text-white rounded-md text-xs font-semibold flex items-center justify-center gap-2 disabled:opacity-50 transition-colors"
            >
              {loading ? (
                <div className="flex flex-col items-center gap-1.5 py-0.5">
                  <div className="flex items-center gap-2">
                    <RefreshCw className="w-4 h-4 animate-spin text-white" />
                    <span className="font-semibold text-xs tracking-wide">Forensic Cart Audit in Progress</span>
                  </div>
                  <span className="text-[11px] font-mono text-zinc-300 font-normal animate-pulse">
                    {auditStep}
                  </span>
                </div>
              ) : (
                <>
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>Audit Entire Cart & Clean Swaps</span>
                </>
              )}
            </button>

            {loading && (
              <LiveInspectionStream
                isCart={true}
                title="Forensic Cart Audit & Transformation Stream"
                subtitle="Retrieving authentic packaging panels via TinyFish and calculating cleaner swaps"
              />
            )}
          </form>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Action Header */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono font-bold px-2.5 py-1 rounded bg-zinc-900 text-white">
                {result.store_name} Cart
              </span>
              <span className="text-xs font-mono text-zinc-500">
                PIN: {result.pincode}
              </span>
            </div>
            <button
              onClick={() => setResult(null)}
              className="px-3 py-1.5 bg-zinc-900 hover:bg-zinc-800 text-white rounded text-xs font-semibold flex items-center gap-1.5 transition-colors"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              Audit Another Cart
            </button>
          </div>

          {/* Cart Health Score Improvement Banner */}
          <div className="p-5 rounded-lg border border-emerald-300 bg-gradient-to-r from-emerald-50 via-teal-50 to-emerald-50 shadow-sm">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div className="flex items-center gap-3.5">
                <div className="w-12 h-12 rounded-full bg-emerald-600 text-white flex items-center justify-center shrink-0 shadow-sm">
                  <Trophy className="w-6 h-6" />
                </div>
                <div>
                  <span className="text-[10px] font-mono uppercase tracking-wider text-emerald-800 font-bold block">
                    Cart Forensic Transformation
                  </span>
                  <div className="flex items-center gap-2 mt-0.5">
                    <span className="text-2xl font-bold font-mono text-zinc-900">
                      {result.original_cart_score}
                    </span>
                    <ArrowRight className="w-4 h-4 text-emerald-700" />
                    <span className="text-2xl font-bold font-mono text-emerald-700">
                      {result.swapped_cart_score} / 100
                    </span>
                    <span className="ml-1 text-xs font-mono font-bold px-2 py-0.5 rounded bg-emerald-100 text-emerald-900 border border-emerald-300">
                      +{result.score_improvement} pts cleaner
                    </span>
                  </div>
                  <p className="text-xs text-emerald-950 font-light mt-1 max-w-xl">
                    {result.summary}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-3 self-start md:self-center shrink-0">
                <div className="text-center px-3 py-2 bg-white/80 rounded border border-emerald-200">
                  <span className="text-lg font-bold font-mono text-zinc-900 block leading-tight">
                    {result.red_flags_prevented_count}
                  </span>
                  <span className="text-[10px] text-zinc-500 font-medium uppercase">
                    Additives Removed
                  </span>
                </div>
                <div className="text-center px-3 py-2 bg-white/80 rounded border border-emerald-200">
                  <span className="text-lg font-bold font-mono text-zinc-900 block leading-tight">
                    {result.total_items}
                  </span>
                  <span className="text-[10px] text-zinc-500 font-medium uppercase">
                    Items Audited
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Itemized Cart List with Direct Swaps */}
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-zinc-900 flex items-center gap-2">
              <span>Item-by-Item Nutritional Breakdown & Available Swaps</span>
              <span className="text-xs font-mono font-normal text-zinc-400">
                ({result.items.length} items)
              </span>
            </h3>

            <div className="space-y-3">
              {result.items.map((item, idx) => {
                const isExpanded = expandedItems.has(idx);
                // Extract 1-2 line concise summary for the compact view
                const conciseSummary = item.key_concerns && item.key_concerns.length > 0
                  ? item.key_concerns.slice(0, 2).join(' • ')
                  : 'Nutritional baseline verified. No high-risk industrial additives or profile conflicts detected.';

                return (
                  <div
                    key={idx}
                    className="p-4 bg-white border border-zinc-200 rounded-lg hover:border-zinc-300 transition-all shadow-sm"
                  >
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 items-start">
                      {/* Original Item Compact Card */}
                      <div className="space-y-2.5">
                        <div className="flex items-start justify-between gap-2">
                          <div className="space-y-1">
                            <div className="flex items-center gap-1.5 flex-wrap">
                              <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded bg-zinc-100 text-zinc-700 font-semibold">
                                In Cart ({item.quantity}x)
                              </span>
                              <span className={`text-[10px] font-mono uppercase px-1.5 py-0.5 rounded font-semibold flex items-center gap-1 ${getVerdictBadge(item.personalized_verdict)}`}>
                                {item.personalized_verdict === 'AVOID (VIOLATES PROFILE)' && (
                                  <XCircle className="w-3 h-3 text-rose-600 shrink-0" />
                                )}
                                {item.personalized_verdict}
                              </span>
                            </div>
                            <h4 className="text-sm font-semibold text-zinc-900 leading-snug">
                              {item.product_name}
                            </h4>
                          </div>

                          {/* Health Score Pill */}
                          <div
                            className={`flex flex-col items-center justify-center w-11 h-11 rounded border font-mono font-bold shrink-0 ${getScoreColor(
                              item.health_score
                            )}`}
                          >
                            <span className="text-sm leading-none">{item.health_score}</span>
                            <span className="text-[8px] opacity-75">/100</span>
                          </div>
                        </div>

                        {/* 1-2 Line Brief Description */}
                        <p className="text-xs text-zinc-600 line-clamp-2 leading-relaxed">
                          {conciseSummary}
                        </p>

                        {/* Details Toggle Button */}
                        {item.key_concerns && item.key_concerns.length > 0 && (
                          <button
                            type="button"
                            onClick={() => toggleExpanded(idx)}
                            className="inline-flex items-center gap-1.5 text-[11px] font-medium text-zinc-700 hover:text-zinc-900 bg-zinc-50 hover:bg-zinc-100 border border-zinc-200 px-2.5 py-1 rounded transition-colors"
                          >
                            <span>{isExpanded ? 'Close Forensic Audit' : 'View Full Forensic Audit'}</span>
                            {isExpanded ? (
                              <ChevronUp className="w-3.5 h-3.5" />
                            ) : (
                              <ChevronDown className="w-3.5 h-3.5" />
                            )}
                          </button>
                        )}

                        {/* Expandable Clinical Details */}
                        {isExpanded && item.key_concerns.length > 0 && (
                          <div className="text-[11px] text-zinc-800 bg-rose-50/50 border border-rose-200/80 rounded-md p-3 space-y-1.5 animate-in fade-in duration-200">
                            <span className="text-[10px] font-mono uppercase tracking-wider text-rose-800 font-bold block mb-1">
                              Clinical Concerns & Additives:
                            </span>
                            {item.key_concerns.map((c, cIdx) => (
                              <div key={cIdx} className="flex items-start gap-1.5 text-zinc-800">
                                <span className="text-rose-500 font-bold shrink-0">•</span>
                                <span className="leading-relaxed">{c}</span>
                              </div>
                            ))}
                          </div>
                        )}

                        {/* View Full Insights Action */}
                        <button
                          type="button"
                          onClick={() => setInspectItem(item)}
                          className="mt-2.5 inline-flex items-center gap-1.5 px-3 py-1.5 bg-zinc-900 hover:bg-zinc-800 text-white rounded-md text-xs font-medium transition-colors cursor-pointer shadow-sm w-fit"
                        >
                          <Eye className="w-3.5 h-3.5" />
                          <span>View Full Insights</span>
                        </button>
                      </div>

                      {/* Cleaner Swap Recommendation */}
                      {item.cleaner_alternative ? (
                        <div className="p-3.5 rounded-lg border border-emerald-200 bg-emerald-50/40 flex flex-col justify-between gap-2.5 h-full">
                          <div>
                            <div className="flex items-center justify-between gap-2 mb-1.5">
                              <span className="text-[10px] font-mono uppercase tracking-wider text-emerald-800 font-bold flex items-center gap-1">
                                <CheckCircle2 className="w-3 h-3 text-emerald-600 shrink-0" />
                                {item.cleaner_alternative.type === 'HOMEMADE_RECIPE' ? 'Homemade Fresh Swap' : 'Recommended Clean Swap'}
                              </span>
                              <span className="text-xs font-mono font-bold text-emerald-800 bg-emerald-100 px-1.5 py-0.5 rounded border border-emerald-300 shrink-0">
                                {item.cleaner_alternative.health_score}/100
                              </span>
                            </div>
                            <h5 className="text-xs font-semibold text-zinc-900 leading-snug">
                              {item.cleaner_alternative.name}
                            </h5>
                            <p className="text-[11px] text-zinc-600 font-light mt-1 leading-relaxed">
                              {item.cleaner_alternative.key_benefit || item.cleaner_alternative.reason}
                            </p>
                          </div>

                          {item.cleaner_alternative.recipe_url ? (
                            <a
                              href={item.cleaner_alternative.recipe_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="self-start mt-1 px-3 py-1.5 bg-purple-700 hover:bg-purple-800 text-white rounded text-xs font-medium flex items-center gap-1.5 transition-colors shadow-sm"
                            >
                              <span>View Recipe on YouTube</span>
                              <ExternalLink className="w-3 h-3" />
                            </a>
                          ) : item.cleaner_alternative.direct_pdp_url ? (
                            <a
                              href={item.cleaner_alternative.direct_pdp_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="self-start mt-1 px-3 py-1.5 bg-emerald-800 hover:bg-emerald-900 text-white rounded text-xs font-medium flex items-center gap-1.5 transition-colors shadow-sm"
                            >
                              <span>Find on {result.store_name}</span>
                              <ExternalLink className="w-3 h-3" />
                            </a>
                          ) : null}
                        </div>
                      ) : item.health_score >= 75 ? (
                        <div className="p-3.5 rounded-lg border border-zinc-200 bg-zinc-50 text-xs text-zinc-600 flex items-center gap-2 h-full">
                          <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                          <span>Already optimal: Verified clean profile with no harmful additives.</span>
                        </div>
                      ) : (
                        <div className="p-3.5 rounded-lg border border-amber-200 bg-amber-50/70 text-xs text-amber-800 flex items-center gap-2 h-full">
                          <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
                          <span>No cleaner packaged swap in local store inventory; consider fresh whole foods or moderation.</span>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* Full Product Breakdown Modal */}
      {inspectItem && (
        <ProductInsightsModal
          isOpen={inspectItem !== null}
          onClose={() => setInspectItem(null)}
          product={
            inspectItem.full_analysis || ({
              is_food_label: true,
              label_type: 'FULL_PANEL',
              cleaner_alternative_exists_in_market: Boolean(inspectItem.cleaner_alternative),
              product_name: inspectItem.product_name,
              health_score: inspectItem.health_score,
              personalized_verdict: (['SAFE FOR YOU', 'CAUTION', 'AVOID (VIOLATES PROFILE)'].includes(inspectItem.personalized_verdict)
                ? inspectItem.personalized_verdict
                : 'CAUTION') as PersonalizedVerdict,
              simple_summary: inspectItem.key_concerns[0] || `Forensic audit of ${inspectItem.product_name}`,
              deceptive_claims_flagged: [],
              fssai_violations: [],
              ingredient_breakdown: inspectItem.key_concerns.map((c) => ({
                ingredient: c.split(':')[0],
                purpose: 'Identified Factor',
                concern_level: (inspectItem.health_score < 45 ? 'HIGH' : 'MEDIUM') as ConcernLevel,
                personalized_warning: c
              })),
              healthier_alternative: inspectItem.cleaner_alternative || {
                name: 'Fresh Whole Food',
                reason: 'Unprocessed natural choice'
              },
              clean_alternatives: inspectItem.cleaner_alternative ? [inspectItem.cleaner_alternative] : []
            } as LabelAnalysisResult)
          }
          productTitle={inspectItem.product_name}
        />
      )}
    </div>
  );
};
