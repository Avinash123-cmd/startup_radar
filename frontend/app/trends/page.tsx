"use client";

import { useEffect, useState } from "react";
import CategoryHeatmap from "../../component/CategoryHeatmap";
import {
  Activity,
  Star,
  MessageSquare,
  Award,
  ChevronRight,
  X,
  ShieldAlert,
  Zap,
  TrendingUp,
  ExternalLink,
  BookOpen,
  PieChart
} from "lucide-react";
import type { TrendSummary, AnalysisResponse } from "../../types/api";

export default function TrendsPage() {
  const [trends, setTrends] = useState<TrendSummary[]>([]);
  const [loading, setLoading] = useState(true);

  // Drawer (deep-dive) states
  const [activeCategorySlug, setActiveCategorySlug] = useState<string | null>(null);
  const [analysisData, setAnalysisData] = useState<AnalysisResponse | null>(null);
  const [analysisLoading, setAnalysisLoading] = useState(false);

  useEffect(() => {
    fetch("http://localhost:8000/trends")
      .then((res) => res.json())
      .then((data) => {
        setTrends(Array.isArray(data) ? data : []);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Trends Page Fetch Error:", err);
        setLoading(false);
      });
  }, []);

  const openAnalysisDrawer = async (slug: string) => {
    setActiveCategorySlug(slug);
    setAnalysisLoading(true);
    setAnalysisData(null);
    try {
      const res = await fetch(`http://localhost:8000/analysis/${slug}`);
      if (!res.ok) throw new Error("Failed to load analysis");
      const data = await res.json();
      setAnalysisData(data);
    } catch (err) {
      console.error("Analysis Drawer Fetch Error:", err);
    } finally {
      setAnalysisLoading(false);
    }
  };

  const closeAnalysisDrawer = () => {
    setActiveCategorySlug(null);
    setAnalysisData(null);
  };

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center p-10 bg-zinc-950">
        <div className="text-center space-y-4">
          <Activity className="h-10 w-10 text-indigo-500 animate-spin mx-auto" />
          <h2 className="text-lg font-bold text-zinc-100">Compiling Category Heatmaps...</h2>
        </div>
      </div>
    );
  }

  return (
    <main className="p-8 max-w-7xl mx-auto w-full space-y-8 bg-zinc-950/20 min-h-screen relative">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-extrabold tracking-tight text-zinc-50">
          AI Niches <span className="gradient-text">Trends</span>
        </h1>
        <p className="text-zinc-400 text-sm mt-2">
          Tracking the growth velocity, signal channels, and developer momentum index of core AI domains.
        </p>
      </div>

      {/* Heatmap Section */}
      {trends.length > 0 && <CategoryHeatmap data={trends} />}

      {/* Categories Catalog */}
      <div className="border border-zinc-800 bg-zinc-900/40 backdrop-blur-md rounded-xl shadow-xl overflow-hidden">
        <div className="p-6 border-b border-zinc-800 flex justify-between items-center bg-zinc-950/25">
          <div>
            <h3 className="text-lg font-bold text-zinc-100">Market Domain Inventory</h3>
            <p className="text-xs text-zinc-400 font-semibold uppercase tracking-wider mt-1">
              Detailed niche catalog and channel telemetry
            </p>
          </div>
          <span className="text-[10px] text-zinc-500 font-bold uppercase tracking-widest bg-zinc-950/40 border border-zinc-800 px-3 py-1 rounded">
            Click row for AI deep-dive
          </span>
        </div>

        <div className="divide-y divide-zinc-800/80">
          {trends.map((cat, index) => {
            // Safe parse of source breakdown from API dict
            const sources = (cat as any).source_breakdown || {};
            const githubCount = sources.github || 0;
            const redditCount = sources.reddit || 0;
            const hnCount = sources.hacker_news || 0;
            const arxivCount = sources.arxiv || 0;
            const phCount = sources.product_hunt || 0;
            const totalSignals = githubCount + redditCount + hnCount + arxivCount + phCount;

            return (
              <div
                key={cat.category_id}
                onClick={() => openAnalysisDrawer(cat.slug)}
                className="p-6 hover:bg-zinc-900/25 transition duration-200 flex flex-col lg:flex-row lg:items-center justify-between gap-6 cursor-pointer group"
              >
                {/* Category info */}
                <div className="lg:max-w-md flex items-start space-x-4">
                  <div className="bg-indigo-950/50 border border-indigo-500/20 px-3 py-1.5 rounded-lg text-sm font-bold text-indigo-400 shrink-0">
                    {index + 1}
                  </div>
                  <div>
                    <h4 className="text-base font-extrabold text-zinc-100 group-hover:text-indigo-400 transition">
                      {cat.name}
                    </h4>
                    <p className="text-xs text-zinc-400 mt-1 leading-relaxed line-clamp-2">{cat.description}</p>
                  </div>
                </div>

                {/* Signal channels pills */}
                <div className="flex flex-col space-y-1.5 max-w-[200px] w-full shrink-0">
                  <div className="text-[9px] uppercase font-bold text-zinc-500 flex items-center space-x-1">
                    <PieChart className="h-3 w-3" />
                    <span>Signal Channels ({totalSignals})</span>
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {githubCount > 0 && (
                      <span className="text-[9px] font-bold text-indigo-400 bg-indigo-950/30 px-1.5 py-0.5 rounded">
                        GH: {githubCount}
                      </span>
                    )}
                    {redditCount > 0 && (
                      <span className="text-[9px] font-bold text-rose-400 bg-rose-950/30 px-1.5 py-0.5 rounded">
                        RD: {redditCount}
                      </span>
                    )}
                    {hnCount > 0 && (
                      <span className="text-[9px] font-bold text-amber-400 bg-amber-950/30 px-1.5 py-0.5 rounded">
                        HN: {hnCount}
                      </span>
                    )}
                    {arxivCount > 0 && (
                      <span className="text-[9px] font-bold text-cyan-400 bg-cyan-950/30 px-1.5 py-0.5 rounded">
                        AX: {arxivCount}
                      </span>
                    )}
                    {phCount > 0 && (
                      <span className="text-[9px] font-bold text-emerald-400 bg-emerald-950/30 px-1.5 py-0.5 rounded">
                        PH: {phCount}
                      </span>
                    )}
                  </div>
                </div>

                {/* Metrics blocks */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-6 text-left shrink-0">
                  {/* Total Stars */}
                  <div className="w-[80px]">
                    <div className="text-[10px] uppercase font-bold text-zinc-500 flex items-center space-x-1">
                      <Star className="h-3 w-3 text-zinc-500" />
                      <span>Stars</span>
                    </div>
                    <div className="text-sm font-bold text-zinc-200 mt-1">{cat.star_count.toLocaleString()}</div>
                  </div>

                  {/* 30d Growth */}
                  <div className="w-[100px]">
                    <div className="text-[10px] uppercase font-bold text-zinc-500">30d Growth</div>
                    <div className="text-sm font-bold text-emerald-400 mt-1">
                      +{cat.star_growth_30d.toLocaleString()}
                    </div>
                  </div>

                  {/* Growth Rate */}
                  <div className="w-[80px]">
                    <div className="text-[10px] uppercase font-bold text-zinc-500">Rate</div>
                    <div className="text-sm font-bold text-emerald-400 mt-1">+{cat.growth_rate}%</div>
                  </div>

                  {/* Momentum Index */}
                  <div className="w-[100px] flex items-center justify-between">
                    <div>
                      <div className="text-[10px] uppercase font-bold text-zinc-500 flex items-center space-x-1">
                        <Award className="h-3 w-3 text-indigo-400" />
                        <span>Momentum</span>
                      </div>
                      <div className="text-sm font-bold text-indigo-400 mt-1">{cat.momentum_score.toFixed(1)}</div>
                    </div>
                    <ChevronRight className="h-5 w-5 text-zinc-600 group-hover:text-indigo-400 transition pl-2" />
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Slide-over Deep-Dive Analysis Drawer */}
      {activeCategorySlug && (
        <div className="fixed inset-y-0 right-0 w-full max-w-lg bg-zinc-900 border-l border-zinc-800 shadow-2xl z-50 flex flex-col h-full animate-slide-in">
          {/* Drawer Header */}
          <div className="p-6 border-b border-zinc-800 flex justify-between items-center bg-zinc-950/40">
            <div>
              <span className="text-[10px] uppercase font-bold text-zinc-500 tracking-wider">AI Analyst Drawer</span>
              <h3 className="text-xl font-bold text-zinc-100 flex items-center space-x-2 mt-1">
                <Zap className="h-5 w-5 text-indigo-400" />
                <span>{analysisData ? analysisData.category : "Loading..."}</span>
              </h3>
            </div>
            <button
              onClick={closeAnalysisDrawer}
              className="p-1 rounded-lg border border-zinc-800 hover:border-zinc-700 text-zinc-400 hover:text-zinc-200 transition cursor-pointer"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          {/* Drawer Content */}
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {analysisLoading ? (
              <div className="h-full flex flex-col justify-center items-center space-y-4">
                <Activity className="h-10 w-10 text-indigo-500 animate-spin" />
                <span className="text-zinc-500 text-xs font-semibold">Running structured analysis...</span>
              </div>
            ) : analysisData ? (
              <div className="space-y-6">
                {/* Confidence & Score widget */}
                <div className="flex items-center justify-between bg-zinc-950/40 p-4 border border-zinc-800/80 rounded-lg">
                  <div>
                    <div className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Data Confidence</div>
                    <div className="text-2xl font-black text-indigo-400 mt-1">
                      {(analysisData.confidence * 100).toFixed(0)}%
                    </div>
                  </div>
                  <div>
                    <div className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest text-right">Momentum</div>
                    <div className="text-2xl font-black text-indigo-400 mt-1 text-right">
                      {analysisData.momentum_score.toFixed(1)}/100
                    </div>
                  </div>
                </div>

                {/* Executive Summary Narrative */}
                <div className="space-y-2">
                  <h4 className="text-xs font-bold text-zinc-300 uppercase tracking-wider flex items-center space-x-1.5">
                    <BookOpen className="h-4 w-4 text-indigo-400" />
                    <span>AI Analysis Synthesis</span>
                  </h4>
                  <p className="text-xs text-zinc-400 leading-relaxed bg-zinc-950/60 p-4 border border-zinc-850 rounded-lg">
                    {analysisData.analysis}
                  </p>
                </div>

                {/* Opportunities & Risks lists */}
                <div className="grid grid-cols-1 gap-6">
                  {/* Strategic Opportunities */}
                  <div className="space-y-2 bg-emerald-950/5 border border-emerald-500/15 p-4 rounded-lg">
                    <h4 className="text-xs font-bold text-emerald-400 uppercase tracking-wider flex items-center space-x-1.5">
                      <Zap className="h-4 w-4 text-emerald-400" />
                      <span>Product Opportunities</span>
                    </h4>
                    <div className="space-y-1.5">
                      {analysisData.opportunities.map((opp, oidx) => (
                        <div key={oidx} className="flex items-start space-x-2 text-xs text-zinc-400 leading-relaxed">
                          <span className="text-emerald-400 font-bold shrink-0 mt-0.5">•</span>
                          <span>{opp}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Risks warning */}
                  <div className="space-y-2 bg-rose-950/5 border border-rose-500/15 p-4 rounded-lg">
                    <h4 className="text-xs font-bold text-rose-400 uppercase tracking-wider flex items-center space-x-1.5">
                      <ShieldAlert className="h-4 w-4 text-rose-400" />
                      <span>Critical Risks</span>
                    </h4>
                    <div className="space-y-1.5">
                      {analysisData.risks.map((risk, ridx) => (
                        <div key={ridx} className="flex items-start space-x-2 text-xs text-zinc-400 leading-relaxed">
                          <span className="text-rose-400 font-bold shrink-0 mt-0.5">•</span>
                          <span>{risk}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Leading Repositories */}
                <div className="space-y-3">
                  <h4 className="text-xs font-bold text-zinc-300 uppercase tracking-wider">Top Niche Repositories</h4>
                  <div className="space-y-2">
                    {analysisData.top_repositories.slice(0, 3).map((repo) => (
                      <div key={repo.full_name} className="p-3 bg-zinc-950/40 border border-zinc-800 rounded-lg flex items-center justify-between text-xs hover:border-zinc-700 transition">
                        <div>
                          <div className="font-bold text-zinc-200">{repo.name}</div>
                          <div className="text-[10px] text-zinc-500 truncate max-w-[240px] mt-0.5">{repo.description}</div>
                        </div>
                        <div className="flex items-center space-x-3 text-[11px] shrink-0 font-medium pl-2">
                          <span className="text-zinc-400 flex items-center space-x-1">
                            <span>{repo.stars.toLocaleString()}</span>
                            <Star className="h-3.5 w-3.5 text-zinc-500" />
                          </span>
                          <a href={repo.url} target="_blank" rel="noopener noreferrer" className="text-zinc-500 hover:text-zinc-300">
                            <ExternalLink className="h-3.5 w-3.5" />
                          </a>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Recent Signal Mentions */}
                <div className="space-y-3">
                  <h4 className="text-xs font-bold text-zinc-300 uppercase tracking-wider">Top Signal Sources (Mentions)</h4>
                  <div className="space-y-2">
                    {analysisData.top_signals.slice(0, 4).map((sig, sidx) => (
                      <div key={sidx} className="flex items-start space-x-2 text-xs text-zinc-400 leading-relaxed bg-zinc-950/30 p-2.5 border border-zinc-900 rounded">
                        <MessageSquare className="h-4 w-4 text-zinc-600 shrink-0 mt-0.5" />
                        <span>{sig}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <div className="h-full flex items-center justify-center text-zinc-500 text-xs">
                No analysis payload compiled.
              </div>
            )}
          </div>

          {/* Drawer Footer */}
          <div className="p-4 border-t border-zinc-800 bg-zinc-950/40 flex justify-end">
            <button
              onClick={closeAnalysisDrawer}
              className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 font-semibold rounded-lg text-xs transition cursor-pointer"
            >
              Close Drawer
            </button>
          </div>
        </div>
      )}
    </main>
  );
}
