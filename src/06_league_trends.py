"""League-specific linear trends: how an AL trend changes the DiD estimates.

For each outcome, sample 1969-1976, team (teamID) + year FE, SEs clustered by franchID:
  (1) Baseline:          Y = b * AL_post + FE
  (2) AL trend, full:    Y = b * AL_post + g * AL * (year - 1972) + FE
      The AL trend is fit on all 8 years. If the DH effect grows over time, the
      trend absorbs part of it.
  (3) AL trend, pre:     Y = g * AL * (year - 1972) + sum_k d_k * AL * 1[year == k], k = 1973..1976 + FE
      Post years are saturated, so g is identified from 1969-1972 only. The DiD
      estimate is the average post-period departure from the extrapolated pre-trend,
      b = mean(d_k). With 4 pre-years (incl. the 1972 AL dip) this trend is noisy.

Outputs:
  output/tables/league_trends.csv
  output/tables/league_trends.tex
  output/figures/fig3_robustness.{png,pdf}      Figure 3: b with 95% CI under each specification
                                                (display units: BA in points, attendance as %)
  output/figures/league_trends_gap_all.png      AL-NL gap with fitted trend lines, 2x2
  output/figures/league_trends_gap_<outcome>.png

Run from the repo root: python src/06_league_trends.py
"""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter, MaxNLocator
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

import plot_style as ps

PANEL = "data/processed/team_panel.csv"
EVENT = "output/tables/event_study.csv"  # baseline event-study points for the gap plots
TAB = "output/tables/"
FIG = "output/figures/"

REF_YEAR = 1972
POST_YEARS = [1973, 1974, 1975, 1976]
OUTCOMES = {
    "BA": "Batting average",
    "R_per_G": "Runs per game",
    "HR_per_G": "Home runs per game",
    "log_att_per_home_game": "Log attendance per home game",
}
SPECS = {
    "baseline": "Baseline TWFE",
    "trend_full": "+ AL trend (1969-76)",
    "trend_pre": "+ AL pre-trend (1969-72)",
}

# Reference palette categorical slots 1-3, one per specification
COLORS = {"baseline": "#2a78d6", "trend_full": "#eb6834", "trend_pre": "#1baf7a"}
MARKERS = {"baseline": "o", "trend_full": "s", "trend_pre": "D"}
INK, INK2, MUTED, GRID, AXIS = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
plt.rcParams.update({
    "font.size": 10, "axes.edgecolor": AXIS, "axes.labelcolor": INK2,
    "xtick.color": MUTED, "ytick.color": MUTED, "axes.titlecolor": INK,
    "figure.facecolor": "white",
})

df = pd.read_csv(PANEL)
df = df[df["main_sample"] == 1].reset_index(drop=True)
df["AL_t"] = df["AL"] * (df["yearID"] - REF_YEAR)
for y in POST_YEARS:
    df[f"AL_{y}"] = df["AL"] * (df["yearID"] == y).astype(int)
post_terms = " + ".join(f"AL_{y}" for y in POST_YEARS)

FORMULAS = {
    "baseline": "{y} ~ AL_post + C(teamID) + C(yearID)",
    "trend_full": "{y} ~ AL_post + AL_t + C(teamID) + C(yearID)",
    "trend_pre": "{y} ~ AL_t + " + post_terms + " + C(teamID) + C(yearID)",
}


def fit(formula):
    return smf.ols(formula, data=df).fit(
        cov_type="cluster", cov_kwds={"groups": df["franchID"]}, use_t=True)


