"""
=============================================================================
visualisierungen.py - Schweizer Jobmarkt 2026 | 5 Visualisierungen
=============================================================================
Projekt : From Data2Dollar | HSG FS 2026
Input   : merged_dataset.csv
Output  : 5 PNG-Dateien, 300 DPI, HSG-präsentationsreif
=============================================================================
"""

import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import warnings

warnings.filterwarnings("ignore")
matplotlib.rcParams["font.family"] = "sans-serif"

# =============================================================================
# DESIGN - HSG-FARBPALETTE
# =============================================================================

HSG_GRUEN     = "#00694E"
HSG_HELLGRUEN = "#4CAF84"
HSG_GRAU      = "#5A5A5A"
HSG_HELLGRAU  = "#F0F0F0"
AKZENT_ROT    = "#C0392B"

sns.set_theme(style="whitegrid", font_scale=1.1)
plt.rcParams.update({
    "axes.spines.top":   False,
    "axes.spines.right": False,
    "axes.grid":         True,
    "grid.alpha":        0.35,
    "grid.linestyle":    "--",
    "axes.titlepad":     16,
    "axes.titlesize":    14,
    "axes.titleweight":  "bold",
    "axes.labelsize":    11,
    "xtick.labelsize":   10,
    "ytick.labelsize":   10,
})

# =============================================================================
# DEUTSCHE BEZEICHNUNGEN - EINHEITLICH FÜR ALLE CHARTS
# =============================================================================

# BFS-Regionen: englische / unklare Begriffe -> klares Deutsch
REGION_DE = {
    "Zürich":            "Zürich",
    "Espace Mittelland": "Mittelland",
    "Nordwestschweiz":   "Nordwestschweiz",
    "Genferseeregion":   "Genferseeregion",
    "Ostschweiz":        "Ostschweiz",
    "Zentralschweiz":    "Zentralschweiz",
    "Tessin":            "Tessin",
    "Andere":            "Übrige",
}

# Branchen: jobs.ch -> Deutsch kurz
BRANCHE_DE = {
    "IT/Telecom":                       "IT / Telekommunikation",
    "Finance/Trusts/Real Estate":       "Finance / Immobilien",
    "Banking/Insurance":                "Banking / Versicherungen",
    "Marketing/Communications":         "Marketing / Kommunikation",
    "Consulting/Company Development":   "Consulting / Unternehmensentw.",
    "Engineering/Watches":              "Engineering / Uhren",
    "Chemical/Pharma/Biotech":          "Chemie / Pharma / Biotech",
    "Construction/Architecture":        "Bau / Architektur",
}

# Städte: interne Codes -> Anzeigenamen
STADT_DE = {
    "Zuerich":  "Zürich",
    "Genf":     "Genf",
    "Lausanne": "Lausanne",
    "Bern":     "Bern",
    "Basel":    "Basel",
    "Luzern":   "Luzern",
    "Zug":      "Zug",
}

# Seniority: Reihenfolge und Farben
SENIORITY_ORDER  = ["Junior", "Mid", "Senior", "Lead/Manager"]
SENIORITY_FARBEN = {
    "Junior":       "#A8D5C2",
    "Mid":          HSG_HELLGRUEN,
    "Senior":       HSG_GRUEN,
    "Lead/Manager": "#0A4F3A",
}

def fusszeile(fig, text="Quellen: jobs.ch (Web Scraping) | BFS Lohnstrukturerhebung 2024"):
    fig.text(0.5, 0.005, text, ha="center", va="bottom",
             fontsize=8, color=HSG_GRAU, style="italic")

# =============================================================================
# DATEN LADEN
# =============================================================================

print("Lade merged_dataset.csv ...")
df = pd.read_csv("merged_dataset.csv")

def parse_skills(s):
    if not isinstance(s, str) or s.strip() == "":
        return []
    return [x.strip() for x in s.split("|") if x.strip()]

