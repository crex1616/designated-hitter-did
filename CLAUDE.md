# CLAUDE.md: DH difference-in-differences project

Notes for Claude sessions working in this repo. Read this file before you change anything.
The design below follows the user's written proposal. Do not change the window, outcomes, or specification without asking.

## Research question
Did the American League's adoption of the designated hitter (DH) in 1973 causally change
offensive output and attendance for AL teams?

## Identification strategy
- **Design:** difference-in-differences (DiD) with team and year fixed effects.
- **Treated:** AL teams. **Control:** NL teams. The NL had no DH until 2022.
- **Main window: 1969–1976.**
  - It starts in 1969 because the mound was lowered and the strike zone shrank that year, raising offense league-wide.
  - It ends in 1976 because the AL expanded in 1977 (Seattle and Toronto), which spread pitching across more teams and could affect offense on its own.
- **Pre-period:** 1969–1972. **Post-period:** 1973–1976.
- **Main sample:** 12 AL and 12 NL teams each year, so 24 × 8 = **192 team-seasons**. The panel is balanced, which `01_clean.py` checks.
- **Specification:** `Y_it = β0 + β1·(AL_i × Post_t) + α_i + γ_t + ε_it`. Here `α_i` is team FE, `γ_t` is year FE, and **β1 is the DiD estimate**. SEs are clustered by franchise. Also report the simple 2×2 (no FE) for comparison.
- **Event study:** AL × year dummies with 1972 omitted, plus team FE, year FE, and franchise-clustered SEs. That gives leads for 1969–1971 (3) and lags for 1973–1976 (4). There are only 3 leads, so the parallel-trends test has little power. Say so in every event-study output.
- **Proposal assumptions:**
  - *Parallel trends.*
  - *No anticipation:* the rule was adopted in January 1973, just before the season.
  - *No spillovers:* there was no interleague play until 1997.
- **Threats the proposal names:**
  - *Stadium openings or renovations* (see caveats).
  - *Mean reversion:* the AL adopted the DH because its offense lagged the NL's. If the AL's pre-1973 dip was temporary, β1 is biased upward. The event study is the check for this.

## Outcomes
These are rates, so seasons of different lengths (e.g., the 1972 strike) are comparable.

| Variable | Definition |
|---|---|
| `BA` | H / AB |
| `R_per_G` | R / G |
| `HR_per_G` | HR / G |
| `att_per_home_game` | attendance / Ghome (descriptive only) |
| `log_att_per_home_game` | ln(attendance / Ghome), the regression outcome for attendance |

**OBP is not an outcome.** HBP and SF are missing for every team in 1969, so OBP can't be computed for one of the window's years. The user decided to drop OBP entirely rather than shorten its sample. Do not construct it or add it back.

## Treatment, sample, and grouping variables
| Variable | Definition |
|---|---|
| `AL` | 1 if `lgID == "AL"` **in that season**, not based on franchise history |
| `post` | 1 if `yearID >= 1973` |
| `AL_post` | AL × post (the DiD term) |
| `main_sample` | 1 if 1969 ≤ `yearID` ≤ 1976 |
| `strike` | 1 if `yearID` in {1972, 1981, 1994, 1995, 2020} |
| `teamID` | **team FE unit** (team-city) |
| `franchID` | **cluster unit** (franchise) |

- Keep only `lgID in {"AL","NL"}`. The 2025 Lahman release also includes Negro Leagues and 19th-century leagues.
- `team_panel.csv` holds the **full AL/NL panel, 1969–2025**, so later extensions are possible. Analysis scripts filter on `main_sample == 1`. League is defined by season, which matters outside the window: the Brewers were AL through 1997 and NL from 1998; the Astros were NL through 2012 and AL from 2013.
- **Why team FE is at `teamID` and clusters at `franchID`:** two AL franchises moved during the pre-period. The Seattle Pilots (SE1, 1969) became Milwaukee (ML4) in 1970, and the Washington Senators (WS2, 1969–71) became Texas (TEX) in 1972. The proposal's FE are meant to absorb fixed team **and city** characteristics, so a relocation gets its own FE (26 FE units). SEs are clustered by franchise (**24 clusters**) so a franchise's errors can be correlated across its move. Because there are so few clusters, wild cluster bootstrap p-values should be reported.

