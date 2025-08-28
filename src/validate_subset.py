# Cell 1: imports
import sys
import argparse
import pandas as pd

# Cell 2: config
REQUIRED_COLS = [
    "UNITID","INSTNM","STABBR","CONTROL","PREDDEG",
    "UGDS","TUITIONFEE_IN","RETENTION_FT_4YR","COMPLETION_150_4YR","PELL_SHARE"
]
PCT_COLS = ["RETENTION_FT_4YR","COMPLETION_150_4YR","PELL_SHARE"]

# Cell 3: load
def load_csv(path: str) -> pd.DataFrame:
    return pd.read_csv(path, low_memory=False)

# Cell 4: checks
def check_columns(df: pd.DataFrame):
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise AssertionError(f"Missing columns: {missing}")

def check_nonempty(df: pd.DataFrame):
    if len(df) == 0:
        raise AssertionError("No rows after preparation.")

def check_numeric_ranges(df: pd.DataFrame):
    for c in PCT_COLS:
        bad = df[c].dropna().pipe(lambda s: (s < 0) | (s > 1))
        if bad.any():
            raise AssertionError(f"{c} contains values outside [0,1].")
    if (df["UGDS"].dropna() < 0).any():
        raise AssertionError("UGDS contains negative values.")
    if (df["TUITIONFEE_IN"].dropna() < 0).any():
        raise AssertionError("TUITIONFEE_IN contains negative values.")

# Cell 5: summary (optional)
def print_summary(df: pd.DataFrame):
    print(f"Rows: {len(df):,}")
    print("States:", ", ".join(sorted(df["STABBR"].dropna().unique())))
    print(df[["RETENTION_FT_4YR","COMPLETION_150_4YR","UGDS"]].describe().to_string())

# Cell 6: cli
if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    args = ap.parse_args()

    try:
        df = load_csv(args.input)
        check_columns(df); check_nonempty(df); check_numeric_ranges(df)
        print_summary(df)
    except Exception as e:
        print(f"VALIDATION FAILED: {e}", file=sys.stderr)
        sys.exit(1)
    print("VALIDATION PASSED")
