"use client";

interface CategoryHeatmapProps {
  data: Array<{
    name: string;
    momentum_score: number;
    growth_rate: number;
    news_volume: number;
  }>;
}

export default function CategoryHeatmap({ data }: CategoryHeatmapProps) {
  // Compute color based on momentum score (ranges ~10 to 99)
  const getIntensityClass = (score: number) => {
    if (score >= 90) return "bg-indigo-600 text-zinc-50 border-indigo-400/50 shadow-[0_0_15px_rgba(99,102,241,0.4)]";
    if (score >= 75) return "bg-indigo-800 text-zinc-100 border-indigo-500/30";
    if (score >= 60) return "bg-violet-900 text-zinc-200 border-violet-800/30";
    if (score >= 40) return "bg-zinc-800 text-zinc-300 border-zinc-700";
    return "bg-zinc-900 text-zinc-400 border-zinc-800";
  };

  return (
    <div className="border border-zinc-800 bg-zinc-900/40 backdrop-blur-md rounded-xl p-6 shadow-xl">
      <h2 className="text-xl font-bold mb-2 text-zinc-100">🔥 Trend Heatmap</h2>
      <p className="text-sm text-zinc-400 mb-6 font-semibold">Visualizing market momentum intensity by category metrics.</p>
      
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {data.map((item) => (
          <div
            key={item.name}
            className={`border rounded-lg p-5 transition-all duration-300 hover:scale-[1.03] flex flex-col justify-between ${getIntensityClass(
              item.momentum_score
            )}`}
          >
            <div>
              <div className="text-xs uppercase tracking-wider font-bold opacity-60">Niche Category</div>
              <h3 className="text-base font-bold mt-1 leading-tight">{item.name}</h3>
            </div>
            
            <div className="mt-8 flex justify-between items-end">
              <div>
                <div className="text-[10px] uppercase tracking-wider font-semibold opacity-60">30d Growth</div>
                <div className="text-lg font-extrabold">+{item.growth_rate}%</div>
              </div>
              <div className="text-right">
                <div className="text-[10px] uppercase tracking-wider font-semibold opacity-60">Momentum</div>
                <div className="text-lg font-extrabold">{item.momentum_score}</div>
              </div>
            </div>
          </div>
        ))}
      </div>
      
      {/* Legend */}
      <div className="mt-6 pt-4 border-t border-zinc-800 flex items-center justify-end space-x-3 text-xs text-zinc-500">
        <span>Cold</span>
        <div className="w-3 h-3 bg-zinc-900 border border-zinc-800 rounded" />
        <div className="w-3 h-3 bg-zinc-800 border border-zinc-700 rounded" />
        <div className="w-3 h-3 bg-violet-900 border border-violet-800/30 rounded" />
        <div className="w-3 h-3 bg-indigo-800 border border-indigo-500/30 rounded" />
        <div className="w-3 h-3 bg-indigo-600 border border-indigo-400/50 rounded shadow-[0_0_5px_rgba(99,102,241,0.4)]" />
        <span>Hot</span>
      </div>
    </div>
  );
}