rows = []
for var, label in OUTCOMES.items():
    for spec, formula in FORMULAS.items():
        res = fit(formula.format(y=var))
        if spec == "trend_pre":
            # Average of the four post-year departures from the extrapolated pre-trend
            R = np.zeros(len(res.params))
            for y in POST_YEARS:
                R[res.params.index.get_loc(f"AL_{y}")] = 1 / len(POST_YEARS)
            tt = res.t_test(R)
            coef, se = float(np.squeeze(tt.effect)), float(np.squeeze(tt.sd))
            p = float(np.squeeze(tt.pvalue))
            lo, hi = np.squeeze(tt.conf_int())
        else:
            coef, se, p = res.params["AL_post"], res.bse["AL_post"], res.pvalues["AL_post"]
            lo, hi = res.conf_int().loc["AL_post"]
        has_trend = "AL_t" in res.params
        rows.append({
            "outcome": var, "label": label, "spec": spec, "spec_label": SPECS[spec],
            "coef": coef, "se": se, "p": p, "ci_low": lo, "ci_high": hi,
            "trend": res.params["AL_t"] if has_trend else np.nan,
            "trend_se": res.bse["AL_t"] if has_trend else np.nan,
            "trend_p": res.pvalues["AL_t"] if has_trend else np.nan,
            "N": int(res.nobs), "clusters": df["franchID"].nunique(),
        })
results = pd.DataFrame(rows)
results.to_csv(TAB + "league_trends.csv", index=False, float_format="%.6f")


# --- LaTeX table -------------------------------------------------------------
def stars(p):
    return "***" if p < 0.01 else "**" if p < 0.05 else "*" if p < 0.10 else ""


def fmt(x, y):
    return f"{x:.4f}" if y in ("BA", "HR_per_G") else f"{x:.3f}"


cols = list(OUTCOMES)
short = {"BA": "BA", "R_per_G": "Runs/G", "HR_per_G": "HR/G", "log_att_per_home_game": "Log att./home G"}
nc = len(cols) + 1
lines = [
    r"\begin{table}[htbp]\centering",
    r"\caption{DiD estimates with league-specific linear trends, 1969--1976}",
    r"\label{tab:league_trends}",
    r"\begin{tabular}{l" + "c" * len(cols) + "}",
    r"\hline\hline",
    " & " + " & ".join(f"({i + 1})" for i in range(len(cols))) + r" \\",
    " & " + " & ".join(short[c] for c in cols) + r" \\",
    r"\hline",
]
titles = {
    "baseline": "Baseline TWFE",
    "trend_full": "AL linear trend, estimated 1969--1976",
    "trend_pre": "AL linear trend, estimated 1969--1972 (avg.\\ post deviation)",
}
for spec in SPECS:
    r = results[results.spec == spec].set_index("outcome").loc[cols]
    lines.append(r"\multicolumn{" + str(nc) + r"}{l}{\textit{" + titles[spec] + r"}} \\")
    lines.append(r"AL $\times$ Post & " + " & ".join(
        fmt(r.loc[y, "coef"], y) + "$^{" + stars(r.loc[y, "p"]) + "}$" for y in cols) + r" \\")
    lines.append(" & " + " & ".join(f"({fmt(r.loc[y, 'se'], y)})" for y in cols) + r" \\")
    if spec != "baseline":
        lines.append(r"AL $\times$ (year $-$ 1972) & " + " & ".join(
            fmt(r.loc[y, "trend"], y) + "$^{" + stars(r.loc[y, "trend_p"]) + "}$" for y in cols) + r" \\")
        lines.append(" & " + " & ".join(f"({fmt(r.loc[y, 'trend_se'], y)})" for y in cols) + r" \\")
    lines.append(r"[0.5ex]")
lines += [
    r"\hline",
    r"Observations & " + " & ".join(str(results.N.iloc[0]) for _ in cols) + r" \\",
    r"Clusters (franchises) & " + " & ".join(str(results.clusters.iloc[0]) for _ in cols) + r" \\",
    r"\hline\hline",
    r"\multicolumn{" + str(nc) + r"}{p{0.9\linewidth}}{\footnotesize "
    r"Notes: All models include team (team-city) and year fixed effects. In the last panel, post years "
    r"are saturated with AL $\times$ year dummies, so the AL trend is identified from 1969--1972 only "
    r"and the reported effect is the average 1973--1976 deviation from the extrapolated trend. "
    r"Standard errors clustered by franchise in parentheses; inference uses $t(G-1)$. "
    r"* $p<0.10$, ** $p<0.05$, *** $p<0.01$.} \\",
    r"\end{tabular}",
    r"\end{table}",
]
with open(TAB + "league_trends.tex", "w") as f:
    f.write("\n".join(lines) + "\n")


