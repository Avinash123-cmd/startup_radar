"use client";

import { useEffect, useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import {
  Activity,
  Lightbulb,
  Sparkles,
  CheckCircle,
  HelpCircle,
  TrendingUp,
  AlertTriangle,
  Bookmark,
  ChevronRight,
  ShieldCheck,
  ChevronDown,
  Info
} from "lucide-react";
import type { OpportunityV2, StartupBriefV2 } from "../../types/api";

function OpportunitiesPageContent() {
  const searchParams = useSearchParams();
  const categoryFilter = searchParams.get("category") || "";

  const [activeTab, setActiveTab] = useState<"gaps" | "blueprints">("gaps");
  const [opportunities, setOpportunities] = useState<OpportunityV2[]>([]);
  const [briefs, setBriefs] = useState<StartupBriefV2[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedBrief, setSelectedBrief] = useState<StartupBriefV2 | null>(null);

  useEffect(() => {
    const fetchOppsAndBriefs = async () => {
      try {
        setLoading(true);
        const [oppsRes, briefsRes] = await Promise.all([
          fetch("http://localhost:8000/opportunities/v2?limit=50").then((res) => res.json()),
          fetch("http://localhost:8000/startup-generator?limit=50").then((res) => res.json()),
        ]);

        const oppsList = Array.isArray(oppsRes.opportunities) ? oppsRes.opportunities : [];
        const briefsList = Array.isArray(briefsRes.briefs) ? briefsRes.briefs : [];

        // Apply URL category filter if present
        if (categoryFilter) {
          const filteredOpps = oppsList.filter((o: OpportunityV2) => o.category_slug === categoryFilter);
          const filteredBriefs = briefsList.filter((b: StartupBriefV2) => b.category_slug === categoryFilter);
          setOpportunities(filteredOpps.length > 0 ? filteredOpps : oppsList);
          setBriefs(filteredBriefs.length > 0 ? filteredBriefs : briefsList);
        } else {
          setOpportunities(oppsList);
          setBriefs(briefsList);
        }

        if (briefsList.length > 0) {
          setSelectedBrief(
            categoryFilter
              ? briefsList.find((b: StartupBriefV2) => b.category_slug === categoryFilter) || briefsList[0]
              : briefsList[0]
          );
        }
        setLoading(false);
      } catch (err) {
        console.error("Opportunities Fetch Error:", err);
        setLoading(false);
      }
    };

    fetchOppsAndBriefs();
  }, [categoryFilter]);

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center p-10 bg-zinc-950">
        <div className="text-center space-y-4">
          <Activity className="h-10 w-10 text-indigo-500 animate-spin mx-auto" />
          <h2 className="text-lg font-bold text-zinc-100">Synthesizing Startup Gaps & Blueprints...</h2>
          <p className="text-xs text-zinc-500">Calculating six-factor criteria, ARR revenue potentials, and GTM paths.</p>
        </div>
      </div>
    );
  }

  return (
    <main className="p-8 max-w-7xl mx-auto w-full space-y-8 bg-zinc-950/20 min-h-screen">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between border-b border-zinc-900 pb-6 gap-4">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-zinc-50">
            Founder <span className="gradient-text">Workspace</span>
          </h1>
          <p className="text-zinc-400 text-sm mt-2">
            Actionable startup entry channels derived from Live Opportunity Scoring V2 and Startup Brief Blueprints.
          </p>
        </div>

        {/* Tab Switcher */}
        <div className="flex bg-zinc-900 border border-zinc-800 p-1.5 rounded-xl space-x-1 self-start md:self-center">
          <button
            onClick={() => setActiveTab("gaps")}
            className={`px-4 py-2 rounded-lg text-xs font-bold transition-all duration-200 cursor-pointer ${
              activeTab === "gaps" ? "bg-indigo-600 text-zinc-50 shadow-md" : "text-zinc-400 hover:text-zinc-200"
            }`}
          >
            Market Gaps Matrix
          </button>
          <button
            onClick={() => setActiveTab("blueprints")}
            className={`px-4 py-2 rounded-lg text-xs font-bold transition-all duration-200 cursor-pointer ${
              activeTab === "blueprints" ? "bg-indigo-600 text-zinc-50 shadow-md" : "text-zinc-400 hover:text-zinc-200"
            }`}
          >
            Startup Blueprints
          </button>
        </div>
      </div>

      {/* Render tab views */}
      {activeTab === "gaps" ? (
        <div className="grid grid-cols-1 gap-8">
          {opportunities.length === 0 ? (
            <div className="py-20 text-center text-zinc-500 border border-dashed border-zinc-850 rounded-xl">
              No matching market gaps scoring available. Run pipelines to update.
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              {opportunities.map((opp, idx) => (
                <div key={`${opp.category_id}-${idx}`} className="glass-card p-6 flex flex-col justify-between relative overflow-hidden group">
                  <div className="absolute top-0 right-0 w-24 h-24 bg-indigo-500/5 rounded-full blur-2xl group-hover:bg-indigo-500/10 transition duration-300 pointer-events-none" />

                  <div className="space-y-6">
                    {/* Header */}
                    <div className="flex justify-between items-start border-b border-zinc-900 pb-4">
                      <div>
                        <span className="text-[10px] uppercase font-bold text-zinc-500 tracking-wider">
                          Market Category
                        </span>
                        <h3 className="text-xl font-bold text-zinc-50 mt-1 flex items-center space-x-2">
                          <Lightbulb className="h-5 w-5 text-indigo-400" />
                          <span>{opp.category}</span>
                        </h3>
                      </div>
                      <div className="text-right">
                        <div className="text-[10px] uppercase font-bold text-zinc-500 tracking-wider">Success Prob</div>
                        <div className="text-3xl font-black text-indigo-400 mt-1">{opp.success_probability}%</div>
                      </div>
                    </div>

                    {/* V2 Six-Factor Gauges */}
                    <div className="space-y-4">
                      <h4 className="text-xs font-bold text-zinc-400 uppercase tracking-widest flex items-center space-x-1">
                        <TrendingUp className="h-3.5 w-3.5 text-zinc-400" />
                        <span>YC Decision Vectors</span>
                      </h4>

                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 bg-zinc-950/40 p-4 border border-zinc-900 rounded-lg">
                        {/* Revenue Potential */}
                        <div className="space-y-1">
                          <div className="flex justify-between text-[11px] font-semibold text-zinc-400">
                            <span>Revenue Potential</span>
                            <span className="text-zinc-200">{opp.factors.revenue_potential.toFixed(0)}/100</span>
                          </div>
                          <div className="w-full bg-zinc-800 h-1.5 rounded-full overflow-hidden">
                            <div className="bg-indigo-500 h-1.5 rounded-full" style={{ width: `${opp.factors.revenue_potential}%` }} />
                          </div>
                        </div>

                        {/* Growth Velocity */}
                        <div className="space-y-1">
                          <div className="flex justify-between text-[11px] font-semibold text-zinc-400">
                            <span>Growth Velocity</span>
                            <span className="text-zinc-200">{opp.factors.growth_velocity.toFixed(0)}/100</span>
                          </div>
                          <div className="w-full bg-zinc-800 h-1.5 rounded-full overflow-hidden">
                            <div className="bg-emerald-500 h-1.5 rounded-full" style={{ width: `${opp.factors.growth_velocity}%` }} />
                          </div>
                        </div>

                        {/* Market Timing */}
                        <div className="space-y-1">
                          <div className="flex justify-between text-[11px] font-semibold text-zinc-400">
                            <span>Market Timing</span>
                            <span className="text-zinc-200">{opp.factors.market_timing.toFixed(0)}/100</span>
                          </div>
                          <div className="w-full bg-zinc-800 h-1.5 rounded-full overflow-hidden">
                            <div className="bg-cyan-500 h-1.5 rounded-full" style={{ width: `${opp.factors.market_timing}%` }} />
                          </div>
                        </div>

                        {/* VC Attractiveness */}
                        <div className="space-y-1">
                          <div className="flex justify-between text-[11px] font-semibold text-zinc-400">
                            <span>VC Attractiveness</span>
                            <span className="text-zinc-200">{opp.factors.vc_attractiveness.toFixed(0)}/100</span>
                          </div>
                          <div className="w-full bg-zinc-800 h-1.5 rounded-full overflow-hidden">
                            <div className="bg-amber-500 h-1.5 rounded-full" style={{ width: `${opp.factors.vc_attractiveness}%` }} />
                          </div>
                        </div>

                        {/* Competition Density */}
                        <div className="space-y-1">
                          <div className="flex justify-between text-[11px] font-semibold text-zinc-400">
                            <span>Less Crowded (Density)</span>
                            <span className="text-zinc-200">{opp.factors.competition_density.toFixed(0)}/100</span>
                          </div>
                          <div className="w-full bg-zinc-800 h-1.5 rounded-full overflow-hidden">
                            <div className="bg-blue-500 h-1.5 rounded-full" style={{ width: `${opp.factors.competition_density}%` }} />
                          </div>
                        </div>

                        {/* Founder Difficulty */}
                        <div className="space-y-1">
                          <div className="flex justify-between text-[11px] font-semibold text-zinc-400">
                            <span>Ease-of-Entry</span>
                            <span className="text-zinc-200">{opp.factors.founder_difficulty.toFixed(0)}/100</span>
                          </div>
                          <div className="w-full bg-zinc-800 h-1.5 rounded-full overflow-hidden">
                            <div className="bg-purple-500 h-1.5 rounded-full" style={{ width: `${opp.factors.founder_difficulty}%` }} />
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Metric Traced Explanation Panel */}
                    <div className="space-y-2">
                      <h4 className="text-xs font-bold text-zinc-400 uppercase tracking-widest flex items-center space-x-1">
                        <Info className="h-3.5 w-3.5 text-indigo-400" />
                        <span>Metric-Traced Logic (Explainability)</span>
                      </h4>
                      <p className="text-xs text-zinc-400 leading-relaxed bg-zinc-950/60 p-4 border border-zinc-900 rounded-lg">
                        {opp.reasoning}
                      </p>
                    </div>

                    {/* Signals & Risks */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      {/* Positive Signals */}
                      <div className="space-y-2">
                        <h4 className="text-[10px] font-bold text-emerald-400 uppercase tracking-wider">Strongest Signals</h4>
                        <div className="space-y-1">
                          {opp.strongest_signals.slice(0, 3).map((sig, idx) => (
                            <div key={idx} className="flex items-start space-x-1.5 text-[11px] text-zinc-400 leading-relaxed">
                              <span className="text-emerald-400 font-bold shrink-0 mt-0.5">•</span>
                              <span>{sig}</span>
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* Headwinds & Risks */}
                      <div className="space-y-2">
                        <h4 className="text-[10px] font-bold text-amber-500 uppercase tracking-wider">Risks & Headwinds</h4>
                        <div className="space-y-1">
                          {opp.risk_factors.slice(0, 3).map((risk, idx) => (
                            <div key={idx} className="flex items-start space-x-1.5 text-[11px] text-zinc-400 leading-relaxed">
                              <span className="text-amber-500 font-bold shrink-0 mt-0.5">•</span>
                              <span>{risk}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Switch to Blueprint action */}
                  <div className="pt-6 border-t border-zinc-900 mt-6 flex justify-end">
                    <button
                      onClick={() => {
                        const matchedBrief = briefs.find((b) => b.category_id === opp.category_id);
                        if (matchedBrief) {
                          setSelectedBrief(matchedBrief);
                          setActiveTab("blueprints");
                        }
                      }}
                      className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-zinc-200 border border-zinc-700 rounded-lg text-xs font-bold transition flex items-center space-x-1 cursor-pointer"
                    >
                      <span>Generate Launch Blueprint</span>
                      <ChevronRight className="h-3.5 w-3.5" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      ) : (
        /* Startup Briefs tab */
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Left Sidebar: Selector list */}
          <div className="lg:col-span-1 border border-zinc-800 bg-zinc-900/40 backdrop-blur-md rounded-xl p-5 shadow-xl space-y-4 max-h-[700px] overflow-y-auto">
            <div className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider border-b border-zinc-800 pb-3">
              Generated SaaS Briefs
            </div>

            {briefs.length === 0 ? (
              <p className="text-xs text-zinc-600 font-semibold p-4 text-center">No briefs available.</p>
            ) : (
              <div className="space-y-2">
                {briefs.map((b, idx) => {
                  const isSelected = selectedBrief?.category_id === b.category_id;
                  return (
                    <button
                      key={`${b.category_id}-${idx}`}
                      onClick={() => setSelectedBrief(b)}
                      className={`w-full text-left p-3.5 rounded-lg border flex flex-col justify-between transition-all duration-200 cursor-pointer ${
                        isSelected
                          ? "bg-indigo-600/10 border-indigo-500/50 text-indigo-400"
                          : "bg-zinc-950/30 border-zinc-850 hover:bg-zinc-900/40 text-zinc-400"
                      }`}
                    >
                      <span className="text-[10px] font-bold uppercase tracking-wide opacity-80">{b.category}</span>
                      <h4 className="text-xs font-extrabold text-zinc-200 line-clamp-1 mt-1">{b.startup_name}</h4>
                      <span className="text-[9px] text-zinc-500 font-extrabold mt-3">{b.success_probability}% Success Prob</span>
                    </button>
                  );
                })}
              </div>
            )}
          </div>

          {/* Right Area: Selected Brief Viewer */}
          <div className="lg:col-span-3 border border-zinc-800 bg-zinc-900/40 backdrop-blur-md rounded-xl p-8 shadow-xl min-h-[500px] space-y-8">
            {selectedBrief ? (
              <div className="space-y-8">
                {/* Header Profile */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-zinc-900 pb-6 gap-4">
                  <div className="space-y-1">
                    <div className="flex items-center space-x-2 text-xs text-zinc-500 font-bold uppercase tracking-widest">
                      <span>Category: {selectedBrief.category}</span>
                      <span>•</span>
                      <span className="text-indigo-400 font-black">{selectedBrief.success_probability}% Success Prob</span>
                    </div>
                    <h2 className="text-2xl font-black text-zinc-50 flex items-center space-x-2">
                      <Sparkles className="h-6 w-6 text-indigo-400" />
                      <span>{selectedBrief.startup_name}</span>
                    </h2>
                  </div>

                  <div className="flex items-center space-x-2 bg-zinc-950/60 border border-zinc-800 p-2.5 rounded-lg text-xs font-bold">
                    <span className="text-zinc-500">Build Difficulty:</span>
                    <span
                      className={`uppercase px-2 py-0.5 rounded border text-[9px] ${
                        selectedBrief.build_difficulty === "Low"
                          ? "text-emerald-400 bg-emerald-950/20 border-emerald-500/20"
                          : selectedBrief.build_difficulty === "High"
                          ? "text-rose-400 bg-rose-950/20 border-rose-500/20"
                          : "text-amber-400 bg-amber-950/20 border-amber-500/20"
                      }`}
                    >
                      {selectedBrief.build_difficulty}
                    </span>
                  </div>
                </div>

                {/* 11-Field Grid Details */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Problem Statement */}
                  <div className="bg-zinc-950/40 border border-zinc-900/80 p-5 rounded-lg space-y-2">
                    <h4 className="text-[10px] font-black uppercase text-zinc-500 tracking-wider">Problem Statement</h4>
                    <p className="text-xs text-zinc-300 leading-relaxed font-semibold">{selectedBrief.problem_statement}</p>
                  </div>

                  {/* Target ICP */}
                  <div className="bg-zinc-950/40 border border-zinc-900/80 p-5 rounded-lg space-y-2">
                    <h4 className="text-[10px] font-black uppercase text-zinc-500 tracking-wider">Ideal Customer Profile (ICP)</h4>
                    <p className="text-xs text-zinc-300 leading-relaxed font-semibold">{selectedBrief.target_customer}</p>
                  </div>

                  {/* Revenue Ceiling */}
                  <div className="bg-zinc-950/40 border border-zinc-900/80 p-5 rounded-lg space-y-2">
                    <h4 className="text-[10px] font-black uppercase text-zinc-500 tracking-wider">ARR Revenue Potential</h4>
                    <p className="text-xs text-zinc-300 leading-relaxed font-semibold">{selectedBrief.revenue_potential}</p>
                  </div>

                  {/* Pricing Model */}
                  <div className="bg-zinc-950/40 border border-zinc-900/80 p-5 rounded-lg space-y-2">
                    <h4 className="text-[10px] font-black uppercase text-zinc-500 tracking-wider">Recommended Pricing structure</h4>
                    <p className="text-xs text-zinc-300 leading-relaxed font-semibold">{selectedBrief.pricing_model}</p>
                  </div>

                  {/* Competitive Advantage */}
                  <div className="bg-zinc-950/40 border border-zinc-900/80 p-5 rounded-lg space-y-2">
                    <h4 className="text-[10px] font-black uppercase text-zinc-500 tracking-wider">Derived Moat & Advantage</h4>
                    <p className="text-xs text-zinc-300 leading-relaxed font-semibold">{selectedBrief.competitive_advantage}</p>
                  </div>

                  {/* GTM Strategy */}
                  <div className="bg-zinc-950/40 border border-zinc-900/80 p-5 rounded-lg space-y-2">
                    <h4 className="text-[10px] font-black uppercase text-zinc-500 tracking-wider">Go-To-Market strategy</h4>
                    <p className="text-xs text-zinc-300 leading-relaxed font-semibold">{selectedBrief.go_to_market}</p>
                  </div>

                  {/* Time to MVP */}
                  <div className="bg-zinc-950/40 border border-zinc-900/80 p-5 rounded-lg space-y-2">
                    <h4 className="text-[10px] font-black uppercase text-zinc-500 tracking-wider">Calendar Time to MVP</h4>
                    <p className="text-xs text-zinc-300 leading-relaxed font-semibold">{selectedBrief.estimated_time_to_mvp}</p>
                  </div>

                  {/* Empty cell or extra details */}
                  <div className="bg-zinc-950/40 border border-zinc-900/80 p-5 rounded-lg flex items-center space-x-3">
                    <ShieldCheck className="h-6 w-6 text-indigo-400 shrink-0" />
                    <div>
                      <h4 className="text-xs font-bold text-zinc-200">YC Decision Grade</h4>
                      <p className="text-[11px] text-zinc-400 mt-0.5">Scored through Live forecast and competitor density telemetry.</p>
                    </div>
                  </div>
                </div>

                {/* MVP Feature List prioritzed by pain terms */}
                <div className="space-y-4">
                  <h4 className="text-xs font-bold text-zinc-400 uppercase tracking-widest flex items-center space-x-1">
                    <CheckCircle className="h-3.5 w-3.5 text-indigo-400" />
                    <span>MVP Feature Priority Roadmap (Pain-Term Ordered)</span>
                  </h4>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    {selectedBrief.mvp_features.map((feature, fidx) => (
                      <div key={fidx} className="flex items-start space-x-2 bg-zinc-950/60 border border-zinc-900 p-4 rounded-lg">
                        <CheckCircle className="h-4 w-4 text-emerald-400 mt-0.5 shrink-0" />
                        <span className="text-xs text-zinc-300 leading-relaxed">{feature}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Why explanation metrics trace */}
                {selectedBrief.why && (
                  <div className="space-y-3 pt-2">
                    <h4 className="text-xs font-bold text-zinc-400 uppercase tracking-widest flex items-center space-x-1">
                      <HelpCircle className="h-3.5 w-3.5 text-indigo-400" />
                      <span>Metric Traceability (The "WHY")</span>
                    </h4>
                    <div className="bg-indigo-950/15 border border-indigo-500/20 rounded-xl p-5 text-xs text-zinc-400 leading-relaxed whitespace-pre-line font-sans">
                      {selectedBrief.why}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="h-full flex items-center justify-center text-zinc-500 text-sm">
                Select a launch blueprint from the catalog.
              </div>
            )}
          </div>
        </div>
      )}
    </main>
  );
}

export default function OpportunitiesPage() {
  return (
    <Suspense fallback={
      <div className="flex-1 flex items-center justify-center p-10 bg-zinc-950">
        <div className="text-center space-y-4">
          <Activity className="h-10 w-10 text-indigo-500 animate-spin mx-auto" />
          <h2 className="text-lg font-bold text-zinc-100">Loading Workspace...</h2>
        </div>
      </div>
    }>
      <OpportunitiesPageContent />
    </Suspense>
  );
}
