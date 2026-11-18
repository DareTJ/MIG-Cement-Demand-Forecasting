# Mathematical diagnosis of forecast limitations

The original objectives remain unchanged. This follow-up investigates why the strict 56-day benchmark did not reach 15% MAPE. The same historical windows are reused for diagnostic experiments, so the results are exploratory, not a new independent holdout. No site-level records are published.

## Physical structure of the recorded target

Let C be observed daily consumption, P the recorded planned pour and A the recorded opening stock plus deliveries. The inventory identity is closing stock = A − C, subject to rounding. Every record satisfies C ≤ P and C ≤ A (to rounding tolerance), and about 84.44% satisfy C = min(P,A) to within 0.011 tonnes. This is an empirical constraint observed in this case-study dataset, not a universally valid causal law.

Observed consumption is therefore not necessarily latent cement demand: availability can constrain the amount consumed. I must not supply a model with future realised inventory, deliveries or closing stock to predict consumption. For decision support, planned demand and simulated supply availability need to be considered separately.

## Why lag-only forecasts are weak

| Diagnostic | Observed aggregate |
| --- | ---: |
| Same-day planned pours vs consumption (Pearson r) | 0.781 |
| Prior-day consumption vs current consumption | 0.215 |
| Seven-day lag vs current consumption | 0.231 |
| Mean within-site lag-one correlation | −0.015 |

Much of the pooled lag association reflects site differences rather than day-to-day predictability. On positive-plan days, average realised consumption was 85.49% of the plan when rainfall was at most 15 mm and 34.16% above 15 mm. The fraction of positive-plan days with zero consumption rose from 0.17% to 64.80%. These are associations in the historical data, not proof of a causal rainfall threshold. The data are strongly suggestive of a bounded, intermittently interrupted process rather than a stable univariate time series.

## Controlled information scenarios

For each of the original 56-day origins, I fitted models only on preceding dates. I compared the original history-only benchmark with two additional information sets:

- Conditional plan: assumes the recorded daily plans are genuinely available at forecast issue; no future observed weather or stock. Plan versions and issue timestamps are absent, so the assumption remains unverified.
- Hindsight weather and plan: additionally supplies actual future rainfall and temperature. This is a diagnostic, not a deployable forecast. It quantifies the predictive value of information unavailable at issue time.

I used a constrained forecast in [0, plan], an MAE-loss LightGBM, a Random Forest, a conditional MAPE-loss LightGBM (positive observations weighted by inverse actual consumption), and a hurdle model estimating probability of positive consumption multiplied by its conditional expectation. A weighted MAPE model is not automatically appropriate for procurement: it may favour low predictions and understate stock needs. The final historical window was already inspected, so these results are not used to replace the previously selected model.

| Information scenario and estimator | Final-window MAE (t) | Nonzero-day MAPE | WAPE |
| --- | ---: | ---: | ---: |
| History-only Random Forest | 11.371 | 38.45% | 48.69% |
| Conditional plan, unchanged | 6.895 | 31.00% | 29.52% |
| Conditional plan, Random Forest | 6.148 | 22.81% | 26.32% |
| Conditional plan, LightGBM MAE | 5.669 | 22.14% | 24.27% |
| Conditional plan, hurdle expectation | 6.062 | 22.43% | 25.95% |
| Conditional plan, LightGBM MAPE | 6.208 | 21.13% | 26.58% |
| Hindsight weather + plan, LightGBM MAE | 3.567 | 18.42% | 15.27% |
| Hindsight weather + plan, LightGBM MAPE | 5.437 | 17.26% | 23.28% |
| Hindsight physical upper bound, min(P,A) | 2.442 | 6.75% | 10.46% |

Each final-window comparison uses 1,680 site-day observations and 1,460 positive-consumption observations for conditional MAPE. All zero days remain in MAE and WAPE. The hindsight physical bound achieves a percentage error below 15% but is not a forecasting model: it uses actual future opening inventory and deliveries. Its accuracy is evidence that supply availability explains a substantial part of the recorded target, not that the original forecasting target has been achieved.

On the earlier two 56-day windows, conditional plan LightGBM MAE had MAE 5.785 and conditional MAPE 24.05%; the MAPE-weighted variant had MAPE 22.45%. This confirms that the conditional improvement is not unique to the final window. Future plan availability still needs verification.

## Capacity reconciliation

15 of 30 sites have recorded closing stock above reported capacity; the maximum ratio is about 172 times capacity. No opening-to-prior-closing discrepancies exceed 0.011 tonnes. This supports arithmetic continuity but not physical feasibility. I retain the source records unchanged and flag the capacity/units issue rather than invent a conversion or silently delete data. The earlier capacity-feasible inventory replay is explicitly hypothetical and needs independent reconciliation.

## Consequences for the case-study objectives

- **15% MAPE:** not achieved under the verified forecast-time information set. Future plan snapshots and dated weather forecasts should be requested or explicitly modelled as scenarios. To measure forecastable demand, separate planned demand from consumption censored by stock availability. Re-evaluate AR, SARIMAX, LightGBM and Random Forest using the same authorised future inputs and a genuinely unseen period.
- **98% pour readiness:** retain the target; estimate stock requirements from a demand distribution rather than just a consumption point estimate. Test a capacity-aware, lead-time-dependent service policy after capacity reconciliation. The prior 97.76% replay is not a real-world guarantee.
- **20% utilisation and 30% write-off reduction:** agree the utilisation baseline and objective direction, reconcile capacity/units and collect expiry/disposal data before claiming benefits. No write-off savings have been established.
- **Dash:** retain the local-only decision-support demonstration; distinguish actual history, forecast and conditional scenario in future iterations.

Reproduce this diagnostic locally after installing the repository dependencies:

```bash
python diagnose.py /path/to/authorised/MIG_Cement_Records.db
```

Only aggregate results are written to the ignored local output directory. The original database remains restricted.
