"use client";

import React, { useRef, useState, useEffect } from 'react';
import { Camera } from 'lucide-react';

interface CameraCaptureProps {
  onCapture: (blob: Blob) => void;
  onCancel: () => void;
}

export const CameraCapture: React.FC<CameraCaptureProps> = ({ onCapture, onCancel }) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    navigator.mediaDevices
      ?.getUserMedia({
        video: { facingMode: 'environment', width: { ideal: 1280 }, height: { ideal: 720 } },
      })
      .then((s) => {
        if (active) {
          streamRef.current = s;
          if (videoRef.current) {
            videoRef.current.srcObject = s;
          }
        }
      })
      .catch((err) => {
        console.error('Camera access error:', err);
        setError('Camera access denied or unavailable. Please upload a screenshot or photo instead.');
      });

    return () => {
      active = false;
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((t) => t.stop());
      }
    };
  }, []);

  const handleSnap = () => {
    if (!videoRef.current) return;
    const canvas = document.createElement('canvas');
    canvas.width = videoRef.current.videoWidth || 640;
    canvas.height = videoRef.current.videoHeight || 480;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);
    canvas.toBlob(
      (blob) => {
        if (blob) {
          onCapture(blob);
          if (streamRef.current) streamRef.current.getTracks().forEach((t) => t.stop());
        }
      },
      'image/jpeg',
      0.92
    );
  };

  return (
    <div className="border border-zinc-200 rounded-md bg-zinc-900 p-4 text-white">
      {error ? (
        <div className="p-8 text-center text-zinc-400">
          <p className="text-xs text-rose-400 font-medium mb-3">{error}</p>
          <button
            onClick={onCancel}
            className="px-3 py-1.5 bg-zinc-800 text-zinc-200 border border-zinc-700 rounded-md text-xs"
          >
            Switch to File Upload
          </button>
        </div>
      ) : (
        <div className="flex flex-col items-center">
          <div className="relative w-full max-w-md aspect-[4/3] bg-black rounded-md overflow-hidden border border-zinc-800">
            <video ref={videoRef} autoPlay playsInline muted className="w-full h-full object-cover" />
            <div className="absolute inset-4 border border-white/20 border-dashed rounded pointer-events-none flex items-center justify-center">
              <span className="text-[10px] font-mono text-white/50 bg-black/40 px-2 py-0.5 rounded">
                Align back-of-pack ingredients
              </span>
            </div>
          </div>

          <div className="mt-4 flex items-center gap-3">
            <button
              onClick={handleSnap}
              className="px-5 py-2 bg-white text-zinc-900 hover:bg-zinc-200 rounded-md text-xs font-semibold flex items-center gap-2"
            >
              <Camera className="w-4 h-4" />
              Capture Label
            </button>
            <button
              onClick={onCancel}
              className="px-3 py-2 bg-zinc-800 text-zinc-300 hover:bg-zinc-700 rounded-md text-xs font-medium"
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
