"""Shared figure style for the presentation figures (fig1-fig3).

Import from a numbered script run at the repo root (python src/0X_name.py puts src/
on the path):  import plot_style as ps

Conventions: left-aligned takeaway title + gray subtitle, light horizontal gridlines,
no top/right spines, direct labels instead of legends, source/notes line at bottom left.
Color meaning is fixed across figures: AL = strong blue, NL = gray.
"""
import textwrap

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

# --- Colors ------------------------------------------------------------------
AL_BLUE = "#2a78d6"        # AL / the main estimate
AL_BLUE_MUTED = "#8db3e2"  # alternative (adjusted) estimates
NL_GRAY = "#8a8984"        # NL
INK = "#0b0b0b"            # titles
INK2 = "#52514e"           # subtitles, axis labels, direct labels
MUTED = "#898781"          # tick labels, notes
GRID = "#e6e5df"           # gridlines
ZERO = "#76756f"           # zero / reference lines (darker than grid)
SHADE = "#f1f0eb"          # strike-season shading

SOURCE = "Source: SABR Lahman Baseball Database (2025)."

FONT = "Arial"


def apply():
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": [FONT, "DejaVu Sans"],
        "font.size": 10,
        "axes.titlesize": 12,
        "axes.titleweight": "bold",
        "axes.titlecolor": INK,
        "axes.titlelocation": "left",
        "axes.labelsize": 11,
        "axes.labelcolor": INK2,
        "axes.edgecolor": "#c3c2b7",
        "axes.facecolor": "white",
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "xtick.color": MUTED,
        "ytick.color": MUTED,
        "xtick.labelcolor": INK2,
        "ytick.labelcolor": INK2,
        "figure.facecolor": "white",
        "savefig.facecolor": "white",
        "pdf.fonttype": 42,  # embed TrueType so text stays editable/selectable
        "ps.fonttype": 42,
    })


def style_axes(ax, grid_axis="y"):
    """Light gridlines on one axis only; no top/right spines, no border."""
    ax.grid(axis=grid_axis, color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    for side in ["top", "right"]:
        ax.spines[side].set_visible(False)
    if grid_axis == "x":
        ax.spines["left"].set_visible(False)
        ax.tick_params(axis="y", length=0)
    ax.tick_params(axis="both", colors=MUTED)


def frame(fig, title, subtitle, notes, top_in=1.15, bottom_in=0.6, left=0.07, right=0.98,
          wspace=None, hspace=None):
    """Left-aligned title/subtitle at top, source+notes at bottom; size the plot area in inches."""
    w, h = fig.get_size_inches()
    x0 = 0.12 / w
    fig.text(x0, 1 - 0.18 / h, title, fontsize=16, fontweight="bold", color=INK, va="top", ha="left")
    fig.text(x0, 1 - 0.52 / h, subtitle, fontsize=12, color=INK2, va="top", ha="left",
             linespacing=1.35)
    note = textwrap.fill(f"{SOURCE} Notes: {notes}", width=int(w * 17.5))
    fig.text(x0, 0.1 / h, note, fontsize=8, color=MUTED, va="bottom", ha="left", linespacing=1.3)
    fig.subplots_adjust(top=1 - top_in / h, bottom=bottom_in / h, left=left, right=right,
                        wspace=wspace, hspace=hspace)


def save(fig, name, folder="output/figures/"):
    fig.savefig(folder + name + ".png", dpi=300)
    fig.savefig(folder + name + ".pdf")
    plt.close(fig)


# --- Display-unit helpers ----------------------------------------------------
def signed(x, decimals=2):
    s = f"{x:+.{decimals}f}"
    return s.replace("-", "−")  # true minus sign


def ba_level(v, _=None):
    """0.245 -> '.245'"""
    return f"{v:.3f}".replace("0.", ".", 1)
