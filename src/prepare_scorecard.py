#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
from pathlib import Path
import sys
import pandas as pd

# ---------- helpers ----------

# canonical columns we want to end up with
CANON = [
    "UNITID", "INSTNM", "STABBR", "CONTROL", "PREDDEG", "LOCALE",
    "UGDS", "RET_FT4", "RET_PT4", "RET_FT2", "RET_PT2",
    "C150_4", "C150_2", "TUITIONFEE_IN", "PCT_PELL"
]

# light synonym map -> list of candidates you might see in the Scorecard CSV
CANDIDATES = {
    "UNITID":        ["unitid"],
    "INSTNM":        ["instnm", "name"],
    "STABBR":        ["stabbr", "stateabbr", "state"],
    "CONTROL":       ["control"],
    "PREDDEG":       ["preddeg", "pred_degree", "predominant_degree"],
    "LOCALE":        ["locale"],
    "UGDS":          ["ugds", "ugds_all", "ugds_male", "ugds_female"],
    "RET_FT4":       ["ret_ft4"],
    "RET_PT4":       ["ret_pt4"],
    "RET_FT2":       ["ret_ft2"],
    "RET_PT2":       ["ret_pt2"],
    "C150_4":        ["c150_4", "c150_4_pooled"],
    "C150_2":        ["c150_2", "c150_2_pooled"],
    "TUITIONFEE_IN": ["tuitionfee_in", "tuition_in_state", "tuition_in"],
    "PCT_PELL":      ["pct_pell", "pell_share"],
}

CONTROL_MAP = {
    1: "Public",
    2: "Private Non-Profit",
    3: "Private For-Profit",
}

DEG_MAP = {
    0: "Non-Degree",
    1: "Certificate",
    2: "Associate",
    3: "Bachelor",
    4: "Graduate",
}

RENAME = {
    "RET_FT4": "RETENTION_FT_4YR",
    "RET_PT4": "RETENTION_PT_4YR",
    "RET_FT2": "RETENTION_FT_2YR",
    "RET_PT2": "RETENTION_PT_2YR",
    "C150_4":  "COMPLETION_150_4YR",
    "C150_2":  "COMPLETION_150_2YR",
    "PCT_PELL":"PELL_SHARE",
}

RATE_COLS_CANON = ["RET_FT4", "RET_PT4", "RET_FT2", "RET_PT2", "C150_4", "C150_2", "PCT_PELL"]
RATE_COLS_FINAL  = [RENAME[c] for c in RATE_COLS_CANON]

def norm_key(s: str) -> str:
    return ''.join(ch for ch in s.lower() if ch.isalnum())

def build_column_map(src_path: Path) -> dict:
    """Map our canonical names to actual CSV headers (case/format tolerant)."""
    header = list(pd.read_csv(src_path, nrows=0).columns)
    norm_to_raw = {norm_key(h): h for h in header}

    colmap = {}
    missing = []
    for canon in CANON:
        found = None
        for cand in CANDIDATES.get(canon, []):
            raw = norm_to_raw.get(norm_key(cand))
            if raw:
                found = raw
                break
        # also accept exact name as-is
        if not found and norm_key(canon) in norm_to_raw:
            found = norm_to_raw[norm_key(canon)]
        if found:
            colmap[canon] = found
        else:
            # not fatal; some columns (e.g., RET_PT2) may not exist in the file
            missing.append(canon)
    if len(colmap) == 0:
        raise RuntimeError("Could not match any expected columns from the Scorecard CSV.")
    if missing:
        print(f"[warn] missing columns in source: {', '.join(missing)}", file=sys.stderr)
    return colmap

def normalize_states_arg(states_arg):
    """Allow 'MD DC VA' or 'MD,DC,VA' or multiple tokens."""
    toks = []
    for s in states_arg:
        for t in s.replace(",", " ").split():
            if t:
                toks.append(t.upper())
    return toks

def to_01(series: pd.Series) -> pd.Series:
    s = pd.to_numeric(series, errors="coerce")
    # If looks like percentages (e.g., 63.5), scale down
    if s.dropna().max() > 1.5:
        s = s / 100.0
    return s.clip(lower=0, upper=1)

# ---------- main prep ----------

def prepare(src_path: Path, dst_path: Path, states):
    colmap = build_column_map(src_path)
    usecols = [colmap[c] for c in colmap]  # only those that exist
    df = pd.read_csv(src_path, usecols=usecols, low_memory=False)

    # Bring to canonical names
    canon_names = {v: k for k, v in colmap.items()}
    df = df.rename(columns=canon_names)

    # Filter states
    states = normalize_states_arg(states)
    if "STABBR" in df.columns and states:
        df = df[df["STABBR"].isin(states)].copy()

    if df.empty:
        print("No rows after state filter.", file=sys.stderr)

    # Human-friendly mappings
    if "CONTROL" in df.columns:
        df["CONTROL"] = pd.to_numeric(df["CONTROL"], errors="coerce").map(CONTROL_MAP)
    if "PREDDEG" in df.columns:
        df["PREDDEG"] = pd.to_numeric(df["PREDDEG"], errors="coerce").map(DEG_MAP)

    # Normalize rate columns to 0–1
    for c in RATE_COLS_CANON:
        if c in df.columns:
            df[c] = to_01(df[c])

    # Numeric cleans
    for c in ["UGDS", "TUITIONFEE_IN"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    # Final rename for presentation
    df = df.rename(columns=RENAME)

    # Order nice columns if present
    final_order = [
        "INSTNM", "STABBR", "CONTROL", "PREDDEG",
        "RETENTION_FT_4YR", "RETENTION_PT_4YR",
        "COMPLETION_150_4YR", "COMPLETION_150_2YR",
        "PELL_SHARE", "UGDS", "TUITIONFEE_IN", "LOCALE", "UNITID"
    ]
    cols = [c for c in final_order if c in df.columns] + [c for c in df.columns if c not in final_order]
    df = df[cols].sort_values(["STABBR","INSTNM"], na_position="last").reset_index(drop=True)

    dst_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(dst_path, index=False)
    print(f"Wrote {len(df):,} rows -> {dst_path}")

# ---------- CLI ----------

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Prepare Scorecard subset CSV for Tableau.")
    ap.add_argument("--input", required=True, help="Path to Most_Recent_Cohorts CSV")
    ap.add_argument("--output", default="data/scorecard_subset.csv", help="Output CSV path")
    ap.add_argument("--states", nargs="+", default=["MD","DC","VA"], help="States to keep (e.g., MD DC VA)")
    args = ap.parse_args()
    prepare(Path(args.input), Path(args.output), args.states)
