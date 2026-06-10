"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import TrendChart from "../component/TrendChart";
import type { ExecutiveDashboardResponse } from "../types/api";
import {
  TrendingUp,
  Lightbulb,
  Database,
  ArrowUpRight,
  Activity,
  Award,
  AlertCircle,
  Bell,
  Sparkles,
  Zap,
  TrendingDown,
  ShieldCheck,
  RefreshCw
} from "lucide-react";
import { API_BASE_URL, fetchWithCache } from "../component/apiHelper";
import WidgetContainer from "../component/WidgetContainer";

export default function Home() {
  const [data, setData] = useState<ExecutiveDashboardResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const fetchData = async (force = false) => {
    try {
      setLoading(true);
      setError(false);
      const url = `${API_BASE_URL}/executive-dashboard${force ? "?force_refresh=true" : ""}`;
      const json = await fetchWithCache<ExecutiveDashboardResponse>(url, { forceRefresh: force });
      setData(json);
    } catch (err) {
      console.error("Dashboard Loading Error:", err);
      setError(true);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  // Aggregate metrics from backend trends list
  const totalStarsCount = data?.fastest_growing_categories?.reduce((acc, curr) => acc + curr.star_count, 0) || 0;
  const totalNewsVolume = data?.fastest_growing_categories?.reduce((acc, curr) => acc + curr.news_volume, 0) || 0;
  const topNiche = data?.fastest_growing_categories?.[0] || null;

  return (
    <main className="p-8 max-w-7xl mx-auto w-full space-y-8 bg-zinc-950/20 min-h-screen">
      {/* Welcome Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between space-y-4 md:space-y-0 border-b border-zinc-900 pb-6">
        <div>
          <h1 className="text-4xl font-extrabold tracking-tight text-zinc-50 font-sans">
            AI Startup <span className="gradient-text">Radar</span> <span className="text-xs font-bold uppercase tracking-widest text-indigo-400 bg-indigo-950/40 border border-indigo-500/30 px-2 py-0.5 rounded ml-2">V3 Platform</span>
          </h1>
          <p className="text-zinc-400 text-sm mt-2">
            Founder Decision Platform converting developer mindshare, forecasts, and anomalies into actionable SaaS opportunities.
          </p>
        </div>
        <div className="flex items-center space-x-4">
          <button
            onClick={() => fetchData(true)}
            disabled={loading}
            className="flex items-center space-x-2 px-4 py-2 bg-zinc-900 hover:bg-zinc-800 disabled:opacity-50 border border-zinc-850 rounded-lg text-xs font-bold text-zinc-300 transition cursor-pointer"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin text-indigo-400' : 'text-zinc-400'}`} />
            <span>{loading ? "Syncing..." : "Sync Engine"}</span>
          </button>
          <div className="flex items-center space-x-2 bg-zinc-900/60 border border-zinc-800 px-4 py-2 rounded-lg text-xs font-semibold text-zinc-400">
            <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
            <span>V3 Live Engines Connected</span>
          </div>
        </div>
      </div>

      {/* Grid: Stat Widgets */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Widget 1: Total Stars */}
        <div className="glass-card p-6 flex flex-col justify-between relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-24 h-24 bg-indigo-500/5 rounded-full blur-2xl group-hover:bg-indigo-500/10 transition duration-300" />
          <div className="flex justify-between items-start">
            <div>
              <span className="text-xs uppercase font-bold text-zinc-500 tracking-wider">Total Repos Stars</span>
              <h3 className="text-3xl font-extrabold mt-1 text-zinc-50">
                {loading ? "..." : error ? "N/A" : totalStarsCount.toLocaleString()}
              </h3>
            </div>
            <div className="p-2.5 rounded-lg bg-indigo-600/10 border border-indigo-500/20 text-indigo-400">
              <Database className="h-5 w-5" />
            </div>
          </div>
          <div className="text-xs text-zinc-400 mt-4 font-semibold">
            Tracked across <span className="text-indigo-400 font-bold">{loading ? "..." : error ? "0" : (data?.fastest_growing_categories?.length || 0)} categories</span>
          </div>
        </div>

        {/* Widget 2: Social Volume */}
        <div className="glass-card p-6 flex flex-col justify-between relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-24 h-24 bg-cyan-500/5 rounded-full blur-2xl group-hover:bg-cyan-500/10 transition duration-300" />
          <div className="flex justify-between items-start">
            <div>
              <span className="text-xs uppercase font-bold text-zinc-500 tracking-wider">30d Mentions & Papers</span>
              <h3 className="text-3xl font-extrabold mt-1 text-zinc-50">
                {loading ? "..." : error ? "N/A" : totalNewsVolume.toLocaleString()}
              </h3>
            </div>
            <div className="p-2.5 rounded-lg bg-cyan-600/10 border border-cyan-500/20 text-cyan-400">
              <TrendingUp className="h-5 w-5" />
            </div>
          </div>
          <div className="text-xs text-zinc-400 mt-4 font-semibold">
            GitHub, Reddit, HN, & arXiv signals
          </div>
        </div>

        {/* Widget 3: Top Niche */}
        <div className="glass-card p-6 flex flex-col justify-between relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-24 h-24 bg-emerald-500/5 rounded-full blur-2xl group-hover:bg-emerald-500/10 transition duration-300" />
          <div className="flex justify-between items-start">
            <div>
              <span className="text-xs uppercase font-bold text-zinc-500 tracking-wider">Fastest Growing Niche</span>
              <h3 className="text-lg font-extrabold mt-2 text-zinc-100 truncate max-w-[200px]">
                {loading ? "Loading..." : error ? "N/A" : (topNiche ? topNiche.name : "N/A")}
              </h3>
            </div>
            <div className="p-2.5 rounded-lg bg-emerald-600/10 border border-emerald-500/20 text-emerald-400">
              <Award className="h-5 w-5" />
            </div>
          </div>
          <div className="text-xs text-zinc-400 mt-4 flex items-center space-x-1 font-semibold">
            <span>Peak growth rate:</span>
            <span className="text-emerald-400 font-extrabold">
              {loading ? "..." : error ? "0%" : `+${topNiche ? topNiche.growth_rate : 0}%`}
            </span>
          </div>
        </div>
      </div>

      {/* AI Analyst Macro Summary Layer */}
      <div className="border border-zinc-800 bg-zinc-900/20 rounded-xl p-6 relative overflow-hidden">
        <div className="absolute top-0 right-0 p-3 text-xs bg-indigo-500/15 text-indigo-400 border-l border-b border-indigo-500/30 rounded-bl-lg font-semibold uppercase tracking-wider flex items-center space-x-1">
          <Sparkles className="h-3.5 w-3.5 animate-pulse" />
          <span>AI Analyst Assessment</span>
        </div>
        <h3 className="text-lg font-bold text-zinc-100 flex items-center space-x-2">
          <span>🤖 Macro Intelligence Briefing</span>
        </h3>
        
        <WidgetContainer title="AI Briefing" loading={loading} error={error || !data?.ai_summary}>
          {data?.ai_summary && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-4 pt-2">
              <div className="space-y-1 bg-zinc-950/40 p-4 border border-zinc-800/80 rounded-lg">
                <h4 className="text-xs font-bold uppercase text-indigo-400 tracking-wider flex items-center space-x-1">
                  <ShieldCheck className="h-3.5 w-3.5 text-indigo-400" />
                  <span>Executive Synthesis</span>
                </h4>
                <p className="text-sm text-zinc-300 leading-relaxed pt-1.5">
                  {data.ai_summary.executive_summary}
                </p>
              </div>

              <div className="space-y-1 bg-zinc-950/40 p-4 border border-zinc-800/80 rounded-lg">
                <h4 className="text-xs font-bold uppercase text-amber-500 tracking-wider flex items-center space-x-1">
                  <AlertCircle className="h-3.5 w-3.5 text-amber-500" />
                  <span>Headwinds & Competition Risks</span>
                </h4>
                <p className="text-sm text-zinc-300 leading-relaxed pt-1.5">
                  {data.ai_summary.market_risk_summary}
                </p>
              </div>
            </div>
          )}
        </WidgetContainer>
      </div>

      {/* YC Partner Launch Cards Panel */}
      <div className="space-y-4">
        <h2 className="text-lg font-bold text-zinc-100 flex items-center space-x-2">
          <Zap className="h-5 w-5 text-indigo-400" />
          <span>Actionable Founder Launch Cards</span>
        </h2>
        
        <WidgetContainer 
          title="Founder Launch Cards" 
          loading={loading} 
          error={error || !data?.founder_recommendations} 
          isEmpty={data?.founder_recommendations?.length === 0}
        >
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {data?.founder_recommendations?.map((rec, idx) => {
              let typeColor = "border-indigo-500/30 bg-indigo-950/10 text-indigo-400";
              let typeLabel = "Conviction Play";
              
              if (rec.rec_type === "entry") {
                typeColor = "border-emerald-500/30 bg-emerald-950/10 text-emerald-400";
                typeLabel = "Lean Entry Index";
              } else if (rec.rec_type === "venture") {
                typeColor = "border-amber-500/30 bg-amber-950/10 text-amber-400";
                typeLabel = "Venture Scale TAM";
              } else if (rec.rec_type === "timing") {
                typeColor = "border-cyan-500/30 bg-cyan-950/10 text-cyan-400";
                typeLabel = "Optimal Timing Window";
              }

              return (
                <div
                  key={`${rec.category}-${rec.rec_type}-${idx}`}
                  className="border border-zinc-800 bg-zinc-900/40 rounded-xl p-5 flex flex-col justify-between hover:border-zinc-700 transition duration-200"
                >
                  <div>
                    <div className={`text-[10px] font-extrabold uppercase px-2 py-0.5 rounded border inline-block ${typeColor}`}>
                      {typeLabel}
                    </div>
                    <h4 className="text-base font-bold text-zinc-100 mt-3">{rec.category}</h4>
                    <p className="text-xs text-zinc-400 mt-2 leading-relaxed">{rec.text}</p>
                  </div>
                  <div className="mt-5 pt-3 border-t border-zinc-950 flex justify-between items-center text-xs">
                    <span className="font-extrabold text-zinc-300">{rec.metric}</span>
                    <Link
                      href={`/opportunities?category=${rec.category_slug}`}
                      className="text-indigo-400 hover:text-indigo-300 font-bold flex items-center space-x-1"
                    >
                      <span>View Launch Brief</span>
                      <ArrowUpRight className="h-3.5 w-3.5" />
                    </Link>
                  </div>
                </div>
              );
            })}
          </div>
        </WidgetContainer>
      </div>

      {/* Grid: Primary chart + Side Column */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Chart Column */}
        <div className="lg:col-span-2 space-y-6">
          <WidgetContainer title="Market Trends Chart" loading={loading} error={error || !data?.fastest_growing_categories}>
            {data?.fastest_growing_categories && (
              <TrendChart data={data.fastest_growing_categories} />
            )}
          </WidgetContainer>

          {/* Watchlist Alerts Tray (Buried alerts decoupled) */}
          <div className="border border-zinc-800 bg-zinc-900/40 rounded-xl p-6 shadow-xl space-y-4">
            <div className="flex justify-between items-center border-b border-zinc-800 pb-3">
              <h3 className="text-sm font-extrabold text-zinc-200 uppercase tracking-wider flex items-center space-x-2">
                <Bell className="h-4 w-4 text-indigo-400" />
                <span>Watchlist Alerts Notification Feed</span>
              </h3>
              <Link href="/watchlist" className="text-xs text-indigo-400 hover:text-indigo-300 font-bold flex items-center space-x-1">
                <span>Anomaly Inbox</span>
                <ArrowUpRight className="h-3.5 w-3.5" />
              </Link>
            </div>

            <WidgetContainer title="Watchlist Notification Feed" loading={loading} error={error || !data?.watchlist_alerts_summary}>
              {data?.watchlist_alerts_summary && (
                <>
                  {data.watchlist_alerts_summary.recent_alerts.length === 0 ? (
                    <p className="text-xs text-zinc-500 font-medium py-4 text-center">No anomalies triggered inside watchlist channels.</p>
                  ) : (
                    <div className="divide-y divide-zinc-800/80">
                      {data.watchlist_alerts_summary.recent_alerts.slice(0, 3).map((alert) => {
                        let alertBadge = "text-blue-400 bg-blue-950/30 border-blue-500/20";
                        if (alert.severity === "CRITICAL") alertBadge = "text-rose-400 bg-rose-950/30 border-rose-500/20";
                        else if (alert.severity === "HIGH") alertBadge = "text-amber-400 bg-amber-950/30 border-amber-500/20";
                        
                        return (
                          <div key={alert.id} className="py-3 flex justify-between items-center text-xs">
                            <div className="space-y-1">
                              <div className="flex items-center space-x-2">
                                <span className={`text-[9px] font-bold px-1.5 py-0.2 rounded border ${alertBadge}`}>
                                  {alert.severity}
                                </span>
                                <span className="font-extrabold text-zinc-200">{alert.title}</span>
                              </div>
                              <p className="text-zinc-400 max-w-lg leading-relaxed">{alert.message}</p>
                            </div>
                            <span className="text-[10px] text-zinc-500 font-semibold uppercase">{alert.alert_type.replace(/_/g, " ")}</span>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </>
              )}
            </WidgetContainer>
          </div>
        </div>

        {/* Side Panel: Predictions and Opportunities */}
        <div className="space-y-8">
          {/* AI Growth Predictions */}
          <div className="border border-zinc-800 bg-zinc-900/40 backdrop-blur-md rounded-xl p-6 shadow-xl">
            <h2 className="text-base font-extrabold text-zinc-100 flex items-center space-x-2 border-b border-zinc-800 pb-4 mb-4">
              <span>🔮 AI Growth Predictions</span>
            </h2>
            <WidgetContainer title="AI Growth Predictions" loading={loading} error={error || !data?.highest_confidence_predictions}>
              <div className="space-y-5">
                {data?.highest_confidence_predictions?.slice(0, 4).map((pred, i) => (
                  <div key={`${pred.category}-${i}`} className="flex flex-col space-y-1.5">
                    <div className="flex justify-between items-center text-sm">
                      <span className="font-bold text-zinc-200 truncate max-w-[150px]">
                        {i + 1}. {pred.category}
                      </span>
                      <div className="flex items-center space-x-2">
                        <span className="text-xs text-zinc-400">({pred.confidence.toFixed(0)}% conf)</span>
                        {pred.slope > 0 ? (
                          <TrendingUp className="h-3.5 w-3.5 text-emerald-400" />
                        ) : (
                          <TrendingDown className="h-3.5 w-3.5 text-rose-400" />
                        )}
                        <span className="font-extrabold text-indigo-400">{pred.growth_probability}% prob</span>
                      </div>
                    </div>
                    <div className="w-full bg-zinc-800/80 rounded-full h-1.5 overflow-hidden">
                      <div
                        className="bg-gradient-to-r from-indigo-500 to-cyan-400 h-1.5 rounded-full"
                        style={{ width: `${pred.growth_probability}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </WidgetContainer>
          </div>

          {/* Startup Opportunities */}
          <div className="border border-zinc-800 bg-zinc-900/40 backdrop-blur-md rounded-xl p-6 shadow-xl">
            <h2 className="text-base font-extrabold text-zinc-100 flex items-center space-x-2 border-b border-zinc-800 pb-4 mb-4">
              <Lightbulb className="h-5 w-5 text-indigo-400 animate-pulse" />
              <span>Conviction Gaps</span>
            </h2>
            <WidgetContainer title="Conviction Gaps" loading={loading} error={error || !data?.top_opportunities}>
              <div className="space-y-4">
                {data?.top_opportunities?.slice(0, 3).map((opp, idx) => (
                  <div key={`${opp.category_id}-${idx}`} className="flex justify-between items-center py-2.5 border-b border-zinc-800 last:border-b-0">
                    <div className="space-y-0.5">
                      <h4 className="text-sm font-bold text-zinc-200">{opp.category}</h4>
                      <div className="flex flex-wrap gap-1">
                        {opp.strongest_signals.slice(0, 1).map((sig, sidx) => (
                          <span key={sidx} className="text-[9px] text-indigo-400 bg-indigo-950/40 border border-indigo-500/20 px-1 py-0.2 rounded font-semibold truncate max-w-[160px]">
                            {sig}
                          </span>
                        ))}
                      </div>
                    </div>
                    <div className="bg-indigo-900/30 border border-indigo-500/25 px-2.5 py-1 rounded text-xs font-black text-indigo-400 shrink-0">
                      {opp.success_probability}% Prob
                    </div>
                  </div>
                ))}
                <div className="pt-2">
                  <Link
                    href="/opportunities"
                    className="w-full py-2.5 rounded-lg bg-zinc-800/80 hover:bg-zinc-800 text-xs font-bold text-zinc-300 flex items-center justify-center space-x-1 border border-zinc-700 transition"
                  >
                    <span>Explore Gaps & Blueprints</span>
                    <ArrowUpRight className="h-3.5 w-3.5" />
                  </Link>
                </div>
              </div>
            </WidgetContainer>
          </div>
        </div>
      </div>
    </main>
  );
}
