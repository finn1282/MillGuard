# MillGuard — Master Plan (Single Source of Truth)

Version 1.11 · Sat 10 Oct 2026, 20:45 MYT · Team: 3 people, 2 computers (A = backend, B = design then frontend, third member = pitch) · Deadline: **Sun 11 Oct, 09:30 MYT**
Owner of this file: the orchestrator chat. Agents read it, they do not rewrite it. Propose changes in `CHANGELOG.md` and the orchestrator merges them.

---

## 0. TL;DR

- **Verdict:** the idea is strong and fits the track well. Keep it, but change four things: (1) no dashboard — the product becomes a **Shift Brief** plus a **Two Mills replay**, (2) cut the scope to fit 19 hours, (3) update the economics to today's numbers, (4) handle the boiler data licence properly.
- **One-line pitch:** *"About 450 mills in Malaysia. One runs on AI, after a multi-million-ringgit rollout. MillGuard is for the rest: it tells the night-shift engineer which machine to fix first, and proves it in ringgit."*
- **Hook number:** a 60 t/h mill that stops puts **about RM51,000 of crude palm oil at risk every hour** (60 t/h × 19.74% OER × RM4,292.50/t, the 2025 MPOB average). At today's spot price (~RM4,420/t) it is ~RM52,000.
- **Build split:** Computer A = backend agent. Computer B = Claude Design first, then frontend agent. Pitch teammate = deck, outreach, script, backup video.
- **Contract first:** the API in section 7 is fixed. The backend ships fixture JSON in the first 60 minutes, so the frontend never waits.

---

## 1. Validation against the brief

### 1.1 Track criteria scorecard

| Track requirement | How MillGuard meets it | Strength |
| --- | --- | --- |
| Solve a specific real-world problem | Unplanned screw press and boiler stops in Malaysian mills, backed by published OEE and FMEA studies | Strong |
| Clearly identify the user | Night-shift maintenance supervisor; one decision per shift: fix now, schedule, or keep watching | Strong |
| Support decisions, not just prediction | Each alert carries RM cost of acting vs waiting, a recommendation and a deadline | Strong (our core) |
| Robust on noisy / unfamiliar data | Simulator has noise, drift and gaps; trained on 9 simulated mills, tested on an unseen 10th; real-data check on MetroPT-3 | Medium → strong if we show it honestly |
| Minimise false alarms | Cost-optimal threshold, max 5 actions per shift, 3-hour persistence, hysteresis, feedback loop | Strong |
| Communicate recommendations clearly | Plain-language action cards, top 3 reasons, BM/EN toggle | Strong if the UX is good |
| Measurable impact, realistic assumptions | Three-policy backtest in RM, low/base/high cases, every assumption labelled validated or assumed | Strong (our proof) |
| Detect / Categorize / Prioritize / Explain | Pipeline maps 1:1 onto these four | Strong |
| **Core question:** better decision, and can you prove it? | Two Mills replay: same months, same failures, run-to-failure vs fixed-interval vs MillGuard, RM totals side by side | This is the winning slide |

### 1.2 Mentor advice check

| Mentor advice | Original plan | Change |
| --- | --- | --- |
| 1. No login screen | None planned | Keep it that way |
| 2. Build only what the demo needs | 48-hour plan, 4 proxy datasets, 4-screen app | Cut to the P0 list in section 5 |
| 3. Validate before building | Done in this file (section 1.4) | Validated against published studies and MPOB data |
| 4. **Avoid a dashboard** | **4-screen Streamlit dashboard — exactly what they warned against** | Replace with Shift Brief (phone) + Two Mills replay (big screen). No grid of charts anywhere |
| 5. Stand out, be clear | Good pitch but long | One hook, one user, one decision, one proof |
| 6. Real problem you know | No personal link to mills | Industry framing + labelled persona, see 1.3 |

### 1.3 Framing: an industry problem, not a personal one (mentor advice 6)

Decision: no personal connection, so we lead with a **national industry story** and say plainly that we are outsiders who did the homework. Never invent a personal story.

1. **National story (the lead).** Palm oil is one of Malaysia's biggest industries; the Ministry is pushing AI into milling right now, and only one of ~446 mills has done it, at multi-million-ringgit cost. MillGuard is the low-cost path for the rest.
2. **A clearly labelled persona.** "Encik Rahman, night-shift maintenance supervisor" — built from real job descriptions and published mill studies, and introduced as a persona, not a real person.
3. **Our own angle.** Zhen's cybersecurity background gives a credible answer to "would a mill let you connect to their machines?": MillGuard is **read-only and OT-safe by design** (section 4.2). Few teams will have this.
4. **Honesty as a strength.** The data slide says up front what is real, what is simulated and what is assumed.

### 1.4 Research findings that change the plan

| Finding | Effect on plan |
| --- | --- |
| Minsawi Industries (Kuala Kangsar) is described as the first AI-run mill; launched Nov 2024 with AIREI; reported OER +0.1%, uptime +5–10% from predictive maintenance, about RM2.6m savings a year | Use as proof the market wants this. Our gap: it is one of ~446 mills, and analysts flag deployment cost as the barrier to scale |
| Ministry of Plantation and Commodities (July 2026) says it will step up AI and automation in milling with MPOB and SPPOMA | "Why now" slide |
| 2025 MPOB average CPO price RM4,292.50/t; national OER 19.74%; physical CPO ~RM4,420/t on 5 Oct 2026 | Replace RM4,180 everywhere. Base case uses the MPOB 2025 average (official, citable); slider covers spot |
| Newer screw press studies give worm maintenance intervals of about 1,200 hours and replacement around 2,000 hours (Indonesian mills, 2021–2026), next to the 700–800 hour worm life already in our plan | Simulator worm life: random between 700 and 2,000 hours, not a fixed number |
| Boiler dataset: real coal-fired boiler, 5 s data, **only 5 days** (27 Mar–1 Apr 2022), 30 variables, 8.6% anomalous; licence **CC BY-NC-ND** | Use only for the boiler anomaly demo. Do **not** commit the raw or modified data to a public repo; download it via script |
| MetroPT-3: real compressor data, Feb–Aug 2020, 208 MB, 4 air-leak failures with dates, CC BY 4.0 | Good real-data robustness test; small enough to run in under an hour |
| Predictive maintenance is the first example on the track slide | Many teams will do generic predictive maintenance on NASA or AI4I data. We win on local context, ringgit decisions, honest data and a non-dashboard UX — not on model accuracy |