def style(ax):
    ax.grid(axis="y", color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    for side in ["top", "right"]:
        ax.spines[side].set_visible(False)


# --- Figure 3: estimates under the three approaches (presentation figure) ----
# Display units only: batting average in points (x1000); log attendance as % via exp(b) - 1.
def to_display(var, x):
    if var == "BA":
        return x * 1000
    if var == "log_att_per_home_game":
        return (np.exp(x) - 1) * 100
    return x


FIG3_ROWS = {  # spec -> (row position, plain-language label)
    "baseline": (2, "Standard estimate"),
    "trend_full": (1, "Adjusting for the\nAL's own trend"),
    "trend_pre": (0, "Projecting the AL's\npre-1973 trend"),
}
FIG3_PANELS = {  # outcome -> (panel title, x-axis label, tick format, value-label format, per-162 noun)
    "BA": ("Batting average", "Points of batting average",
           lambda v: ps.signed(v, 0), lambda v: ps.signed(v, 0) + " pts", None),
    "R_per_G": ("Runs per game", "Runs per game",
                lambda v: ps.signed(v, 1), lambda v: ps.signed(v, 2), "runs"),
    "HR_per_G": ("Home runs per game", "Home runs per game",
                 lambda v: ps.signed(v, 1), lambda v: ps.signed(v, 2), "HR"),
    "log_att_per_home_game": ("Attendance per home game", "% change in attendance",
                              lambda v: ps.signed(v, 0) + "%", lambda v: ps.signed(v, 0) + "%", None),
}

LABEL_BOX = dict(boxstyle="square,pad=0.15", fc="white", ec="none")  # keeps labels legible over lines

with ps.plt.rc_context():
    ps.apply()
    fig, axes = ps.plt.subplots(1, 4, figsize=(14, 6.2), sharey=True)
    for i, (ax, (var, (title, xlab, tick_fmt, val_fmt, per162))) in enumerate(zip(axes, FIG3_PANELS.items())):
        r = results[results.outcome == var].set_index("spec")
        ax.axvline(0, color=ps.ZERO, lw=1.2, zorder=1)
        for spec, (ypos, _) in FIG3_ROWS.items():
            est = to_display(var, r.loc[spec, "coef"])
            lo, hi = to_display(var, r.loc[spec, "ci_low"]), to_display(var, r.loc[spec, "ci_high"])
            main = spec == "baseline"
            color = ps.AL_BLUE if main else ps.AL_BLUE_MUTED
            ax.hlines(ypos, lo, hi, color=color, lw=2.8 if main else 2, zorder=2)
            ax.plot(est, ypos, "o", color=color, ms=10 if main else 8, mec="white", mew=1.3, zorder=3)
            ax.annotate(val_fmt(est), (est, ypos), xytext=(0, 9), textcoords="offset points",
                        ha="center", va="bottom", fontsize=10.5 if main else 10,
                        fontweight="bold" if main else "normal", color=ps.INK if main else ps.INK2,
                        bbox=LABEL_BOX)
            if per162:
                ax.annotate(f"≈{est * 162:.0f} {per162} per 162 games", (est, ypos), xytext=(0, -10),
                            textcoords="offset points", ha="center", va="top", fontsize=8.5, color=ps.MUTED,
                            bbox=LABEL_BOX)
        ax.set_title(title, pad=10)
        ax.set_xlabel(xlab, labelpad=6)
        ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _, f=tick_fmt: f(v) if abs(v) > 1e-9 else "0"))
        ax.xaxis.set_major_locator(MaxNLocator(5, steps=[1, 2, 5, 10]))
        ps.style_axes(ax, grid_axis="x")
        if i == 0:
            ax.annotate("No effect", (0, 2.62), xytext=(5, 0), textcoords="offset points",
                        ha="left", va="bottom", fontsize=9, color=ps.INK2, bbox=LABEL_BOX)
    axes[0].set_yticks([y for y, _ in FIG3_ROWS.values()], [lab for _, lab in FIG3_ROWS.values()])
    for lab in axes[0].get_yticklabels():
        if lab.get_text() == "Standard estimate":
            lab.set_fontweight("bold")
            lab.set_color(ps.INK)
    axes[0].tick_params(axis="y", labelsize=11)
    axes[0].set_ylim(-0.7, 2.85)

    ps.frame(
        fig,
        title="The standard estimate shows a clear DH boost only for AL batting average",
        subtitle="Estimated effect of the DH on AL teams, 1973–1976, under three approaches. Dots are "
                 "estimates; bars show 95% confidence intervals.\nAdjusting for the AL's pre-1973 decline makes "
                 "every hitting effect larger; the attendance effect is uncertain under every approach.",
        notes="Standard estimate: regression with team and year fixed effects, 1969–1976 (192 team-seasons). "
              "\"Adjusting for the AL's own trend\" adds a separate straight-line AL trend fit to all eight "
              "seasons. \"Projecting the AL's pre-1973 trend\" fits that line to 1969–72 only and averages "
              "how far 1973–76 sit above its projection; because AL hitting dipped in 1972, this projection "
              "slopes down and may overstate the effect. Intervals clustered by franchise (24 clusters). Batting "
              "average in points (1 point = .001); attendance converted from log points to percent with "
              "exp(b) − 1; per-162-game figures multiply the per-game effect by 162.",
        top_in=1.55, bottom_in=1.35, left=0.135, right=0.985, wspace=0.12,
    )
    ps.save(fig, "fig3_robustness")

