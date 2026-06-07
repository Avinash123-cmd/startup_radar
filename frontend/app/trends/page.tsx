"use client";

import { useEffect, useState } from "react";
import CategoryHeatmap from "../../component/CategoryHeatmap";
import { Activity, Star, MessageSquare, Award } from "lucide-react";

export default function TrendsPage() {
  const [trends, setTrends] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

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
    <main className="p-8 max-w-7xl mx-auto w-full space-y-8 bg-zinc-950/20 min-h-screen">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-extrabold tracking-tight text-zinc-50">
          AI Niches <span className="gradient-text">Trends</span>
        </h1>
        <p className="text-zinc-400 text-sm mt-2">
          Tracking the growth velocity, news volumes, and developer momentum index of core AI domains.
        </p>
      </div>

      {/* Heatmap Section */}
      {trends.length > 0 && <CategoryHeatmap data={trends} />}

      {/* Categories Catalog */}
      <div className="border border-zinc-800 bg-zinc-900/40 backdrop-blur-md rounded-xl shadow-xl overflow-hidden">
        <div className="p-6 border-b border-zinc-800">
          <h3 className="text-lg font-bold text-zinc-100">Market Domain Inventory</h3>
          <p className="text-xs text-zinc-400 font-semibold uppercase tracking-wider mt-1">Detailed niche catalog and growth diagnostics</p>
        </div>
        
        <div className="divide-y divide-zinc-800">
          {trends.map((cat, index) => (
            <div key={cat.category_id} className="p-6 hover:bg-zinc-900/25 transition duration-200 flex flex-col md:flex-row md:items-center justify-between gap-6">
              {/* Category info */}
              <div className="md:max-w-md flex items-start space-x-4">
                <div className="bg-indigo-950/50 border border-indigo-500/20 px-3 py-1.5 rounded-lg text-sm font-bold text-indigo-400">
                  {index + 1}
                </div>
                <div>
                  <h4 className="text-base font-extrabold text-zinc-100">{cat.name}</h4>
                  <p className="text-xs text-zinc-400 mt-1 leading-relaxed">{cat.description}</p>
                </div>
              </div>

              {/* Metrics blocks */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-6 text-left">
                {/* Total Stars */}
                <div>
                  <div className="text-[10px] uppercase font-bold text-zinc-500 flex items-center space-x-1">
                    <Star className="h-3 w-3" />
                    <span>Total Stars</span>
                  </div>
                  <div className="text-sm font-bold text-zinc-200 mt-1">
                    {cat.star_count.toLocaleString()}
                  </div>
                </div>

                {/* 30d Growth */}
                <div>
                  <div className="text-[10px] uppercase font-bold text-zinc-500">30d Growth</div>
                  <div className="text-sm font-bold text-emerald-400 mt-1">
                    +{cat.star_growth_30d.toLocaleString()} (+{cat.growth_rate}%)
                  </div>
                </div>

                {/* News Mentions */}
                <div>
                  <div className="text-[10px] uppercase font-bold text-zinc-500 flex items-center space-x-1">
                    <MessageSquare className="h-3 w-3" />
                    <span>Mentions</span>
                  </div>
                  <div className="text-sm font-bold text-zinc-200 mt-1">
                    {cat.news_volume}
                  </div>
                </div>

                {/* Momentum Index */}
                <div>
                  <div className="text-[10px] uppercase font-bold text-zinc-500 flex items-center space-x-1">
                    <Award className="h-3 w-3" />
                    <span>Momentum</span>
                  </div>
                  <div className="text-sm font-bold text-indigo-400 mt-1">
                    {cat.momentum_score}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </main>
  );
}
