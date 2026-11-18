# MIG Cement Demand Forecasting & Inventory Optimisation
## Business-first operational reassessment — 18 November 2026

**Status: Executed historical analysis and hypothetical inventory tests; not a verified operational deployment.**

### Executive conclusion

I inspected the authorised SQLite data, reran the forecasting and weather modelling work, and separately tested inventory decisions against original objectives. The project reveals a plausible path to better procurement decisions using reliable near-term pour schedules. A schedule-informed rule achieves **98.42% simulated scheduled-pour availability** on the later 56-day window under specific assumptions, compared with **96.37%** for a historical-mean rule. However, the same rule achieves **97.20%** on an earlier window; the improvement is sensitive to delivery lead times, opening stock and suspect silo capacities. I therefore **do not claim that the original 98% readiness target is consistently achieved**, much less proven in real operations.

The original 15% MAPE target was **not met**. The 20% inventory-utilisation objective remains **ill-defined and unverified**, and the 30% write-off objective **cannot be measured** from the supplied records. A local Plotly Dash prototype exists, but it is not a production procurement system.

### 1. Source integrity and what the data means

- **32,880** records; **30** sites; daily dates **1 January 2022–31 December 2024**; three reported cement grades.
- SQLite integrity passed; no missing observations; daily continuity and foreign-key consistency validated.
- **11,439** closing-stock records (**34.79%**) exceed the stated silo capacity, affecting **15 sites**. The most extreme stock/capacity ratio is **172.16**. These balances cannot be accepted as physically usable stock without reconciling storage scope and units.
- All 30 sites have all three observed cement grades across time, but site inventory is recorded as one pooled balance. **Grade-specific availability cannot be verified.**
- There are **29,887** scheduled site-days. On **9,566** of those days, recorded opening stock plus same-day deliveries is below the scheduled pour tonnes: **67.99%** is the *optimistic historical stock-availability proxy*, which assumes receipts precede pours. This is **not** the historical actual completion rate.
- Total planned tonnes are **1,009,322.57**; recorded consumption is **779,929.21**. The difference, **229,393.36 tonnes (22.73%)**, cannot automatically be interpreted as waste or lost demand.
- On **1,010** scheduled days recorded consumption is zero. The data do not identify the actual cancellation or rescheduling reason.

**Historical descriptive signal:** Among scheduled days with rain above 15 mm, the zero-consumption rate was roughly **47.9%** where the recorded balance could cover the plan and **99.8%** where it could not. On days with 15 mm or less rain, the analogous rates were approximately **0%** and **0.5%**. These are *associations in this case-study data*, not validated causal effects or guaranteed weather rules.

### 2. Forecast evidence (same historical data, 56-day origins)

| Model/information assumption | Later-window positive-day MAPE | Interpretation |
|---|---:|---|
| History-only Random Forest, earlier published benchmark | 38.45% | Forecast-time historical features; did not reach 15% |
| Plan-conditional percentage-error-oriented LightGBM | **22.060%** | Development-selected model, but unverified availability of 56-day planned pours |
| Plan-conditional two-stage expected-consumption model | **22.664%** | More suitable for expected recorded consumption; 26.156% WAPE and −0.078 t mean bias |
| Plan plus **realised** future-weather percentage-error model | **17.885%** | Retrospective diagnostic **only**; cannot be deployed as a genuine future forecast |

The models were rerun against the actual database. All 56-day forecast windows have complete site-day coverage in the experiments reported here. MAPE excludes zero actual consumption and is accompanied in the notebook by MAE, RMSE, WAPE and signed bias on all days. The final historical comparison period had already been inspected in earlier research, so it is **not** a new independent holdout. A different installed package version can slightly change fitted-model metrics.

**Decision:** The **15% MAPE target is not met** by the tested models. Future plan versions and archived weather forecasts must be captured before validating a prospective forecast.

### 3. Inventory policy experiment — the operational question

**Decision:** Order enough cement to cover scheduled work while avoiding unnecessary inventory, subject to supplier and storage constraints. This is evaluated separately from forecasting *recorded consumption* (which may be stock constrained).

**Common assumptions:** 56 days per site; same hypothetical beginning stock for both policies (minimum of recorded opening and stated capacity); excess opening stock segregated hypothetically, not written off; all grades pooled; no incoming outstanding orders at origin; deliveries arrive before pours; end-of-day ordering; full recorded future plans assumed known for the schedule-informed rule. The historical-mean rule uses only preceding consumption. A limit of **50 tonnes/site/day** is an exploratory delivery sensitivity motivated by the maximum recorded daily deliveries, **not** a verified supplier commitment.

