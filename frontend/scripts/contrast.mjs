// WCAG contrast check for every text/background pair in tokens.css and lib/faultColors.ts. Exit 1 on any failure.
import { readFileSync } from "node:fs";
const here = (p) => new URL(p, import.meta.url);
const vars = Object.fromEntries([...readFileSync(here("../src/tokens.css"), "utf8").matchAll(/--([\w-]+):\s*(#[0-9A-Fa-f]{6})/g)].map((m) => [m[1], m[2]]));
vars.white = "#FFFFFF";
const lum = (hex) => {
  const c = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255).map((v) => (v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4));
  return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2];
};
const ratio = (a, b) => { const [x, y] = [lum(a), lum(b)].sort((p, q) => q - p); return (x + 0.05) / (y + 0.05); };

// [text, background, minimum]; 3 = icons, focus rings, the active-nav bar and large numbers only.
const pairs = [
  ["ink", "paper"], ["ink", "card"], ["ink-2", "card"], ["ink-2", "paper"],
  ["muted", "card"], ["muted", "paper"], ["muted", "rule-soft"], ["muted", "act-tint"], ["muted", "watch-tint"], ["muted", "paper-bar"],
  ["white", "act"], ["act", "card"], ["act", "act-tint", 3], ["ink", "act-tint"], ["loss", "card"], ["loss", "paper"],
  ["watch-ink", "watch-bg"], ["watch-ink", "watch-tint"], ["ink", "watch-tint"],
  ["ok", "card"], ["ok", "paper"], ["ok", "ok-bg", 3], ["ok-ink", "ok-bg"],
  ["link", "card"], ["link", "paper"], ["link-hover", "card"],
  ["white", "brand"], ["white", "brand-2"], ["db-label", "brand"], ["db-sub", "brand"],
  ["db-loss", "brand"], ["db-protect", "brand"], ["gold", "brand"],
  ["gold-ink", "card"], ["gold-ink", "paper"], ["info", "card"], ["info", "paper"],
  ["sample-ink", "sample-bg"],
  ["focus", "card", 3], ["focus", "paper", 3], ["gold", "brand", 3], ["gold", "brand-2", 3], ["gold", "ink", 3],
].map(([f, b, min = 4.5]) => [f, b, vars[f], vars[b], min]);

const src = readFileSync(here("../src/lib/faultColors.ts"), "utf8");
for (const m of src.matchAll(/(\w+): \{ accent: "(#\w+)", tint: "(#\w+)", ink: "(#\w+)" \}/g)) {
  pairs.push([`${m[1]}.ink`, `${m[1]}.tint`, m[4], m[3], 4.5], [`${m[1]}.ink`, "white", m[4], "#FFFFFF", 4.5]);
}

let bad = 0;
for (const [f, b, fh, bh, min] of pairs) {
  if (!fh || !bh) { console.log(`MISSING ${f} on ${b}`); bad++; continue; }
  const r = ratio(fh, bh);
  const ok = r >= min;
  if (!ok) bad++;
  console.log(`${ok ? "ok  " : "FAIL"} ${r.toFixed(2).padStart(5)}:1 (min ${min})  ${f} ${fh} on ${b} ${bh}`);
}
console.log(bad ? `${bad} failing pairs` : "all pairs pass");
process.exit(bad ? 1 : 0);