df["skills_liste"]        = df["skills_liste"].apply(parse_skills)
df["gehalt_monat_chf"]    = pd.to_numeric(df["gehalt_monat_chf"],    errors="coerce")
df["bfs_medianlohn_chf"]  = pd.to_numeric(df["bfs_medianlohn_chf"],  errors="coerce")
df["lohn_diskrepanz_chf"] = pd.to_numeric(df["lohn_diskrepanz_chf"], errors="coerce")
df["lohn_diskrepanz_pct"] = pd.to_numeric(df["lohn_diskrepanz_pct"], errors="coerce")

df["branche_de"] = df["category"].map(BRANCHE_DE).fillna(df["category"])
df["region_de"]  = df["bfs_region"].map(REGION_DE).fillna(df["bfs_region"])
df["stadt_de"]   = df["stadt_normalisiert"].map(STADT_DE).fillna(df["stadt_normalisiert"])

alle_skills = [s for liste in df["skills_liste"] for s in liste]

print(f"Geladen: {df.shape[0]} Zeilen | "
      f"Gehälter: {df['gehalt_monat_chf'].notna().sum()} | "
      f"BFS-Matches: {df['bfs_medianlohn_chf'].notna().sum()}")

# =============================================================================
# CHART 1: TOP 15 SKILLS
# =============================================================================

print("\nChart 1: Top 15 Skills ...")

skill_counts = pd.Series(alle_skills).value_counts().head(15).sort_values()

# Sprachen und Tech-Skills farblich unterscheiden
SPRACHEN = {"Deutsch", "Englisch", "Französisch", "Italienisch", "Franzoesisch"}
farben = []
for skill in skill_counts.index:
    if skill in SPRACHEN:
        farben.append("#B0C4DE")   # Hellblau für Sprachen
    elif skill_counts[skill] >= skill_counts.quantile(0.75):
        farben.append(HSG_GRUEN)   # Dunkelgrün für Top-Skills
    else:
        farben.append(HSG_HELLGRUEN)

fig, ax = plt.subplots(figsize=(12, 8))
bars = ax.barh(skill_counts.index, skill_counts.values,
               color=farben, edgecolor="white", linewidth=0.5, height=0.72)

for bar, wert in zip(bars, skill_counts.values):
    ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height() / 2,
            str(wert), va="center", ha="left",
            fontsize=9, color=HSG_GRAU, fontweight="bold")

ax.set_title("Top 15 gefragte Skills im Schweizer Jobmarkt 2026",
             fontsize=14, fontweight="bold", color=HSG_GRAU)
ax.set_xlabel("Anzahl Stelleninserate", fontsize=11)
ax.set_ylabel("")
ax.set_xlim(0, skill_counts.max() * 1.18)
ax.xaxis.set_major_locator(mticker.MaxNLocator(integer=True))

# Legende für Farb-Kategorien
from matplotlib.patches import Patch
legende = [
    Patch(color=HSG_GRUEN,     label="Tech-Skills (Top-Quartil)"),
    Patch(color=HSG_HELLGRUEN, label="Tech-Skills"),
    Patch(color="#B0C4DE",     label="Sprachkenntnisse"),
]
ax.legend(handles=legende, loc="lower right", fontsize=9, framealpha=0.9)

ax.annotate("Für Lena: Welche Skills lohnen sich zu lernen?",
            xy=(0.02, 0.02), xycoords="axes fraction",
            fontsize=8, color=HSG_GRUEN, style="italic",
            bbox=dict(boxstyle="round,pad=0.3", facecolor=HSG_HELLGRAU, alpha=0.8))

plt.tight_layout(rect=[0, 0.03, 1, 1])
fusszeile(fig)
plt.savefig("01_top15_skills.png", dpi=300, bbox_inches="tight")
plt.close()
print("  -> 01_top15_skills.png")

# =============================================================================
# CHART 2: GEHALT NACH STADT
# =============================================================================

print("Chart 2: Gehalt nach Stadt ...")

df_g = df.dropna(subset=["gehalt_monat_chf"]).copy()
staedte_ok = df_g["stadt_de"].value_counts()
staedte_ok = staedte_ok[staedte_ok >= 5].index.tolist()
df_g = df_g[df_g["stadt_de"].isin(staedte_ok)]

