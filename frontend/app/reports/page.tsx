"use client";

import { useCallback, useEffect, useState } from "react";
import {
  Activity,
  FileText,
  Calendar,
  Eye,
  TrendingUp,
  Database,
  Lightbulb,
  Award,
  BookOpen
} from "lucide-react";
import type { WeeklyReport } from "../../types/api";

export default function ReportsPage() {
  const [reports, setReports] = useState<WeeklyReport[]>([]);
  const [selectedReport, setSelectedReport] = useState<WeeklyReport | null>(null);
  const [loadingList, setLoadingList] = useState(true);
  const [loadingReport, setLoadingReport] = useState(false);

  const loadReportContent = useCallback(async (slug: string) => {
    setLoadingReport(true);
    try {
      const res = await fetch(`http://localhost:8000/reports/${slug}`);
      const data: WeeklyReport = await res.json();
      setSelectedReport(data);
    } catch (err) {
      console.error("Report Content Fetch Error:", err);
    } finally {
      setLoadingReport(false);
    }
  }, []);

  useEffect(() => {
    fetch("http://localhost:8000/reports")
      .then((res) => res.json())
      .then((data: WeeklyReport[] | unknown) => {
        const list = Array.isArray(data) ? data : [];
        setReports(list);
        setLoadingList(false);
        if (list.length > 0) {
          loadReportContent(list[0].slug);
        }
      })
      .catch((err) => {
        console.error("Reports List Fetch Error:", err);
        setLoadingList(false);
      });
  }, [loadReportContent]);

  if (loadingList) {
    return (
      <div className="flex-1 flex items-center justify-center p-10 bg-zinc-950">
        <div className="text-center space-y-4">
          <Activity className="h-10 w-10 text-indigo-500 animate-spin mx-auto" />
          <h2 className="text-lg font-bold text-zinc-100">Fetching Intelligence Briefings...</h2>
        </div>
      </div>
    );
  }

  // Markdown rendering parser
  const renderMarkdown = (text: string) => {
    if (!text) return null;

    return text.split("\n").map((line, index) => {
      const trimmed = line.trim();

      if (trimmed.startsWith("# ")) {
        return (
          <h1 key={index} className="text-3xl font-extrabold text-zinc-100 mt-6 mb-4 font-sans">
            {trimmed.replace("# ", "")}
          </h1>
        );
      }
      if (trimmed.startsWith("## ")) {
        return (
          <h2
            key={index}
            className="text-lg font-bold text-indigo-400 mt-6 mb-3 pb-1 border-b border-zinc-800/80"
          >
            {trimmed.replace("## ", "")}
          </h2>
        );
      }
      if (trimmed.startsWith("### ")) {
        return (
          <h3 key={index} className="text-sm font-bold text-zinc-200 mt-4 mb-2">
            {trimmed.replace("### ", "")}
          </h3>
        );
      }
      if (trimmed.startsWith("- ") || trimmed.startsWith("* ")) {
        const itemText = trimmed.substring(2);
        return (
          <li key={index} className="ml-5 list-disc text-xs text-zinc-300 mb-2 leading-relaxed">
            {parseBoldText(itemText)}
          </li>
        );
      }
      if (trimmed === "") {
        return <div key={index} className="h-3" />;
      }

      return (
        <p key={index} className="text-xs text-zinc-400 mb-3 leading-relaxed">
          {parseBoldText(trimmed)}
        </p>
      );
    });
  };

  const parseBoldText = (str: string) => {
    const parts = str.split(/\*\*(.*?)\*\*/g);
    return parts.map((part, i) =>
      i % 2 === 1 ? (
        <strong key={i} className="text-zinc-200 font-extrabold">
          {part}
        </strong>
      ) : (
        part
      )
    );
  };

  // Safe parsing of context snapshot JSON
  const getParsedSnapshot = () => {
    if (!selectedReport || !selectedReport.context_snapshot) return null;
    try {
      return JSON.parse(selectedReport.context_snapshot);
    } catch (e) {
      console.error("Context Snapshot Parse Error:", e);
      return null;
    }
  };

  const snapshot = getParsedSnapshot();

  return (
    <main className="p-8 max-w-7xl mx-auto w-full space-y-8 bg-zinc-950/20 min-h-screen">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-extrabold tracking-tight text-zinc-50 flex items-center space-x-2">
          <FileText className="h-8 w-8 text-indigo-500" />
          <span>Weekly Market Reports</span>
        </h1>
        <p className="text-zinc-400 text-sm mt-2">
          AI synthesized market briefs with auditable snapshot context logs for complete analytical transparency.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        {/* Reports History List Sidebar (1 Col) */}
        <div className="lg:col-span-1 space-y-4">
          <div className="text-[10px] font-bold uppercase tracking-wider text-zinc-500 mb-2">Report Archives</div>

          {reports.length === 0 ? (
            <div className="text-xs text-zinc-600 font-semibold p-4 border border-zinc-800 rounded-lg">
              No reports synthesized yet.
            </div>
          ) : (
            <div className="space-y-2 max-h-[600px] overflow-y-auto pr-1">
              {reports.map((rep) => {
                const isSelected = selectedReport?.slug === rep.slug;
                const formattedDate = new Date(rep.published_at).toLocaleDateString(undefined, {
                  month: "short",
                  day: "numeric",
                  year: "numeric",
                });

                return (
                  <button
                    key={rep.id}
                    onClick={() => loadReportContent(rep.slug)}
                    className={`w-full text-left p-4 rounded-xl border flex flex-col justify-between transition-all duration-200 cursor-pointer ${
                      isSelected
                        ? "bg-indigo-600/10 border-indigo-500/50 shadow-md text-zinc-100"
                        : "bg-zinc-900/40 border-zinc-800 hover:bg-zinc-900/60 text-zinc-400"
                    }`}
                  >
                    <div className="flex items-center space-x-2 text-[10px] font-bold uppercase tracking-wider mb-2">
                      <FileText className={`h-4 w-4 ${isSelected ? "text-indigo-400" : "text-zinc-500"}`} />
                      <span>Weekly Brief</span>
                    </div>
                    <h4 className="text-xs font-extrabold text-zinc-200 line-clamp-2 leading-tight">
                      {rep.title}
                    </h4>
                    <div className="mt-4 flex items-center space-x-1.5 text-[9px] text-zinc-500 font-semibold">
                      <Calendar className="h-3.5 w-3.5" />
                      <span>{formattedDate}</span>
                    </div>
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Selected Report Viewer (2 Cols) */}
        <div className="lg:col-span-2 border border-zinc-800 bg-zinc-900/40 backdrop-blur-md rounded-xl p-8 shadow-xl min-h-[500px]">
          {loadingReport ? (
            <div className="h-full flex items-center justify-center py-20">
              <Activity className="h-8 w-8 text-indigo-500 animate-spin" />
            </div>
          ) : selectedReport ? (
            <div className="prose prose-invert max-w-none">
              <div className="flex items-center space-x-2 text-[10px] text-zinc-500 font-bold uppercase tracking-widest mb-4">
                <span>Weekly Briefing Content</span>
                <span>•</span>
                <span>
                  {new Date(selectedReport.published_at).toLocaleDateString(undefined, {
                    month: "long",
                    day: "numeric",
                    year: "numeric",
                  })}
                </span>
              </div>
              <div className="space-y-4">{renderMarkdown(selectedReport.content)}</div>
            </div>
          ) : (
            <div className="h-full flex items-center justify-center text-zinc-500 text-sm">
              Please select a briefing from the archive index.
            </div>
          )}
        </div>

        {/* Historical Context Snap Auditor Sidebar (1 Col) */}
        <div className="lg:col-span-1 border border-zinc-800 bg-zinc-900/40 backdrop-blur-md rounded-xl p-6 shadow-xl space-y-6 self-start max-h-[700px] overflow-y-auto">
          <h3 className="text-xs font-bold uppercase tracking-widest text-zinc-400 border-b border-zinc-800 pb-3 flex items-center space-x-2">
            <Eye className="h-4 w-4 text-indigo-400" />
            <span>Context Snapshot Auditor</span>
          </h3>

          {!snapshot ? (
            <p className="text-xs text-zinc-500 leading-relaxed py-4 text-center">
              No historical data snapshot exists for this report or parsing failed.
            </p>
          ) : (
            <div className="space-y-5">
              {/* Leaders */}
              {snapshot.trends && snapshot.trends.length > 0 && (
                <div className="space-y-2">
                  <div className="text-[10px] font-bold uppercase text-zinc-500 tracking-wider flex items-center space-x-1">
                    <Award className="h-3.5 w-3.5 text-indigo-400" />
                    <span>Market Leaders</span>
                  </div>
                  <div className="space-y-1.5">
                    {snapshot.trends.slice(0, 3).map((trend: any) => (
                      <div key={trend.category_id} className="p-2 bg-zinc-950/40 border border-zinc-900 rounded text-xs flex justify-between">
                        <span className="font-bold text-zinc-300">{trend.name}</span>
                        <span className="text-indigo-400 font-extrabold">{trend.momentum_score.toFixed(0)} score</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Forecasts */}
              {snapshot.forecasts && snapshot.forecasts.length > 0 && (
                <div className="space-y-2">
                  <div className="text-[10px] font-bold uppercase text-zinc-500 tracking-wider flex items-center space-x-1">
                    <Lightbulb className="h-3.5 w-3.5 text-indigo-400" />
                    <span>Forecast Probability</span>
                  </div>
                  <div className="space-y-1.5">
                    {snapshot.forecasts.slice(0, 3).map((f: any, idx: number) => (
                      <div key={`${f.category_id || f.category}-${idx}`} className="p-2 bg-zinc-950/40 border border-zinc-900 rounded text-xs flex justify-between">
                        <span className="font-bold text-zinc-300">{f.category}</span>
                        <span className="text-indigo-400 font-extrabold">{f.growth_probability}%</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Repositories */}
              {snapshot.top_repositories && snapshot.top_repositories.length > 0 && (
                <div className="space-y-2">
                  <div className="text-[10px] font-bold uppercase text-zinc-500 tracking-wider flex items-center space-x-1">
                    <Database className="h-3.5 w-3.5 text-indigo-400" />
                    <span>Repos Monitored</span>
                  </div>
                  <div className="space-y-1.5">
                    {snapshot.top_repositories.slice(0, 3).map((repo: any) => (
                      <div key={repo.name} className="p-2 bg-zinc-950/40 border border-zinc-900 rounded text-[11px] flex justify-between items-center">
                        <span className="font-bold text-zinc-300 truncate max-w-[130px]">{repo.name.split("/")[1] || repo.name}</span>
                        <span className="text-zinc-500 font-semibold">{repo.stars.toLocaleString()} stars</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Signals */}
              {snapshot.top_signals && snapshot.top_signals.length > 0 && (
                <div className="space-y-2">
                  <div className="text-[10px] font-bold uppercase text-zinc-500 tracking-wider flex items-center space-x-1">
                    <BookOpen className="h-3.5 w-3.5 text-indigo-400" />
                    <span>Active Spike Signals</span>
                  </div>
                  <div className="space-y-1.5">
                    {snapshot.top_signals.slice(0, 2).map((sig: any, sidx: number) => (
                      <div key={sidx} className="p-2 bg-zinc-950/40 border border-zinc-900 rounded text-[10px] leading-relaxed text-zinc-400">
                        <span className="text-indigo-400 font-bold uppercase text-[8px] tracking-wide block mb-0.5">{sig.source}</span>
                        <span className="line-clamp-2">{sig.title}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
