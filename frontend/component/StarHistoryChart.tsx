"use client";

import {
  AreaChart,
  Area,
  Tooltip,
  ResponsiveContainer,
  XAxis
} from "recharts";

interface StarHistoryChartProps {
  data: Array<{
    recorded_at: string;
    stars: number;
  }>;
}

export default function StarHistoryChart({ data }: StarHistoryChartProps) {
  const chartData = data.map(d => ({
    date: new Date(d.recorded_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric' }),
    Stars: d.stars
  }));

  return (
    <div className="w-full h-40">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={chartData} margin={{ top: 5, right: 5, left: 5, bottom: 5 }}>
          <defs>
            <linearGradient id="colorStars" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#06b6d4" stopOpacity={0} />
            </linearGradient>
          </defs>
          <XAxis 
            dataKey="date" 
            hide={false} 
            stroke="#52525b" 
            fontSize={9} 
            tickLine={false} 
            axisLine={false}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "#18181b",
              borderColor: "#3f3f46",
              borderRadius: "6px",
              color: "#f4f4f5",
              fontSize: "10px"
            }}
          />
          <Area
            type="monotone"
            dataKey="Stars"
            stroke="#22d3ee"
            strokeWidth={1.5}
            fillOpacity={1}
            fill="url(#colorStars)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
