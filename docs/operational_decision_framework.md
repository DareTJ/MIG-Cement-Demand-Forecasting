# MIG | Operational decision framework and evidence gates

**Purpose.** I use this framework to test whether a forecasting result can actually support cement purchasing and pour readiness. I keep the original case-study targets unchanged. This document explains the decision contract; it is **not** a claim that the objectives have been met.

## 1. The operating decision comes before the algorithm

At each site and order date, I want to decide **how many tonnes of each cement grade to order, when to order them, and how much usable stock to hold**. A policy is useful only if it respects physically verified capacity, supplier lead times and the site’s scheduled work. “Better forecast MAPE” does not automatically imply fewer missed pours or lower working capital.

The case-study operating process uses a rolling **four-week** planning schedule, whereas its forecasting target is **eight weeks (56 days)**. I cannot assume that the current version of a future plan was available 56 days earlier. I would record each plan’s issue timestamp, revision, effective date, approval status and cement grade. A genuinely prospective test must reconstruct the exact information available at each historical forecast origin.

## 2. Separate five different quantities

| Quantity | Meaning | Source or uncertainty |
| --- | --- | --- |
| Scheduled cement requirement | Planned tonnes for the pour | Recorded planned pours are present; dated plan versions are not |
| Unconstrained demand | Tonnes actually needed if all scheduled work proceeds | Not directly measured |
| Recorded consumption | Tonnes consumed under real conditions | Observed; may be censored by stock or operational stoppages |
| Physically usable stock | Material ready for the pour, by grade and time | Daily inventory exists, but capacity definitions and intraday delivery times need reconciliation |
| Delivered replenishment | Supply that arrives when it can actually be unloaded | Daily delivery tonnes exist; order dates, promised/actual lead times and unloading limits are missing |

For the supplied daily data, consumption does not exceed either planned pours or opening inventory plus deliveries (within tolerance). Approximately **84.44%** of rows match the minimum of those two recorded quantities. This describes the **case-study dataset only**; it is not proof of causation and cannot be used as a deployable future predictor when stock/deliveries are unknown.

## 3. Physical and data-quality reconciliation

The earlier diagnostic recorded **32,880 site-days across 30 sites**, with **11,439 closing inventory records above reported capacity**, spanning **15 sites**, and an extreme capacity ratio of roughly **172**. Daily inventory arithmetic was largely consistent, with only seven discrepancies within the 0.011-tonne tolerance. Arithmetic coherence alone does **not** establish that the stated silo capacities reflect usable physical storage.

Before issuing an ordering recommendation, I would ask for:

- The units and scope of `silo_capacity` (one vessel, all vessels, or shared off-silo stock), plus grade-level and site-level capacity.
- Physical stock counts and measurement methods, the date each capacity was effective and any transfers.
- Purchase order, planned arrival, actual arrival and unloading timestamps; order quantity constraints and costs.
- Pour completion, rescheduling and cancellation records, with cancellation reasons.
- Inventory expiry dates, disposal logs, write-off tonnage and cost, so the 30% waste target is actually measurable.

I will **not** silently clip historical stock, infer disposal from apparent overcapacity or rescale capacity by an arbitrary conversion factor.

## 4. Define an as-of forecast and make information scenarios explicit

At forecast issue time **t**, a legitimate 56-day predictor can use the observed history through **t−1**, known calendar features, approved planning snapshots actually issued by **t**, and archived weather forecasts available by **t**. It cannot use future realised rainfall, actual delivery quantities, future observed consumption, future stock balances or later versions of pour plans.

I distinguish:

1. **Strict history-only benchmark:** uses genuinely historical observations and calendar information.
2. **Plan-conditional scenario:** adds recorded future pour plans; informative but *not verified as available at t*.
3. **Realised-weather hindsight:** adds actual target-date weather solely to diagnose the potential value of missing future information.
4. **Physical hindsight bound:** adds observed future available stock; useful for identifying constraints but **not a forecast**.

