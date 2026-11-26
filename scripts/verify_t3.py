"""Reproduce the fixed T3 values shown on the Overview tab.

Usage (from the repository root, after building airtel.db):
    python scripts/verify_t3.py

Test: per-subscriber mean daily data (MB) over the offer window
(1 May - 30 Jun 2025), group B vs group A. Equal variances are tested
first (F-test); Welch's t-test is used because they differ. One-tailed,
H1: mean(B) > mean(A). Needs scipy (installed with the notebook libraries).
"""
import sqlite3
from pathlib import Path

import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parent.parent
DB = next(p for p in (ROOT / "data" / "raw" / "airtel.db",
                      ROOT / "data" / "airtel.db", ROOT / "airtel.db")
          if p.exists())

SQL = """
SELECT c.ab_group AS g, u.customer_id, AVG(u.data_mb) AS m
  FROM usage_daily u
  JOIN customers c ON c.customer_id = u.customer_id
 WHERE u.usage_date >= '2025-05-01'
 GROUP BY u.customer_id
"""
with sqlite3.connect(DB) as conn:
    df = pd.read_sql_query(SQL, conn)

a = df.loc[df.g == "A", "m"]
b = df.loc[df.g == "B", "m"]
f = a.var(ddof=1) / b.var(ddof=1)
f_p = 2 * min(stats.f.cdf(f, len(a) - 1, len(b) - 1),
              stats.f.sf(f, len(a) - 1, len(b) - 1))
t = stats.ttest_ind(b, a, equal_var=False, alternative="greater")
print(f"n A = {len(a):,}, n B = {len(b):,}")
print(f"mean A = {a.mean():,.0f} MB, mean B = {b.mean():,.0f} MB")
print(f"F-test (equal variances) two-tailed p = {f_p:.2e}")
print(f"Welch t = {t.statistic:.2f}, df = {t.df:,.0f}, "
      f"one-tailed p (B > A) = {t.pvalue:.2e}")
