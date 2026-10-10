# MillGuard: headline numbers and sources

All results are from simulated mills (mill 10 is unseen in training) unless marked real. Re-generate: `make all && make pitch`.

## Inputs
| Number | Value | Source |
|---|---|---|
| Mill throughput | 60 t FFB/h | params.yaml economics.throughput_tph |
| Oil extraction rate | 19.74% | params.yaml economics.oer (MPOB 2025) |
| CPO price | RM4,292.5 /t | params.yaml economics.cpo_price_rm_per_t (MPOB 2025 average) |
| Value of a mill-hour | RM50,840 | /api/meta rm_per_mill_hour |
| Share of delayed output truly lost | 30% (assumed; slider range 20-40%) | params.yaml economics.lost_share |
| Press breakdown cost (worm wear) | RM24,252 | /api/assumptions derived.breakdown_cost_press |
| Boiler breakdown cost | RM126,517 | /api/assumptions derived.breakdown_cost_boiler |

## Four policies, mill 10, 2025 (base case)
| Policy | Cost | Breakdowns | Planned fixes | False alarms | Source |
|---|---|---|---|---|---|
| Fix when it breaks | RM972,848 | 34 | 0 | 0 | /api/backtest policies[run_to_failure] |
| Fixed schedule | RM723,550 | 10 | 56 | 0 | /api/backtest policies[fixed_interval] |
| MillGuard alone | RM557,570 | 12 | 22 | 68 | /api/backtest policies[millguard] |
| Schedule + MillGuard | RM421,040 | 3 | 51 | 68 | /api/backtest policies[schedule_plus_millguard] |

- Schedule + MillGuard saves **RM551,808** a year vs fixing when it breaks (57%) and **RM302,510** vs the best fixed schedule (42%). Source: /api/backtest.
- Strict case (a wrong-class alert never finds the fault, `inspection_accuracy=0`): Schedule + MillGuard RM558,159, still RM165,391 below the fixed schedule. Source: /api/backtest?inspection_accuracy=0.
- The fixed schedule is the best interval found by a sweep on training mills (0.5 x mean part life); Schedule + MillGuard uses 0.6 x. Source: backend/artifacts/policy_fit.json.

## Detection quality (mill 10, MillGuard alerts)
| Number | Value | Source |
|---|---|---|
| Failures caught before they happened | 22 of 34 | /api/robustness test_mill |
| Median warning time | 63 h | backend/artifacts/episodes.parquet (alert open to failure) |
| False alarms per week | 1.3 | /api/robustness test_mill.false_alarms_per_week |
| Press risk model AUC, 72 h / 168 h | 0.904 / 0.903 | backend/artifacts/model_metrics.json |
| Boiler risk model AUC, 24 h | 0.998 | backend/artifacts/model_metrics.json |

## Real-data checks (honest)
| Test | Result | Source |
|---|---|---|
| MetroPT-3 real compressor, 4 air-leak failures | 0 of 4 flagged before they started; 0.1 false alarms per week | /api/robustness |
| Real coal-fired boiler, steam excursions 10-15 min ahead | 7 of 16 caught, precision 17.4%, 38.5 false alarms per day. No usable skill (AUC 0.54). | /api/robustness extra[] |

## Stress test (mill 10, no retraining, thresholds unchanged)
| Condition | Caught | Schedule + MillGuard | Fixed schedule |
|---|---|---|---|
| No perturbation (reference) | 22/34 | RM421,040 | RM723,550 |
| Sensor noise x2 | 9/34 | RM1,187,186 | RM723,550 |
| 20% of readings missing | 24/34 | RM445,118 | RM723,550 |
| 40% of readings missing | 21/34 | RM622,117 | RM723,550 |
| Slow sensor drift (+10% over the year on current and vibration) | 24/34 | RM428,666 | RM723,550 |
| 25% of work orders with the wrong fault class | 21/34 | RM428,966 | RM723,550 |

**Why noise ×3 is not on the slide:** at ×3 the model catches only 5 of 34 failures and mostly stops alerting, so its cost (RM635,716) comes from the fixed schedule underneath, not from MillGuard. It is in /api/robustness extra[] and backend/artifacts/stress_table.json if a judge asks. Noise ×2 (worse than fixed) is on the slide on purpose: MillGuard needs reasonably clean sensors or retraining on the mill's own data.

## Assumptions to say out loud
- Mills are simulated; warning periods before failure (worm 300 h, gearbox 400 h, bearing 150 h, cone 200 h) are assumed.
- Crew inspection finds the real fault 50% of the time when the predicted class is wrong (`inspection_finds_wrong_class`; slider = `inspection_accuracy`).
- Alert threshold uses a false-alarm multiplier fitted on training mills only; nothing is tuned on mill 10.
- Press fault fingerprints use the machine's own previous 30 days as 'normal'.
