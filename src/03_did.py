"""Main difference-in-differences: TWFE and simple 2x2, clustered by franchise.

For each outcome Y in {BA, R/G, HR/G, log attendance per home game}, sample 1969-1976:
  TWFE: Y_it = b1 * AL_post + team FE (teamID) + year FE + e
  2x2:  Y_it = b0 + AL + post + b1 * AL_post + e
SEs clustered by franchID (24 clusters); inference uses t(G-1).

Outputs:
  output/tables/did_main.csv   long format: one row per outcome x specification
  output/tables/did_main.tex   formatted regression table

Run from the repo root: python src/03_did.py
"""
import pandas as pd
import statsmodels.formula.api as smf

PANEL = "data/processed/team_panel.csv"
TAB = "output/tables/"

OUTCOMES = {
    "BA": "BA",
    "R_per_G": "Runs/G",
    "HR_per_G": "HR/G",
    "log_att_per_home_game": "Log att./home G",
}
SPECS = {
    "TWFE": "{y} ~ AL_post + C(teamID) + C(yearID)",
    "2x2": "{y} ~ AL + post + AL_post",
}

df = pd.read_csv(PANEL)
df = df[df["main_sample"] == 1].reset_index(drop=True)
n_clusters = df["franchID"].nunique()


def fit(formula, data):
    return smf.ols(formula, data=data).fit(
        cov_type="cluster", cov_kwds={"groups": data["franchID"]}, use_t=True)


rows = []
for spec, template in SPECS.items():
    for y, label in OUTCOMES.items():
        res = fit(template.format(y=y), df)
        lo, hi = res.conf_int().loc["AL_post"]
        rows.append({
            "outcome": y, "label": label, "spec": spec,
            "coef": res.params["AL_post"], "se": res.bse["AL_post"],
            "t": res.tvalues["AL_post"], "p": res.pvalues["AL_post"],
            "ci_low": lo, "ci_high": hi,
            "N": int(res.nobs), "clusters": n_clusters, "r2": res.rsquared,
            "pre_mean_AL": df.loc[(df.AL == 1) & (df.post == 0), y].mean(),
        })
results = pd.DataFrame(rows)
results.to_csv(TAB + "did_main.csv", index=False, float_format="%.6f")


# --- LaTeX table: outcomes in columns, specs in row blocks -------------------
def stars(p):
    return "***" if p < 0.01 else "**" if p < 0.05 else "*" if p < 0.10 else ""


def fmt(x, y):
    # BA and HR/G need more decimals to be readable
    return f"{x:.4f}" if y in ("BA", "HR_per_G") else f"{x:.3f}"


cols = list(OUTCOMES)
lines = [
    r"\begin{table}[htbp]\centering",
    r"\caption{Effect of the designated hitter on AL teams, 1969--1976}",
    r"\label{tab:did_main}",
    r"\begin{tabular}{l" + "c" * len(cols) + "}",
    r"\hline\hline",
    " & " + " & ".join(f"({i + 1})" for i in range(len(cols))) + r" \\",
    " & " + " & ".join(OUTCOMES.values()) + r" \\",
    r"\hline",
]
for spec, title in [("TWFE", "Two-way fixed effects"), ("2x2", "Simple $2\\times2$ (no FE)")]:
    r = results[results.spec == spec].set_index("outcome").loc[cols]
    lines.append(r"\multicolumn{" + str(len(cols) + 1) + r"}{l}{\textit{" + title + r"}} \\")
    lines.append(r"AL $\times$ Post & " + " & ".join(
        fmt(r.loc[y, "coef"], y) + "$^{" + stars(r.loc[y, "p"]) + "}$" for y in cols) + r" \\")
    lines.append(" & " + " & ".join(f"({fmt(r.loc[y, 'se'], y)})" for y in cols) + r" \\")
    lines.append(r"$R^2$ & " + " & ".join(f"{r.loc[y, 'r2']:.3f}" for y in cols) + r" \\")
    lines.append(r"[0.5ex]")
r = results[results.spec == "TWFE"].set_index("outcome").loc[cols]
lines += [
    r"\hline",
    r"AL pre-period mean & " + " & ".join(fmt(r.loc[y, "pre_mean_AL"], y) for y in cols) + r" \\",
    r"Observations & " + " & ".join(str(r.loc[y, "N"]) for y in cols) + r" \\",
    r"Clusters (franchises) & " + " & ".join(str(n_clusters) for _ in cols) + r" \\",
    r"\hline\hline",
    r"\multicolumn{" + str(len(cols) + 1) + r"}{p{0.9\linewidth}}{\footnotesize "
    r"Notes: AL and NL teams, 1969--1976. Post = 1 from 1973. TWFE includes team (team-city) "
    r"and year fixed effects. Standard errors clustered by franchise in parentheses; "
    r"inference uses $t(G-1)$. * $p<0.10$, ** $p<0.05$, *** $p<0.01$.} \\",
    r"\end{tabular}",
    r"\end{table}",
]
with open(TAB + "did_main.tex", "w") as f:
    f.write("\n".join(lines) + "\n")

print(results[["label", "spec", "coef", "se", "p", "ci_low", "ci_high", "N"]]
      .to_string(index=False, float_format=lambda x: f"{x:.4f}"))
print("Saved", TAB + "did_main.csv", "and", TAB + "did_main.tex")