## Data caveats (verified against data/raw/Teams.csv, Lahman 2025)
- The raw file starts with a **UTF-8 BOM**. Read it with `encoding="utf-8-sig"`.
- HBP and SF are missing for all teams in 1969 (the reason OBP was dropped). No other column used here has missing values in 1969–1976.
- **2020 attendance is recorded as 0** (no fans were admitted). `01_clean.py` sets it to NaN. It is outside the main window.
- **1972 is both a strike season** (G = 153–156) **and the event-study reference year.** Using rates handles the shorter season. If a robustness check drops 1972, it must re-anchor the event study (e.g., on 1971) and say so.
- **Ballpark changes inside the window** (from the `park` column):
  - NL, pre-period: CIN Riverfront (mid-1970), PIT Three Rivers (mid-1970), PHI Veterans Stadium (1971). These may raise NL attendance before treatment, which is a pre-trend risk for attendance.
  - AL, at treatment: KC Royals Stadium (1973), which coincides exactly with the DH.
  - AL, post: the Yankees played at Shea Stadium in 1974–75 during renovation and returned to the renovated Yankee Stadium in 1976.
  - Team FE do not absorb any of these. They are candidates for drop-one-team robustness checks.
- AL relocations are covered under "Treatment, sample, and grouping variables" above.

## Coding conventions
- Every script runs top to bottom **from the repo root**: `python src/0X_name.py`.
- Use relative paths only. No absolute paths.
- **`data/raw/` is read-only.** Never modify or re-save `data/raw/Teams.csv`.
- `01_clean.py` reads the raw file. All other scripts read `data/processed/team_panel.csv`.
- Every table goes to `output/tables/` (CSV, plus LaTeX for regression tables), and every figure goes to `output/figures/` (PNG). Nothing that matters is only printed to the console.
- Use one script per phase with no cross-imports between numbered scripts. The one shared module is `src/plot_style.py`.
- **Presentation figures** `fig1_trends` (02), `fig2_event_study` (04), and `fig3_robustness` (06) are graded on visualization quality and follow Schwabish-style rules:
  - Use `plot_style` for everything: the takeaway title, the subtitle, the "Source: SABR Lahman..." notes line, and saving at 300 dpi as PNG + PDF.
  - Colors keep one meaning: AL = blue, NL = gray, and in Figure 3 the standard estimate is strong blue with alternatives in muted blue.
  - Label lines and points directly; no legends.
  - Use plain-language labels; never show variable names or econometric jargon in visible text.
  - Display units only: batting average ×1000 as "points", log attendance as % via exp(b)−1.
  - **Every title claim must be checked against the saved outputs.** If the estimates change, re-check the titles.
  - Older figure versions live in `output/figures/archive/`. The `league_trends_gap_*` plots keep the older style.
- Regressions use statsmodels OLS with `C(teamID) + C(yearID)` dummies and `cov_type="cluster"` on `franchID`.
- After you write or edit a script, run it and fix any errors before moving on.
- **Never invent results.** Every number in README.md must come from a file in `output/`. Update the README "Results & caveats" section whenever the estimates change.

## How to run the pipeline
```bash
pip install -r requirements.txt
python src/01_clean.py         # -> data/processed/team_panel.csv
python src/02_eda.py
python src/03_did.py
python src/04_event_study.py
python src/05_robustness.py
python src/06_league_trends.py # reads output/tables/event_study.csv, so run after 04
python src/07_offense_window.py # Figure 1b: offensive trends, 1969-1976 only
```

## Project status
- [x] Phase 1: setup and data inspection
- [x] Phase 2: cleaning (`01_clean.py`)
- [x] Phase 3: descriptives (`02_eda.py`)
- [x] Phase 4: main DiD (`03_did.py`)
- [x] Phase 5: event study (`04_event_study.py`)
- [ ] Phase 6: robustness (`05_robustness.py`). Its check list was written for the old 1969–1996 window and needs to be revisited with the user.
- [x] Extra (user request): league-specific linear trends (`06_league_trends.py`). This script has three specs: baseline; `AL × (year − 1972)` fit over the full window; and the AL trend identified from 1969–72 only (post years saturated with AL × year dummies, effect = average post deviation, via `t_test`). The gap plots read the event-study points from `04`'s output, and their trend lines use the regression slopes anchored to those points.

## Findings so far that later work should keep in mind
- In 1972 the AL had a sharp, AL-only dip in BA, R/G, and HR/G (`output/tables/yearly_means.csv`). Since 1972 is the event-study reference year, the R/G and HR/G leads come out positive (joint pre-trend p = 0.09 and 0.11). This is the mean-reversion threat from the proposal. Robustness checks should include re-anchoring the event study (e.g., on 1971 or on the 1969–71 average) and dropping 1972.
- AL-specific linear trends come out negative for every outcome, mostly because of that 1972 dip, so trend adjustment *raises* the DiD estimates (e.g., R/G: 0.27 → 0.50 with the full-window trend → 0.71 with the pre-period trend). Present these as sensitivity checks, not as the preferred specification. They extrapolate the 1972 dip, which is the opposite of what the mean-reversion threat calls for.