All modelling should be evaluated with complete site-horizon coverage and issue-date-based, non-overlapping tests. MAPE applies only to positive observed consumption, with its denominator coverage reported. I also evaluate MAE, RMSE, WAPE and signed bias on **all** days, including zero consumption. A forecast with lower MAPE can still systematically under-order cement.

## 5. Explicit inventory decision model

For an illustrative daily replay by site and cement grade:

- Start with **verified usable stock** and known outstanding orders, not the uncorrected book balance.
- Receive only deliveries due according to the declared lead-time scenario. A daily file alone cannot establish that a same-day receipt preceded the scheduled pour.
- Mark a scheduled pour as “availability-ready” only if usable stock is sufficient for its required tonnes. This is a **proxy** until actual pour completion and timing logs exist.
- Serve the declared requirement, record shortfall, then decide the next order; track outstanding orders to avoid double ordering.
- Enforce storage limits at delivery, record tonnes that cannot be unloaded, and treat any opening excess as **segregated hypothetical stock**, not as a proven write-off.
- Compare identical policy scenarios using the same start date, opening conditions, lead time, demand assumptions, order constraints and horizon.

Two particularly different demand scenarios are required: **observed consumption** (an optimistic lower-bound proxy for material required when interruptions were present) and **full planned pours** (a more demanding stress case, not a forecast of guaranteed executed work). Neither should be described as observed true demand.

**Important limitation:** A simple forecast-based reorder target does not guarantee a 98% pour-readiness service level. A deployment design should evaluate the **distribution of demand during replenishment lead time**, supplier variability, schedule uncertainty and inventory at the exact pour time; it should enforce grade-specific capacity and procurement rules.

## 6. The original objective scorecard

| Requirement | Original target | Current defensible statement |
| --- | --- | --- |
| Daily forecast, 56-day horizon | MAPE ≤ **15%** | Earlier history-only Random Forest holdout MAPE **38.45%**; target **not met** |
| Scheduled pour readiness | **≥98%** | Earlier capacity-feasible consumption replay **97.76%** proxy; target **not demonstrated** |
| Stock utilisation improvement | **≥20%** | Earlier mean ratio **59.77% → 60.57%** (0.80 percentage points, ~1.34% relative); definition and value of “improvement” still need agreement |
| Write-off reduction | **≥30%** | Not measurable without expiry, disposal and write-off records |
| Planner/site decision dashboard | Plotly Dash | Existing local prototype; not a production decision engine |

The published figures above came from the earlier executed scripts, documented in [results.md](results.md). **The consolidated notebook’s new scenarios have not been rerun against the authorised source within this review.** Its synthetic consistency tests do not validate the business targets.

## 7. Release and decision gates

**Gate A — data:** Database integrity, daily continuity, inventory balances, units and physically usable capacity have been checked and reconciled.

**Gate B — information:** Each future plan and weather input has a documented as-of timestamp, or the experiment is labelled conditional/hindsight.

**Gate C — accuracy:** Models are tested in date-ordered, complete-coverage windows using appropriate all-day and positive-day metrics. Test results are not selected or tuned on the same held-out period.

**Gate D — inventory:** Policies are compared on a common demand scenario and opening stock; lead-time and capacity sensitivity are evaluated; stockout and missed-pour proxies are labelled accurately.

**Gate E — value:** The 20% utilisation target has a defined denominator and economic direction. The 30% write-off target has real disposal evidence. No unsupported cost or environmental savings are claimed.

**Gate F — privacy:** Only aggregate examples, explanations and code are published. SQLite data, site identifiers in outputs, operational traces and local Dash output are not committed.

## 8. Next engineering priorities

I would first reconcile the capacity and inventory semantics and obtain schedule-vintage and supplier information. After this, I would run **shorter lead-time-aligned forecasts** alongside the strict 56-day reporting objective, calibrate demand scenarios or quantiles for inventory service, and compare against MIG’s true current ordering practice. Only after these gates would I recommend a procurement pilot.

The strongest portfolio conclusion is not that every target has been reached; it is that I can **identify operational constraints, choose honest metrics, challenge unrealistic assumptions and recommend defensible next decisions**.
