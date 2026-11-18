# Model comparison and business outcomes

## Evaluation design

All results below were executed against the supplied private SQLite database on 18 November 2026. They are network-level aggregates only. Each model issues 56 daily forecasts per site from each origin, with no updates from actual observations during that window. The first two origins (1 July and 26 August 2024) form the comparison period; 21 October 2024 begins the final holdout. The preceding history is used for training at each origin. Hyperparameters were fixed; the validation result selects the model by MAE. The final holdout is not used to choose the model or buffer.

## Data validation

The database integrity, foreign key, site-date uniqueness, daily completeness, nonnegative physical measures and capacity consistency checks passed. Seven inventory-balance discrepancies were each at most 0.01 tonnes, consistent with rounding. Many historical records exceed reported capacity; this is a serious reconciliation issue, not proof of physical stock overflow. Zero consumption is retained. No individual site data is published.

## Forecast model selection

| Model | Validation MAE (t) | Validation RMSE (t) | Validation WAPE | Coverage |
| --- | ---: | ---: | ---: | ---: |
| Random Forest | 10.845 | 14.521 | 46.60% | 3,360/3,360 |
| AR(7) | 10.848 | 14.485 | 46.62% | 3,360/3,360 |
| LightGBM | 10.860 | 14.529 | 46.67% | 3,360/3,360 |
| Seasonal naive | 15.018 | 20.810 | 64.53% | 3,360/3,360 |
| SARIMAX | Not ranked | Not ranked | Not ranked | 2,128/3,360 |

Random Forest is selected by the predeclared MAE criterion, but the absolute differences with AR and LightGBM are tiny. I would retain AR as a low-complexity challenger rather than claim clear superiority. SARIMAX failed to converge on 32 of 90 site-origin fits overall. Its observed errors refer only to successful fits and cannot fairly rank above the complete models.

## Final 56-day holdout

| Model | MAE (t) | RMSE (t) | WAPE | Nonzero-day MAPE | Bias (t) | Coverage |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Random Forest (selected) | 11.371 | 15.224 | 48.69% | 38.45% | +0.326 | 1,680/1,680 |
| LightGBM | 11.366 | 15.197 | 48.66% | 38.47% | +0.627 | 1,680/1,680 |
| AR(7) | 11.373 | 15.122 | 48.69% | 38.74% | +0.343 | 1,680/1,680 |
| Seasonal naive | 15.535 | 21.245 | 66.52% | 58.86% | -0.039 | 1,680/1,680 |
| SARIMAX (partial) | 9.426 | 13.186 | 44.39% | 36.94% | -0.167 | 1,120/1,680 |

The selected model improves MAE by 26.8% versus seasonal naive. LightGBM is marginally better on holdout MAE and AR on RMSE; neither difference establishes a meaningful advantage. The selected model's nonzero-day MAPE remains above 15%. It includes 1,460 positive-consumption observations; 220 zero-consumption days remain in MAE, RMSE and WAPE. Bias is prediction minus observed consumption. I do not compare MAPE calculated on different zero-day conventions.

## Inventory planning replay

The policy assumes a two-day lead time and searches buffer days of 2, 4, 6, 8, 10 and 14 on validation. None reaches 98% scheduled-pour readiness. Ten days is selected for the highest readiness with the lower stock requirement than the tied 14-day candidate (97.71% validation readiness). The buffer is fixed before the revised final replay. The initial stock replay exposed extreme recorded overcapacity, so the simulation was revised to run a capacity-feasible scenario. Both policies start from stock limited to reported silo capacity, with excess explicitly tracked as segregated stock. This is a scenario, not evidence that the excess can be removed in practice. Because the scenario was revised after inspecting the initial replay, the final inventory comparison is exploratory, not a pristine independent policy test.

| Final-window measure | Seasonal-naive policy | Random Forest policy |
| --- | ---: | ---: |
| Scheduled-pour readiness proxy | 97.43% | 97.76% |
| Recorded consumption fill rate | 98.43% | 98.50% |
| Mean silo utilisation | 59.77% | 60.57% |
| Simulated overflow days | 0 | 0 |

Readiness improves by 0.33 percentage points. Mean utilisation increases by 0.80 percentage points (about 1.34% relative), far below a 20% relative increase, if that is the intended definition. Higher average stock is not automatically an efficiency gain, so the metric and baseline require agreement. A capacity-constrained replay is not a claim about historical performance or actual operational savings. The final days of finite-horizon replay can be affected by end-of-window ordering limits.

## Objective scorecard

| Objective | Outcome |
| --- | --- |
| MAPE ≤ 15% | Not met; conditional MAPE 38.45% |
| Pour readiness ≥ 98% | Not met; simulated 97.76% |
| Utilisation improvement ≥ 20% | Not demonstrated |
| Write-offs reduction ≥ 30% | Not measurable from the supplied tables |
| Interactive Dash views | Implemented and locally smoke-tested |

## Recommended next actions

I would reconcile silo capacities and inventory units with the data owner, capture dated pour-plan and weather-forecast snapshots, and record expiry/disposal and actual pour cancellations. These inputs would support a stronger forecasting and replenishment policy, confidence intervals and measurable cost or waste outcomes. I would also test shorter lead-time-aligned forecasts and compare simple AR against the tree models in additional rolling periods.
