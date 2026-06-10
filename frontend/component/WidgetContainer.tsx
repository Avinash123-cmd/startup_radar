"use client";

import React from "react";
import { AlertCircle, Activity } from "lucide-react";

interface WidgetContainerProps {
  title: string;
  loading: boolean;
  error: boolean;
  isEmpty?: boolean;
  children: React.ReactNode;
}

export default function WidgetContainer({
  title,
  loading,
  error,
  isEmpty = false,
  children
}: WidgetContainerProps) {
  if (loading) {
    return (
      <div className="border border-zinc-900 bg-zinc-900/20 rounded-xl p-6 flex flex-col items-center justify-center h-48 animate-pulse">
        <Activity className="h-6 w-6 text-indigo-500/60 animate-spin" />
        <span className="text-xs text-zinc-500 mt-2 font-semibold">Compiling {title}...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="border border-red-950/20 bg-red-950/5 rounded-xl p-6 flex flex-col items-center justify-center text-center h-48">
        <AlertCircle className="h-6 w-6 text-rose-500 mb-2" />
        <h4 className="text-xs font-bold text-zinc-300 uppercase tracking-wider">{title} Unavailable</h4>
        <p className="text-[10px] text-zinc-500 mt-1 max-w-[200px] leading-relaxed">
          Telemetry failed to load for this widget channel.
        </p>
      </div>
    );
  }

  if (isEmpty) {
    return (
      <div className="border border-zinc-900 bg-zinc-900/20 rounded-xl p-6 flex flex-col items-center justify-center text-center h-48">
        <AlertCircle className="h-6 w-6 text-zinc-500 mb-2" />
        <h4 className="text-xs font-bold text-zinc-300 uppercase tracking-wider">{title} Empty</h4>
        <p className="text-[10px] text-zinc-500 mt-1 max-w-[200px] leading-relaxed">
          No signal data points recorded.
        </p>
      </div>
    );
  }

  return <>{children}</>;
}
