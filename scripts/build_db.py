"""Build airtel.db from the six raw CSV files.

Usage (from the repository root):
    python scripts/build_db.py

Reads  data/raw/{circles,plans,customers,usage_daily,recharges,complaints}.csv
Writes data/raw/airtel.db   (git-ignored: databases and CSVs are never committed)
"""
import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
DB = RAW / "airtel.db"
TABLES = ["circles", "plans", "customers", "usage_daily", "recharges",
          "complaints"]

missing = [t for t in TABLES if not (RAW / f"{t}.csv").exists()]
if missing:
    raise SystemExit(
        f"Missing CSV files in {RAW}: {', '.join(t + '.csv' for t in missing)}"
    )

with sqlite3.connect(DB) as conn:
    for table in TABLES:
        df = pd.read_csv(RAW / f"{table}.csv")
        df.to_sql(table, conn, if_exists="replace", index=False)
        print(f"{table:12s} {len(df):>9,} rows")
    conn.execute("CREATE INDEX IF NOT EXISTS ix_u_cust ON usage_daily(customer_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS ix_u_date ON usage_daily(usage_date)")
    conn.commit()

print(f"Built {DB}")