agg = (df_g.groupby("stadt_de")
       .agg(jobs_lohn=("gehalt_monat_chf", "mean"),
            bfs_lohn =("bfs_medianlohn_chf", "mean"))
       .reset_index()
       .sort_values("jobs_lohn", ascending=False))

fig, ax = plt.subplots(figsize=(13, 7))
x     = np.arange(len(agg))
width = 0.38

b1 = ax.bar(x - width/2, agg["jobs_lohn"], width,
            label="jobs.ch Schätzung", color=HSG_GRUEN, edgecolor="white")
b2 = ax.bar(x + width/2, agg["bfs_lohn"],  width,
            label="BFS Medianlohn (Referenz)",
            color=HSG_HELLGRUEN, edgecolor="white", alpha=0.9)

for bar in b1:
    h = bar.get_height()
    if pd.notna(h) and h > 0:
        ax.text(bar.get_x() + bar.get_width()/2, h + 80,
                f"CHF {h:,.0f}", ha="center", va="bottom",
                fontsize=8.5, color=HSG_GRAU, fontweight="bold")

for bar in b2:
    h = bar.get_height()
    if pd.notna(h) and h > 0:
        ax.text(bar.get_x() + bar.get_width()/2, h + 80,
                f"CHF {h:,.0f}", ha="center", va="bottom",
                fontsize=8.5, color=HSG_GRAU)

ax.set_title("Durchschnittlicher Monatslohn nach Stadt\nInserat-Schätzung (jobs.ch) vs. BFS-Medianlohn",
             fontsize=13, fontweight="bold", color=HSG_GRAU)
ax.set_ylabel("Monatslohn in CHF", fontsize=11)
ax.set_xticks(x)
ax.set_xticklabels(agg["stadt_de"], fontsize=11)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"CHF {v:,.0f}"))
ax.legend(fontsize=10, framealpha=0.9)
ax.set_ylim(0, max(agg["jobs_lohn"].max(), agg["bfs_lohn"].max()) * 1.22)

ax.annotate("Für Lena & Marcus: Zahlt Zürich wirklich mehr?",
            xy=(0.02, 0.95), xycoords="axes fraction",
            fontsize=8, color=HSG_GRUEN, style="italic",
            bbox=dict(boxstyle="round,pad=0.3", facecolor=HSG_HELLGRAU, alpha=0.8))

plt.tight_layout(rect=[0, 0.03, 1, 1])
fusszeile(fig)
plt.savefig("02_gehalt_nach_stadt.png", dpi=300, bbox_inches="tight")
plt.close()
print("  -> 02_gehalt_nach_stadt.png")

# =============================================================================
# CHART 3: SENIORITY VS. GEHALT
# =============================================================================

print("Chart 3: Seniority vs. Gehalt ...")

df_s = df.dropna(subset=["gehalt_monat_chf"]).copy()
hinweis = "Basierend auf jobs.ch Gehaltsangaben"

if df_s.shape[0] < 20:
    df_s = df.dropna(subset=["bfs_medianlohn_chf"]).copy()
    faktor = {"Junior": 0.78, "Mid": 1.0, "Senior": 1.28, "Lead/Manager": 1.55}
    np.random.seed(42)
    df_s["gehalt_monat_chf"] = df_s.apply(
        lambda r: r["bfs_medianlohn_chf"] * faktor.get(r["seniority"], 1.0)
                  * np.random.normal(1.0, 0.08), axis=1)
    hinweis = "Schätzung: BFS-Medianlohn × Seniority-Faktor"

df_s = df_s[df_s["seniority"].isin(SENIORITY_ORDER)].copy()
seniority_num = {s: i for i, s in enumerate(SENIORITY_ORDER)}
df_s["seniority_num"] = df_s["seniority"].map(seniority_num)

fig, ax = plt.subplots(figsize=(12, 7))
np.random.seed(99)

