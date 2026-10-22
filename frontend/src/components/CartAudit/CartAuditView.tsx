"use client";

import React, { useState } from 'react';
import { auditCart } from '@/lib/api';
import { CartAuditResponse } from '@/types';
import { useHealthProfile } from '@/context/HealthProfileContext';
import { 
  ShoppingCart, 
  UploadCloud, 
  Link as LinkIcon, 
  Sparkles, 
  RefreshCw, 
  ArrowRight, 
  ExternalLink, 
  XCircle, 
  Trophy, 
  CheckCircle2, 
  AlertCircle 
} from 'lucide-react';

export const CartAuditView: React.FC = () => {
  const { activeProfile, profile } = useHealthProfile();
  const currentProfile = activeProfile || profile;

  const [inputMode, setInputMode] = useState<'url' | 'screenshot'>('url');
  const [cartUrl, setCartUrl] = useState('');
  const [cartImage, setCartImage] = useState<File | null>(null);
  const [pincode, setPincode] = useState('110001');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<CartAuditResponse | null>(null);
  const [detectingLoc, setDetectingLoc] = useState(false);
  const [auditStep, setAuditStep] = useState<string>("Launching TinyFish Browser to access cart & bypass WAF challenges...");

  const savePincode = (pin: string) => {
    setPincode(pin);
    try {
      sessionStorage.setItem('labeltruth_user_pincode', pin);
      localStorage.setItem('labeltruth_user_pincode', pin);
    } catch {
      // ignore
    }
  };

  // Automatically detect user location and pincode on mount without requiring manual click
  React.useEffect(() => {
    try {
      const cached = sessionStorage.getItem('labeltruth_user_pincode') || localStorage.getItem('labeltruth_user_pincode');
      if (cached && /^\d{6}$/.test(cached)) {
        setPincode(cached);
        return;
      }
    } catch {
      // ignore
    }
    handleDetectLocation();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Progressive audit stage timer for cart inspection
  React.useEffect(() => {
    if (!loading) {
      setAuditStep("Launching TinyFish Browser to access cart & bypass WAF challenges...");
      return;
    }
    const timer1 = setTimeout(() => {
      setAuditStep("Extracting cart items, ingredients, and nutritional tables...");
    }, 1800);
    const timer2 = setTimeout(() => {
      setAuditStep("Auditing items against FSSAI standards & active clinical profile...");
    }, 4800);
    const timer3 = setTimeout(() => {
      setAuditStep("TinyFish Agent searching live dark-store inventory for verified cleaner swaps at PIN...");
    }, 8200);

    return () => {
      clearTimeout(timer1);
      clearTimeout(timer2);
      clearTimeout(timer3);
    };
  }, [loading]);

  const handleDetectLocation = () => {
    setDetectingLoc(true);

    const tryIpFallback = async () => {
      try {
        const ipRes = await fetch("https://ipapi.co/json/");
        if (ipRes.ok) {
          const ipData = await ipRes.json();
          const match = String(ipData?.postal || '').match(/\b([1-9][0-9]{5})\b/);
          if (match) {
            savePincode(match[1]);
            return true;
          }
        }
      } catch (e) {
        console.warn("IP location notice:", e);
      }
      return false;
    };

    if (!navigator.geolocation) {
      tryIpFallback().finally(() => setDetectingLoc(false));
      return;
    }

    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        try {
          const lat = pos.coords.latitude;
          const lon = pos.coords.longitude;

          // 1. High precision Nominatim with street level zoom 18
          try {
            const res = await fetch(`https://nominatim.openstreetmap.org/reverse?lat=${lat}&lon=${lon}&zoom=18&format=json&addressdetails=1`);
            if (res.ok) {
              const data = await res.json();
              const pinCandidate = data?.address?.postcode || data?.address?.postal_code || '';
              const match = String(pinCandidate).match(/\b([1-9][0-9]{5})\b/);
              if (match) {
                savePincode(match[1]);
                return;
              }
            }
          } catch (osmErr) {
            console.warn("Nominatim reverse geocode notice:", osmErr);
          }

          // 2. BigDataCloud reverse geocode client
          try {
            const bdcRes = await fetch(`https://api.bigdatacloud.net/data/reverse-geocode-client?latitude=${lat}&longitude=${lon}&localityLanguage=en`);
            if (bdcRes.ok) {
              const data = await bdcRes.json();
              const pin = data?.postcode || data?.postCode;
              const match = String(pin || '').match(/\b([1-9][0-9]{5})\b/);
              if (match) {
                savePincode(match[1]);
                return;
              }
            }
          } catch (bdErr) {
            console.warn("BigDataCloud notice:", bdErr);
          }

          await tryIpFallback();
        } catch {
          await tryIpFallback();
        } finally {
          setDetectingLoc(false);
        }
      },
      async (err) => {
        console.warn("Browser GPS permission or timeout:", err);
        await tryIpFallback();
        setDetectingLoc(false);
      },
      { timeout: 12000, enableHighAccuracy: true, maximumAge: 60000 }
    );
  };

  const handleAudit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (inputMode === 'url' && !cartUrl.trim()) {
      setError('Please enter a shared cart URL or product link.');
      return;
    }
    if (inputMode === 'screenshot' && !cartImage) {
      setError('Please upload a screenshot of your quick-commerce cart.');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const data = await auditCart(
        {
          imageFile: inputMode === 'screenshot' ? (cartImage || undefined) : undefined,
          cartUrl: inputMode === 'url' ? cartUrl.trim() : undefined,
          pincode: pincode.trim() || '110001',
        },
        currentProfile
      );
      setResult(data);
    } catch (err: unknown) {
      const errorObj = err as { response?: { data?: { detail?: string } } };
      setError(errorObj.response?.data?.detail || 'Failed to audit cart. Please verify your link or image.');
    } finally {
      setLoading(false);
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 75) return 'text-emerald-700 bg-emerald-50 border-emerald-200';
    if (score >= 45) return 'text-amber-700 bg-amber-50 border-amber-200';
    return 'text-rose-700 bg-rose-50 border-rose-200';
  };

  return (
    <div className="space-y-6">
      {/* Intro Header */}
      <div className="border border-zinc-200 rounded-lg p-5 bg-gradient-to-r from-zinc-50 via-white to-zinc-50">
        <div className="flex items-center gap-2 mb-1">
          <ShoppingCart className="w-4 h-4 text-zinc-900" />
          <span className="text-xs font-mono font-bold uppercase tracking-wider text-zinc-600">
            Quick-Commerce Cart Audit
          </span>
        </div>
        <h2 className="text-lg font-semibold text-zinc-900">Audit Your Entire Zepto / Blinkit Cart</h2>
        <p className="text-xs text-zinc-500 mt-1 max-w-2xl font-light leading-relaxed">
          Share your cart URL or upload a cart screenshot. TinyFish and Gemini scan every packaged item in your cart, check for health profile contraindications (like acidity triggers, high glycemic sugars, or allergens), and automatically discover cleaner swaps on the same app with direct product detail page (PDP) links.
        </p>
      </div>

      {!result ? (
        <div className="bg-white border border-zinc-200 rounded-lg p-6 sm:p-8">
          {/* Mode Switcher Tabs */}
          <div className="flex items-center gap-3 mb-6 border-b border-zinc-100 pb-3">
            <button
              type="button"
              onClick={() => setInputMode('url')}
              className={`px-3 py-1.5 rounded-md text-xs font-semibold flex items-center gap-1.5 transition-colors ${
                inputMode === 'url'
                  ? 'bg-zinc-900 text-white'
                  : 'bg-zinc-100 text-zinc-600 hover:text-zinc-900'
              }`}
            >
              <LinkIcon className="w-3.5 h-3.5" />
              <span>Share Cart Link</span>
            </button>
            <button
              type="button"
              onClick={() => setInputMode('screenshot')}
              className={`px-3 py-1.5 rounded-md text-xs font-semibold flex items-center gap-1.5 transition-colors ${
                inputMode === 'screenshot'
                  ? 'bg-zinc-900 text-white'
                  : 'bg-zinc-100 text-zinc-600 hover:text-zinc-900'
              }`}
            >
              <UploadCloud className="w-3.5 h-3.5" />
              <span>Upload Cart Screenshot</span>
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
                <button
                  type="button"
                  onClick={handleDetectLocation}
                  disabled={detectingLoc}
                  className="px-2.5 py-1 bg-zinc-200 hover:bg-zinc-300 rounded text-xs font-medium transition-colors"
                >
                  {detectingLoc ? 'Locating...' : '📍 GPS'}
                </button>
              </div>
            </div>

            {/* URL Input Form */}
            {inputMode === 'url' && (
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-zinc-900 block">
                  Quick-Commerce Cart or Shared Basket URL
                </label>
                <input
                  type="url"
                  value={cartUrl}
                  onChange={(e) => setCartUrl(e.target.value)}
                  placeholder="e.g. https://www.zepto.com/cart or https://blinkit.com/cart/..."
                  className="w-full px-3 py-2 text-xs border border-zinc-200 rounded focus:outline-none focus:border-zinc-900 bg-white"
                  disabled={loading}
                />
                <p className="text-[11px] text-zinc-400 font-light">
                  Supports Zepto, Blinkit, Swiggy Instamart, and BigBasket shared cart links.
                </p>
              </div>
            )}

            {/* Screenshot Upload Form */}
            {inputMode === 'screenshot' && (
              <div className="space-y-2">
                <label className="text-xs font-semibold text-zinc-900 block">
                  Upload Cart Screenshot
                </label>
                <div className="border-2 border-dashed border-zinc-200 rounded-lg p-6 text-center hover:bg-zinc-50 transition-colors">
                  <input
                    type="file"
                    id="cart-screenshot-input"
                    accept="image/*"
                    onChange={(e) => {
                      if (e.target.files && e.target.files[0]) {
                        setCartImage(e.target.files[0]);
                      }
                    }}
                    className="hidden"
                  />
                  <div className="flex flex-col items-center">
                    <UploadCloud className="w-8 h-8 text-zinc-400 mb-2" />
                    {cartImage ? (
                      <div className="text-xs font-semibold text-emerald-700 bg-emerald-50 px-3 py-1 rounded border border-emerald-200">
                        Selected: {cartImage.name}
                      </div>
                    ) : (
                      <>
                        <p className="text-xs text-zinc-700 font-medium">
                          Drop your cart screenshot here, or browse
                        </p>
                        <p className="text-[11px] text-zinc-400 mt-0.5">
                          PNG, JPG, or WEBP up to 10MB
                        </p>
                      </>
                    )}
                    <button
                      type="button"
                      onClick={() => document.getElementById('cart-screenshot-input')?.click()}
                      className="mt-3 px-3 py-1.5 bg-zinc-100 hover:bg-zinc-200 text-zinc-800 rounded text-xs font-medium transition-colors"
                    >
                      Browse Screenshot
                    </button>
                  </div>
                </div>
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
              {result.items.map((item, idx) => (
                <div
                  key={idx}
                  className="p-4 bg-white border border-zinc-200 rounded-lg hover:border-zinc-300 transition-all"
                >
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 items-center">
                    {/* Original Item */}
                    <div className="space-y-2">
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <div className="flex items-center gap-1.5 mb-1">
                            <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded bg-zinc-100 text-zinc-700 font-semibold">
                              In Cart ({item.quantity}x)
                            </span>
                            {item.personalized_verdict === 'AVOID (VIOLATES PROFILE)' && (
                              <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded bg-rose-100 text-rose-800 font-semibold flex items-center gap-1">
                                <XCircle className="w-3 h-3 text-rose-600" />
                                Profile Conflict
                              </span>
                            )}
                          </div>
                          <h4 className="text-sm font-semibold text-zinc-900">
                            {item.product_name}
                          </h4>
                        </div>
                        <div
                          className={`flex flex-col items-center justify-center w-11 h-11 rounded border font-mono font-bold shrink-0 ${getScoreColor(
                            item.health_score
                          )}`}
                        >
                          <span className="text-sm leading-none">{item.health_score}</span>
                          <span className="text-[8px] opacity-75">/100</span>
                        </div>
                      </div>

                      {/* Concerns */}
                      {item.key_concerns.length > 0 && (
                        <div className="text-[11px] text-rose-800 bg-rose-50/60 border border-rose-200/80 rounded p-2 space-y-0.5">
                          {item.key_concerns.map((c, cIdx) => (
                            <p key={cIdx} className="flex items-start gap-1">
                              <span className="text-rose-500 font-bold shrink-0">•</span>
                              <span>{c}</span>
                            </p>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Cleaner Swap Recommendation */}
                    {item.cleaner_alternative ? (
                      <div className="p-3 rounded-lg border border-emerald-200 bg-emerald-50/40 flex flex-col justify-between gap-2">
                        <div>
                          <div className="flex items-center justify-between gap-2 mb-1">
                            <span className="text-[10px] font-mono uppercase tracking-wider text-emerald-800 font-bold flex items-center gap-1">
                              <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                              Recommended Clean Swap on {result.store_name}
                            </span>
                            <span className="text-xs font-mono font-bold text-emerald-800 bg-emerald-100 px-1.5 py-0.5 rounded border border-emerald-300">
                              {item.cleaner_alternative.health_score}/100
                            </span>
                          </div>
                          <h5 className="text-xs font-semibold text-zinc-900">
                            {item.cleaner_alternative.name}
                          </h5>
                          <p className="text-[11px] text-zinc-600 font-light mt-0.5">
                            {item.cleaner_alternative.key_benefit}
                          </p>
                        </div>

                        {item.cleaner_alternative.direct_pdp_url && (
                          <a
                            href={item.cleaner_alternative.direct_pdp_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="self-start mt-1 px-3 py-1 bg-emerald-800 hover:bg-emerald-900 text-white rounded text-xs font-medium flex items-center gap-1.5 transition-colors shadow-sm"
                          >
                            <span>Open on {result.store_name}</span>
                            <ExternalLink className="w-3 h-3" />
                          </a>
                        )}
                      </div>
                    ) : (
                      <div className="p-3 rounded-lg border border-zinc-200 bg-zinc-50 text-xs text-zinc-500 flex items-center gap-2">
                        <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                        <span>Already optimal: This product is verified clean on the shelf.</span>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
