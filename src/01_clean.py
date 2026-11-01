"""Build the cleaned team-season panel -> data/processed/team_panel.csv.

Keeps AL/NL teams from 1969 through the latest season, constructs rate outcomes,
treatment indicators, and sample/strike flags. Main sample = 1969-1976.
OBP is intentionally not constructed (HBP/SF missing for all teams in 1969).

Run from the repo root: python src/01_clean.py
"""
import numpy as np
import pandas as pd

RAW = "data/raw/Teams.csv"
OUT = "data/processed/team_panel.csv"

FIRST_YEAR = 1969
TREAT_YEAR = 1973
MAIN_END = 1976
STRIKE_YEARS = [1972, 1981, 1994, 1995, 2020]

# Raw file has a UTF-8 BOM
raw = pd.read_csv(RAW, encoding="utf-8-sig")

df = raw[raw["lgID"].isin(["AL", "NL"]) & (raw["yearID"] >= FIRST_YEAR)].copy()

keep = ["yearID", "lgID", "teamID", "franchID", "name", "park",
        "G", "Ghome", "AB", "H", "HR", "BB", "R", "attendance"]
df = df[keep].sort_values(["yearID", "lgID", "teamID"]).reset_index(drop=True)

# 2020 had no fans; attendance is recorded as 0, which is not a real observation
df.loc[df["attendance"] == 0, "attendance"] = np.nan

# Outcomes (rates, so strike-shortened seasons are comparable)
df["BA"] = df["H"] / df["AB"]
df["R_per_G"] = df["R"] / df["G"]
df["HR_per_G"] = df["HR"] / df["G"]
df["att_per_home_game"] = df["attendance"] / df["Ghome"]
df["log_att_per_home_game"] = np.log(df["att_per_home_game"])

# Treatment: league in that season, not franchise history
df["AL"] = (df["lgID"] == "AL").astype(int)
df["post"] = (df["yearID"] >= TREAT_YEAR).astype(int)
df["AL_post"] = df["AL"] * df["post"]

df["main_sample"] = df["yearID"].between(FIRST_YEAR, MAIN_END).astype(int)
df["strike"] = df["yearID"].isin(STRIKE_YEARS).astype(int)

# Sanity checks on the main sample: balanced 12 AL + 12 NL teams, 1969-1976
main = df[df["main_sample"] == 1]
outcomes = ["BA", "R_per_G", "HR_per_G", "log_att_per_home_game"]
assert len(main) == 192, len(main)
assert (main.groupby(["yearID", "lgID"]).size() == 12).all()
assert main["franchID"].nunique() == 24
assert main[outcomes].notna().all().all()
assert (main.groupby("franchID")["lgID"].nunique() == 1).all()

df.to_csv(OUT, index=False)

print(f"Saved {OUT}: {len(df)} rows, {df.yearID.min()}-{df.yearID.max()}")
print(f"Main sample: {len(main)} team-seasons, {main.teamID.nunique()} teamIDs, "
      f"{main.franchID.nunique()} franchises")
print(f"Attendance set to NaN (recorded as 0): {df.attendance.isna().sum()} rows")
