#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import sys
import pandas as pd

REQUIRED = [
    "INSTNM", "STABBR",
    "RETENTION_FT_4YR",
    "COMPLETION_150_4YR",
    "PELL_SHARE",
    "UGDS",
    "TUITIONFEE_IN",
]

RATE_COLS = ["RETENTION_FT_4YR", "COMPLETION_150_4YR", "PELL_SHARE"]

def normalize01(df, cols):
    for c in cols:
        if c not in df.columns:
            print(f"[warn] missing column: {c}", file=sys.stderr)
            continue
        s = pd.to_numeric(df[c], errors="coerce")
        if s.dropna().max() > 1.5:
            print(f"[info] normalizing {c} from 0–100 to 0–1", file=sys.stderr)
            s = s / 100.0
        df[c] = s
    return df

def fail(msg):
    print(f"VALIDATION FAILED: {msg}", file=sys.stderr)
    sys.exit(1)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    args = ap.parse_args()

    df = pd.read_csv(args.input)
    if df.empty:
        fail("No rows after preparation.")

    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        fail(f"Missing required columns: {', '.join(missing)}")

    df = normalize01(df, RATE_COLS)

    for c in RATE_COLS:
        s = pd.to_numeric(df[c], errors="coerce")
        if (s.dropna() < 0).any() or (s.dropna() > 1).any():
            fail(f"{c} contains values outside [0,1].")

    # light sanity checks
    if (pd.to_numeric(df["UGDS"], errors="coerce") < 0).any():
        fail("UGDS has negative values.")
    if (pd.to_numeric(df["TUITIONFEE_IN"], errors="coerce") < 0).any():
        fail("TUITIONFEE_IN has negative values.")

    print(f"VALIDATION OK: {len(df):,} rows, columns good.")