### 1.5 Uniqueness verdict

Sufficient and distinctive, **if** we lead with the decision and the proof, not the model. Our edge over other teams: real Malaysian economics, a physics-based simulator with a cited parameter table, a three-policy backtest in ringgit, and a UX that is a briefing, not a dashboard. Our edge over AIREI-style vendors: cheap clamp-on sensors plus existing Excel logs, and cost-ranked actions instead of limit alarms.

---

## 2. What we are building (demo scope)

### 2.1 The user and the decision

**User:** night-shift maintenance supervisor at a 60 t/h mill with 4 screw presses and 1 boiler.
**Decision, every shift, for each asset:** fix now / schedule at the next planned stop / keep monitoring — whichever has the lowest expected cost.

### 2.2 The experience (replaces the dashboard)

Three surfaces, nothing else:

1. **Shift Brief (phone, the product).** What the supervisor sees at 19:00. A short stack of up to 5 action cards, most expensive first. Each card: asset, likely fault, risk, RM at risk, what to do, by when. Tap a card to see the top 3 reasons in plain words and one small trend line. Buttons: Fix now / Schedule / Keep watching, and "Was this useful?". BM/EN toggle. An empty brief says "Nothing needs you tonight" — no false alarms is a feature.
2. **The Line (context).** A simple left-to-right strip of the mill (ramp → sterilizer → digesters → Press 1–4 → clarification; boiler underneath). Machines glow by risk. A time scrubber lets the presenter fast-forward the night. This is a process picture, not a chart grid.
3. **Two Mills (the proof, on the big screen).** Two copies of the same mill run the same months with the same hidden wear. Left: run-to-failure (or fixed interval, toggle). Right: MillGuard. Breakdowns appear as red events; ringgit counters climb on each side. Sliders: CPO price, cost of a missed failure, alert budget. The gap between the counters is our answer to "can you prove it?".

Optional (P1): the same brief arrives as a **Telegram message** on a judge's phone during the demo.

### 2.3 Demo script (3 minutes)

1. **Quiet night (20 s):** brief says nothing needs you. The Line is all green.
2. **Fast-forward (40 s):** Press 2 current per tonne creeps up over 5 days. A worm-wear card appears about 2 days ahead.
3. **Open the card (40 s):** three reasons in plain words, RM at risk, "change worm at tomorrow's 06:00 stop". Switch to BM for 3 seconds.
4. **Competing alert (30 s):** a boiler anomaly the same night. MillGuard ranks it first because the boiler stops the whole mill, and says why.
5. **Proof (50 s):** Two Mills. Let a judge move the CPO price slider and watch the gap and the alert count change.

Backup: recorded video of the same run, plus the frontend's built-in fixture mode (works with no backend).

---

## 3. Data plan (cut to fit)

Confirmed again on 10 Oct: **no public palm oil mill sensor or failure dataset exists.** We say so on the data slide.

| Source | Real? | Use | Licence | Size / effort | Priority |
| --- | --- | --- | --- | --- | --- |
| **Our screw press simulator** | Simulated, calibrated | Main training and demo data | Ours | ~350k rows, fast | **P0 – need** |
| **MPOB 2025 monthly CPO production** | Real | Crop seasonality curve in the simulator (Feb low ~1.19 Mt → Oct peak ~2.04 Mt, about 1.7×) | Public stats | 12 numbers, typed in | **P0 – need** |
| **MPOB / published economics** (`params.yaml`) | Real | Cost engine | Public | Typed in | **P0 – need** |
| **MetroPT-3** | Real compressor, 4 dated failures | Robustness test: same alert logic on real noisy data | CC BY 4.0 | 208 MB CSV, `ucimlrepo` | **P0 – need** |
| **Boiler dataset** | Real coal-fired boiler, 5 days | Boiler anomaly demo | CC BY-NC-ND (non-commercial, no derivatives) | Small CSV via figshare; never committed | P1 – should |
| Paderborn bearings | Real lab rig | Bearing fault signatures | CC BY-NC 4.0 | 64 kHz MATLAB files, 4 s clips — heavy to process | P2 – skip unless ahead |
| UCI Hydraulic | Real test rig | Cone hydraulic fault class | CC BY 4.0 | ~2,200 cycles | P2 – skip unless ahead |
| Azure PdM | Synthetic | Table layout only (telemetry / errors / maintenance / failures) | — | No download needed | Schema only |
| NASA C-MAPSS, AI4I | Simulated | — | — | — | Dropped |

If Paderborn is skipped, the simulator still models the textbook bearing pattern (kurtosis rises first, then RMS), with a literature citation.

### 3.1 Simulator spec

- **Mill:** 4 presses at 15 t/h each (60 t/h total), 1 boiler. Hourly data.
- **Calendar:** simulate calendar year 2025 (1 Jan–31 Dec), so MPOB 2025 monthly seasonality lines up. Mill 10 is unseen in training, so its whole year is valid for the demo replay.
- **Fixture numbers are samples.** In fixture mode the frontend shows a small "Sample data" badge. Final pitch numbers come only from the pipeline output.
- **Many mills, not one:** simulate **10 mills × 12 months** with different seeds, noise and drift. Train on mills 1–9 (months 1–8), test on unseen mill 10 and on months 9–12. Demo replays mill 10. This gives enough failures to train and a real "unfamiliar data" test.
- **Hidden states per press:** worm wear (grows with tonnes), bearing health, gearbox health, cone hydraulic health.
- **Observed signals:** motor current, throughput, current per tonne, cone hydraulic pressure, gearbox oil temperature, vibration RMS and kurtosis, daily lab fibre oil loss.
- **Physics links:** worn worm → more current per tonne and more oil lost in fibre. Failing bearing → kurtosis rises first, then RMS. Gearbox → oil temperature drift. Cone → unstable pressure.
- **Realism:** sensor noise, slow drift, missing readings, shift patterns, crop seasonality from MPOB 2025 monthly production, one planned weekly stop.
- **Messy logs on purpose:** about 10% of work orders get the wrong fault class or a late timestamp, like real Excel logs. The model must cope.
- **Failures:** when a hidden state crosses its limit; written to a work-order log (time, asset, fault class, downtime hours, parts) in Azure PdM-style tables. Failure modes follow the screw press FMEA studies: worm screw, press cage, shaft, bearing, oil seal / hydraulics.
- **Calibration anchors:** cone pressure up to ~60 bar; fibre oil loss ~4% as the mill alarm line (Thai mill study); worm life 700–2,000 h; target about 25–50 unplanned press stops per mill-year (the North Sumatra mill logged 65 in 7 months).
- **Every number lives in `params.yaml`** with a `source` and a `status: validated | assumed`. The frontend shows this table; the pitch quotes it.

