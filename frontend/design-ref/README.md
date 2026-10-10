# MillGuard design reference (Direction B, final)

Approved 10 Oct, updated for contract v1.7. Live canvas: the "MillGuard Design" artifact, page "Direction B — Final".

**All numbers in these screens are mock-ups.** The app reads every number and label from the API (fixtures = real pipeline snapshot). Use the screens for layout, hierarchy and wording only.

## Files

| File | What it shows |
|---|---|
| `tokens.css` | Colours (with contrast ratios), fonts, hero RM sizes |
| `screens/Machine-Press2-*.html` | Machine page, press Act now — desktop, mobile, mobile BM |
| `screens/Machine-Boiler1-*.html` | Machine page, whole-mill (boiler) Act now |
| `screens/Machine-Normal-*.html` | Machine page, Normal state |
| `screens/Mill-*.html` | Mill page, alert night |
| `screens/Mill-Quiet-*.html` | Mill page, quiet night |
| `screens/Impact-*.html` | Impact page (sliders: right panel on desktop, bottom sheet on mobile) |
| `screens/How-*.html` | How it works |
| `screens/Components.html` | Component sheet |
| `screens/StressTest.html` | Smallest/largest ringgit, partial fingerprints, 7-digit RM at 390 px in EN + BM |

Open the screens directly in a browser (fonts load from Google Fonts). Desktop screens are fluid; mobile screens are fixed at 390 px.

## Field mapping (contract v1.7)

| UI element | Field |
|---|---|
| Status band / chip | `status` → Act now / Watch / Normal (colour + icon + word) |
| Band right text, primary button | `deadline_label_en/ms` (when to act) |
| Risk sentence | "If not fixed at {deadline_label}: {risk_pct}% chance it fails {window_label}" — `window_label_en/ms` is the end of the `horizon_h` risk window |
| Expected loss (hero RM) | `rm_at_risk` |
| Maths line | `{risk_pct}% × RM{rm_breakdown_cost}` — never divide in the UI |
| Fix cost | `rm_cost_to_act` |
| You protect | `rm_saved_if_acted` |
| "Why first" strip | `why_rank_en/ms`, shown when `fix.stop` or asset scope is whole-mill |
| Fix plan meta | `crew`, `est_hours`, `stop` (none / machine / whole_mill), `lost_production` |
| Fingerprint rows | `diagnosis.fingerprint[]` → label / observed / matches |
| Evidence rows | `series[]` with `summary_en/ms`, dashed line at `limit` |
| Normal state | `last_service`, `next_check`, plus at-risk and cost-to-act |
| Mill summary | `/api/brief` `rm_protected_total`, `watching_count`, `suppressed_count` |
| Bookmark chips | `/api/replay/markers` labels (Quiet night / Press 2 act now / Whole mill) |

## Layout rules that the real numbers depend on

1. **RM is always the biggest type on the screen.** Hero 64 px desktop / 42 px mobile; protect 54 / 36; card 34 / 28. Never scale RM down to fit — let it wrap below its label instead (`flex-wrap: wrap`, `margin-left: auto`).
2. **Full ringgit with commas** (RM1,240 … RM1,186,400) on Mill and Machine. `RMx.xxm` only on Impact.
3. **Saved = 0** (`rm_saved_if_acted` min 0): swap the dark "You protect" bar for the light "Waiting is cheaper by RM x" bar (= cost − at risk) and make Keep watching the filled button.
4. **Recommended action = the only filled button.** Schedule (orange) for planned-stop fixes, Fix now for boiler / fix_now, Keep watching when saving is 0.
5. **Fingerprint "N of M match"** is computed from `matches`. If fewer than half match, show the amber "Early pattern" line under the list. 3- and 4-row lists use the same row height.
6. **BM runs ~30% longer.** Nothing truncates: status band, chips and tab labels wrap to two lines. Don't set fixed heights on cards or chips, and don't use `text-overflow: ellipsis`.
7. **Status is never colour alone:** Act now = triangle, Watch = eye, Normal = tick, Not monitored = dashed outline.
8. Desktop body text ≥ 16 px (projector at 3 m). Tap targets ≥ 44 px; primary buttons 52–60 px.
9. "Sample data" badge on every page in fixture mode.

## Wording (EN / BM)

| EN | BM |
|---|---|
| Act now / Watch / Normal | Bertindak sekarang / Pantau / Normal |
| Expected loss if you skip it | Jangkaan kerugian jika dilangkau |
| Fix at the planned stop | Baiki semasa hentian terancang |
| You protect | Anda lindungi |
| What's wrong / What to do | Apa yang rosak / Apa yang perlu dibuat |
| Fault fingerprint | Cap jari kerosakan |
| Schedule / Fix now / Keep watching | Jadualkan / Baiki sekarang / Terus pantau |
| Mill / Machine / Impact / How it works | Kilang / Mesin / Impak / Cara ia berfungsi |

BM strings are a first pass. Have a native speaker check the mill terms (skru cacing, galas, hentian terancang) before the demo.
