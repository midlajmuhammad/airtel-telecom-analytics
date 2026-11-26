# Airtel Telecom Analytics | Group 3, Domain C

An interactive dashboard for a **Network Capacity Planner** to review network demand, subscriber usage patterns, and capacity-planning needs.

## Dashboard

The Streamlit dashboard has two tabs:

- **Overview:** validated usage-day count, the fixed T3 test result, subscriber data rates by denominator, monthly activity, and plan allowance use.
- **Detail:** select a month to inspect active subscribers, data carried, daily load, experiment-group usage distributions, and device usage distributions.

Each chart has its own **Filters** popover for circle, date range, customer segment, plan type, region, connection type, and device type. Detail charts also have their own month selector, so every chart can be filtered independently. Sidebar filters affect summary metrics only. Chart subtitles show each chart's active filter scope. The visuals use heatmaps, a treemap, violin plots, and a box plot; the dashboard does not use pie, doughnut, 3D, dual-axis, gauge, or word-cloud charts.

## Run locally

1. Install Python 3.10 or newer.
2. Create and activate a virtual environment.
3. Install the requirements:

   ```bash
   python -m pip install -r requirements.txt
   ```

4. Place the six source files in `data/raw/`: `circles.csv`, `plans.csv`, `customers.csv`, `usage_daily.csv`, `recharges.csv`, and `complaints.csv`.
5. Build the local SQLite database:

   ```bash
   python scripts/build_db.py
   ```

6. Start the dashboard:

   ```bash
   streamlit run dashboard/app.py
   ```

If you already have a compatible database elsewhere, set `AIRTEL_DB` to its path before starting Streamlit. The app checks `data/raw/airtel.db`, `data/airtel.db`, and the project root by default.

In the supplied workspace, `data/airtel.db` is an empty SQLite shell; the populated database is `data/raw/airtel.db`. The app selects the populated database after checking that it contains the required tables.

The raw CSVs and `.db` files are ignored by Git. They must be supplied locally; the dashboard cannot rebuild a database without the six source CSV files. A fresh-clone setup therefore requires the dataset before step 5.

## Streamlit Community Cloud database setup

The SQLite database and its ZIP archive are deliberately excluded from Git. The app can load it in two ways on Community Cloud.

**Password-protected ZIP upload (no API or Drive link required):**

1. In the deployed app's Streamlit workspace, open the app menu → **Settings** → **Secrets** and add a private setup password:

   ```toml
   [database]
   upload_password = "CHOOSE_A_LONG_RANDOM_PASSWORD"
   ```

2. Save Secrets and reboot the app.
3. Open the app URL, enter the setup password, and upload `data/raw/airtel_database.zip`.

The app extracts only `airtel.db` into temporary Cloud storage, validates the SQLite tables, and reads it in read-only mode. The database stays out of GitHub. Cloud temporary storage can be cleared when the app instance restarts, so upload the ZIP again if the setup screen returns. If you prefer a private HTTPS storage service, you can instead set `url` and an optional bearer `token` under `[database]`; never use a public file link or commit secrets to Git.

## Metric definitions

- **Usage-day:** one subscriber with a usage record on one date. It may differ from a calendar day.
- **Active subscriber:** a subscriber with at least one usage-day in the selected period.
- **Data per usage-day:** for each subscriber, data divided by that subscriber's own usage-days; the dashboard then averages across subscribers.
- **Data per calendar day:** for each subscriber, data divided by the number of calendar days in the period; the dashboard then averages across the selected population.
- **Data carried:** total data volume. The dashboard converts MB to TB using 1 TB = 1,024 × 1,024 MB.
- **Allowance use:** each subscriber's data averaged across the observed months, divided by the monthly plan allowance. A per-day plan quota is multiplied by 30. Plans with fewer than 100 subscribers under the current filter are omitted from the rate comparison.
- **Groups A/B:** source labels for the experiment groups. Their comparison does not establish a causal effect.

## Fixed validation result and caveats

The usage-day total and T3 test are fixed validated results and are explicitly tagged `FIXED`; they do not change with dashboard filters. T3 is a one-tailed Welch two-sample t-test for group B's mean being greater than group A's during May–June 2025. The displayed values are t = 19.45, df = 17,444, p = 1.1e-83; validated means are 1,867 MB for B and 1,393 MB for A. A p-value is not an effect size, and statistical association does not prove causation. See `scripts/verify_t3.py` and the validated analysis notebook for the calculation.

Dashboard measures are calculated in SQL through the read-only `q()` helper in `dashboard/app.py`. Python formats query results and maps them into Plotly chart shapes. The app does not write to the database.

## Project structure

```text
dashboard/app.py                  Streamlit entry point
dashboard/assets/airtel_logo.png  Transparent Airtel logo shown at the sidebar bottom
dashboard/assets/airtel_header.webp Animated dashboard header background
dashboard/assets/airtel_sidebar.webp Airtel image shown at the sidebar top
dashboard/assets/airtel_tab_background.png Airtel night-building background behind both dashboard tabs
data/                             Local database and source data (not committed)
notebook/                         Data validation, preparation, and analysis notebooks
reports/                          Dashboard sketches, ER diagram, and viva notes
scripts/build_db.py               Build airtel.db from the six CSV files
scripts/verify_t3.py              Reproduce the validated T3 result
sql/practice/                     SQL practice queries
requirements.txt                  Runtime dependencies
```

## Repository handover

Before submitting from a fresh clone, add the source dataset locally, build the database, start `dashboard/app.py`, and confirm that both tabs load. Check the independent filters on each chart and the summary filters in the sidebar. Confirm the chart labels, units, filter scope, and non-scrolling layout at full-screen and normal zoom on the smallest available laptop.