### 3.2 Economics (`params.yaml`, base case)

| Parameter | Value | Status |
| --- | --- | --- |
| Throughput | 60 t FFB/h (15 per press) | Validated (published mill simulation) |
| OER | 19.74% | Validated (MPOB 2025) |
| CPO price | RM4,292.50/t base; slider RM3,800–5,000 | Validated (MPOB 2025 average); spot ~RM4,420 |
| RM per mill-hour | ≈ RM50,800 | Derived |
| RM per press-hour | ≈ RM12,700 | Derived |
| Unplanned press stop | 4 h | Assumed |
| Planned repair at weekly stop | 0 extra lost hours | Assumed |
| Share of delayed output truly lost | 30% (20–40%) | Assumed (rest is caught up) |
| Inspection cost per false alarm | RM300 | Assumed |
| Repair parts + labour per fault class | placeholder per class | Assumed — shown as a slider, flagged on the data slide |
| Criticality | boiler = whole mill; one press = ¼ mill | Derived |

The old ROI table in the original plan used RM4,180/t. **Do not hand-edit ROI numbers**: `backend/scripts/roi.py` regenerates the low/base/high table from `params.yaml`.

---

## 4. Backend

### 4.1 Demo stack (what we build tonight)

| Layer | Choice | Why |
| --- | --- | --- |
| Language | Python 3.11 | Team skill, ML ecosystem |
| Data | pandas, NumPy, SciPy, Parquet files | Small data (~350k rows); no database needed |
| Models | LightGBM (72 h failure risk), scikit-learn Isolation Forest (unknown patterns), LightGBM or rules (fault class) | Fast, explainable |
| Explain | SHAP → template sentences in EN and BM | Grounded, no hallucination risk |
| Optional LLM polish | Claude API, prompted only with model outputs | P2; template is the default |
| API | FastAPI + Pydantic + Uvicorn | Contract becomes typed models and auto OpenAPI docs |
| State | **Stateless.** Every endpoint takes `at` (a timestamp); predictions are precomputed per hour into Parquet | The frontend controls time; nothing to break in a live demo |
| Bot (P1) | python-telegram-bot | Live message on a judge's phone |
| Hosting | Run locally on Computer A; expose with a tunnel (Cloudflare Tunnel or ngrok) for Computer B; Render/Railway only if time allows | Fewest moving parts |

**Pipeline (offline, `make all`):** simulate → features (rolling 6/24/72 h means, slopes, std; current per tonne; hours since service) → train → predict every hour for mill 10 → threshold + alert control → cost engine → backtest three policies → write `artifacts/*.parquet` + JSON. The API only reads artifacts, except `/backtest`, which re-runs the cheap cost maths with slider values.

**Alert control:** alert when P(fail) > C_FP / (C_FP + C_FN); must hold 3 consecutive hours; clears only well below the threshold; max 5 per shift; only if there is still time to act.

