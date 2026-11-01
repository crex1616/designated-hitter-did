"""Event study: AL x year interactions relative to 1972, and Figure 2.

For each outcome, sample 1969-1976:
  Y_it = sum_{k != 1972} b_k * AL_i * 1[year == k] + team FE (teamID) + year FE + e
SEs clustered by franchID (24 clusters); inference uses t(G-1).
Only 3 pre-period leads (1969-1971), so the parallel-trends test has limited power.

Outputs:
  output/tables/event_study.csv           b_k, SE, 95% CI per outcome x year (1972 = 0 by construction)
  output/tables/event_study_pretrends.csv joint test that the 3 leads are zero, per outcome
  output/figures/fig2_event_study.{png,pdf}  Figure 2 (display units: BA in points,
                                             attendance as % via exp(b) - 1)

Run from the repo root: python src/04_event_study.py
"""
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from matplotlib.ticker import FuncFormatter

import plot_style as ps

PANEL = "data/processed/team_panel.csv"
TAB = "output/tables/"
FIG = "output/figures/"

REF_YEAR = 1972
TREAT_YEAR = 1973
OUTCOMES = {
    "BA": "Batting average",
    "R_per_G": "Runs per game",
    "HR_per_G": "Home runs per game",
    "log_att_per_home_game": "Log attendance per home game",
}

df = pd.read_csv(PANEL)
df = df[df["main_sample"] == 1].reset_index(drop=True)
years = sorted(df["yearID"].unique())
event_years = [y for y in years if y != REF_YEAR]
leads = [y for y in event_years if y < REF_YEAR]

for y in event_years:
    df[f"AL_{y}"] = df["AL"] * (df["yearID"] == y).astype(int)
terms = " + ".join(f"AL_{y}" for y in event_years)

coef_rows, test_rows = [], []
for var, label in OUTCOMES.items():
    res = smf.ols(f"{var} ~ {terms} + C(teamID) + C(yearID)", data=df).fit(
        cov_type="cluster", cov_kwds={"groups": df["franchID"]}, use_t=True)
    ci = res.conf_int()
    for y in years:
        if y == REF_YEAR:
            coef_rows.append({"outcome": var, "year": y, "coef": 0.0, "se": np.nan, "p": np.nan,
                              "ci_low": np.nan, "ci_high": np.nan, "reference": 1})
        else:
            k = f"AL_{y}"
            coef_rows.append({"outcome": var, "year": y, "coef": res.params[k], "se": res.bse[k],
                              "p": res.pvalues[k], "ci_low": ci.loc[k, 0], "ci_high": ci.loc[k, 1],
                              "reference": 0})
    wald = res.f_test(", ".join(f"AL_{y} = 0" for y in leads))
    test_rows.append({"outcome": var, "n_leads": len(leads), "F": float(np.squeeze(wald.fvalue)),
                      "df_num": int(wald.df_num), "df_denom": int(wald.df_denom),
                      "p": float(wald.pvalue), "N": int(res.nobs),
                      "clusters": df["franchID"].nunique()})

coefs = pd.DataFrame(coef_rows)
tests = pd.DataFrame(test_rows)
coefs.to_csv(TAB + "event_study.csv", index=False, float_format="%.6f")
tests.to_csv(TAB + "event_study_pretrends.csv", index=False, float_format="%.6f")


# --- Figure 2 ------------------------------------------------------------------
# Display units only: batting average in points (x1000); log attendance as % change.
def to_display(var, x):
    x = np.asarray(x, dtype=float)
    if var == "BA":
        return x * 1000
    if var == "log_att_per_home_game":
        return (np.exp(x) - 1) * 100
    return x


PANELS = {
    "BA": ("Batting average", "Points of batting average (1 point = .001)",
           lambda v, _: ps.signed(v, 0) if v else "0"),
    "R_per_G": ("Runs per game", "Runs per team per game",
                lambda v, _: ps.signed(v, 1) if v else "0"),
    "HR_per_G": ("Home runs per game", "Home runs per team per game",
                 lambda v, _: ps.signed(v, 1) if v else "0"),
    "log_att_per_home_game": ("Attendance per home game", "Percent difference in fans per home game",
                              lambda v, _: ps.signed(v, 0) + "%" if v else "0%"),
}
p_lead = tests.set_index("outcome")["p"]

