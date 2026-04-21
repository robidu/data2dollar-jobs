"""
=============================================================================
visualisierungen.py - Schweizer Jobmarkt 2026 | 5 Visualisierungen
=============================================================================
Projekt      : From Data2Dollar | HSG FS 2026
Autor        : Robin D.
Input        : merged_dataset.csv
Output       : 5 PNG-Dateien, 300 DPI, HSG-praesentationsreif

-----------------------------------------------------------------------------
KI-DEKLARATION (vgl. KI_DEKLARATION.md)
-----------------------------------------------------------------------------
# HUMAN          = Konzept, Design und Storytelling vom Autor
# KI-ASSISTIERT  = iterativ mit Claude/Copilot entwickelt
# VIBE-CODED     = primaer von KI, vom Autor verstanden und getestet
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
# HUMAN: Farbpalette komplett vom Autor. HSG-Gruen als Primaerfarbe
# (offizielles CI der Universitaet St. Gallen), plus Akzentfarben.

HSG_GRUEN     = "#00694E"
HSG_HELLGRUEN = "#4CAF84"
HSG_GRAU      = "#5A5A5A"
HSG_HELLGRAU  = "#F0F0F0"
AKZENT_ROT    = "#C0392B"

# KI-ASSISTIERT: rcParams-Konfiguration von Claude empfohlen fuer saubere Grafik-Defaults
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
# DEUTSCHE BEZEICHNUNGEN - EINHEITLICH FUER ALLE CHARTS
# =============================================================================
# HUMAN: Alle Uebersetzungen / Mappings vom Autor definiert.
# Ziel: Konsistente deutsche Begriffe in allen Charts fuer CH-Publikum.

# HUMAN: BFS-Regionen Normalisierung
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

# HUMAN: Branchen ins Deutsche - gewaehlt so dass sie in Chart-Achsen passen
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

# HUMAN: Staedtenamen - interne ASCII-Codes aus cleaning.py zurueck zu Umlauten
STADT_DE = {
    "Zuerich":  "Zürich",
    "Genf":     "Genf",
    "Lausanne": "Lausanne",
    "Bern":     "Bern",
    "Basel":    "Basel",
    "Luzern":   "Luzern",
    "Zug":      "Zug",
}

# HUMAN: Seniority-Farben - Gradient von hell (Junior) zu dunkel (Lead).
# Semantik: Mehr Erfahrung = dunkleres HSG-Gruen.
SENIORITY_ORDER  = ["Junior", "Mid", "Senior", "Lead/Manager"]
SENIORITY_FARBEN = {
    "Junior":       "#A8D5C2",
    "Mid":          HSG_HELLGRUEN,
    "Senior":       HSG_GRUEN,
    "Lead/Manager": "#0A4F3A",
}

def fusszeile(fig, text="Quellen: jobs.ch (Web Scraping) | BFS Lohnstrukturerhebung 2024"):
    """HUMAN: Hilfsfunktion fuer einheitliche Quellen-Fusszeile in allen Charts."""
    fig.text(0.5, 0.005, text, ha="center", va="bottom",
             fontsize=8, color=HSG_GRAU, style="italic")

# =============================================================================
# DATEN LADEN
# =============================================================================
# HUMAN: Standard-Dateneinlese

print("Lade merged_dataset.csv ...")
df = pd.read_csv("merged_dataset.csv")

def parse_skills(s):
    """HUMAN: Umgekehrte Operation zu cleaning.py - String wieder in Liste zerlegen."""
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
# HUMAN: Chart-Konzept vom Autor - horizontaler Barplot weil Skill-Namen
# lang sind und vertikal abgeschnitten wuerden. Farbkodierung unterscheidet
# Top-Quartil (HSG-Dunkelgruen), Standard-Tech (Hellgruen) und Sprachen (Hellblau)
# damit visuell sofort erkennbar ist welche Skills technisch vs. linguistisch sind.

print("\nChart 1: Top 15 Skills ...")

skill_counts = pd.Series(alle_skills).value_counts().head(15).sort_values()

# HUMAN: Sprachen-Set explizit definiert fuer Farbkodierung
SPRACHEN = {"Deutsch", "Englisch", "Französisch", "Italienisch", "Franzoesisch"}
farben = []
for skill in skill_counts.index:
    if skill in SPRACHEN:
        farben.append("#B0C4DE")   # Hellblau fuer Sprachen
    elif skill_counts[skill] >= skill_counts.quantile(0.75):
        farben.append(HSG_GRUEN)   # Dunkelgruen fuer Top-Skills
    else:
        farben.append(HSG_HELLGRUEN)

fig, ax = plt.subplots(figsize=(12, 8))
bars = ax.barh(skill_counts.index, skill_counts.values,
               color=farben, edgecolor="white", linewidth=0.5, height=0.72)

# KI-ASSISTIERT: Zahlen am Bar-Ende als Label - gaengiges Matplotlib-Pattern
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

# HUMAN: Legende definiert fuer die drei Farb-Kategorien
from matplotlib.patches import Patch
legende = [
    Patch(color=HSG_GRUEN,     label="Tech-Skills (Top-Quartil)"),
    Patch(color=HSG_HELLGRUEN, label="Tech-Skills"),
    Patch(color="#B0C4DE",     label="Sprachkenntnisse"),
]
ax.legend(handles=legende, loc="lower right", fontsize=9, framealpha=0.9)

# HUMAN: Persona-Annotation - Brueckenschlag zu Lena als Storytelling-Element
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
# HUMAN: Chart-Konzept vom Autor - gruppierter Barplot um jobs.ch-Angaben mit
# BFS-Referenzwert zu vergleichen. Zeigt direkt: "Wo zahlen Arbeitgeber ueber
# oder unter Benchmark?" Filter >= 5 Jobs/Stadt damit keine Einzel-Ausreisser
# die Analyse verfaelschen.

print("Chart 2: Gehalt nach Stadt ...")

df_g = df.dropna(subset=["gehalt_monat_chf"]).copy()
# HUMAN: Verschaerfte Mindest-Jobs pro Stadt = 15 (statt 5).
# Grund: Bei n<15 entstehen zufaellige Ausreisser die den Stadtvergleich verzerren.
# Agglomerationen werden bereits in cleaning.py zusammengefasst (Rotkreuz->Zug,
# Burgdorf->Bern, Egerkingen->Solothurn, Montreux->Genferseeregion) damit wir
# aussagekraeftige Fallzahlen haben.
MIN_N_STADT = 15
staedte_ok = df_g["stadt_de"].value_counts()
staedte_ok = staedte_ok[staedte_ok >= MIN_N_STADT].index.tolist()
df_g = df_g[df_g["stadt_de"].isin(staedte_ok)]

agg = (df_g.groupby("stadt_de")
       .agg(jobs_lohn=("gehalt_monat_chf", "mean"),
            bfs_lohn =("bfs_medianlohn_chf", "mean"),
            n        =("gehalt_monat_chf", "count"))
       .reset_index()
       .sort_values("jobs_lohn", ascending=False)
       .head(8))

fig, ax = plt.subplots(figsize=(13, 7))
# KI-ASSISTIERT: Dual-Bar-Muster mit x +/- width/2 - Standard Matplotlib-Trick
x     = np.arange(len(agg))
width = 0.38

b1 = ax.bar(x - width/2, agg["jobs_lohn"], width,
            label="jobs.ch Schätzung", color=HSG_GRUEN, edgecolor="white")
b2 = ax.bar(x + width/2, agg["bfs_lohn"],  width,
            label="BFS Medianlohn (Referenz)",
            color=HSG_HELLGRUEN, edgecolor="white", alpha=0.9)

# KI-ASSISTIERT: Bar-Labels mit CHF-Formatierung
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
                fontsize=8.5, color=HSG_GRAU, fontweight="bold")

ax.set_title(f"Gehaltsvergleich nach Stadt: jobs.ch vs. BFS-Medianlohn  (min n={MIN_N_STADT} pro Stadt)",
             fontsize=13, fontweight="bold", color=HSG_GRAU)
ax.set_xlabel("Stadt", fontsize=11)
ax.set_ylabel("Monatslohn in CHF", fontsize=11)
ax.set_xticks(x)
# HUMAN: Stichprobengroesse unter Stadtnamen, damit Lesbarkeit klar bleibt
xlabels = [f"{s}\n(n={int(n)})" for s, n in zip(agg["stadt_de"], agg["n"])]
ax.set_xticklabels(xlabels, rotation=0, fontsize=10)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"CHF {v:,.0f}"))
ax.legend(loc="upper right", framealpha=0.9, fontsize=10)
ax.set_ylim(0, max(agg["jobs_lohn"].max(), agg["bfs_lohn"].max()) * 1.22)

# HUMAN: Persona-Annotation fuer Lena (oben links damit keine Ueberlappung)
ax.annotate("Für Lena: Wo kann sie als Einsteigerin am meisten verdienen?",
            xy=(0.02, 0.92), xycoords="axes fraction",
            fontsize=8, color=HSG_GRUEN, style="italic",
            bbox=dict(boxstyle="round,pad=0.3", facecolor=HSG_HELLGRAU, alpha=0.8))

plt.tight_layout(rect=[0, 0.03, 1, 1])
fusszeile(fig)
plt.savefig("02_gehalt_nach_stadt.png", dpi=300, bbox_inches="tight")
plt.close()
print("  -> 02_gehalt_nach_stadt.png")

# =============================================================================
# CHART 3: SENIORITY VS. GEHALT (NUR HOCHLOHN-BRANCHEN)
# =============================================================================
# HUMAN: Chart komplett ueberarbeitet. Problem im v1: Ueber alle 18 Branchen
# gemischt zeigte "Mid" (CHF 6684) weniger als "Junior" (CHF 7416) - das ist
# kontraintuitiv und ein Artefakt der Branchen-Mischung.
# Hintergrund: "Mid" ist Default-Kategorie wenn kein Seniority-Keyword gefunden
# wurde. Viele Tieflohn-Jobs (Gastgewerbe, Detailhandel) fallen in "Mid" und
# druecken den Median nach unten. Junior-Jobs kommen hingegen ueberproportional
# aus Tech/Finance wo Eintrittsloehne bereits hoch sind.
#
# Loesung: Analyse beschraenken auf Hochlohn-Branchen. Dort ist Seniority
# tatsaechlich der dominante Gehaltstreiber, nicht die Branche.

print("Chart 3: Seniority vs. Gehalt (Hochlohn-Branchen) ...")

df_s = df.dropna(subset=["gehalt_monat_chf"]).copy()

# HUMAN: Filter auf Hochlohn-Branchen - nur dort ist Seniority-Progression klar
df_s = df_s[df_s["lohnkategorie"] == "Hochlohn"].copy()
df_s = df_s[df_s["seniority"].isin(SENIORITY_ORDER)].copy()

# HUMAN: Mindest-Fallzahl pro Stufe = 10 (statt 5).
# Grund: Bei n<10 ist Median zu anfaellig fuer Einzel-Ausreisser.
# Junior in Hochlohn-Branchen hat oft nur 5 Datenpunkte, das reicht nicht
# fuer einen belastbaren Medianvergleich.
n_pro_stufe = df_s["seniority"].value_counts()
ausreichend = n_pro_stufe[n_pro_stufe >= 10].index.tolist()
df_s = df_s[df_s["seniority"].isin(ausreichend)].copy()

seniority_num = {s: i for i, s in enumerate(SENIORITY_ORDER) if s in ausreichend}
df_s["seniority_num"] = df_s["seniority"].map(seniority_num)

fig, ax = plt.subplots(figsize=(12, 7))
np.random.seed(99)

# KI-ASSISTIERT: Jitter-Scatter + Median-Linie - Standard-Pattern fuer kategorielle Daten
for level in [s for s in SENIORITY_ORDER if s in seniority_num]:
    sub = df_s[df_s["seniority"] == level]
    if sub.empty:
        continue
    jitter = sub["seniority_num"] + np.random.uniform(-0.18, 0.18, len(sub))
    ax.scatter(jitter, sub["gehalt_monat_chf"],
               color=SENIORITY_FARBEN[level], alpha=0.6, s=55,
               edgecolors="white", linewidth=0.4, label=level, zorder=3)
    # HUMAN: Median-Bar pro Stufe als zentrale Insight-Linie
    n   = seniority_num[level]
    med = sub["gehalt_monat_chf"].median()
    ax.hlines(med, n-0.32, n+0.32,
              colors=SENIORITY_FARBEN[level], linewidths=3, zorder=4)
    ax.text(n+0.36, med, f"Median:\nCHF {med:,.0f}\n(n={len(sub)})",
            va="center", fontsize=9,
            color=SENIORITY_FARBEN[level], fontweight="bold")

ax.set_title("Lohnt sich mehr Erfahrung? Seniority vs. Monatsgehalt\n"
             "(nur Hochlohn-Branchen: Banken, IT, Pharma, Consulting, Versicherungen, Medtech)",
             fontsize=12, fontweight="bold", color=HSG_GRAU)
ax.set_ylabel("Monatslohn in CHF", fontsize=11)
ax.set_xlabel("Karrierestufe", fontsize=11)
ax.set_xticks(list(seniority_num.values()))
ax.set_xticklabels(list(seniority_num.keys()), fontsize=11)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"CHF {v:,.0f}"))
ax.legend(title="Karrierestufe", loc="upper left", framealpha=0.9, fontsize=9)

# HUMAN: Persona-Annotation fuer Marcus + Methoden-Hinweis
ax.annotate(
    "Für Marcus: Federt Senior-Erfahrung den Branchenwechsel ab?\n"
    "Hinweis: 'Mid' = Default-Kategorie für Jobs ohne Seniority-Keyword | Stufen mit n<10 ausgeschlossen",
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
# HUMAN: Chart-Konzept vom Autor - 100% stacked horizontal bar zeigt
# Anteile (nicht Absolutzahlen) und ermoeglicht direkten Branchenvergleich.
# Sortierung nach Hybrid-Anteil aufsteigend = welche Branchen sind am flexibelsten

print("Chart 4: Arbeitsmodell nach Branche ...")

df_c = (df.groupby(["branche_de", "contract_type"])
        .size().reset_index(name="anzahl"))
df_tot = df.groupby("branche_de").size().reset_index(name="total")
df_c = df_c.merge(df_tot, on="branche_de")
df_c["pct"] = (df_c["anzahl"] / df_c["total"] * 100).round(1)

# KI-ASSISTIERT: Pivot-Table mit fill_value fuer fehlende Kategorien
pivot = (df_c.pivot_table(index="branche_de", columns="contract_type",
                          values="pct", fill_value=0))
for col in ["On-site", "Hybrid", "Remote"]:
    if col not in pivot.columns:
        pivot[col] = 0.0

pivot = pivot.sort_values("Hybrid", ascending=True)

# HUMAN: Farb-Semantik: HSG-Gruen fuer On-site (traditionell), hellgruen fuer
# Hybrid (mittlerer Weg), sehr hell fuer Remote (modern/flexibel)
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

# VIBE-CODED: Stacked-Bar-Implementierung mit kumulativem 'links'-Offset.
# Standard-Pattern fuer horizontale Stacked-Bars in matplotlib, von Claude
# erklaert - jede neue Farb-Schicht startet links am Ende der vorherigen.
for col in ["On-site", "Hybrid", "Remote"]:
    werte = pivot[col].values
    bars  = ax.barh(y, werte, height=h, left=links,
                    color=FARBEN_CONTRACT[col],
                    label=LABEL_CONTRACT[col],
                    edgecolor="white", linewidth=0.5)
    # KI-ASSISTIERT: Labels nur bei Segmenten > 6% um Ueberlappung zu vermeiden
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

# HUMAN: Persona-Annotation fuer Marcus (Familienvater, Flexibilitaet wichtig)
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
# CHART 5: LOHN-LUECKE HEATMAP
# =============================================================================
# HUMAN: Chart-Konzept vom Autor - Heatmap als "Big Picture" Chart zum Abschluss.
# Zeigt alle 5 Forschungsfragen auf einem Bild: welche Branchen / Regionen
# zahlen mehr oder weniger als BFS-Benchmark. Diverging Colormap (RdYlGn)
# mit Zentrum bei 0 zeigt sofort positive / negative Abweichungen.

print("Chart 5: Lohn-Lücke Heatmap ...")

df_h = df.dropna(subset=["lohn_diskrepanz_pct"]).copy()

# HUMAN: Mindestanzahl Datenpunkte pro Zelle (Branche x Region).
# Vorher: Zellen mit n=1 (z.B. 1 Apprenti-Job in Genferseeregion) produzierten
# statistische Ausreisser wie +249% die die ganze Heatmap unglaubwuerdig machten.
# Jetzt: Zellen mit n<3 werden leer gelassen.
MIN_N_ZELLE = 3

# HUMAN: Gruppierung mit Mean + Count, dann Filter auf min n=3
gruppen = df_h.groupby(["branche_de", "region_de"]).agg(
    mittel=("lohn_diskrepanz_pct", "mean"),
    anzahl=("lohn_diskrepanz_pct", "count")
).reset_index()
gruppen_gefiltert = gruppen[gruppen["anzahl"] >= MIN_N_ZELLE]

# KI-ASSISTIERT: Pivot mit dem gefilterten DataFrame
pivot_h = (gruppen_gefiltert
           .pivot_table(index="branche_de", columns="region_de", values="mittel")
           .round(1))

# HUMAN: Spalten-Reihenfolge bewusst nach wirtschaftlicher Bedeutung gewaehlt
reihenfolge = ["Zürich", "Genferseeregion", "Mittelland",
               "Nordwestschweiz", "Zentralschweiz", "Ostschweiz",
               "Tessin", "Übrige"]
pivot_h = pivot_h.reindex(columns=[c for c in reihenfolge if c in pivot_h.columns])

# HUMAN: Zeilen nach Lohnkategorie gruppieren (Hochlohn oben, Tieflohn unten)
lohnkat_map = df.drop_duplicates("category").set_index("category")["lohnkategorie"].to_dict()
branche_to_kat = df.drop_duplicates("branche_de").set_index("branche_de")["lohnkategorie"].to_dict()

lohnkat_order = []
for kat in ["Hochlohn", "Mittellohn", "Tieflohn", "Andere"]:
    for b in pivot_h.index:
        if branche_to_kat.get(b, "Andere") == kat and b not in lohnkat_order:
            lohnkat_order.append(b)
pivot_h = pivot_h.reindex([b for b in lohnkat_order if b in pivot_h.index])

# HUMAN: n-Anzahl-Matrix fuer Annotations (zeigt Fallzahl pro Zelle)
n_matrix = (gruppen_gefiltert
            .pivot_table(index="branche_de", columns="region_de", values="anzahl")
            .reindex(index=pivot_h.index, columns=pivot_h.columns))

fig, ax = plt.subplots(figsize=(15, 10))

# VIBE-CODED: Annotation-Override-Trick. Seaborn heatmap zeigt standardmaessig
# nur Zahlen. Ich wollte aber "+12.5%\n(n=7)" Format mit Vorzeichen und Fallzahl.
# Loesung: zweiten DataFrame mit String-Werten bauen und als annot= uebergeben.
annot_df = pivot_h.copy().astype(object)
for col in annot_df.columns:
    for idx in annot_df.index:
        wert = pivot_h.loc[idx, col]
        n    = n_matrix.loc[idx, col]
        if pd.notna(wert):
            annot_df.loc[idx, col] = f"{wert:+.1f}%\n(n={int(n)})"
        else:
            annot_df.loc[idx, col] = ""

sns.heatmap(
    pivot_h, ax=ax,
    annot=annot_df, fmt="",
    cmap="RdYlGn", center=0,
    linewidths=0.6, linecolor="white",
    cbar_kws={"label": "Diskrepanz in %\n(+ = Inserat über BFS-Median)", "shrink": 0.75},
    annot_kws={"size": 7.5, "weight": "bold"},
    vmin=-40, vmax=40,
)

# HUMAN: Trennlinien zwischen Lohnkategorien fuer bessere Lesbarkeit
hochlohn_n   = sum(1 for b in pivot_h.index if branche_to_kat.get(b) == "Hochlohn")
mittellohn_n = sum(1 for b in pivot_h.index if branche_to_kat.get(b) == "Mittellohn")
if hochlohn_n > 0:
    ax.axhline(y=hochlohn_n, color="white", linewidth=3)
if mittellohn_n > 0:
    ax.axhline(y=hochlohn_n + mittellohn_n, color="white", linewidth=3)

ax.set_title(
    f"Lohn-Lücke: Stelleninserate vs. BFS-Medianlohn nach Branche und Region (%)\n"
    f"(min n={MIN_N_ZELLE} pro Zelle, Sortierung: Hochlohn / Mittellohn / Tieflohn)",
    fontsize=12, fontweight="bold", color=HSG_GRAU, pad=15)
ax.set_xlabel("BFS-Grossregion", fontsize=11)
ax.set_ylabel("Branche", fontsize=11)
ax.tick_params(axis="x", rotation=30, labelsize=9)
ax.tick_params(axis="y", rotation=0,  labelsize=9)

# HUMAN: Doppel-Funktion Fusszeile: Quelle und Persona-Interpretation
fig.text(
    0.5, 0.005,
    "Für Marcus: Grün = Inserate über BFS-Median | Rot = Inserate unter BFS-Median | "
    "Leere Zellen = zu wenig Daten | Quellen: jobs.ch | BFS LSE 2024",
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