#!/usr/bin/env python
# Cell 1: imports & constants
import argparse
from pathlib import Path
import pandas as pd

# Canonical keys we want in the final CSV
CANON_KEYS = [
    "UNITID","INSTNM","STABBR","CONTROL","PREDDEG","LOCALE","UGDS",
    "RET_FT4","RET_PT4","RET_FTL4","RET_PTL4","C150_4","C150_L4","TUITIONFEE_IN","PCT_PELL"
]

# Acceptable name variants found in Scorecard files
SYNONYMS = {
    "UNITID": ["UNITID"],
    "INSTNM": ["INSTNM"],
    "STABBR": ["STABBR"],
    "CONTROL": ["CONTROL"],
    "PREDDEG": ["PREDDEG"],
    "LOCALE": ["LOCALE"],
    "UGDS": ["UGDS"],
    "RET_FT4": ["RET_FT4"],
    "RET_PT4": ["RET_PT4"],
    "RET_FTL4": ["RET_FTL4"],
    "RET_PTL4": ["RET_PTL4"],
    "C150_4": ["C150_4"],
    "C150_L4": ["C150_L4"],
    "TUITIONFEE_IN": ["TUITIONFEE_IN"],
    "PCT_PELL": ["PCT_PELL", "PCTPELL"],   # <-- robust to underscore/no-underscore
}

CONTROL_MAP = {1: "Public", 2: "Private Non-Profit", 3: "Private For-Profit"}
DEG_MAP     = {0: "Non-Degree", 1: "Certificate", 2: "Associate", 3: "Bachelor", 4: "Graduate"}
RATE_COLS   = ["RET_FT4","RET_PT4","RET_FTL4","RET_PTL4","C150_4","C150_L4","PCT_PELL"]

# Cell 2: map available columns in the input file to canonical names
def build_column_map(src_path: Path):
    header = pd.read_csv(src_path, nrows=0, low_memory=False).columns
    upper_to_orig = {c.upper(): c for c in header}

    colmap = {}     # canonical -> original name in file
    missing = []    # canonical keys not found
    for key, opts in SYNONYMS.items():
        found = None
        for opt in opts:
            if opt.upper() in upper_to_orig:
                found = upper_to_orig[opt.upper()]
                break
        if found:
            colmap[key] = found
        else:
            missing.append(key)

    return colmap, missing

# Cell 3: core prep
def prepare(src_path: Path, dst_path: Path, states):
    colmap, missing = build_column_map(src_path)

    # Read only the columns we actually found
    usecols = list(colmap.values())
    df = pd.read_csv(src_path, usecols=usecols, low_memory=False)

    # Rename to canonical keys
    df.rename(columns={v: k for k, v in colmap.items()}, inplace=True)

    # Optional subset by states (e.g., MD/DC/VA)
    if states:
        states = [s.strip().upper() for s in states]
        if "STABBR" in df.columns:
            df = df[df["STABBR"].isin(states)].copy()

    # Human-friendly labels (if present)
    if "CONTROL" in df.columns:
        df["CONTROL"] = pd.to_numeric(df["CONTROL"], errors="coerce").map(CONTROL_MAP)
    if "PREDDEG" in df.columns:
        df["PREDDEG"] = pd.to_numeric(df["PREDDEG"], errors="coerce").map(DEG_MAP)

    # Convert proportions → percentages where appropriate
    for c in RATE_COLS:
        if c in df.columns:
            ser = pd.to_numeric(df[c], errors="coerce")
            # Heuristic: if 95% of values <= 1.1, treat as proportions (0–1) and scale to %
            try:
                if ser.dropna().quantile(0.95) <= 1.1:
                    ser = ser * 100.0
            except Exception:
                pass
            df[c] = ser

    # Final rename for clarity
    rename_final = {
        "RET_FT4":  "RETENTION_FT_4YR",
        "RET_PT4":  "RETENTION_PT_4YR",
        "RET_FTL4": "RETENTION_FT_2YR",
        "RET_PTL4": "RETENTION_PT_2YR",
        "C150_4":   "COMPLETION_150_4YR",
        "C150_L4":  "COMPLETION_150_2YR",
        "PCT_PELL": "PELL_SHARE",
    }
    for old, new in rename_final.items():
        if old in df.columns:
            df.rename(columns={old: new}, inplace=True)

    # Column order (keep only what exists)
    final_order = [
        "UNITID","INSTNM","STABBR","CONTROL","PREDDEG","LOCALE","UGDS",
        "RETENTION_FT_4YR","RETENTION_PT_4YR","RETENTION_FT_2YR","RETENTION_PT_2YR",
        "COMPLETION_150_4YR","COMPLETION_150_2YR","TUITIONFEE_IN","PELL_SHARE"
    ]
    final_cols = [c for c in final_order if c in df.columns]
    out = df[final_cols].copy()

    dst_path.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(dst_path, index=False)

    # Simple runtime summary
    print(f"[OK] Wrote {dst_path.resolve()} (rows={len(out)}, cols={len(final_cols)})")
    if missing:
        print(f"[Note] Missing in source (skipped): {', '.join(missing)}")

# Cell 4: CLI
if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Prepare Scorecard subset CSV for Tableau.")
    ap.add_argument("--input", required=True, help="Path to raw Scorecard CSV (Most_Recent_Cohorts*.csv)")
    ap.add_argument("--output", default="data/scorecard_subset.csv", help="Output CSV path")
    ap.add_argument("--states", nargs="*", default=["MD","DC","VA"], help="States to keep (e.g., MD DC VA)")
    args = ap.parse_args()
    prepare(Path(args.input), Path(args.output), args.states)