ps.apply()
fig, axes = ps.plt.subplots(2, 2, figsize=(12, 9))
for i, (ax, (var, (title, sub, fmt))) in enumerate(zip(axes.flat, PANELS.items())):
    d = coefs[coefs["outcome"] == var].sort_values("year")
    x = d["year"].values
    est = to_display(var, d["coef"])
    lo = to_display(var, d["ci_low"].fillna(0))  # reference year: interval is exactly 0
    hi = to_display(var, d["ci_high"].fillna(0))
    ref = d["reference"].values == 1

    ax.axhline(0, color=ps.ZERO, lw=1.1, zorder=1)
    ax.axvline(REF_YEAR + 0.5, color=ps.ZERO, ls="--", lw=1, zorder=1)
    ax.fill_between(x, lo, hi, color=ps.AL_BLUE, alpha=0.14, lw=0, zorder=2)
    ax.plot(x, est, color=ps.AL_BLUE, lw=1.3, zorder=3)
    ax.plot(x[~ref], est[~ref], "o", color=ps.AL_BLUE, ms=7, mec="white", mew=1.2, zorder=4)
    ax.plot(x[ref], est[ref], "o", mfc="white", mec=ps.INK2, mew=1.6, ms=8, zorder=5)
    ax.annotate("reference\nyear", (REF_YEAR, 0), xytext=(0, -12), textcoords="offset points",
                ha="center", va="top", fontsize=8.5, color=ps.INK2)

    ax.set_title(title, pad=24)
    ax.text(0, 1.035, sub, transform=ax.transAxes, fontsize=10, color=ps.INK2, va="bottom")
    ax.yaxis.set_major_formatter(FuncFormatter(fmt))
    ax.set_xticks(years)
    ax.set_xlim(years[0] - 0.4, years[-1] + 1.3)
    ps.style_axes(ax)
    # Leave room under the zero line for the "reference year" label
    y0, y1 = ax.get_ylim()
    ax.set_ylim(min(y0, -0.22 * (y1 - y0)), y1)

    if i == 0:
        ax.text(REF_YEAR + 0.6, 0.98, "DH introduced", transform=ax.get_xaxis_transform(),
                fontsize=9, color=ps.INK2, va="top", ha="left")
        ax.annotate("No difference\nfrom 1972", (years[-1] + 0.35, 0), xytext=(0, 4),
                    textcoords="offset points", fontsize=8.5, color=ps.INK2, va="bottom", ha="left")

fig.supylabel("Difference between AL and NL, relative to 1972", x=0.012, fontsize=11, color=ps.INK2)
ps.frame(
    fig,
    title="AL batting average jumped in 1973 and stayed above its 1972 level",
    subtitle="Each dot is the AL–NL gap in that year minus the gap in 1972; shaded bands show 95% "
             "confidence intervals.\nCaution: 1972 was an unusually weak year for AL hitters, so most "
             "earlier years also sit above zero, especially for runs and home runs.",
    notes="Estimates from a regression of each measure on AL-by-year indicators with team and year fixed "
          "effects, 1969–1976 (192 team-seasons; 1972 omitted). Intervals clustered by franchise "
          "(24 clusters). Attendance converted from log points to percent with exp(b) − 1. Only three "
          "pre-1973 years are available, so the check for pre-existing differences has limited power; "
          "joint test that 1969–71 are all zero: "
          f"p = {p_lead['BA']:.2f} (batting), {p_lead['R_per_G']:.2f} (runs), "
          f"{p_lead['HR_per_G']:.2f} (home runs), {p_lead['log_att_per_home_game']:.2f} (attendance). "
          "Batting intervals for 1975–76 include zero.",
    top_in=1.5, bottom_in=0.95, left=0.075, right=0.975, hspace=0.5, wspace=0.18,
)
ps.save(fig, "fig2_event_study")

print(coefs.to_string(index=False, float_format=lambda x: f"{x:.4f}"))
print(tests.to_string(index=False, float_format=lambda x: f"{x:.4f}"))
print("NOTE: only 3 pre-period leads; the parallel-trends test has limited power.")
