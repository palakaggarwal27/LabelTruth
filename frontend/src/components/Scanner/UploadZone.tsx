"use client";

import React, { useRef, useState } from 'react';
import { UploadCloud, Camera } from 'lucide-react';

interface UploadZoneProps {
  onFileSelect: (file: File) => void;
  onOpenLiveCamera: () => void;
  onTextSubmit?: (query: string, pincode?: string) => void;
  loading: boolean;
}

export const UploadZone: React.FC<UploadZoneProps> = ({ onFileSelect, onOpenLiveCamera, onTextSubmit, loading }) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const [textQuery, setTextQuery] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragover') setIsDragOver(true);
    else setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      onFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      onFileSelect(e.target.files[0]);
    }
  };

  const [pincode, setPincode] = useState('110001');
  const [detectingLoc, setDetectingLoc] = useState(false);

  const handleDetectLocation = () => {
    setDetectingLoc(true);

    const tryIpFallback = async () => {
      try {
        const ipRes = await fetch("https://ipapi.co/json/");
        if (ipRes.ok) {
          const ipData = await ipRes.json();
          if (ipData?.postal) {
            setPincode(ipData.postal.replace(/\s+/g, ''));
            return true;
          }
        }
      } catch (e) {
        console.warn("IP-based location detection failed:", e);
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
          // Free, high-reliability CORS-enabled reverse geocoding
          const res = await fetch(`https://api.bigdatacloud.net/data/reverse-geocode-client?latitude=${lat}&longitude=${lon}&localityLanguage=en`);
          if (res.ok) {
            const data = await res.json();
            const pin = data?.postcode || data?.postCode;
            if (pin && /^\d{6}$/.test(pin.replace(/\s+/g, ''))) {
              setPincode(pin.replace(/\s+/g, ''));
              return;
            }
          }
          // Secondary fallback to openstreetmap
          const osmRes = await fetch(`https://nominatim.openstreetmap.org/reverse?lat=${lat}&lon=${lon}&format=json`, {
            headers: { 'Accept': 'application/json' }
          });
          const osmData = await osmRes.json();
          const detectedPin = osmData?.address?.postcode || '';
          if (detectedPin) {
            setPincode(detectedPin.replace(/\s+/g, ''));
          } else {
            await tryIpFallback();
          }
        } catch {
          await tryIpFallback();
        } finally {
          setDetectingLoc(false);
        }
      },
      async (err) => {
        console.warn("Browser GPS permission denied or timeout:", err);
        // Seamless fallback to IP location without prompting permissions
        await tryIpFallback();
        setDetectingLoc(false);
      },
      { timeout: 7000, enableHighAccuracy: true }
    );
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (textQuery.trim() && onTextSubmit) {
      onTextSubmit(textQuery.trim(), pincode.trim() || '110001');
    }
  };

  return (
    <div className="space-y-4">
      {/* Product Name / Quick-Commerce Link Search Box */}
      {onTextSubmit && (
        <form onSubmit={handleSearchSubmit} className="p-4 bg-zinc-50 border border-zinc-200 rounded-md">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-1">
            <label className="text-xs font-semibold text-zinc-900 block">
              Search by Product Name or Quick-Commerce Link
            </label>
            <div className="flex items-center gap-1.5 text-xs text-zinc-600">
              <span className="text-[11px] font-mono">Delivery PIN:</span>
              <input
                type="text"
                maxLength={6}
                value={pincode}
                onChange={(e) => setPincode(e.target.value)}
                placeholder="110001"
                className="w-20 px-2 py-0.5 text-xs font-mono border border-zinc-200 rounded focus:outline-none focus:border-zinc-900 bg-white"
                title="Pincode for live Zepto/Blinkit availability check"
              />
              <button
                type="button"
                onClick={handleDetectLocation}
                disabled={detectingLoc}
                className="px-2 py-0.5 bg-zinc-200 hover:bg-zinc-300 rounded text-[11px] font-medium transition-colors"
                title="Detect current location pincode"
              >
                {detectingLoc ? "Locating..." : "📍 GPS"}
              </button>
            </div>
          </div>
          <p className="text-[11px] text-zinc-500 mb-2">
            No photo? Enter product name or paste Blinkit / Zepto URL to auto-fetch ingredients and verify clean swaps available at your pincode.
          </p>
          <div className="flex gap-2">
            <input
              type="text"
              placeholder="e.g. Bournvita, Maggi Atta Noodles, Epigamia Greek Yogurt, or paste link"
              value={textQuery}
              onChange={(e) => setTextQuery(e.target.value)}
              disabled={loading}
              className="flex-1 px-3 py-2 text-xs border border-zinc-200 rounded focus:outline-none focus:border-zinc-900 bg-white"
            />
            <button
              type="submit"
              disabled={loading || !textQuery.trim()}
              className="px-4 py-2 bg-zinc-900 hover:bg-zinc-800 text-white rounded text-xs font-semibold disabled:opacity-50 transition-colors"
            >
              {loading ? 'Searching...' : 'Search & Audit'}
            </button>
          </div>
        </form>
      )}

      {/* Divider */}
      <div className="flex items-center gap-3">
        <div className="h-px bg-zinc-200 flex-1" />
        <span className="text-[11px] font-mono uppercase text-zinc-400">or upload packaging photo</span>
        <div className="h-px bg-zinc-200 flex-1" />
      </div>

      <div
        onDragOver={handleDrag}
        onDragLeave={handleDrag}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-md p-8 sm:p-10 text-center transition-colors ${
          isDragOver
            ? 'border-zinc-900 bg-zinc-100'
            : 'border-zinc-200 bg-zinc-50/50 hover:bg-zinc-100/50'
        }`}
      >
        <input
          ref={inputRef}
          id="label-image-upload"
          aria-label="Upload food label image or screenshot"
          type="file"
          accept="image/*"
          onChange={handleChange}
          className="hidden"
        />

        <div className="flex flex-col items-center">
          <div className="w-10 h-10 rounded-md bg-white border border-zinc-200 flex items-center justify-center text-zinc-700 mb-2.5">
            <UploadCloud className="w-5 h-5" />
          </div>

          <h3 className="text-sm font-semibold text-zinc-900">
            Upload Food Packaging Photo or Screenshot
          </h3>
          <p className="text-xs text-zinc-500 mt-1 max-w-sm font-light">
            Works with Front-of-pack, Back-of-pack ingredients, or nutrition table. TinyFish AI automatically fetches missing panels online!
          </p>

          <div className="mt-4 flex flex-wrap items-center justify-center gap-2">
            <button
              type="button"
              disabled={loading}
              onClick={() => inputRef.current?.click()}
              className="px-4 py-2 bg-zinc-900 hover:bg-zinc-800 text-white rounded-md text-xs font-semibold disabled:opacity-50"
            >
              Browse Image File
            </button>

            <button
              type="button"
              disabled={loading}
              onClick={onOpenLiveCamera}
              className="px-4 py-2 bg-white hover:bg-zinc-100 border border-zinc-200 text-zinc-800 rounded-md text-xs font-medium flex items-center gap-1.5 disabled:opacity-50"
            >
              <Camera className="w-3.5 h-3.5" />
              Use Live Camera
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