# --- Figure 2: AL-NL gap with fitted trend lines -----------------------------
# Points are the baseline event-study estimates (AL-NL gap relative to 1972).
# Lines use the regression slopes and effects; their intercepts are set by least
# squares to the plotted points (the panel fits match these up to the city-level FE
# for relocated teams, so the lines are a close visual guide, not a refit).
es = pd.read_csv(EVENT)
years = np.arange(1969, 1977)
t = years - REF_YEAR
post = (years >= POST_YEARS[0]).astype(float)


def draw_gap(ax, var, label):
    g = es[es.outcome == var].set_index("year").loc[years]
    r = results[results.outcome == var].set_index("spec")
    pts = g["coef"].values
    pre = years <= REF_YEAR

    # (2) Full-window trend with a level shift at 1973
    b2, g2 = r.loc["trend_full", "coef"], r.loc["trend_full", "trend"]
    c2 = np.mean(pts - g2 * t - b2 * post)
    line2 = c2 + g2 * t + b2 * post
    ax.plot(years[pre], line2[pre], color=COLORS["trend_full"], lw=2, zorder=2)
    ax.plot(years[~pre], line2[~pre], color=COLORS["trend_full"], lw=2, zorder=2)

    # (3) Pre-period trend, extrapolated into the post-period
    g3 = r.loc["trend_pre", "trend"]
    c3 = np.mean(pts[pre] - g3 * t[pre])
    line3 = c3 + g3 * t
    ax.plot(years[pre], line3[pre], color=COLORS["trend_pre"], lw=2, zorder=2)
    ax.plot(years[years >= REF_YEAR], line3[years >= REF_YEAR], color=COLORS["trend_pre"],
            lw=2, ls="--", zorder=2)
    # Shade post-period departures from the extrapolated pre-trend
    ax.vlines(years[~pre], line3[~pre], pts[~pre], color=COLORS["trend_pre"], lw=1, alpha=0.6, zorder=1)

    # (1) Baseline: the event-study points themselves
    ax.plot(years[years != REF_YEAR], pts[years != REF_YEAR], "o", color=COLORS["baseline"], ms=7,
            mec="white", mew=1.2, zorder=4)
    ax.plot([REF_YEAR], [0], "o", mfc="white", mec=COLORS["baseline"], mew=1.5, ms=7, zorder=4)

    ax.axhline(0, color=AXIS, lw=1, zorder=0)
    ax.axvline(REF_YEAR + 0.5, color=MUTED, ls=":", lw=1.2, zorder=0)
    ax.set_xticks(years)
    ax.set_xlim(1968.5, 1976.5)
    ax.set_ylabel(f"AL - NL gap, {label.lower()}\n(relative to 1972)", fontsize=9)
    style(ax)

    est = {s: fmt(r.loc[s, "coef"], var) for s in SPECS}
    return [
        Line2D([], [], marker="o", ls="", color=COLORS["baseline"], mec="white",
               label=f"Event-study gap; baseline DiD = {est['baseline']}"),
        Line2D([], [], color=COLORS["trend_full"], lw=2,
               label=f"AL trend 1969-76 + shift; DiD = {est['trend_full']}"),
        Line2D([], [], color=COLORS["trend_pre"], lw=2, ls="--",
               label=f"AL pre-trend extrapolated; DiD = {est['trend_pre']}"),
    ]


