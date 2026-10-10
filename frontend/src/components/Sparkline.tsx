import { Line, LineChart, ReferenceLine, ResponsiveContainer, YAxis } from "recharts";

// 7-day trend. Dashed line = limit. Rust = signal behind the alert, grey = context.
export function Sparkline({ points, limit, hot, label }:
  { points: [string, number][]; limit?: number | null; hot?: boolean; label: string }) {
  const data = points.filter((p) => p[1] != null).map(([t, v]) => ({ t, v }));
  const vals = data.map((d) => d.v).concat(limit != null ? [limit] : []);
  const lo = Math.min(...vals), hi = Math.max(...vals), pad = (hi - lo) * 0.08 || 1;
  return (
    <div role="img" aria-label={label} className="w-[104px] h-9 lg:w-[200px] lg:h-[52px] flex-none">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 3, right: 2, bottom: 3, left: 2 }}>
          <YAxis hide domain={[lo - pad, hi + pad]} />
          {limit != null && <ReferenceLine y={limit} stroke="var(--muted)" strokeDasharray="5 5" />}
          <Line dataKey="v" dot={false} isAnimationActive={false} strokeWidth={hot ? 3 : 2.5}
            stroke={hot ? "var(--act)" : "var(--muted)"} strokeLinejoin="round" />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
