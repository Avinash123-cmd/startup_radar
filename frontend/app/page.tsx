"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import TrendChart from "../component/TrendChart";
import type { CategoryPrediction, Opportunity, QuickInsight, TrendSummary } from "../types/api";
import { 
  TrendingUp, 
  Lightbulb, 
  Database, 
  ArrowUpRight, 
  Activity, 
  Award,
  AlertCircle
} from "lucide-react";

export default function Home() {
  const [trends, setTrends] = useState<TrendSummary[]>([]);
  const [insight, setInsight] = useState<QuickInsight | null>(null);
  const [predictions, setPredictions] = useState<CategoryPrediction[]>([]);
  const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const [trendsRes, insightRes, predictionsRes, oppsRes] = await Promise.all([
          fetch("http://localhost:8000/trends").then(res => res.json()),
          fetch("http://localhost:8000/insights").then(res => res.json()),
          fetch("http://localhost:8000/predictions").then(res => res.json()),
          fetch("http://localhost:8000/opportunities").then(res => res.json())
        ]);
        
        setTrends(Array.isArray(trendsRes) ? trendsRes : []);
        setInsight(insightRes);
        setPredictions(Array.isArray(predictionsRes) ? predictionsRes : []);
        setOpportunities(Array.isArray(oppsRes) ? oppsRes : []);
        setError(false);
      } catch (err) {
        console.error("Dashboard Loading Error:", err);
        setError(true);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center p-10 bg-zinc-950">
        <div className="text-center space-y-4">
          <Activity className="h-12 w-12 text-indigo-500 animate-spin mx-auto" />
          <h2 className="text-xl font-bold text-zinc-100">Synchronizing Market Signals...</h2>
          <p className="text-zinc-500 text-sm">Please wait while the AI Startup Radar loads emerging niche signals.</p>
        </div>
      </div>
    );
  }

  if (error || trends.length === 0) {
    return (
      <div className="flex-1 p-10 bg-zinc-950 max-w-7xl mx-auto w-full flex flex-col justify-center">
        <div className="border border-zinc-800 bg-zinc-900/40 backdrop-blur-md rounded-xl p-8 max-w-xl mx-auto text-center space-y-4">
          <AlertCircle className="h-12 w-12 text-indigo-500 mx-auto" />
          <h2 className="text-2xl font-bold text-zinc-100">No signals found</h2>
          <p className="text-zinc-400 text-sm leading-relaxed">
            The database appears to be offline or initializing. Please configure your settings or trigger a manual synchronization.
          </p>
          <div className="pt-4">
            <Link href="/settings" className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 font-semibold text-sm transition-all">
              <span>Go to Settings</span>
              <ArrowUpRight className="h-4 w-4" />
            </Link>
          </div>
        </div>
      </div>
    );
  }

  // Calculate high-level summary metrics
  const topCategory = trends.length > 0 ? [...trends].sort((a, b) => b.momentum_score - a.momentum_score)[0] : null;
  const totalNewsVolume = trends.reduce((acc, curr) => acc + curr.news_volume, 0);
  const totalStarsCount = trends.reduce((acc, curr) => acc + curr.star_count, 0);

  return (
    <main className="p-8 max-w-7xl mx-auto w-full space-y-8 bg-zinc-950/20 min-h-screen">
      {/* Welcome Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between space-y-4 md:space-y-0">
        <div>
          <h1 className="text-4xl font-extrabold tracking-tight text-zinc-50">
            AI Startup <span className="gradient-text">Radar</span>
          </h1>
          <p className="text-zinc-400 text-sm mt-2">
            AI-powered market intelligence dashboard tracking emerging tech niches and SaaS opportunities.
          </p>
        </div>
        <div className="flex items-center space-x-2 bg-zinc-900/60 border border-zinc-800 px-4 py-2 rounded-lg text-xs font-semibold text-zinc-400">
          <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
          <span>Pipeline Ingestion Active</span>
        </div>
      </div>

      {/* Grid: Stat Widgets */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Widget 1: Total Stars */}
        <div className="glass-card p-6 flex flex-col justify-between">
          <div className="flex justify-between items-start">
            <div>
              <span className="text-xs uppercase font-bold text-zinc-500 tracking-wider">Total Repos Stars</span>
              <h3 className="text-3xl font-extrabold mt-1 text-zinc-50">{totalStarsCount.toLocaleString()}</h3>
            </div>
            <div className="p-2.5 rounded-lg bg-indigo-600/10 border border-indigo-500/20 text-indigo-400">
              <Database className="h-5 w-5" />
            </div>
          </div>
          <div className="text-xs text-zinc-400 mt-4 font-semibold">
            Tracked across <span className="text-zinc-200">{trends.length} categories</span>
          </div>
        </div>

        {/* Widget 2: Social Volume */}
        <div className="glass-card p-6 flex flex-col justify-between">
          <div className="flex justify-between items-start">
            <div>
              <span className="text-xs uppercase font-bold text-zinc-500 tracking-wider">30d Mentions & Papers</span>
              <h3 className="text-3xl font-extrabold mt-1 text-zinc-50">{totalNewsVolume.toLocaleString()}</h3>
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
        <div className="glass-card p-6 flex flex-col justify-between">
          <div className="flex justify-between items-start">
            <div>
              <span className="text-xs uppercase font-bold text-zinc-500 tracking-wider">Emerging Leader</span>
              <h3 className="text-lg font-extrabold mt-2 text-zinc-100 truncate max-w-[200px]">
                {topCategory ? topCategory.name : "N/A"}
              </h3>
            </div>
            <div className="p-2.5 rounded-lg bg-emerald-600/10 border border-emerald-500/20 text-emerald-400">
              <Award className="h-5 w-5" />
            </div>
          </div>
          <div className="text-xs text-zinc-400 mt-4 flex items-center space-x-1 font-semibold">
            <span>Momentum index:</span>
            <span className="text-emerald-400 font-extrabold">{topCategory ? topCategory.momentum_score : 0}</span>
          </div>
        </div>
      </div>

      {/* Grid: Primary content + side bar */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main Chart Column */}
        <div className="lg:col-span-2 space-y-6">
          <TrendChart data={trends} />
          
          {/* AI Briefing Summary Widget */}
          {insight && (
            <div className="border border-zinc-800 bg-zinc-900/20 rounded-xl p-6 relative overflow-hidden">
              <div className="absolute top-0 right-0 p-3 text-xs bg-indigo-500/15 text-indigo-400 border-l border-b border-indigo-500/30 rounded-bl-lg font-semibold uppercase tracking-wider">
                AI Intelligence Layer
              </div>
              <h3 className="text-lg font-bold text-zinc-100 flex items-center space-x-2">
                <span>💡 Weekly Synthesis</span>
              </h3>
              <p className="text-sm text-zinc-400 leading-relaxed mt-4">
                {insight.insight}
              </p>
              <div className="mt-6 flex justify-between items-center text-xs pt-4 border-t border-zinc-900">
                <span className="text-zinc-500">Market Leader: <strong className="text-zinc-300">{insight.leader}</strong></span>
                <Link href="/reports" className="text-indigo-400 hover:text-indigo-300 font-bold flex items-center space-x-1">
                  <span>Read full report</span>
                  <ArrowUpRight className="h-3.5 w-3.5" />
                </Link>
              </div>
            </div>
          )}
        </div>

        {/* Side column: Predictions and Opportunity ranks */}
        <div className="space-y-8">
          {/* Predict List */}
          <div className="border border-zinc-800 bg-zinc-900/40 backdrop-blur-md rounded-xl p-6 shadow-xl">
            <h2 className="text-lg font-bold text-zinc-100 flex items-center space-x-2 border-b border-zinc-800 pb-4 mb-4">
              <span>🔮 AI Growth Predictions</span>
            </h2>
            <div className="space-y-4">
              {predictions.slice(0, 4).map((pred, i) => (
                <div key={pred.category} className="flex flex-col space-y-1.5">
                  <div className="flex justify-between text-sm">
                    <span className="font-semibold text-zinc-300 truncate max-w-[170px]">
                      {i + 1}. {pred.category}
                    </span>
                    <span className="font-bold text-indigo-400">{pred.growth_probability}% prob</span>
                  </div>
                  <div className="w-full bg-zinc-800 rounded-full h-1.5 overflow-hidden">
                    <div 
                      className="bg-gradient-to-r from-indigo-500 to-cyan-400 h-1.5 rounded-full" 
                      style={{ width: `${pred.growth_probability}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Opportunity highlight list */}
          <div className="border border-zinc-800 bg-zinc-900/40 backdrop-blur-md rounded-xl p-6 shadow-xl">
            <h2 className="text-lg font-bold text-zinc-100 flex items-center space-x-2 border-b border-zinc-800 pb-4 mb-4">
              <Lightbulb className="h-5 w-5 text-zinc-100" />
              <span>Startup Opportunities</span>
            </h2>
            <div className="space-y-4">
              {opportunities.slice(0, 3).map((opp) => (
                <div key={opp.id} className="flex justify-between items-center py-2 border-b border-zinc-800 last:border-b-0">
                  <div>
                    <h4 className="text-sm font-bold text-zinc-200">{opp.title}</h4>
                    <span className="text-[10px] text-zinc-500 font-semibold uppercase">{opp.niche}</span>
                  </div>
                  <div className="bg-indigo-900/30 border border-indigo-500/20 px-2 py-1 rounded text-xs font-bold text-indigo-400">
                    Score: {opp.opportunity_score}
                  </div>
                </div>
              ))}
              <div className="pt-2">
                <Link href="/opportunities" className="w-full py-2.5 rounded-lg bg-zinc-800/80 hover:bg-zinc-800 text-xs font-bold text-zinc-300 flex items-center justify-center space-x-1 border border-zinc-700">
                  <span>Explore Gaps & Ideas</span>
                  <ArrowUpRight className="h-3.5 w-3.5" />
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
