import React, { useState } from 'react';
import { HealthierAlternative } from '@/types';
import { Sparkles, ExternalLink, MapPin } from 'lucide-react';
import { buildStoreOptions } from '@/utils/affiliate';

interface AlternativeCardProps {
  alternative: HealthierAlternative;
  cleanAlternatives?: HealthierAlternative[];
}

export const AlternativeCard: React.FC<AlternativeCardProps> = ({ alternative, cleanAlternatives }) => {
  const [userCity, setUserCity] = useState('');
  const allAlternatives = cleanAlternatives && cleanAlternatives.length > 0 
    ? cleanAlternatives 
    : [alternative];

  return (
    <div className="space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div className="flex items-center gap-2 text-xs font-mono uppercase tracking-wider text-emerald-800">
          <Sparkles className="w-4 h-4 text-emerald-600" />
          <span className="font-semibold">Clean Whole-Food Alternatives</span>
        </div>

        {/* Location / City Pincode filter */}
        <div className="flex items-center gap-1.5 self-start sm:self-auto bg-zinc-50 border border-zinc-200 rounded px-2 py-1 text-xs text-zinc-600">
          <MapPin className="w-3.5 h-3.5 text-zinc-500" />
          <input
            type="text"
            placeholder="Your City or Pincode"
            value={userCity}
            onChange={(e) => setUserCity(e.target.value)}
            className="bg-transparent border-none focus:outline-none text-xs w-32 placeholder:text-zinc-400"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {allAlternatives.map((alt, idx) => {
          const storeOptions = buildStoreOptions(alt.name, userCity);

          return (
            <div
              key={idx}
              className="p-5 bg-white border border-zinc-200 hover:border-zinc-400 rounded-md transition-all flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between gap-2 mt-1">
                  <span className={`text-[10px] font-mono uppercase px-2 py-0.5 rounded font-semibold border ${
                    alt.type === 'HOMEMADE_RECIPE'
                      ? 'bg-purple-50 text-purple-800 border-purple-200'
                      : alt.type === 'BEST_COMMERCIAL_AVAILABLE'
                      ? 'bg-amber-50 text-amber-800 border-amber-200'
                      : 'bg-emerald-50 text-emerald-800 border-emerald-200'
                  }`}>
                    {alt.type === 'HOMEMADE_RECIPE' ? 'Whole-Food Recipe' : alt.type === 'BEST_COMMERCIAL_AVAILABLE' ? 'Best Available' : `Clean Upgrade #${idx + 1}`}
                  </span>
                  <div className="flex items-center gap-1.5">
                    {alt.delta_vs_scanned && (
                      <span className="text-[10px] font-mono font-bold px-1.5 py-0.5 rounded bg-zinc-100 text-zinc-800 border border-zinc-200">
                        {alt.delta_vs_scanned}
                      </span>
                    )}
                    {alt.health_score && (
                      <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-emerald-100 text-emerald-900 border border-emerald-300">
                        {alt.health_score}/100
                      </span>
                    )}
                  </div>
                </div>

                <h4 className="text-sm font-semibold text-zinc-900 mt-2">
                  {alt.product_name || alt.name}
                </h4>

                {/* Tier 2 Warning Tag */}
                {alt.warning_tag && (
                  <div className="mt-1.5 p-2 bg-amber-50 border border-amber-200 rounded text-[11px] text-amber-900 font-medium">
                    {alt.warning_tag}
                  </div>
                )}

                <p className="text-xs text-zinc-600 mt-1 font-light leading-relaxed">
                  {alt.reason || alt.key_benefit}
                </p>

                {/* Action Button: Direct PDP vs YouTube Recipe Search */}
                {alt.is_direct_pdp && alt.direct_pdp_url ? (
                  <div className="mt-2.5">
                    <button
                      onClick={() => window.open(alt.direct_pdp_url, '_blank')}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded text-xs font-semibold shadow-sm transition-colors"
                    >
                      <span>Direct Product Link (PDP)</span>
                      <ExternalLink className="w-3 h-3" />
                    </button>
                  </div>
                ) : alt.recipe_url || alt.type === 'HOMEMADE_RECIPE' ? (
                  <div className="mt-2.5">
                    <button
                      onClick={() => window.open(alt.recipe_url || `https://www.youtube.com/results?search_query=${encodeURIComponent(alt.name || alt.product_name || 'healthy recipe')}`, '_blank')}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-purple-700 hover:bg-purple-800 text-white rounded text-xs font-semibold shadow-sm transition-colors"
                    >
                      <span>Watch Verified YouTube Recipe</span>
                      <ExternalLink className="w-3 h-3" />
                    </button>
                  </div>
                ) : null}

                <div className="mt-3 pt-3 border-t border-zinc-100 text-[11px] space-y-1">
                  <div className="text-zinc-500">
                    <span className="font-medium text-zinc-700">Price:</span> {alt.price_comparison || 'Comparable'}
                  </div>
                  <div className="text-zinc-500">
                    <span className="font-medium text-zinc-700">Profile Fit:</span> {alt.personalized_fit || 'Clean Whole-Food'}
                  </div>
                </div>
              </div>

              {/* Multi-Store Buttons: Render only for commercial packaged alternatives, NOT for homemade recipes */}
              {alt.type !== 'HOMEMADE_RECIPE' && (
                <div className="mt-4 pt-3 border-t border-zinc-100">
                  <span className="text-[10px] uppercase font-mono text-zinc-500 block mb-1.5">
                    Check Quick-Commerce Availability:
                  </span>
                  <div className="grid grid-cols-2 gap-1.5">
                    {storeOptions.map((store) => (
                      <a
                        key={store.name}
                        href={store.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="py-1.5 px-2 bg-zinc-50 hover:bg-zinc-900 hover:text-white border border-zinc-200 rounded text-[11px] font-medium flex items-center justify-between text-zinc-800 transition-colors"
                        title={`Search on ${store.name}`}
                      >
                        <span className="truncate">{store.name}</span>
                        <ExternalLink className="w-2.5 h-2.5 opacity-60 ml-1 shrink-0" />
                      </a>
                    ))}
                  </div>
                  <div className="mt-2 text-[10px] text-zinc-400 font-light text-center">
                    {userCity ? `Availability verified for ${userCity}` : 'Tap store to check live delivery in your pincode'}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
