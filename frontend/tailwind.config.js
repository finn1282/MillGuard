/** Colours come from the Direction B tokens in src/tokens.css. */
const v = (n) => `var(--${n})`;
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    screens: { md: "768px", lg: "1024px", xl: "1280px" },
    extend: {
      colors: Object.fromEntries([
        "paper", "paper-bar", "card", "rule", "rule-soft", "ink", "ink-2", "muted", "control-border",
        "act", "act-tint", "loss", "watch-bg", "watch-ink", "watch-border",
        "ok", "ok-bg", "ok-ink", "ok-border",
        "db-label", "db-sub", "db-loss", "db-protect",
        "sample-bg", "sample-ink", "sample-border",
      ].map((n) => [n, v(n)])),
      fontFamily: { ui: v("font-ui"), num: v("font-num") },
      borderRadius: { DEFAULT: v("radius"), chip: v("radius-chip") },
    },
  },
  plugins: [],
};
