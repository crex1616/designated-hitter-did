"""Offensive outcomes, AL vs NL, inside the 1969-1976 estimation window (Figure 1b).

Outputs:
  output/tables/offense_window_data.csv              yearly AL and NL means + AL-NL gap, 1969-1976
  output/figures/fig1b_offense_window.{png,pdf}      batting average, runs/game, HR/game side by side
  output/figures/fig1b_offense_window_{var}.{png,pdf} one figure per outcome

Descriptive companion to Figure 1, zoomed to the estimation window. Title claims are
computed from the data and asserted below, so a stale title fails the script.

Run from the repo root: python src/07_offense_window.py
"""
import textwrap

import pandas as pd
from matplotlib.ticker import FuncFormatter, MultipleLocator

import plot_style as ps

PANEL = "data/processed/team_panel.csv"
TAB = "output/tables/"

TREAT_YEAR = 1973
START, END = 1969, 1976
STRIKE_YEAR = 1972

PANELS = [
    ("BA", "Batting average", "Hits per at-bat, league average", ps.ba_level),
    ("R_per_G", "Runs per game", "Runs scored per team per game", lambda v, _: f"{v:.1f}"),
    ("HR_per_G", "Home runs per game", "Home runs hit per team per game", lambda v, _: f"{v:.2f}"),
]
LINE = {"AL": dict(color=ps.AL_BLUE, lw=2.6, zorder=3), "NL": dict(color=ps.NL_GRAY, lw=1.8, zorder=2)}
MARKER = {"AL": 5.5, "NL": 4.5}

NOTES = ("Averages are across the 12 teams in each league. 1972 (shaded) was shortened by a player "
         "strike; all measures are per game or per at-bat, so seasons remain comparable. Descriptive "
         "only; the difference-in-differences estimates give the effect of the DH.")

df = pd.read_csv(PANEL)
df = df[df["main_sample"] == 1]
vars_ = [p[0] for p in PANELS]
trend = df.groupby(["yearID", "lgID"])[vars_].mean().reset_index()

wide = trend.pivot(index="yearID", columns="lgID", values=vars_)
out = trend.copy()
for v in vars_:
    gap = (wide[(v, "AL")] - wide[(v, "NL")]).rename(f"{v}_gap_AL_minus_NL")
    out = out.merge(gap, left_on="yearID", right_index=True)
out.to_csv(TAB + "offense_window_data.csv", index=False, float_format="%.5f")

# --- Check every title claim against the data --------------------------------
pre = wide.index < TREAT_YEAR
gap = {v: wide[(v, "AL")] - wide[(v, "NL")] for v in vars_}
# BA: AL trailed every pre season, led every post season
assert (gap["BA"][pre] < 0).all() and (gap["BA"][~pre] > 0).all()
# R/G: 1972 was the AL's low in the window; AL led in exactly 3 of 4 post seasons
assert wide[("R_per_G", "AL")].idxmin() == STRIKE_YEAR
assert (gap["R_per_G"][~pre] > 0).sum() == 3
# HR/G: AL rose from 1972 to 1973, then both leagues ended 1976 below 1973
al_hr, nl_hr = wide[("HR_per_G", "AL")], wide[("HR_per_G", "NL")]
assert al_hr[1973] > al_hr[STRIKE_YEAR]
assert al_hr[END] < al_hr[1973] and nl_hr[END] < nl_hr[1973]
# Combined subtitle: AL's 1971->72 drop was larger than the NL's, and all AL measures rose in 1973
for v in vars_:
    al, nl = wide[(v, "AL")], wide[(v, "NL")]
    assert al[1971] - al[STRIKE_YEAR] > nl[1971] - nl[STRIKE_YEAR]
    assert al[1973] > al[STRIKE_YEAR]

TITLES = {
    "BA": "With the DH, the AL went from trailing the NL in batting average every season to leading every season",
    "R_per_G": "AL scoring rebounded from its 1972 low and topped the NL in three of four DH seasons",
    "HR_per_G": "AL home runs rebounded in 1973, then fell along with the NL's through 1976",
}
SUBTITLE = "Yearly league averages, American League (AL, blue) vs. National League (NL, gray), 1969–1976."

ps.apply()


def draw(ax, var, title, sub, fmt, first=False):
    ax.axvspan(STRIKE_YEAR - 0.5, STRIKE_YEAR + 0.5, color=ps.SHADE, lw=0, zorder=0)
    ax.axvline(TREAT_YEAR - 0.5, color=ps.ZERO, ls="--", lw=1, zorder=1)

    end = trend[trend["yearID"] == END].set_index("lgID")[var]
    for lg in ["AL", "NL"]:
        d = trend[trend["lgID"] == lg]
        ax.plot(d["yearID"], d[var], marker="o", ms=MARKER[lg], **LINE[lg])
        # Direct label at the right end; nudge apart so close endpoints don't collide
        dy = 7 if end[lg] >= end.drop(lg).iloc[0] else -7
        ax.annotate(lg, (END, end[lg]), xytext=(8, dy), textcoords="offset points",
                    va="center", fontsize=11, fontweight="bold", color=LINE[lg]["color"])

    ax.set_title(title, pad=24)
    ax.text(0, 1.035, sub, transform=ax.transAxes, fontsize=10, color=ps.INK2, va="bottom")
    ax.yaxis.set_major_formatter(FuncFormatter(fmt))
    if var == "BA":
        ax.yaxis.set_major_locator(MultipleLocator(0.005))  # whole points only, no rounded .2525 ticks
    ax.set_xlim(START - 0.5, END + 0.9)
    ax.set_xticks(range(START, END + 1))
    ax.margins(y=0.08)  # room for the end labels
    ps.style_axes(ax)

    if first:
        ax.text(TREAT_YEAR - 0.35, 0.04, "DH introduced\nin AL (1973)", transform=ax.get_xaxis_transform(),
                fontsize=9, color=ps.INK2, va="bottom", ha="left")
        ax.text(STRIKE_YEAR, 0.985, "Strike-\nshortened", transform=ax.get_xaxis_transform(),
                fontsize=8.5, color=ps.MUTED, va="top", ha="center")


# --- Combined figure ---------------------------------------------------------
fig, axes = ps.plt.subplots(1, 3, figsize=(13, 5.4))
for i, (ax, (var, title, sub, fmt)) in enumerate(zip(axes, PANELS)):
    draw(ax, var, title, sub, fmt, first=(i == 0))
ps.frame(
    fig,
    title=TITLES["BA"],
    subtitle=SUBTITLE + "\nThe AL slumped in 1972, far more than the NL; all three AL measures rebounded when the DH arrived in 1973.",
    notes=NOTES,
    top_in=1.65, bottom_in=0.85, left=0.06, right=0.97, wspace=0.28,
)
ps.save(fig, "fig1b_offense_window")

# --- One figure per outcome --------------------------------------------------
for var, title, sub, fmt in PANELS:
    fig, ax = ps.plt.subplots(figsize=(8, 5.8))
    draw(ax, var, title, sub, fmt, first=True)
    # Long takeaway titles wrap to two lines; the leading newline pushes the subtitle below them
    title = textwrap.fill(TITLES[var], width=62)
    subtitle = ("\n" if "\n" in title else "") + SUBTITLE
    ps.frame(fig, title=title, subtitle=subtitle, notes=NOTES,
             top_in=1.7, bottom_in=0.85, left=0.1, right=0.93)
    ps.save(fig, f"fig1b_offense_window_{var}")

print(out.to_string(index=False))
print("Saved", TAB + "offense_window_data.csv", "and fig1b_offense_window figures to output/figures/")
