"""Summary statistics by league/period and Figure 1 (AL vs NL yearly trends).

Outputs:
  output/tables/summary_by_league_period.csv  mean/sd/N of each outcome by league x period, 1969-1976
  output/tables/summary_by_league_period.tex
  output/tables/yearly_means.csv              yearly AL and NL means, 1969-1976
  output/tables/fig1_trends_data.csv          yearly AL and NL means, 1969-1996 (data behind Figure 1)
  output/figures/fig1_trends.{png,pdf}        Figure 1: AL vs NL yearly averages, 1969-1996

Figure 1 is descriptive and extends past the 1969-1976 estimation window to 1996
(the last season before interleague play). All estimates use 1969-1976 only.

Run from the repo root: python src/02_eda.py
"""
import numpy as np
import pandas as pd
from matplotlib.ticker import FuncFormatter

import plot_style as ps

PANEL = "data/processed/team_panel.csv"
TAB = "output/tables/"
FIG = "output/figures/"

TREAT_YEAR = 1973
FIG1_END = 1996
STRIKE_SPANS = [(1972, 1972), (1981, 1981), (1994, 1995)]

OUTCOMES = {
    "BA": "Batting average",
    "R_per_G": "Runs per game",
    "HR_per_G": "Home runs per game",
    "log_att_per_home_game": "Log attendance per home game",
}

df = pd.read_csv(PANEL)
df = df[df["main_sample"] == 1].copy()
df["period"] = np.where(df["post"] == 1, "Post (1973-76)", "Pre (1969-72)")

# --- Summary stats by league x period ---------------------------------------
rows = []
for var, label in OUTCOMES.items():
    for (lg, period), g in df.groupby(["lgID", "period"]):
        rows.append({"outcome": label, "league": lg, "period": period,
                     "mean": g[var].mean(), "sd": g[var].std(), "N": g[var].count()})
summary = pd.DataFrame(rows)
summary["period"] = pd.Categorical(summary["period"], ["Pre (1969-72)", "Post (1973-76)"])
summary["outcome"] = pd.Categorical(summary["outcome"], list(OUTCOMES.values()))
summary = summary.sort_values(["outcome", "league", "period"]).reset_index(drop=True)
summary.to_csv(TAB + "summary_by_league_period.csv", index=False, float_format="%.4f")

# Wide version for LaTeX: one row per outcome, mean (sd) in each league x period cell
wide = summary.assign(cell=summary.apply(lambda r: f"{r['mean']:.3f} ({r['sd']:.3f})", axis=1))
wide = wide.pivot(index="outcome", columns=["league", "period"], values="cell")
wide = wide.reindex(list(OUTCOMES.values()))
wide.to_latex(TAB + "summary_by_league_period.tex",
              caption="Means (SD) by league and period, 1969--1976. N = 48 team-seasons per cell.",
              label="tab:summary", multicolumn_format="c")

# --- Yearly league means ----------------------------------------------------
yearly = df.groupby(["yearID", "lgID"])[list(OUTCOMES)].mean().reset_index()
yearly["geo_att_per_home_game"] = np.exp(yearly["log_att_per_home_game"])
yearly.to_csv(TAB + "yearly_means.csv", index=False, float_format="%.5f")

# --- Figure 1: AL vs NL yearly averages, 1969-1996 ---------------------------
ps.apply()
full = pd.read_csv(PANEL)
full = full[full["yearID"] <= FIG1_END]
trend = (full.groupby(["yearID", "lgID"])[["BA", "R_per_G", "HR_per_G", "att_per_home_game"]]
         .mean().reset_index())
trend["att_thousands"] = trend["att_per_home_game"] / 1000
trend.to_csv(TAB + "fig1_trends_data.csv", index=False, float_format="%.5f")

PANELS = [
    ("BA", "Batting average", "Hits per at-bat, league average", ps.ba_level),
    ("R_per_G", "Runs per game", "Runs scored per team per game", lambda v, _: f"{v:.1f}"),
    ("HR_per_G", "Home runs per game", "Home runs hit per team per game", lambda v, _: f"{v:.2f}"),
    ("att_thousands", "Attendance per home game", "Average fans per home game, in thousands",
     lambda v, _: f"{v:.0f}k"),
]
LINE = {"AL": dict(color=ps.AL_BLUE, lw=2.6, zorder=3), "NL": dict(color=ps.NL_GRAY, lw=1.8, zorder=2)}
NAME = {"AL": "American League", "NL": "National League"}

fig, axes = ps.plt.subplots(2, 2, figsize=(12, 8.6))
for i, (ax, (var, title, sub, fmt)) in enumerate(zip(axes.flat, PANELS)):
    for a, b in STRIKE_SPANS:
        ax.axvspan(a - 0.5, b + 0.5, color=ps.SHADE, lw=0, zorder=0)
    ax.axvline(TREAT_YEAR, color=ps.ZERO, ls="--", lw=1, zorder=1)

    end = trend[trend["yearID"] == FIG1_END].set_index("lgID")[var]
    for lg in ["AL", "NL"]:
        d = trend[trend["lgID"] == lg]
        ax.plot(d["yearID"], d[var], **LINE[lg])
        # Direct label at the right end; nudge apart so close endpoints don't collide
        dy = 7 if end[lg] >= end.drop(lg).iloc[0] else -7
        ax.annotate(lg, (FIG1_END, end[lg]), xytext=(6, dy), textcoords="offset points",
                    va="center", fontsize=11, fontweight="bold", color=LINE[lg]["color"])

    ax.set_title(title, pad=24)
    ax.text(0, 1.035, sub, transform=ax.transAxes, fontsize=10, color=ps.INK2, va="bottom")
    ax.yaxis.set_major_formatter(FuncFormatter(fmt))
    ax.set_xlim(1968.5, FIG1_END + 2.2)
    ax.set_xticks(range(1969, FIG1_END + 1, 3))
    ps.style_axes(ax)

    if i == 0:
        ax.text(TREAT_YEAR + 0.4, 0.04, "DH introduced\nin AL (1973)", transform=ax.get_xaxis_transform(),
                fontsize=9, color=ps.INK2, va="bottom", ha="left")
        ax.text(1981, 0.97, "Strike-shortened\nseasons shaded", transform=ax.get_xaxis_transform(),
                fontsize=8.5, color=ps.MUTED, va="top", ha="center")

ps.frame(
    fig,
    title="After the DH arrived in 1973, AL hitters out-hit the NL every season through 1996",
    subtitle="Yearly league averages, American League (AL, blue) vs. National League (NL, gray), 1969–1996.\n"
             "AL batting average trailed the NL in all four seasons before 1973 and led in all 24 after.",
    notes="Averages are across teams in each league (12 per league in 1969–76; the AL grew to 14 teams "
          "in 1977 and the NL in 1993). Shaded seasons (1972, 1981, 1994–95) were shortened by player "
          "strikes; all measures are per game or per at-bat, so shorter seasons remain comparable. The "
          "project's estimates use 1969–1976 only; later years are shown for context and also reflect "
          "expansion and other changes.",
    top_in=1.45, bottom_in=0.95, left=0.06, right=0.97, hspace=0.55, wspace=0.18,
)
ps.save(fig, "fig1_trends")

print(summary.to_string(index=False))
print("Saved tables to", TAB, "and Figure 1 to", FIG + "fig1_trends.{png,pdf}")
