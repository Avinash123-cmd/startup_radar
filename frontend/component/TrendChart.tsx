"use client";

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid
} from "recharts";

interface TrendChartProps {
  data: Array<{
    name: string;
    momentum_score: number;
    growth_rate: number;
  }>;
}

export default function TrendChart({ data }: TrendChartProps) {
  // Sort data by momentum to show ordered rankings
  const chartData = [...data].sort((a, b) => b.momentum_score - a.momentum_score);

  return (
    <div className="border border-zinc-800 bg-zinc-900/40 backdrop-blur-md rounded-xl p-6 shadow-xl relative overflow-hidden">
      {/* Background Glow accent */}
      <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-500/5 rounded-full blur-3xl pointer-events-none" />
      
      <h2 className="text-xl font-bold mb-6 text-zinc-100 flex items-center space-x-2">
        <span>📈 Category Momentum Index</span>
      </h2>

      <div className="w-full h-80">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="colorMomentum" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#6366f1" stopOpacity={0.4} />
                <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#27272a" vertical={false} />
            <XAxis 
              dataKey="name" 
              stroke="#71717a" 
              fontSize={11} 
              tickLine={false} 
              axisLine={false} 
              tickFormatter={(value) => value.split(" ")[0]} // Shorten titles
            />
            <YAxis 
              stroke="#71717a" 
              fontSize={11} 
              tickLine={false} 
              axisLine={false} 
            />
            <Tooltip 
              contentStyle={{ 
                backgroundColor: "#18181b", 
                borderColor: "#3f3f46", 
                borderRadius: "8px",
                color: "#f4f4f5",
                fontSize: "12px",
                boxShadow: "0 10px 20px -5px rgba(0,0,0,0.3)"
              }} 
            />
            <Area 
              type="monotone" 
              dataKey="momentum_score" 
              stroke="#818cf8" 
              strokeWidth={2}
              fillOpacity={1} 
              fill="url(#colorMomentum)" 
              name="Momentum Score"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}