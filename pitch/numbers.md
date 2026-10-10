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
| Fix when it breaks | RM3,189,545 | 110 | 0 | 0 | /api/backtest policies[run_to_failure] |
| Fixed schedule (published RCM intervals) | RM2,814,203 | 64 | 113 | 0 | /api/backtest policies[fixed_interval] |
| MillGuard alone | RM1,740,300 | 38 | 72 | 16 | /api/backtest policies[millguard] |
| Schedule + MillGuard | RM1,563,350 | 19 | 158 | 16 | /api/backtest policies[schedule_plus_millguard] |

- Schedule + MillGuard saves **RM1,626,195** a year vs fixing when it breaks (51%) and **RM1,250,853** vs the best fixed schedule (44%). Source: /api/backtest.
- Strict case (a wrong-class alert never finds the fault, `inspection_accuracy=0`): Schedule + MillGuard RM1,595,654, still RM1,218,549 below the fixed schedule. Source: /api/backtest?inspection_accuracy=0.
- The fixed schedule uses the published RCM intervals (Ishak et al. 2024: worm 525 h, bearing 533 h, shaft 400 h), no tuning; Schedule + MillGuard uses the same schedule. Source: backend/artifacts/policy_fit.json.

## Detection quality (mill 10, MillGuard alerts)
| Number | Value | Source |
|---|---|---|
| Failures caught before they happened | 72 of 110 | /api/robustness test_mill |
| Median warning time | 70 h | backend/artifacts/episodes.parquet (alert open to failure) |
| False alarms per week | 0.31 | /api/robustness test_mill.false_alarms_per_week |
| Press risk model AUC, 72 h / 168 h | 0.939 / 0.906 | backend/artifacts/model_metrics.json |
| Boiler risk model AUC, 24 h | 0.995 | backend/artifacts/model_metrics.json |

## Real-data checks (honest)
| Test | Result | Source |
|---|---|---|
| MetroPT-3 real compressor, 4 air-leak failures | 0 of 4 flagged before they started; 0.1 false alarms per week | /api/robustness |
| Real coal-fired boiler, steam excursions 10-15 min ahead | 7 of 16 caught, precision 17.4%, 38.5 false alarms per day. No usable skill (AUC 0.54). | /api/robustness extra[] |

## Stress test (mill 10, nothing retrained on mill 10, thresholds unchanged; models trained with noise x2 and drift copies of mills 1-9)
| Condition | Caught | False alarms/week | Schedule + MillGuard | Fixed schedule |
|---|---|---|---|---|
| No perturbation (reference) | 72/110 | 0.31 | RM1,563,350 | RM2,814,203 |
| Sensor noise x2 | 73/110 | 0.67 | RM1,614,806 | RM2,814,203 |
| Sensor noise x3 | 48/110 | 5.81 | RM3,164,774 | RM2,814,203 |
| 20% of readings missing | 72/110 | 0.84 | RM1,567,124 | RM2,814,203 |
| 40% of readings missing | 74/110 | 1.50 | RM1,597,202 | RM2,814,203 |
| Slow sensor drift (+10% over the year on current and vibration) | 72/110 | 0.33 | RM1,556,024 | RM2,814,203 |
| 25% of work orders with the wrong fault class | 69/110 | 0.40 | RM1,604,730 | RM2,814,203 |

**Say it plainly:** the models were trained with noisy (x2) and drifting copies of the training mills, so those rows test conditions it learned. Noise x3 is beyond training: it catches 48 of 110 at 5.8 false alarms a week and costs RM3,164,774, more than the fixed schedule (RM2,814,203). That is the limit: past it a mill needs better sensors, and the sensor-health checks flag it. When readings go missing, catches hold but false alarms rise (see the column above).

## Assumptions to say out loud
- Mills are simulated. The bearing warning period (98.5 h) is measured on NASA/IMS run-to-failure bearings; the other warning periods (worm, gearbox, cone) are assumed.
- Crew inspection finds the real fault 50% of the time when the predicted class is wrong (`inspection_finds_wrong_class`; slider = `inspection_accuracy`).
- Alert threshold uses a false-alarm multiplier fitted on training mills only; nothing is tuned on mill 10.
- Press fault fingerprints use the machine's own previous 30 days as 'normal'.