GAP_NOTE = ("Points: baseline event-study estimates (1972 = 0). Lines: AL-specific linear trends using the "
            "regression slopes; dashed = pre-trend projected past 1973,\nthin bars = post-period departures "
            "from it (their average is the pre-trend DiD). Lines are anchored to the plotted points, so "
            "they are a close visual guide to the regressions in league_trends.csv.")

fig, axes = plt.subplots(2, 2, figsize=(12, 8.5))
for ax, (var, label) in zip(axes.flat, OUTCOMES.items()):
    handles = draw_gap(ax, var, label)
    ax.set_title(label, loc="left", fontsize=11)
    ax.legend(handles=handles, frameon=False, fontsize=7.5, loc="lower left",
              bbox_to_anchor=(0, 1.06), ncol=1)
fig.suptitle("AL - NL gap and league-specific trends, 1969-1976", x=0.01, ha="left",
             fontsize=12, color=INK)
fig.text(0.01, 0.01, GAP_NOTE, fontsize=7.5, color=MUTED)
fig.tight_layout(rect=(0, 0.05, 1, 0.97), h_pad=2.5)
fig.savefig(FIG + "league_trends_gap_all.png", dpi=200)
plt.close(fig)

for var, label in OUTCOMES.items():
    fig, ax = plt.subplots(figsize=(7, 4.8))
    handles = draw_gap(ax, var, label)
    ax.set_title(f"{label}: AL - NL gap and league trends", loc="left", fontsize=11, pad=52)
    ax.legend(handles=handles, frameon=False, fontsize=8, loc="lower left",
              bbox_to_anchor=(0, 1.0), ncol=1)
    fig.text(0.01, 0.01, GAP_NOTE.replace("\n", " ").replace("; dashed", ";\ndashed")
             .replace(" Lines are", "\nLines are"), fontsize=6.5, color=MUTED)
    fig.tight_layout(rect=(0, 0.09, 1, 1))
    fig.savefig(FIG + f"league_trends_gap_{var}.png", dpi=200)
    plt.close(fig)

print(results[["label", "spec", "coef", "se", "p", "trend", "trend_se", "trend_p"]]
      .to_string(index=False, float_format=lambda x: f"{x:.4f}"))
print("Saved", TAB + "league_trends.{csv,tex}", "and figures league_trends_*.png")