**Sanity fixes (v1.2, 15:20):**
- **Fix now vs wait needs the risk up to the next planned stop**, which can be up to 7 days away. Train LightGBM for three horizons (24 h, 72 h, 168 h) and interpolate P(fail before next stop). Fix now = stop hours × RM/h + parts. Wait = P(fail before stop) × breakdown cost + parts.
- **Fair baselines.** The fixed-interval policy uses the best interval found by a sweep on training mills (not a weak guess); run-to-failure is as-is. Judges will ask whether we beat a strawman.
- **v1.4 (16:50), after the first full run.** Press catch was ~20%, median lead 16 h; the margin over a swept fixed interval was RM93k; MetroPT-3 caught 0 of 4. Changes:
  1. **Realistic P-F intervals.** Gradual faults must show a detectable warning before they fail. Typical P-F interval (time from first detectable sign to failure): worm wear and gearbox several days to weeks; bearing several days. Electrical faults stay mostly sudden. Report catch rate **per fault class**; sudden faults are expected misses.
  2. **Add a fourth policy, "Schedule + MillGuard".** Keep the mill's existing schedule, stretched to a longer interval, and let MillGuard catch what fails in between. This is how a real mill would adopt it, and it is the headline comparison.
  3. **One targeted MetroPT-3 retry** with domain features (compressor duty cycle, load cycles per hour, recharge time — the compressor's version of current per tonne). Threshold still set only on Feb–Mar healthy data. Max 90 minutes; if it still misses, report it honestly.
  4. **Real MPOB 2025 monthly CPO production** for seasonality (tonnes): Jan 1,239,895; Feb 1,188,443; Mar 1,387,616; Apr 1,686,379; May 1,771,621; Jun 1,692,370; Jul 1,812,467; Aug 1,854,756; Sep 1,840,983; Oct 2,043,886; Nov 1,935,510 (revised); Dec 1,829,549 (preliminary). Normalise to the mean.
  5. **inspection_finds_wrong_class** stays as an assumption (default 50%, slider 0–100%); the deck shows the strict result too.
  6. **Telegram bot dropped.** The real boiler dataset stays P1, only if everything above is done by 23:00.
- **Boiler is P0 in simulated form.** The demo's competing alert needs it. Add 1 boiler to the simulator (steam temperature drift outside 530–545 °C, feed-water quality drift, rare tube-leak events). The real 5-day boiler dataset stays P1, as a "same detector works on real boiler data" check.

### 4.2 Professional stack (for the "path to a real mill" slide)

```
 MILL FLOOR (OT)                      MILL SITE (EDGE)                 PLATFORM (on-prem or Malaysian cloud region)
 ───────────────                      ────────────────                 ───────────────────────────────────────────
 Clamp-on CT sensors  ─┐              Industrial edge gateway          MQTT broker (EMQX), TLS + device certs
 Accelerometers       ─┼─► (wired) ─► • feature extraction (RMS,   ─►  Ingestion service
 Temperature probes   ─┘               kurtosis, FFT bands)            TimescaleDB (sensor time series)
 Existing PLC / DCS ──► read-only ──► • store-and-forward when        PostgreSQL (assets, work orders, feedback)
   (Modbus / OPC UA)     tap           the link drops                  Prefect: nightly features, weekly retrain
 Lab results, Excel ────────────────► • local copy of the model       MLflow: model registry and versions
   maintenance logs                     so alerts work offline         FastAPI decision service (cost engine)
                                                                       Evidently: data drift monitoring
                                                                       Grafana + Prometheus: system health
                                                                       Alerts: WhatsApp Business / Telegram / SMS
                                                                       Shift Brief web app (PWA)
```

- **Deploy:** Docker Compose on one mill-site server for a pilot; k3s when there are several mills. On-prem by default because OER and oil loss data are commercially sensitive.
- **Security (our differentiator):** strictly read-only from the control network; no inbound connections to PLCs; network zones following IEC 62443 (sensor network → edge → platform, one direction); device certificates; role-based access; audit log of every acknowledged alert; PDPA for operator data; NDA and on-prem processing for mill data.
- **Integrations:** import Excel work orders on day one; connect a CMMS later.
- **Cost:** retrofit kit roughly RM2,000–5,000 per press; Industry4WRD grants may co-fund eligible SMEs.
- **Pilot:** 4–8 weeks on one press with 12 months of digitised maintenance logs; compare MillGuard alerts with what actually broke.

---

## 5. Scope — P0 / P1 / P2

**P0 (must exist at 03:00 freeze)**
- Simulator (10 mills × 12 months) + `params.yaml` with sources
- LightGBM 72 h risk model + Isolation Forest + fault classifier (worm, bearing, gearbox/shaft, hydraulic cone, electrical, unknown)
- Cost engine, threshold, alert budget, persistence
- SHAP → plain-language reasons (EN + BM)
- Three-policy backtest with slider inputs
- MetroPT-3 robustness numbers
- API (section 7) + fixtures
- Frontend: Shift Brief, The Line with time scrubber, Two Mills replay, assumptions table, fixture mode
- Backup video, deck

**P1 (only after P0 is green)**
- Boiler anomaly module on the real boiler data
- Telegram bot pushing the brief
- Feedback button that visibly moves the threshold in the replay

**P2 (stretch, likely skip)**
- Paderborn bearing signatures, UCI Hydraulic cone class, LLM-polished wording, cloud hosting

**Out of scope:** login, user management, whole-mill coverage, mobile native app, real sensor hardware.

---

## 6. Timeline (MYT)

| Time | Backend (Computer A) | Frontend (Computer B) | Pitch teammate | Gate |
| --- | --- | --- | --- | --- |
| 15:00–15:45 | Repo, skeleton, `params.yaml`, **fixtures for every endpoint** | Claude Design: 2–3 directions for Shift Brief + Two Mills | Industry story research; deck outline | Repo up, fixtures pushed |
| 15:45–17:30 | Simulator + work-order log | Design iterations; **team approves one direction by 17:30** | Problem + evidence slides | Design approved |
| 17:30–21:00 | Features, models, time-based split, mill-10 test | Build on fixtures: Shift Brief + The Line | Persona, user, data-honesty slide | — |
| 21:00–23:30 | Cost engine, alert control, SHAP cards, backtest | Two Mills replay + sliders + assumptions table | Draft script, ask mentors for feedback | **23:30: real API live, first integration** |
| 23:30–03:00 | MetroPT-3 test, P1 boiler, P1 Telegram | Integration, polish, BM/EN, fixture fallback | Deck v1 with real numbers | **03:00: feature freeze** |
| 03:00–05:30 | Regenerate final numbers, bug fixes only | Bug fixes only | Sleep (from 01:00) | Sleep shifts: pitch 01:00–04:00, Computer B person 03:00–05:30, Computer A person 04:00–06:30; agents keep running |
| 05:30–07:30 | Freeze artifacts; `roi.py` final table | Final polish; record backup video | Final deck; rehearse | Video recorded |
| 07:30–09:00 | Standby | Standby | Two full rehearsals with Q&A | — |
| **09:00** | | | **Submit (30 min buffer)** | Done by 09:15 |

Rules: no new features after 03:00. If anything P0 is red at 23:30, drop all P1 and fix P0.

---

## 7. API contract v1 (frozen; changes need a CHANGELOG entry)

Base URL `/api`. All times ISO 8601 in MYT. All money in RM (integers). Every GET takes `at` (the replay clock); default = latest.

```ts
type FaultClass = "worm_wear" | "bearing" | "gearbox_shaft" | "hydraulic_cone"
                | "electrical" | "boiler_steam" | "boiler_water" | "unknown";
type Recommendation = "fix_now" | "schedule_next_stop" | "monitor";
type AssetStatus = "ok" | "watch" | "act";

interface Reason { text_en: string; text_ms: string; signal: string;
                   direction: "up" | "down"; contribution: number; }  // contribution 0..1

interface Action {
  id: string; asset_id: string; asset_name: string; asset_type: "press" | "boiler";
  fault_class: FaultClass; risk_pct: number; horizon_h: number;
  rm_at_risk: number; rm_cost_to_act: number; rm_saved_if_acted: number;
  recommendation: Recommendation; deadline: string;
  headline_en: string; headline_ms: string;
  reasons: Reason[];            // exactly 3
  why_rank_en: string; why_rank_ms: string;   // e.g. "Boiler stops the whole mill"
  criticality: "whole_mill" | "partial";
}
```

| Endpoint | Returns |
| --- | --- |
| `GET /api/meta` | `{ mill: {name, throughput_tph, presses, oer, cpo_price_rm}, replay: {start, end, step_h}, rm_per_mill_hour }` |
| `GET /api/brief?at=` | `{ at, shift: "day"|"night", actions: Action[] /* ≤5, sorted by rm_saved_if_acted */, watching_count, suppressed_count }` |
| `GET /api/line?at=` | `{ at, assets: [{id, name, type, stage, status, risk_pct}] }` |
| `GET /api/assets/{id}?at=&window_h=168` | `{ asset, series: [{signal, label_en, label_ms, unit, points: [[t, v]]}], alert_windows: [{start, end}], failures: [{t, fault_class}], action: Action|null }` |
| `GET /api/backtest?cpo_price=&miss_cost_mult=&alert_budget=&compare=run_to_failure|fixed_interval` | `{ threshold, policies: [{id, total_cost_rm, breakdowns, planned_stops, false_alarms, downtime_h, lost_cpo_t}], timeline: [{t, cost: {run_to_failure, fixed_interval, millguard}, events: [{policy, type: "breakdown"|"planned_fix"|"false_alarm", asset_id}]}] }` |
| `GET /api/assumptions` | `[{key, label, value, unit, source, status: "validated"|"assumed"}]` (English only) |
| `GET /api/robustness` | `{ dataset: "MetroPT-3", failures_total, caught, median_lead_h, false_alarms_per_week, note }` |
| `GET /api/replay/markers` | `[{t, kind: "bookmark"|"alert"|"breakdown", label_en, label_ms, asset_id?}]` (v1.1) |
| `POST /api/feedback` | body `{action_id, useful?: boolean, decision?: Recommendation}` → `{ ok: true }` (v1.1) |

**Contract v1.5 changes (10 Oct, 17:15) — machine-first redesign (see section 14):**

```ts
interface FingerprintCheck { signal: string; label_en: string; label_ms: string;
  expected: "up" | "down" | "unstable" | "spike"; observed_en: string; observed_ms: string; matches: boolean; }
interface Diagnosis { fault_class: FaultClass; name_en: string; name_ms: string; confidence_pct: number;
  plain_en: string; plain_ms: string;                 // one sentence: what is physically happening
  alternatives: { fault_class: FaultClass; confidence_pct: number }[];
  fingerprint: FingerprintCheck[]; }                  // 3–4 checks
interface FixPlan { title_en: string; title_ms: string; steps_en: string[]; steps_ms: string[];
  parts: { name_en: string; name_ms: string; qty: number }[];
  crew: number; est_hours: number; needs_stop: boolean; best_window: string; }  // ISO time
interface HistoryItem { t: string; fault_class: FaultClass; what_en: string; what_ms: string;
  downtime_h: number; was_predicted: boolean; }
interface FaultGuide { fault_class: FaultClass; name_en: string; name_ms: string;
  what_en: string; what_ms: string; why_en: string; why_ms: string;
  signs: { signal: string; label_en: string; label_ms: string; expected: FingerprintCheck["expected"] }[];
  fix_steps_en: string[]; fix_steps_ms: string[];
  typical_downtime_h: number; typical_cost_rm: number; onset: "gradual" | "sudden"; }
```

- `GET /api/assets/{id}` adds `status`, `risk_pct`, `diagnosis: Diagnosis | null`, `fix: FixPlan | null`, `history: HistoryItem[]` (last 12 months for that machine).
- `GET /api/line` assets add `summary_en`, `summary_ms` (e.g. "Worm wearing" / "Normal").
- New `GET /api/faults` → `FaultGuide[]` (static, from the FMEA studies; drives the fault guide).
- `/api/backtest` policies include `schedule_plus_millguard` (v1.4). The Impact page's "After" = `schedule_plus_millguard`, "Before" = `run_to_failure`.
- Fix steps are generic maintenance actions (inspect, replace, check), written in plain language.
- **Money semantics (v1.6, 17:45; replaces the 17:30 rule):** "wait" means **skipping this chance to fix it**.
  - `fix_now`: window = now → next planned stop.
  - `schedule_next_stop`: window = now → the planned stop **after** the next one (skipping this stop means running a week longer).
  - `horizon_h` = that window in hours; `risk_pct` = P(fail within it); `rm_at_risk` = risk × full breakdown cost; `rm_saved_if_acted` = `rm_at_risk − rm_cost_to_act` (min 0).
  - UI wording: "If not fixed at tomorrow's 06:00 stop: 74% chance it fails before the next one" and "Expected loss if you skip it: RM17,900 (74% × RM24,200 breakdown)". The full breakdown cost is `round(rm_at_risk / (risk_pct/100))`.
- **v1.9 contract additions (20:15, additive):** `LineAsset.name_ms`, `Action.asset_name_ms` (one Malay term map `MS_TERM` in text.py: Penekan, Dandang), `Series.unit_ms`, `Outlook.note_en/ms`; v1.9b adds `Outlook.handled_at?` (time of the repair that closed the last alert). Series serve running hours only; every summary is computed from the served points (checked in `make fixtures`).
- **Handled machines:** after an alert is acted on, the machine reads ok with risk 0 and a note ("Already handled …") until the risk clears. Known approximation (disclose if asked): the backtest replays fixed simulated telemetry, so signals after an early repair still show the old wear until the original failure time; we treat the part as renewed and don't model its slightly earlier next wear-out (median lead 63 h vs part life 700–2,000 h, a small bias in MillGuard's favour).
- **Final demo bookmarks:** Quiet night 2025-07-30 19:00 (0 actions, 1 weak signal ignored); Whole mill 2025-09-14 03:00 (Boiler 1 feed-water fault, 99%, protects RM122,252); Act now 2025-09-29 15:00 (Press 2 cone hydraulic fault, 84%, 3 of 3 signs, protects RM6,096).
- **v1.7 contract additions (18:00, requested by design; additive, no removals):**
  - `FingerprintCheck.expected` adds `"steady"`.
  - `Action` adds `rm_breakdown_cost` (explicit; UI never divides), `deadline_label_en/ms` (e.g. "tomorrow's 06:00 stop"), and `window_label_en/ms` describing the end of the risk window (e.g. "before the next stop, Sun 06:00"). `horizon_h` stays = the v1.6 risk window, **not** hours to the deadline.
  - `FixPlan`: `needs_stop` → `stop: "none" | "machine" | "whole_mill"` plus `lost_production: boolean`.
  - `/api/assets/{id}` adds `last_service: {t, what_en, what_ms, hours_since}` and `next_check: {t, label_en, label_ms}`; for status `ok`, the response also carries the at-risk and cost-to-act figures so the UI can say "waiting is cheaper by RM x".
  - `Series` adds `limit?: number` and `summary_en/ms` (e.g. "4.1 → 4.6 A/t"). Every `Reason.signal` exists in `series`.
  - `/api/brief` adds `rm_protected_total`.
  - `/api/backtest`: `compare` accepts `run_to_failure | fixed_interval | millguard_only`; always returns all four policies.
  - `/api/robustness` adds `test_mill: {id, by_fault_class: [{fault_class, total, caught, median_lead_h}], false_alarms_per_week}` next to MetroPT-3 and `extra[]`.
  - Every user-facing text field has an `_ms` twin, with no abbreviations.
  - FaultClass stays as is (no new "tube leak" class; boiler alternatives use existing classes).
