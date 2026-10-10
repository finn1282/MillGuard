/** Colours come from the tokens in src/tokens.css. */
const v = (n) => `var(--${n})`;
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    screens: { md: "768px", lg: "1024px", xl: "1280px" },
    extend: {
      colors: Object.fromEntries([
        "paper", "paper-bar", "card", "rule", "rule-soft", "ink", "ink-2", "muted", "control-border",
        "brand", "brand-2", "brand-line", "gold", "gold-ink", "info", "link", "link-hover", "focus", "overlay", "shadow",
        "act", "act-tint", "act-tint-border", "loss", "watch-bg", "watch-tint", "watch-ink", "watch-border",
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
