# The Designated Hitter and AL Offense and Attendance: A Difference-in-Differences Study

## Start here (for collaborators)
A quick way to get up to speed:

1. **Read this README top to bottom.** It covers the design, the data, and the results so far.
2. **Look at the three presentation figures** in `output/figures/`:
   - `fig1_trends.png`: AL vs. NL averages over time (`fig1b_offense_window.png` zooms in on 1969–1976)
   - `fig2_event_study.png`: the year-by-year AL–NL difference relative to 1972
   - `fig3_robustness.png`: the DH effect with and without league-specific trend adjustments
3. **Check the main numbers** in `output/tables/did_main.csv` and `output/tables/event_study_pretrends.csv`.
4. **Read [`CLAUDE.md`](CLAUDE.md)** for the full project notes: design decisions (and why they were made), data caveats, coding conventions, and project status.
5. **Reproduce everything** with the commands under [Installation and running](#installation-and-running). The whole pipeline takes about a minute, and every output is already committed, so you can browse results without running anything.

**Where things stand**

| Phase | Script | Status |
|---|---|---|
| Data cleaning | `src/01_clean.py` | Done |
| Descriptives and Figure 1 | `src/02_eda.py`, `src/07_offense_window.py` | Done |
| Main DiD | `src/03_did.py` | Done |
| Event study and Figure 2 | `src/04_event_study.py` | Done |
| League-specific trends and Figure 3 | `src/06_league_trends.py` | Done |
| Robustness checks | `src/05_robustness.py` | **Not started.** The check list still needs to be agreed on. |

**Next up (robustness):** wild cluster bootstrap p-values (only 24 clusters), re-anchoring the event study on 1971 or on the 1969–71 average, dropping the 1972 strike season, and drop-one-team checks for the ballpark changes listed in `CLAUDE.md`.

## Summary
In 1973 the American League adopted the designated hitter (DH), which lets a full-time hitter bat in place of the pitcher. The National League kept pitchers batting until 2022. This project uses that split to estimate how the DH affected AL teams' batting average, runs per game, home runs per game, and attendance per home game.

The design is a difference-in-differences comparison of AL teams (treated) with NL teams (control), using team and year fixed effects:

$$Y_{it} = \beta_0 + \beta_1 (AL_i \times Post_t) + \alpha_i + \gamma_t + \varepsilon_{it}$$

- **Window:** 1969–1976.
  - It starts in 1969, when MLB lowered the mound and shrank the strike zone.
  - It ends in 1976, because the AL expanded in 1977 and spread its pitching across more teams.
- **Pre-period:** 1969–1972. **Post-period:** 1973–1976.
- **Sample:** 12 AL and 12 NL teams each season, for **192 team-seasons**.
- **Outcomes:** all rates, so the strike-shortened 1972 season is comparable to the others.
- **Standard errors:** clustered by franchise (24 clusters).
- **Event study:** checks the parallel-trends assumption and the risk of mean reversion.

## Data
Team-season statistics come from the **Lahman Baseball Database** (`Teams.csv`), maintained by the Society for American Baseball Research (SABR).

> Lahman, S. (2025). *Lahman Baseball Database*, 2025 version. Society for American Baseball Research. https://sabr.org/lahman-database/

The raw file is stored unmodified in `data/raw/Teams.csv`. The cleaned panel covers all AL and NL teams from 1969 to 2025 and marks the 1969–1976 analysis sample.

Notes on the data:
- **OBP is not analyzed.** Hit-by-pitch and sacrifice flies are missing for every team in 1969, so OBP can't be computed for one year of the window.
- **Team fixed effects are at the team-city level.** The Seattle Pilots became the Milwaukee Brewers in 1970, and the Washington Senators became the Texas Rangers in 1972. Each city gets its own fixed effect, and standard errors are still clustered by franchise.

## Installation and running
Requires Python 3.10+.

```bash
pip install -r requirements.txt
```

Clone the repository, then run the scripts in order from the repository root:

```bash
git clone https://github.com/crex1616/designated-hitter-did.git
cd designated-hitter-did
```

```bash
python src/01_clean.py
python src/02_eda.py
python src/03_did.py
python src/04_event_study.py
python src/05_robustness.py   # not yet written
python src/06_league_trends.py   # needs output/tables/event_study.csv from 04 for its gap plots
python src/07_offense_window.py
```

## Repository layout
```
data/
  raw/               Teams.csv (original Lahman file; never modified)
  processed/         team_panel.csv (cleaned panel, built by 01_clean.py)
src/
  01_clean.py        filter leagues, construct outcomes and treatment variables
  02_eda.py          summary statistics and AL vs. NL trend plots
  03_did.py          main DiD regressions (TWFE and simple 2x2)
  04_event_study.py  year-by-year AL-NL differences relative to 1972
  05_robustness.py   robustness checks (to come)
  06_league_trends.py  DiD with AL-specific linear trends
  07_offense_window.py AL vs. NL offensive trends zoomed to 1969-1976 (Figure 1b)
  plot_style.py      shared style for Figures 1-3 (imported by 02, 04, 06)
output/
  figures/           all plots (PNG)
  tables/            all tables (CSV and LaTeX)
CLAUDE.md            detailed project notes and conventions
requirements.txt     Python dependencies
```

## Outputs
| Output | Description |
|---|---|
| `data/processed/team_panel.csv` | Cleaned team-season panel: outcomes, treatment indicators, sample and strike flags |
| `output/tables/summary_by_league_period.{csv,tex}` | Mean, SD, and N of each outcome by league and period |
| `output/tables/yearly_means.csv` | Yearly AL and NL means (the data behind the trend plots) |
| `output/tables/fig1_trends_data.csv` | Yearly AL and NL averages, 1969–1996 (the data behind Figure 1) |
| `output/figures/fig1_trends.{png,pdf}` | **Figure 1.** AL vs. NL yearly averages, 1969–1996, with the 1973 DH line and strike seasons shaded |
| `output/tables/offense_window_data.csv` | Yearly AL and NL batting average, runs/game, HR/game and AL−NL gaps, 1969–1976 (the data behind Figure 1b) |
| `output/figures/fig1b_offense_window.{png,pdf}` | **Figure 1b.** AL vs. NL batting average, runs per game, and home runs per game, 1969–1976 only |
| `output/figures/fig1b_offense_window_{BA,R_per_G,HR_per_G}.{png,pdf}` | Figure 1b split into one figure per offensive statistic |
| `output/tables/did_main.{csv,tex}` | Main DiD estimates (TWFE and 2×2) for each outcome |
| `output/tables/event_study.csv` | Event-study coefficients, SEs, and 95% CIs by year |
| `output/tables/event_study_pretrends.csv` | Joint test that the three pre-period coefficients are zero |
| `output/figures/fig2_event_study.{png,pdf}` | **Figure 2.** Year-by-year AL–NL difference relative to 1972, with 95% intervals (batting in points, attendance in %) |
| `output/tables/league_trends.{csv,tex}` | DiD estimates with no trend, an AL trend fit on 1969–76, and an AL trend fit on 1969–72 only |
| `output/figures/fig3_robustness.{png,pdf}` | **Figure 3.** The DH effect under the standard estimate and the two trend adjustments, for each outcome |
| `output/figures/archive/` | Earlier versions of Figures 1–3, kept for reference |
| `output/figures/league_trends_gap_all.png`, `league_trends_gap_<outcome>.png` | The AL–NL gap by year with each fitted trend line, showing where the trend-adjusted estimates come from |

## Results & caveats
*All numbers below come from `output/tables/did_main.csv` and `output/tables/event_study_pretrends.csv`. The robustness checks, including wild cluster bootstrap p-values, are not done yet.*

**Main DiD estimates (β1 on AL × Post).** Standard errors are clustered by franchise, 24 clusters, N = 192.

| Outcome | TWFE β1 (SE) | p | 2×2 β1 (SE) | p | AL pre-period mean | Pre-trend test p |
|---|---|---|---|---|---|---|
| Batting average | 0.0090 (0.0035) | 0.018 | 0.0091 (0.0032) | 0.009 | 0.2453 | 0.77 |
| Runs per game | 0.274 (0.151) | 0.082 | 0.267 (0.132) | 0.054 | 3.898 | 0.09 |
| HR per game | 0.0275 (0.0531) | 0.61 | 0.0239 (0.0460) | 0.61 | 0.786 | 0.11 |
| Log attendance per home game | 0.132 (0.146) | 0.38 | 0.140 (0.133) | 0.30 | — | 0.36 |

**Interpretation, with caveats:**
- **Batting average** rises by about 9 points (0.009) relative to the NL. This is the only estimate significant at 5%, and its event-study leads are flat (joint p = 0.77).
- **Runs per game** rise by about 0.27, but this is only marginally significant. The event-study leads for 1969 and 1971 are positive and about as large as the post-period coefficients (`event_study.csv`), and the joint pre-trend test gives p = 0.09.
  - That pattern comes from a sharp AL-only dip in 1972. AL runs per game fell to 3.47 while the NL stayed at 3.91 (`yearly_means.csv`).
  - Because 1972 is the event-study reference year and the year just before treatment, part of the runs estimate may be the mean reversion the proposal warns about rather than a DH effect.
- **Home runs per game** and **attendance** show no statistically detectable effect.
  - Several NL teams opened new stadiums in 1970–71 (Cincinnati, Pittsburgh, Philadelphia), and Kansas City opened Royals Stadium in 1973, the same year as treatment.
  - The team fixed effects absorb none of these.

**League-specific linear trends** (from `output/tables/league_trends.csv`). These are DiD estimates with clustered SEs. The "AL pre-trend" column is the average 1973–76 departure from an AL trend fit on 1969–72 only.

| Outcome | Baseline | + AL trend (1969–76) | + AL pre-trend (1969–72) | AL pre-trend slope per year (p) |
|---|---|---|---|---|
| Batting average | 0.0090 (0.0035) | 0.0143 (0.0054) | 0.0140 (0.0092) | −0.0013 (0.55) |
| Runs per game | 0.274 (0.151) | 0.500 (0.191) | 0.705 (0.289) | −0.109 (0.11) |
| HR per game | 0.0275 (0.0531) | 0.1147 (0.0660) | 0.2471 (0.1060) | −0.0556 (0.052) |
| Log attendance per home game | 0.132 (0.146) | 0.134 (0.091) | 0.329 (0.203) | −0.050 (0.42) |

- **Adding an AL trend makes every offensive estimate larger, not smaller.** For example, runs per game rises from 0.27 to 0.50 to 0.71.
  - The estimated AL trend before 1973 slopes downward for every outcome.
  - Projecting that decline forward makes the post-1973 AL numbers look even better by comparison (`league_trends_gap_all.png`).
- **This doesn't settle the mean-reversion concern; it sharpens it.**
  - The downward AL pre-trend comes mostly from the AL-only slump in 1972.
  - A linear trend treats that slump as a lasting decline. If it was instead a temporary dip, the trend-adjusted estimates overstate the DH effect, and so, to a lesser degree, does the baseline.
  - The trend-adjusted results are best read as a sensitivity check, not as preferred estimates.
- **The trend-adjusted estimates are less precise.** Fitting a slope to four pre-period years is noisy. With the pre-trend adjustment, batting average is no longer significant (p = 0.14), while runs per game (p = 0.023) and HR per game (p = 0.029) are.
- With only three pre-period years, the parallel-trends tests have little power. With 24 clusters, conventional clustered standard errors may be too small. Wild cluster bootstrap p-values are planned for the robustness stage.
