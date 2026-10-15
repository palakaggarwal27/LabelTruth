"use client";

import React, { useRef, useState } from 'react';
import { UploadCloud, Camera } from 'lucide-react';

interface UploadZoneProps {
  onFileSelect: (file: File) => void;
  onOpenLiveCamera: () => void;
  loading: boolean;
}

export const UploadZone: React.FC<UploadZoneProps> = ({ onFileSelect, onOpenLiveCamera, loading }) => {
  const [isDragOver, setIsDragOver] = useState(false);
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

  return (
    <div
      onDragOver={handleDrag}
      onDragLeave={handleDrag}
      onDrop={handleDrop}
      className={`border-2 border-dashed rounded-md p-8 sm:p-12 text-center transition-colors ${
        isDragOver
          ? 'border-zinc-900 bg-zinc-100'
          : 'border-zinc-200 bg-zinc-50/50 hover:bg-zinc-100/50'
      }`}
    >
      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        onChange={handleChange}
        className="hidden"
      />

      <div className="flex flex-col items-center">
        <div className="w-12 h-12 rounded-md bg-white border border-zinc-200 flex items-center justify-center text-zinc-700 mb-3">
          <UploadCloud className="w-6 h-6" />
        </div>

        <h3 className="text-sm font-semibold text-zinc-900">
          Upload or Drop Food Packaging Screenshot
        </h3>
        <p className="text-xs text-zinc-500 mt-1 max-w-sm font-light">
          Works with photos or screenshots from Blinkit, Zepto, Swiggy Instamart, or Amazon Fresh.
        </p>

        <div className="mt-5 flex flex-wrap items-center justify-center gap-2">
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
  );
};
