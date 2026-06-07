"use client";

import { useEffect, useState } from "react";
import { Activity, FileText, Calendar, ArrowRight } from "lucide-react";

export default function ReportsPage() {
  const [reports, setReports] = useState<any[]>([]);
  const [selectedReport, setSelectedReport] = useState<any>(null);
  const [loadingList, setLoadingList] = useState(true);
  const [loadingReport, setLoadingReport] = useState(false);

  useEffect(() => {
    fetch("http://localhost:8000/reports")
      .then((res) => res.json())
      .then((data) => {
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
  }, []);

  const loadReportContent = async (slug: string) => {
    setLoadingReport(true);
    try {
      const res = await fetch(`http://localhost:8000/reports/${slug}`);
      const data = await res.json();
      setSelectedReport(data);
    } catch (err) {
      console.error("Report Content Fetch Error:", err);
    } finally {
      setLoadingReport(false);
    }
  };

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

  // Simple custom Markdown rendering parser to avoid heavy dependency installations.
  // It handles headers (h1, h2, h3), lists, paragraphs, and bold formatting natively!
  const renderMarkdown = (text: string) => {
    if (!text) return null;
    
    return text.split("\n").map((line, index) => {
      const trimmed = line.trim();
      
      if (trimmed.startsWith("# ")) {
        return <h1 key={index} className="text-3xl font-extrabold text-zinc-100 mt-6 mb-4">{trimmed.replace("# ", "")}</h1>;
      }
      if (trimmed.startsWith("## ")) {
        return <h2 key={index} className="text-xl font-bold text-indigo-400 mt-6 mb-3 pb-1 border-b border-zinc-800/80">{trimmed.replace("## ", "")}</h2>;
      }
      if (trimmed.startsWith("### ")) {
        return <h3 key={index} className="text-lg font-bold text-zinc-200 mt-4 mb-2">{trimmed.replace("### ", "")}</h3>;
      }
      if (trimmed.startsWith("- ") || trimmed.startsWith("* ")) {
        const itemText = trimmed.substring(2);
        // Bold parsing inside list
        return (
          <li key={index} className="ml-5 list-disc text-sm text-zinc-300 mb-2 leading-relaxed">
            {parseBoldText(itemText)}
          </li>
        );
      }
      if (trimmed === "") {
        return <div key={index} className="h-3" />;
      }
      
      return <p key={index} className="text-sm text-zinc-400 mb-3 leading-relaxed">{parseBoldText(trimmed)}</p>;
    });
  };

  const parseBoldText = (str: string) => {
    // Basic parser for **bold** markers
    const parts = str.split(/\*\*(.*?)\*\*/g);
    return parts.map((part, i) => i % 2 === 1 ? <strong key={i} className="text-zinc-200 font-extrabold">{part}</strong> : part);
  };

  return (
    <main className="p-8 max-w-7xl mx-auto w-full space-y-8 bg-zinc-950/20 min-h-screen">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-extrabold tracking-tight text-zinc-50">
          Weekly Market <span className="gradient-text">Reports</span>
        </h1>
        <p className="text-zinc-400 text-sm mt-2">
          Synthesized AI briefs detailing developer mindshare movements and emerging opportunities.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        {/* Reports History List Sidebar */}
        <div className="lg:col-span-1 space-y-4">
          <div className="text-xs font-bold uppercase tracking-wider text-zinc-500 mb-2">Report Archives</div>
          
          {reports.length === 0 ? (
            <div className="text-xs text-zinc-600 font-semibold p-4 border border-zinc-800 rounded-lg">
              No reports synthesized yet.
            </div>
          ) : (
            <div className="space-y-2">
              {reports.map((rep) => {
                const isSelected = selectedReport?.slug === rep.slug;
                const formattedDate = new Date(rep.published_at).toLocaleDateString(undefined, {
                  month: "short",
                  day: "numeric",
                  year: "numeric"
                });
                
                return (
                  <button
                    key={rep.id}
                    onClick={() => loadReportContent(rep.slug)}
                    className={`w-full text-left p-4 rounded-xl border flex flex-col justify-between transition-all ${
                      isSelected
                        ? "bg-indigo-600/10 border-indigo-500/50 shadow-md text-zinc-100"
                        : "bg-zinc-900/40 border-zinc-800 hover:bg-zinc-900/60 text-zinc-400"
                    }`}
                  >
                    <div className="flex items-center space-x-2 text-xs font-bold uppercase tracking-wider mb-2">
                      <FileText className={`h-4 w-4 ${isSelected ? "text-indigo-400" : "text-zinc-500"}`} />
                      <span>Report Archive</span>
                    </div>
                    <h4 className="text-sm font-bold text-zinc-200 line-clamp-2 leading-tight">
                      {rep.title}
                    </h4>
                    <div className="mt-4 flex items-center space-x-1.5 text-[10px] text-zinc-500 font-semibold">
                      <Calendar className="h-3.5 w-3.5" />
                      <span>{formattedDate}</span>
                    </div>
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Selected Report Viewer */}
        <div className="lg:col-span-3 border border-zinc-800 bg-zinc-900/40 backdrop-blur-md rounded-xl p-8 shadow-xl min-h-[400px]">
          {loadingReport ? (
            <div className="h-full flex items-center justify-center py-20">
              <Activity className="h-8 w-8 text-indigo-500 animate-spin" />
            </div>
          ) : selectedReport ? (
            <div className="prose prose-invert max-w-none">
              <div className="flex items-center space-x-2 text-xs text-zinc-500 font-bold uppercase tracking-widest mb-4">
                <span>Weekly Briefing</span>
                <span>•</span>
                <span>
                  {new Date(selectedReport.published_at).toLocaleDateString(undefined, {
                    month: "long",
                    day: "numeric",
                    year: "numeric"
                  })}
                </span>
              </div>
              <div className="space-y-4">
                {renderMarkdown(selectedReport.content)}
              </div>
            </div>
          ) : (
            <div className="h-full flex items-center justify-center text-zinc-500 text-sm">
              Please select a briefing from the archive index.
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