- **Design sample values are mock-ups only.** Fixtures stay a real snapshot (v1.6). The frontend reads every number and label from the API, and the layout must handle real ranges (press cards ~RM1–20k, boiler cards larger). Real press breakdown cost ≈ RM24k (4 h × RM12,700 × 30% truly lost + repair); the design's RM51,000 assumed 100% loss. Bookmark labels come from `/api/replay/markers` (now Quiet night / Press 2 act now / Whole mill).
- **v1.6 contract change:** `/api/backtest` takes `inspection_accuracy` (0–1, default 0.5) = `inspection_finds_wrong_class`.
- **Demo moments (rule, not cherry-picking totals):** Act-now bookmark = an alert on a gradual fault that was later prevented (true positive), placed at the hour in its alert window where the fingerprint matches most checks; prefer Press 2. Both-alerts bookmark = a night where a boiler alert and a press alert are both Act now, with the largest combined saving. Quiet bookmark = a night with 0 actions and non-zero watching/suppressed. Yearly totals are unaffected.
- **Fixtures = real snapshot.** Once bookmarks are final, regenerate every fixture from the real API at those bookmarks (and the real backtest), so fixture mode (the demo backup) shows true numbers. Repeat at the 03:00 freeze.
- **Results v1.4 (mill 10, 2025):** run-to-failure RM973k / 34 breakdowns; fixed (swept) RM724k / 10; MillGuard alone RM558k / 12; schedule + MillGuard RM421k / 3. Catch 22/34, median lead 63 h, 1.3 false alarms/week. Strict inspection case: schedule + MillGuard RM558k. Caveats to disclose: assumed P-F warning periods (worm 300 h, gearbox 400 h, bearing 150 h, cone 200 h); the "schedule + MillGuard" schedule is 0.6× mean life (close to the plain schedule's 0.5×, so not truly stretched); MetroPT-3 0/4 caught early.

**Contract v1.1 changes (10 Oct, 15:10):**
- New `GET /api/replay/markers`. Bookmarks are the 3 demo moments on mill 10, chosen by the backend: quiet night, Press 2 worm-wear alert onset, boiler + press alerts on the same night. Alerts are every MillGuard alert. Breakdowns are failures under run-to-failure.
- `/api/backtest`: `timeline` is **daily** (365 points, `{t, cost: {...}}`); `events` moves to a top-level array `[{t, policy, type, asset_id}]` with exact hourly timestamps.
- `/api/line`: `stage` is `"press" | "boiler"` only; add `position` (1–4 for presses, 0 for boiler). The frontend draws ramp, sterilizer, thresher, digesters and clarification as static shapes.
- `POST /api/feedback`: optional `decision` records Fix now / Schedule / Keep watching. Button state stays client-side.
- Slider ranges (the frontend owns these; the backend clamps inputs): CPO RM3,800–5,000 (default 4,292.5); `miss_cost_mult` 0.5–3 (default 1); `alert_budget` 1–10 (default 5).

Fixtures live in `contracts/fixtures/*.json`, one file per endpoint, built from the real Pydantic models so they cannot drift.

---

## 8. Repo and git rules

```
millguard/
  MASTER_PLAN.md        ← this file (orchestrator owns)
  CLAUDE.md             ← short rules for agents; points here
  CHANGELOG.md          ← every contract or scope change, one line each
  contracts/            ← api.ts types + fixtures/*.json (backend owns, frontend reads)
  backend/
    sim/  features/  models/  engine/  api/  scripts/
    params.yaml
    data/               ← gitignored (raw downloads; boiler data never committed)
    artifacts/          ← generated; commit only small demo JSON
  frontend/             ← frontend owns
  pitch/                ← deck exports, script, video link
```

- One repo, `main` branch only, each agent touches only its own folder. `git pull --rebase` before every push; push small and often.
- Only the backend edits `contracts/`. A contract change = edit, regenerate fixtures, one line in CHANGELOG, tell the orchestrator.
- `.gitignore`: `backend/data/`, large Parquet, `.env`, `node_modules/`.
- Secrets (Telegram token, API keys) in `.env`, never committed.

---

## 9. Frontend

### 9.1 Claude Design brief (paste this into Claude Design on Computer B)

> Design a demo app called **MillGuard** for a hackathon. It helps the night-shift maintenance supervisor at a Malaysian palm oil mill decide which machine to fix first, ranked by ringgit at risk.
>
> **Hard rule: this is not a dashboard.** No grid of KPI tiles, no sidebar of charts. It should feel like a calm, confident briefing.
>
> Design three surfaces:
> 1. **Shift Brief (mobile, 390 px wide).** A short stack of up to 5 action cards. Each card shows: machine name, likely fault ("Worm wear"), risk %, RM at risk, the recommendation ("Change worm at tomorrow's 06:00 stop"), and a deadline. Tapping opens the "why": three plain-language reasons and one small trend line. Buttons: Fix now / Schedule / Keep watching, and a small "Was this useful?". A BM/EN language toggle. Also design the empty state: "Nothing needs you tonight."
> 2. **The Line (desktop).** A simple horizontal process strip of the mill: ramp → sterilizer → digesters → Press 1–4 → clarification, boiler underneath. Each machine glows calm / watch / act. A time scrubber across the bottom to fast-forward the night.
> 3. **Two Mills (desktop, for a projector).** Two copies of the same mill side by side over 12 months: "Fix when it breaks" vs "MillGuard". Breakdowns appear as red events, planned fixes as calm markers, and two large ringgit counters climb. Below: three sliders (CPO price, cost of a missed failure, alerts per shift) and a toggle to compare against "Fixed schedule" instead. The gap between the counters is the hero.
>
> Tone: industrial, trustworthy, plain language for non-experts. Must read clearly on a projector. Use real-looking sample data: Press 2, worm wear, 41% risk in 48 h, RM18,000 protected; Boiler 1, steam temperature anomaly, stops the whole mill.
>
> Give me 2–3 distinct visual directions first, then we will pick one.

**Approval checklist (team decides by 17:30):** readable from 3 m on a projector; the RM number is the first thing the eye lands on; nothing looks like a dashboard; works at 390 px; BM text fits.

### 9.2 Build stack (after approval)

- React + Vite + TypeScript, Tailwind CSS, Framer Motion for the replay, a light chart lib (Recharts) only for the small trend lines and counters.
- Types copied from `contracts/api.ts`; a single `api.ts` client with a **fixture mode** switch (`VITE_USE_FIXTURES=true`) so the demo never depends on the network.
- Routes: `/brief` (mobile frame on desktop), `/line`, `/proof`. No login, no settings.
- Hosting: local `vite preview` for the demo; Vercel as a shareable link if time allows.

---

## 10. Kickoff prompts

### 10.1 Backend agent (Computer A)

> Read `MASTER_PLAN.md` fully; it is the single source of truth. You own `backend/` and `contracts/`. Work in this order and commit after each step:
> 1. Create the repo skeleton from section 8, `CLAUDE.md`, `CHANGELOG.md`, `.gitignore`, `backend/params.yaml` (values and sources from section 3.2).
> 2. Write Pydantic models for the API in section 7, export `contracts/api.ts`, and generate realistic fixtures in `contracts/fixtures/` for every endpoint. Push within 60 minutes — the frontend is waiting on these.
> 3. Build the simulator (section 3.1), then features, models (time-based splits, train mills 1–9, test mill 10), alert control, cost engine, SHAP reasons in EN and BM, backtest, then the FastAPI app reading precomputed artifacts.
> 4. Then MetroPT-3 robustness, then P1 items.
> Keep code simple with minimal comments. Print a short metrics summary (failures caught, median lead time, false alarms per week, RM per policy) after each pipeline run. Never commit `backend/data/`. Ask before changing the contract.

### 10.2 Frontend agent (Computer B, after design approval)

> Read `MASTER_PLAN.md` fully; it is the single source of truth. You own `frontend/` only. Build the approved Claude Design direction with the stack in section 9.2, using `contracts/api.ts` types and `contracts/fixtures/` until the backend is live. Build in order: Shift Brief → Two Mills → The Line. Fixture mode must always work. No login, no dashboard grids. Keep code simple with minimal comments. Pull before every push and never edit `contracts/`.

---

## 11. Pitch (for the pitch teammate)

**Slide order (~7 min + demo):**
1. Hook: RM51,000 an hour. A photo of a screw press.
2. Problem: boiler station OEE 27% vs 85% world class; 65 press breakdowns in 7 months at one mill; maintenance run from Excel and memory.
3. Why now: one AI mill out of ~446; the Ministry is pushing AI into milling.
4. The user and the one decision.
5. Honest data: no public mill dataset exists; our simulator + real data checks; assumptions table (validated vs assumed).
6. How it works: Detect → Categorize → Prioritize → Explain.
7. Live demo.
8. Proof: Two Mills result + low/base/high table (from `roi.py`).
9. False alarms and robustness: alert budget, unseen mill 10, MetroPT-3.
10. Path to a real mill: read-only, OT-safe pilot, retrofit cost, grants.
11. Close: "MillGuard tells the night shift what to fix first, and proves it in ringgit."

**Q&A additions to the original table:**
- *"AIREI already does this."* — Yes, at one mill, as a full multi-million-ringgit transformation. We are a cheap, read-only layer on clamp-on sensors and existing Excel logs.
- *"Is it safe to connect to our plant?"* — Read-only by design, no path back into the PLCs, network zones per IEC 62443, data stays on-site.
- *"Why should we trust simulated data?"* — Every simulator number has a source; we test on a mill the model never saw and on real compressor data; we show the cases where it does worse.

---

## 12. Risks

| Risk | Fix |
| --- | --- |
| Behind schedule at 23:30 | Drop all P1/P2; fixture mode carries the demo |
| Model too accurate on simulated data (looks fake) | Report on unseen mill 10 and MetroPT-3; show misses honestly |
| Backend down during demo | Frontend fixture mode + recorded video |
| Merge conflicts | Separate folders, only backend touches `contracts/` |
| Boiler data licence | Never committed; fetched by script; cited |
| Team exhaustion | Sleep shifts 03:00–05:30; freeze at 03:00 |

---

## 14. Frontend v2 — machine-first redesign (17:15; supersedes sections 2.2, 2.3 and 9.1)

**Goal:** the user can see which machine is malfunctioning, what is wrong with it, and how to fix it, with the same layout logic on mobile and desktop.

**Principles:** the machine is the main thing; problem first, then fix, always in that order; one status vocabulary (Normal / Watch / Act now, always colour + icon + word); show the fault fingerprint; ringgit on every decision; no KPI grids.

**Pages (same order on both devices; mobile bottom tabs, desktop left rail):**
1. **Mill** — time bar, attention summary, ranked attention cards, mill map by station (unmonitored stations greyed out), quiet state.
2. **Machine** — header (status, risk, RM), What's wrong (diagnosis, confidence, alternatives), fault fingerprint checks, 3 evidence items with 7-day trends, What to do (fix plan: when, steps, parts, crew, hours, needs stop), decision bar (wait vs fix vs protected), action buttons, history (predicted / missed), link to the fault guide. Desktop: two columns (problem left, fix right, sticky). Mobile: stacked in the same order, buttons pinned to the bottom.
3. **Impact** — Before (fix when it breaks) vs After (schedule + MillGuard): RM per year, breakdowns, downtime; savings headline; 12-month replay strip; what-if sliders; compare toggle (fixed schedule only / MillGuard only).
4. **How it works** — five-step explainer (Sense, Warning signs, Predict, Decide, Explain) using Press 2 as the example; fault guide; data honesty (real / simulated / assumed) plus robustness.

**Global:** EN/BM toggle, "Sample data" badge in fixture mode, presenter shortcuts (1–4 pages, B next bookmark).

**Demo flow:** Mill quiet night → Press 2 bookmark (Act now) → open Press 2 (fingerprint, fix, RM18k, BM toggle) → boiler + press night (boiler first, whole mill) → Impact (before/after, judge moves a slider). How it works is kept for Q&A.

**Build order:** Machine page → Mill → Impact → How it works.

**Expert advice — now IN SCOPE (v1.10, 20:40; P0 is green). Spec below replaces the stretch notes that follow.**
- `POST /api/advice {asset_id, at, lang: "en" | "ms"}` → `{title, sections: [{heading, items: string[]}], sources: [{label, url?}], disclaimer, generated_at, cached: boolean, model}` (ask the model for JSON matching this shape; validate it with Pydantic and retry once on invalid JSON). Sections in this order: "Check first", "Step by step", "Safety", "Parts and tools", "Call the manufacturer if".
- **LLM provider (v1.11):** Grafilab's OpenAI-compatible endpoint via the `openai` Python package: `base_url` from `LLM_BASE_URL` (default `https://llm.grafilab.ai/v1`), model from `LLM_MODEL` (default `gemini/gemini-3-flash`), key from `LLM_API_KEY` in `backend/.env` (never committed, printed or logged). Use `chat.completions.create` with a system + user message, `temperature` 0.3 (factual guidance, not creative), a 30 s timeout and one retry. All provider settings live in one module (`backend/advice/llm.py`) so the provider can be swapped by changing env vars only. Inputs are grounded only: the asset's diagnosis, fingerprint, fix plan, history and outlook, plus our notes in `backend/knowledge/*.md` (fault guide, FMEA findings and figures we cite, written in our own words with source links). The prompt forbids inventing manufacturer part numbers, torque values or procedures, and requires lock-out/tag-out in Safety for any machine stop.
- Cache: responses stored by (asset, at, lang); `make fixtures` writes `advice_<asset>[_act|_quiet]_<lang>.json` for the 3 bookmarks so fixture mode and the demo never call the network. No key or network → `{cached: false}` with a friendly message, never a crash.
- UI: "Get detailed advice" button under the fix plan; a panel with the sections, sources, and the label "AI-generated guidance — check against the manufacturer's manual and your SOP". Loading and error states. EN/BM follows the toggle.
- Pitch: "Phase 2 grounds this in each mill's own manuals and SOPs."

**Earlier stretch notes (superseded):**
- An "Ask for detailed advice" button under the fix plan calls a new `POST /api/advice {asset_id, at}` that returns `{text_en, text_ms, sources[]}`.
- Backend calls the Claude API with only grounded inputs: the diagnosis, fingerprint, fix plan, machine history, and (if we find them) public manufacturer manual excerpts for screw presses and boilers, stored in `backend/knowledge/` with their source links. No free-form guessing.
- The UI labels it "AI-generated guidance — check against the manufacturer's manual" and lists sources; the generic fix plan stays the default.
- Pitch framing even if not built: "Phase 2 connects MillGuard to each mill's own equipment manuals and SOPs."
- Risk: needs an API key and network at demo time, so it falls back to a cached answer for the demo bookmarks.

## 15. Messaging alerts (18:05; P1, after backend P0 is green)

**Channel:** Telegram for the demo; WhatsApp Business in the production roadmap (needs Meta business verification and approved templates, too risky tonight).

**What gets sent (same content as the app, EN or BM per subscriber):**
- **New Act-now alert:** "⚠️ Press 2 · Hydraulic cone fault · 84% chance it fails before the next stop · Fix now · Protects RM6,096". Then the top reason and a link to the Machine page (only if the frontend has a public URL).
- **Shift brief at 19:00:** the attention list, or "Nothing needs you tonight".
- **Inline buttons:** Fix now / Schedule / Keep watching → recorded via the same feedback logic as `POST /api/feedback`.
- One message per alert id (no repeats); max 5 per shift, same alert budget as the app.

**Design:**
- `backend/notify/telegram_bot.py` using python-telegram-bot with **long polling** (no public URL needed; runs on Computer A next to the API). `/start` subscribes a chat; `/bm` and `/en` switch language; `/brief` sends the current brief.
- Token and allowed chat IDs in `.env` (never committed). A Telegram **group** for the demo; judges join via a QR code on a slide.
- Message text built from the same `text.py` templates as the API, so app and message always match.
- **Contract v1.8 (additive):** `POST /api/notify {at, kind: "alert" | "brief"}` → `{ok, sent: number}` (sends what the replay clock shows at `at`); `GET /api/notify/status` → `{enabled, channel, subscribers}`.
- **Frontend:** a small "Send to phone" button in the time bar, shown only when `/api/notify/status` says enabled. Presenter use only.

**Demo moment:** at the Act-now bookmark, press "Send to phone"; the message lands on the judges' phones in the group; tap "Schedule" on the phone.

**Production roadmap:** an hourly job sends new alerts automatically; WhatsApp Business Cloud API with approved templates; SMS fallback for areas with weak data coverage.

## 13. Sources (new this round)

- MPOB, Overview of the Malaysian Oil Palm Industry 2025 — OER 19.74%, 2025 average CPO RM4,292.50/t: https://bepi.mpob.gov.my/images/overview/Overview2025.pdf
- Bernama, CPO futures 5 Oct 2026 — physical CPO ~RM4,420/t: https://bernama.com/en/market/news.php?id=2615837
- Bernama, Minsawi AI mill launch (Nov 2024), 446 mills: https://www.bernama.com/en/news.php?id=2365111
- The Star via Perak Sejahtera — RM2.6m yearly savings claim: https://www.peraksejahtera.com/perak-facility-is-worlds-first-palm-oil-mill-to-adopt-ai/
- theSun — OER +0.1%, uptime +5–10%: https://thesun.my/business-news/ai-slashes-palm-oil-labour-needs-by-45-JJ14484937
- CropGPT analysis — deployment cost as the barrier to scale: https://cropgpt.ai/malaysia-palm-artificial-intelligence-mill-integration-and-labour-reduction-claims
- The Star (July 2026) — Ministry to step up AI in milling: https://www.thestar.com.my/news/nation/2026/07/26/high-tech-future-eyed-for-palm-oil-productivity
- RCM II screw press study (2026) — worm interval ~1,217 h: https://eprints.umm.ac.id/id/eprint/35590/
- RCM screw press scheduling (2021) — worm replacement ~2,035 h: https://repository.uin-suska.ac.id/38385/
- Boiler dataset (Scientific Data 2025, CC BY-NC-ND): https://www.nature.com/articles/s41597-025-05096-4
- MetroPT-3 (UCI, CC BY 4.0): https://archive.ics.uci.edu/dataset/791/metropt+3+dataset
- MPOB monthly summary 2025 (CPO production by month): https://bepi.mpob.gov.my/stat/web_report1.php?val=202584
- Thai mill sensor study — fibre oil loss threshold 4%: https://www.scielo.org.za/pdf/sajie/v36n1/07.pdf
- Paderborn Bearing DataCenter (CC BY-NC 4.0): https://mb.uni-paderborn.de/kat/forschung/kat-datacenter/bearing-datacenter
- All other sources: see `MillGuard_Full_Hackathon_Plan.md`.