Buffers were selected using the **26 August 2024** window, then fixed for **21 October 2024**. Results below serve the *full planned pour tonnage* as a stress case, not assumed actual future consumption.

| Historical 56-day window | Historical-mean rule | Schedule-informed rule | Outcome |
|---|---:|---:|---|
| 26 Aug–20 Oct, 2-day lead, 50-t/day cap | **95.56%** | **97.20%** | Improved, but misses 98% |
| 21 Oct–15 Dec, 2-day lead, 50-t/day cap | **96.37%** | **98.42%** | Crosses 98% *conditionally* |
| 21 Oct–15 Dec, **3-day** lead, 50-t/day cap | **93.93%** | **96.57%** | Both below target |
| 21 Oct–15 Dec, 2-day lead, **unlimited** receipts | **96.50%** | **98.55%** | Optimistic upper scenario, not supplier-confirmed |

For the two-day, 50-t/day October comparison, mean *closing stock as a proportion of stated capacity* fell from **50.17%** under the historical-mean rule to **25.51%** under the schedule-informed rule. Lower inventory occupancy could reduce capital exposure **if** capacities, units and carrying costs are valid, but it is **not** proof of a 20% improvement in the case study's undefined utilisation metric. No actual cost or waste saving has been measured.

**Opening-stock sensitivity for the schedule-informed rule (October, 2 days, 50 t/day):** 98.42% with capped recorded opening stocks; **96.30%** with empty opening stock; **99.80%** with 50% of each site's capacity available initially. Restricting the analysis to the 15 sites without recorded over-capacity events gives **97.17%** under the capped-recorded opening rule. None of these alternatives resolves missing grade-level balances.

**Decision:** The service-level objective can be crossed numerically in one stylised scenario, but it is **not robust across windows and assumptions**. It must not be reported as achieved in practice.

### 4. Original objective scorecard

| Original target | Evidence-based status |
|---|---|
| **MAPE ≤15%, 56-day horizon** | **Not met**: 22.06% on best development-selected plan-conditional later comparison; future information unverified |
| **Pour readiness ≥98%** | **Conditional scenario only**: 98.42% in later window, 97.20% in earlier; no actual pour-completion logs |
| **Inventory utilisation improvement ≥20%** | **Not demonstrated**: no agreed definition or verified cost/stock baseline |
| **Write-offs reduced ≥30%** | **Not measurable**: missing expiry and disposal events |
| **Plotly Dash visibility** | **Prototype available** locally, not production validated |

### 5. What I would request before operational piloting

1. Reconciled site and silo capacities, storage units, grade-specific inventories and permitted grade substitutions (if any).
2. Historical, **issue-dated** 28/56-day pour-plan snapshots and recorded revisions.
3. Supplier order timestamps, delivery lead-time distributions, minimum orders, truck/unloading limits, and outstanding purchase orders.
4. Actual pour completion/cancellation timestamps and reasons, including rain and other operational interruptions.
5. Write-off, expiry and disposal events, plus holding, emergency ordering and shortage costs.
6. A documented *current ordering policy* to serve as the real-world comparator, not just a historical-mean analytical benchmark.

### 6. Reproduction and privacy

The accompanying **single** `MIG_Cement_Demand_Forecasting.ipynb` notebook retains first-person Markdown, all original analysis phases and the new operational policy test. Put an authorised local `MIG_Cement_Records.db` beside the notebook and run it in order after installing the required packages. The database and any site-level execution outputs must **not** be published. The optional local Dash UI requires the `dash` and `plotly` packages; it is not automatically launched during execution.

**Validation:** The original notebook's analytical cells executed successfully against the recovered database. The revised notebook adds grade-level limitations, policy optimisation with buffer selection on a preceding window, supply-capacity sensitivity and alternative opening stock. Do not interpret successful synthetic/unit checks as operational validation.

**Reproducibility note:** For this run, pandas 2.2.3, NumPy 2.3.5, scikit-learn 1.8.0, LightGBM 4.6.0, XGBoost 3.1.3 and CatBoost 1.2.8 were installed. The October period was already inspected in prior project work, and the forecast was not prospectively issued in 2024.

**Bottom line:** I can defend a viable **conditional decision concept** and diagnose substantial data-quality and planning constraints. I cannot yet claim that the original service, utilisation, write-off or forecasting targets have all been achieved. A more sophisticated model alone will not fix unavailable plan versions, supplier terms, grade-level stock or waste records.