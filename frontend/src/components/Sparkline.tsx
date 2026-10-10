import { Line, LineChart, ReferenceLine, ResponsiveContainer, XAxis, YAxis } from "recharts";

type Pt = { x: number; v: number | null; w: number | null };

// Series skip stopped hours (v1.9): break the line where a step is over twice the usual spacing.
function withGaps(points: [string, number][], handledAt?: number): Pt[] {
  const ps = points.filter((p) => p[1] != null).map(([t, v]) => ({ x: new Date(t).getTime(), v }));
  const steps = ps.slice(1).map((p, i) => p.x - ps[i].x).sort((a, b) => a - b);
  const usual = steps[Math.floor(steps.length / 2)] ?? 0;
  const join = handledAt == null ? -1 : ps.findIndex((p) => p.x >= handledAt);
  const out: Pt[] = [];
  ps.forEach((p, i) => {
    if (i && usual && p.x - ps[i - 1].x > 2 * usual) out.push({ x: (p.x + ps[i - 1].x) / 2, v: null, w: null });
    // v = before the repair (solid), w = after it (faded). The repair point sits on both so the line joins.
    const after = handledAt != null && p.x >= handledAt;
    const before = !after || i === join;
    out.push({ x: p.x, v: before ? p.v : null, w: after ? p.v : null });
  });
  return out;
}

// 7-day trend. Dashed line = limit. Rust = signal behind the alert, grey = context. Faded = after a repair.
export function Sparkline({ points, limit, hot, label, handledAt }:
  { points: [string, number][]; limit?: number | null; hot?: boolean; label: string; handledAt?: string | null }) {
  const h = handledAt ? new Date(handledAt).getTime() : undefined;
  const data = withGaps(points, h);
  const vals = points.map((p) => p[1]).filter((v) => v != null).concat(limit != null ? [limit] : []);
  const lo = Math.min(...vals), hi = Math.max(...vals), pad = (hi - lo) * 0.08 || 1;
  const xs = data.map((d) => d.x);
  const stroke = hot ? "var(--act)" : "var(--muted)";
  return (
    <div role="img" aria-label={label} className="w-[104px] h-9 lg:w-[200px] lg:h-[52px] flex-none">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 3, right: 2, bottom: 3, left: 2 }}>
          <XAxis dataKey="x" type="number" hide domain={[Math.min(...xs), Math.max(...xs)]} />
          <YAxis hide domain={[lo - pad, hi + pad]} />
          {limit != null && <ReferenceLine y={limit} stroke="var(--muted)" strokeDasharray="5 5" />}
          {h != null && h >= xs[0] && h <= xs[xs.length - 1] && <ReferenceLine x={h} stroke="var(--ok)" strokeWidth={2} />}
          <Line dataKey="v" dot={false} isAnimationActive={false} connectNulls={false} strokeWidth={hot ? 3 : 2.5}
            stroke={stroke} strokeLinejoin="round" />
          {h != null && <Line dataKey="w" dot={false} isAnimationActive={false} connectNulls={false} strokeWidth={2.5}
            stroke={stroke} strokeOpacity={0.3} strokeLinejoin="round" />}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