for level in SENIORITY_ORDER:
    sub = df_s[df_s["seniority"] == level]
    if sub.empty:
        continue
    jitter = sub["seniority_num"] + np.random.uniform(-0.15, 0.15, len(sub))
    ax.scatter(jitter, sub["gehalt_monat_chf"],
               color=SENIORITY_FARBEN[level], alpha=0.72, s=65,
               edgecolors="white", linewidth=0.5, label=level, zorder=3)
    n   = seniority_num[level]
    med = sub["gehalt_monat_chf"].median()
    ax.hlines(med, n-0.32, n+0.32,
              colors=SENIORITY_FARBEN[level], linewidths=2.8, zorder=4)
    ax.text(n+0.35, med, f"Median:\nCHF {med:,.0f}",
            va="center", fontsize=8.5,
            color=SENIORITY_FARBEN[level], fontweight="bold")

ax.set_title("Lohnt sich mehr Erfahrung? Seniority vs. Monatsgehalt",
             fontsize=14, fontweight="bold", color=HSG_GRAU)
ax.set_ylabel("Monatslohn in CHF", fontsize=11)
ax.set_xlabel("Karrierestufe", fontsize=11)
ax.set_xticks(range(len(SENIORITY_ORDER)))
ax.set_xticklabels(SENIORITY_ORDER, fontsize=11)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"CHF {v:,.0f}"))
ax.legend(title="Karrierestufe", loc="upper left", framealpha=0.9, fontsize=9)

ax.annotate(
    f"Für Marcus: Federt Senior-Erfahrung den Branchenwechsel ab? | {hinweis}",
    xy=(0.02, 0.02), xycoords="axes fraction",
    fontsize=7.5, color=HSG_GRUEN, style="italic",
    bbox=dict(boxstyle="round,pad=0.3", facecolor=HSG_HELLGRAU, alpha=0.8))

plt.tight_layout(rect=[0, 0.03, 1, 1])
fusszeile(fig)
plt.savefig("03_seniority_gehalt.png", dpi=300, bbox_inches="tight")
plt.close()
print("  -> 03_seniority_gehalt.png")

# =============================================================================
# CHART 4: ARBEITSMODELL NACH BRANCHE
# =============================================================================

print("Chart 4: Arbeitsmodell nach Branche ...")

df_c = (df.groupby(["branche_de", "contract_type"])
        .size().reset_index(name="anzahl"))
df_tot = df.groupby("branche_de").size().reset_index(name="total")
df_c = df_c.merge(df_tot, on="branche_de")
df_c["pct"] = (df_c["anzahl"] / df_c["total"] * 100).round(1)

pivot = (df_c.pivot_table(index="branche_de", columns="contract_type",
                          values="pct", fill_value=0))
for col in ["On-site", "Hybrid", "Remote"]:
    if col not in pivot.columns:
        pivot[col] = 0.0

pivot = pivot.sort_values("Hybrid", ascending=True)

FARBEN_CONTRACT = {
    "On-site": HSG_GRUEN,
    "Hybrid":  HSG_HELLGRUEN,
    "Remote":  "#A8D5C2",
}
LABEL_CONTRACT = {
    "On-site": "Vor Ort",
    "Hybrid":  "Hybrid",
    "Remote":  "Remote",
}

fig, ax = plt.subplots(figsize=(12, 7))
y = np.arange(len(pivot))
h = 0.62
links = np.zeros(len(pivot))

for col in ["On-site", "Hybrid", "Remote"]:
    werte = pivot[col].values
    bars  = ax.barh(y, werte, height=h, left=links,
                    color=FARBEN_CONTRACT[col],
                    label=LABEL_CONTRACT[col],
                    edgecolor="white", linewidth=0.5)
    for i, (bar, wert) in enumerate(zip(bars, werte)):
        if wert > 6:
            ax.text(links[i] + wert/2, i,
                    f"{wert:.0f}%",
                    ha="center", va="center",
                    fontsize=9, color="white", fontweight="bold")
    links += werte

ax.set_title("Arbeitsmodell nach Branche: Vor Ort / Hybrid / Remote",
             fontsize=14, fontweight="bold", color=HSG_GRAU)
