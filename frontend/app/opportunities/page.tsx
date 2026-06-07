"use client";

import { useEffect, useState } from "react";
import { Activity, Lightbulb, TrendingUp, Sparkles, CheckCircle } from "lucide-react";

export default function OpportunitiesPage() {
  const [opportunities, setOpportunities] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("http://localhost:8000/opportunities")
      .then((res) => res.json())
      .then((data) => {
        setOpportunities(Array.isArray(data) ? data : []);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Opportunities Fetch Error:", err);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center p-10 bg-zinc-950">
        <div className="text-center space-y-4">
          <Activity className="h-10 w-10 text-indigo-500 animate-spin mx-auto" />
          <h2 className="text-lg font-bold text-zinc-100">Synthesizing Startup Gaps...</h2>
        </div>
      </div>
    );
  }

  return (
    <main className="p-8 max-w-7xl mx-auto w-full space-y-8 bg-zinc-950/20 min-h-screen">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-extrabold tracking-tight text-zinc-50">
          Startup <span className="gradient-text">Opportunities</span>
        </h1>
        <p className="text-zinc-400 text-sm mt-2">
          Gaps in the AI ecosystem identified by comparing high demand volume against existing tool density.
        </p>
      </div>

      {/* Opportunities Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {opportunities.map((opp) => (
          <div key={opp.id} className="glass-card p-6 flex flex-col justify-between relative overflow-hidden">
            {/* Corner Score Glow */}
            <div className="absolute top-0 right-0 w-24 h-24 bg-indigo-500/10 rounded-full blur-2xl pointer-events-none" />
            
            <div>
              {/* Header */}
              <div className="flex justify-between items-start">
                <div>
                  <span className="text-[10px] uppercase font-bold text-zinc-500 tracking-wider">Market Niche: {opp.niche}</span>
                  <h3 className="text-xl font-bold text-zinc-50 mt-1 flex items-center space-x-2">
                    <Lightbulb className="h-5 w-5 text-indigo-400" />
                    <span>{opp.title}</span>
                  </h3>
                </div>
                
                <div className="text-center">
                  <div className="text-[10px] uppercase font-bold text-zinc-500 tracking-wider">Opportunity</div>
                  <div className="text-2xl font-black text-indigo-400 mt-0.5">{opp.opportunity_score}</div>
                </div>
              </div>

              {/* Description */}
              <p className="text-zinc-400 text-sm mt-4 leading-relaxed">
                {opp.description}
              </p>

              {/* Metric Scores */}
              <div className="grid grid-cols-2 gap-4 mt-6 py-4 border-t border-b border-zinc-800/80">
                {/* Demand */}
                <div className="space-y-1">
                  <div className="flex justify-between text-xs font-semibold text-zinc-400">
                    <span>Market Demand</span>
                    <span className="text-zinc-200">{opp.demand_score}/100</span>
                  </div>
                  <div className="w-full bg-zinc-800 h-1 rounded-full overflow-hidden">
                    <div className="bg-emerald-500 h-1 rounded-full" style={{ width: `${opp.demand_score}%` }} />
                  </div>
                </div>

                {/* Competition */}
                <div className="space-y-1">
                  <div className="flex justify-between text-xs font-semibold text-zinc-400">
                    <span>Competition Density</span>
                    <span className="text-zinc-200">{opp.competition_score}/100</span>
                  </div>
                  <div className="w-full bg-zinc-800 h-1 rounded-full overflow-hidden">
                    <div className="bg-rose-500 h-1 rounded-full" style={{ width: `${opp.competition_score}%` }} />
                  </div>
                </div>
              </div>

              {/* Startup Launch Ideas */}
              <div className="mt-6 space-y-3">
                <h4 className="text-xs font-bold uppercase text-zinc-300 tracking-wider flex items-center space-x-1.5">
                  <Sparkles className="h-3.5 w-3.5 text-indigo-400" />
                  <span>SaaS Launch Concepts</span>
                </h4>
                <div className="space-y-2">
                  {(opp.parsed_ideas || []).map((idea: string, idx: number) => (
                    <div key={idx} className="flex items-start space-x-2 bg-zinc-900/40 border border-zinc-800/50 p-3 rounded-lg text-xs text-zinc-300 hover:border-zinc-800 transition">
                      <CheckCircle className="h-4 w-4 text-indigo-500/80 mt-0.5 shrink-0" />
                      <span className="leading-relaxed">{idea}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </main>
  );
}