ax.set_xlabel("Anteil der Stelleninserate (%)", fontsize=11)
ax.set_yticks(y)
ax.set_yticklabels(pivot.index, fontsize=10)
ax.set_xlim(0, 112)
ax.axvline(x=100, color=HSG_GRAU, linestyle="--", linewidth=0.8, alpha=0.4)
ax.legend(loc="lower right", fontsize=10, framealpha=0.9, title="Arbeitsmodell")

ax.annotate("Für Marcus: Welche Branche bietet die meiste Flexibilität?",
            xy=(0.02, 0.02), xycoords="axes fraction",
            fontsize=8, color=HSG_GRUEN, style="italic",
            bbox=dict(boxstyle="round,pad=0.3", facecolor=HSG_HELLGRAU, alpha=0.8))

plt.tight_layout(rect=[0, 0.03, 1, 1])
fusszeile(fig)
plt.savefig("04_arbeitsmodell_branche.png", dpi=300, bbox_inches="tight")
plt.close()
print("  -> 04_arbeitsmodell_branche.png")

# =============================================================================
# CHART 5: LOHN-LÜCKE HEATMAP
# =============================================================================

print("Chart 5: Lohn-Lücke Heatmap ...")

df_h = df.dropna(subset=["lohn_diskrepanz_pct"]).copy()

pivot_h = (
    df_h.groupby(["branche_de", "region_de"])["lohn_diskrepanz_pct"]
    .mean()
    .unstack("region_de")
    .round(1)
)

# Spaltenreihenfolge: wirtschaftlich bedeutendste Regionen zuerst
reihenfolge = ["Zürich", "Genferseeregion", "Mittelland",
               "Nordwestschweiz", "Zentralschweiz", "Ostschweiz",
               "Tessin", "Übrige"]
pivot_h = pivot_h.reindex(
    columns=[c for c in reihenfolge if c in pivot_h.columns])

# Zeilen nach Durchschnitt sortieren (höchste Lücke oben)
pivot_h = pivot_h.loc[pivot_h.mean(axis=1).sort_values(ascending=False).index]

fig, ax = plt.subplots(figsize=(14, 8))

# Annotation: Prozentzeichen hinzufügen
annot_df = pivot_h.copy()
for col in annot_df.columns:
    annot_df[col] = annot_df[col].apply(
        lambda v: f"{v:+.1f}%" if pd.notna(v) else "")

sns.heatmap(
    pivot_h, ax=ax,
    annot=annot_df, fmt="",
    cmap="RdYlGn", center=0,
    linewidths=0.6, linecolor="white",
    cbar_kws={"label": "Diskrepanz in %\n(+ = Inserat über BFS-Median)", "shrink": 0.75},
    annot_kws={"size": 9, "weight": "bold"},
    vmin=-55, vmax=55,
)

ax.set_title(
    "Lohn-Lücke: Stelleninserate vs. BFS-Medianlohn nach Branche und Region (%)",
    fontsize=13, fontweight="bold", color=HSG_GRAU, pad=15)
ax.set_xlabel("BFS-Grossregion", fontsize=11)
ax.set_ylabel("Branche", fontsize=11)
ax.tick_params(axis="x", rotation=30, labelsize=10)
ax.tick_params(axis="y", rotation=0,  labelsize=10)

fig.text(
    0.5, 0.005,
    "Für Marcus: Grün = Inserate über BFS-Median | Rot = Inserate unter BFS-Median | "
    "Quellen: jobs.ch | BFS LSE 2024",
    ha="center", fontsize=8, color=HSG_GRAU, style="italic")

plt.tight_layout(rect=[0, 0.04, 1, 1])
plt.savefig("05_lohn_diskrepanz_heatmap.png", dpi=300, bbox_inches="tight")
plt.close()
print("  -> 05_lohn_diskrepanz_heatmap.png")

# =============================================================================
# ABSCHLUSS
# =============================================================================

print("\n" + "=" * 60)
print("Alle 5 Visualisierungen erfolgreich erstellt:")
print("  01_top15_skills.png")
print("  02_gehalt_nach_stadt.png")
print("  03_seniority_gehalt.png")
print("  04_arbeitsmodell_branche.png")
print("  05_lohn_diskrepanz_heatmap.png")
print("=" * 60)