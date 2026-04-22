"""
=============================================================================
app.py - Swiss Job Market 2026 | Interaktives Dashboard v2
=============================================================================
Projekt      : From Data2Dollar | HSG FS 2026
Autor        : Robin D.
Input        : merged_dataset.csv (1'762 Zeilen, 21 Spalten, 18 Branchen)
Run          : streamlit run app.py

-----------------------------------------------------------------------------
KI-DEKLARATION
-----------------------------------------------------------------------------
# HUMAN         = Konzept, Filter-Logik, Persona-Storytelling, Farbpalette
# KI-ASSISTIERT = Plotly-Umsetzung der 5 Charts iterativ mit Claude entwickelt
# VIBE-CODED    = Streamlit-Scaffold und CSS-Layout primaer von KI
=============================================================================
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# =============================================================================
# PAGE CONFIG
# =============================================================================
st.set_page_config(
    page_title="Swiss Job Market 2026 | HSG Data2Dollar",
    page_icon="🇨🇭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =============================================================================
# DESIGN - HSG-FARBPALETTE (identisch zu visualisierungen.py)
# =============================================================================
HSG_GRUEN     = "#00694E"
HSG_HELLGRUEN = "#4CAF84"
HSG_GRAU      = "#5A5A5A"
HSG_HELLGRAU  = "#F0F0F0"
AKZENT_ROT    = "#C0392B"

SENIORITY_ORDER  = ["Junior", "Mid", "Senior", "Lead/Manager"]
SENIORITY_FARBEN = {
    "Junior":       "#A8D5C2",
    "Mid":          HSG_HELLGRUEN,
    "Senior":       HSG_GRUEN,
    "Lead/Manager": "#0A4F3A",
}

FARBEN_CONTRACT = {
    "On-site": HSG_GRUEN,
    "Hybrid":  HSG_HELLGRUEN,
    "Remote":  "#A8D5C2",
}
LABEL_CONTRACT = {"On-site": "Vor Ort", "Hybrid": "Hybrid", "Remote": "Remote"}

# Lohnkategorie-Farben: semantisch (hoch = dunkelgrün, tief = hellgrün)
LOHNKAT_FARBEN = {
    "Hochlohn":   HSG_GRUEN,
    "Mittellohn": HSG_HELLGRUEN,
    "Tieflohn":   "#A8D5C2",
}
LOHNKAT_ORDER = ["Hochlohn", "Mittellohn", "Tieflohn"]

REGION_DE = {
    "Zürich": "Zürich", "Espace Mittelland": "Mittelland",
    "Nordwestschweiz": "Nordwestschweiz", "Genferseeregion": "Genferseeregion",
    "Ostschweiz": "Ostschweiz", "Zentralschweiz": "Zentralschweiz",
    "Tessin": "Tessin", "Andere": "Übrige",
}
STADT_DE = {
    "Zuerich": "Zürich", "Genf": "Genf", "Lausanne": "Lausanne",
    "Bern": "Bern", "Basel": "Basel", "Luzern": "Luzern", "Zug": "Zug",
}

SPRACHEN = {"Deutsch", "Englisch", "Französisch", "Italienisch", "Franzoesisch"}

# Custom CSS fuer HSG-Look
st.markdown(f"""
<style>
    .main .block-container {{padding-top: 2rem;}}
    h1 {{color: {HSG_GRUEN};}}
    h2, h3 {{color: {HSG_GRAU};}}
    [data-testid="stMetricValue"] {{color: {HSG_GRUEN}; font-weight: 700;}}
    .persona-box {{
        background-color: {HSG_HELLGRAU};
        border-left: 4px solid {HSG_GRUEN};
        padding: 0.8rem 1rem;
        border-radius: 4px;
        font-style: italic;
        color: {HSG_GRUEN};
        margin: 0.5rem 0 1rem 0;
    }}
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {{
        font-weight: 600;
    }}
    .lohnkat-badge {{
        display: inline-block;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 600;
        color: white;
        margin-right: 6px;
    }}
</style>
""", unsafe_allow_html=True)


# =============================================================================
# DATEN LADEN
# =============================================================================
@st.cache_data
def load_data(path="merged_dataset.csv"):
    """Laedt und praepariert den Datensatz - Logik synchron zu visualisierungen.py."""
    df = pd.read_csv(path)

    def parse_skills(s):
        if not isinstance(s, str) or s.strip() == "":
            return []
        return [x.strip() for x in s.split("|") if x.strip()]

    df["skills_liste"] = df["skills_liste"].apply(parse_skills)

    numeric_cols = ["gehalt_monat_chf", "gehalt_jahr_chf", "bfs_medianlohn_chf",
                    "lohn_diskrepanz_chf", "lohn_diskrepanz_pct", "skills_anzahl"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "lohnkategorie" not in df.columns:
        df["lohnkategorie"] = "Andere"

    df["region_de"] = df["bfs_region"].map(REGION_DE).fillna(df["bfs_region"])
    df["stadt_de"]  = df["stadt_normalisiert"].map(STADT_DE).fillna(df["stadt_normalisiert"])

    return df


try:
    df = load_data()
except FileNotFoundError:
    st.error("❌ `merged_dataset.csv` nicht gefunden. Bitte in denselben Ordner wie `app.py` legen.")
    st.stop()


# =============================================================================
# HEADER
# =============================================================================
col_t1, col_t2 = st.columns([4, 1])
with col_t1:
    st.title("🇨🇭 Swiss Job Market 2026")
    st.markdown(
        f"<p style='color:{HSG_GRAU}; font-size: 1.05rem; margin-top: -0.5rem;'>"
        "Welche Skills zahlen sich aus und wo bezahlt die Schweiz am besten?"
        "</p>",
        unsafe_allow_html=True
    )
with col_t2:
    st.markdown(
        f"<div style='text-align:right; color:{HSG_GRAU}; font-size: 0.85rem; padding-top: 1rem;'>"
        "<b>HSG Data2Dollar</b><br>FS 2026 | Robin D."
        "</div>",
        unsafe_allow_html=True
    )

st.divider()


# =============================================================================
# SIDEBAR - FILTER
# =============================================================================
st.sidebar.markdown(f"<h2 style='color:{HSG_GRUEN};'>🔍 Filter</h2>", unsafe_allow_html=True)

# Persona-Switcher nutzt neue lohnkategorie-Spalte (sauberer als Keyword-Match)
persona = st.sidebar.radio(
    "**Persona-Perspektive**",
    ["Alle Daten", "👩 Lena (Einstieg)", "👨 Marcus (Senior-Wechsel)"],
    help="Setzt passende Filter für die Persona automatisch."
)

st.sidebar.markdown("---")

# NEU: Lohnkategorie als erster Filter (strukturell wichtigster Befund)
lohnkats_available = [k for k in LOHNKAT_ORDER if k in df["lohnkategorie"].unique()]
default_lohnkat = lohnkats_available
if persona == "👨 Marcus (Senior-Wechsel)":
    default_lohnkat = ["Hochlohn"] if "Hochlohn" in lohnkats_available else lohnkats_available

selected_lohnkat = st.sidebar.multiselect(
    "Lohnkategorie",
    lohnkats_available,
    default=default_lohnkat,
    help="BFS-basierte Klassifikation: Hochlohn (6 Branchen), Mittellohn (8), Tieflohn (4)"
)

# Branche (reagiert auf Lohnkategorie-Filter)
if selected_lohnkat:
    categories_available = sorted(df[df["lohnkategorie"].isin(selected_lohnkat)]["category"].dropna().unique().tolist())
else:
    categories_available = sorted(df["category"].dropna().unique().tolist())

selected_categories = st.sidebar.multiselect("Branche", categories_available, default=categories_available)

# Stadt
cities = sorted(df["stadt_de"].dropna().unique().tolist())
selected_cities = st.sidebar.multiselect("Stadt", cities, default=cities)

# Region
regions = sorted(df["region_de"].dropna().unique().tolist())
selected_regions = st.sidebar.multiselect("Grossregion", regions, default=regions)

# Seniority
seniorities = [s for s in SENIORITY_ORDER if s in df["seniority"].unique()]
default_sen = seniorities
if persona == "👩 Lena (Einstieg)":
    default_sen = [s for s in seniorities if s in ["Junior", "Mid"]] or seniorities
elif persona == "👨 Marcus (Senior-Wechsel)":
    default_sen = [s for s in seniorities if s in ["Senior", "Lead/Manager"]] or seniorities

selected_seniority = st.sidebar.multiselect("Seniority", seniorities, default=default_sen)

# Arbeitsmodell
contracts = sorted(df["contract_type"].dropna().unique().tolist())
selected_contracts = st.sidebar.multiselect("Arbeitsmodell", contracts, default=contracts)

# Gehaltsrange (aus Plausibilitätsgrenze: 3'500 - 20'000)
sal_series = df["gehalt_monat_chf"].dropna()
if len(sal_series) > 0:
    s_min, s_max = int(sal_series.min()), int(sal_series.max())
    salary_range = st.sidebar.slider(
        "Gehaltsrange (CHF/Monat)",
        min_value=s_min, max_value=s_max,
        value=(s_min, s_max), step=500,
        help="Plausibilitätsgrenze: CHF 3'500 - 20'000"
    )
else:
    salary_range = (0, 100000)

st.sidebar.markdown("---")
st.sidebar.markdown(
    f"<small style='color:{HSG_GRAU};'>"
    "<b>Datensatz:</b><br>"
    f"{len(df):,} Stelleninserate · 18 Branchen<br>"
    f"{df['gehalt_monat_chf'].notna().sum()} mit Gehaltsangabe<br><br>"
    "<b>Quellen:</b><br>"
    "jobs.ch (Web Scraping)<br>"
    "BFS Lohnstrukturerhebung 2024"
    "</small>", unsafe_allow_html=True
)


# =============================================================================
# FILTER ANWENDEN
# =============================================================================
def apply_filters(df):
    f = df.copy()
    if selected_lohnkat:
        f = f[f["lohnkategorie"].isin(selected_lohnkat)]
    if selected_categories:
        f = f[f["category"].isin(selected_categories)]
    if selected_cities:
        f = f[f["stadt_de"].isin(selected_cities)]
    if selected_regions:
        f = f[f["region_de"].isin(selected_regions)]
    if selected_seniority:
        f = f[f["seniority"].isin(selected_seniority)]
    if selected_contracts:
        f = f[f["contract_type"].isin(selected_contracts)]
    mask = (f["gehalt_monat_chf"].between(*salary_range)) | (f["gehalt_monat_chf"].isna())
    f = f[mask]
    return f


df_f = apply_filters(df)

if len(df_f) == 0:
    st.warning("⚠️ Keine Stelleninserate für die aktuellen Filter. Bitte Filter anpassen.")
    st.stop()


# =============================================================================
# KPI-HEADER (5 Metriken inkl. Lohnkategorie-Breakdown)
# =============================================================================
k1, k2, k3, k4, k5 = st.columns(5)
with k1:
    st.metric("📋 Stelleninserate", f"{len(df_f):,}")
with k2:
    with_salary = df_f["gehalt_monat_chf"].notna().sum()
    st.metric("💰 Mit Gehalt", f"{with_salary} ({with_salary/len(df_f)*100:.0f}%)")
with k3:
    avg_sal = df_f["gehalt_monat_chf"].mean()
    st.metric("Ø Monatslohn", f"CHF {avg_sal:,.0f}" if pd.notna(avg_sal) else "–")
with k4:
    med_disc = df_f["lohn_diskrepanz_pct"].median()
    st.metric("📊 Median Diskrepanz",
              f"{med_disc:+.1f} %" if pd.notna(med_disc) else "–",
              help="Inserat vs. BFS-Medianlohn")
with k5:
    n_hochlohn = (df_f["lohnkategorie"] == "Hochlohn").sum()
    n_mittel   = (df_f["lohnkategorie"] == "Mittellohn").sum()
    n_tief     = (df_f["lohnkategorie"] == "Tieflohn").sum()
    st.metric("🏷️ Hoch / Mittel / Tief", f"{n_hochlohn} / {n_mittel} / {n_tief}")

st.markdown("")


# =============================================================================
# TABS
# =============================================================================
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🔧 Top Skills",
    "🏙️ Gehalt nach Stadt",
    "📈 Seniority vs. Gehalt",
    "🏢 Arbeitsmodell",
    "🌡️ Lohn-Lücke",
    "📄 Rohdaten",
])


# -----------------------------------------------------------------------------
# CHART 1: TOP SKILLS
# -----------------------------------------------------------------------------
with tab1:
    c1, c2 = st.columns([3, 1])
    with c1:
        st.subheader("Top gefragte Skills im Schweizer Jobmarkt 2026")
    with c2:
        top_n = st.slider("Anzahl Skills", 5, 30, 15, key="skills_n")

    alle_skills = [s for liste in df_f["skills_liste"] for s in liste]
    if len(alle_skills) == 0:
        st.info("Keine Skills im gefilterten Datensatz.")
    else:
        skill_counts = pd.Series(alle_skills).value_counts().head(top_n)
        skills_df = pd.DataFrame({"Skill": skill_counts.index, "Anzahl": skill_counts.values})

        quartil_75 = skill_counts.quantile(0.75)

        def skill_farbe(row):
            if row["Skill"] in SPRACHEN:
                return "Sprachkenntnisse"
            elif row["Anzahl"] >= quartil_75:
                return "Tech-Skills (Top-Quartil)"
            else:
                return "Tech-Skills"

        skills_df["Kategorie"] = skills_df.apply(skill_farbe, axis=1)

        fig = px.bar(
            skills_df, x="Anzahl", y="Skill",
            color="Kategorie", orientation="h",
            color_discrete_map={
                "Tech-Skills (Top-Quartil)": HSG_GRUEN,
                "Tech-Skills":               HSG_HELLGRUEN,
                "Sprachkenntnisse":          "#B0C4DE",
            },
            text="Anzahl",
            category_orders={"Kategorie": ["Tech-Skills (Top-Quartil)", "Tech-Skills", "Sprachkenntnisse"]},
        )
        fig.update_traces(textposition="outside", textfont=dict(color=HSG_GRAU, size=11))
        fig.update_layout(
            height=max(400, 28 * len(skills_df)),
            yaxis=dict(categoryorder="total ascending", title=""),
            xaxis_title="Anzahl Stelleninserate",
            plot_bgcolor="white",
            legend=dict(title="", orientation="h", y=-0.08),
            margin=dict(l=0, r=40, t=20, b=40),
        )
        fig.update_xaxes(gridcolor="#E5E5E5")
        st.plotly_chart(fig, use_container_width=True)

        st.markdown(
            '<div class="persona-box">👩 Für Lena: Welche Skills lohnen sich zu lernen? '
            'Sprachkenntnisse dominieren den Schweizer Jobmarkt (Deutsch, Englisch, Französisch).</div>',
            unsafe_allow_html=True
        )


# -----------------------------------------------------------------------------
# CHART 2: GEHALT NACH STADT
# -----------------------------------------------------------------------------
with tab2:
    st.subheader("Gehaltsvergleich nach Stadt: jobs.ch vs. BFS-Medianlohn")

    df_g = df_f.dropna(subset=["gehalt_monat_chf"]).copy()

    c1, c2 = st.columns([1, 3])
    with c1:
        min_jobs = st.slider("Min. Jobs pro Stadt", 1, 30, 15, key="min_jobs_stadt",
                             help="Plausibilitätsfilter (statisches Chart: n≥15)")
    staedte_ok = df_g["stadt_de"].value_counts()
    staedte_ok = staedte_ok[staedte_ok >= min_jobs].index.tolist()
    df_g = df_g[df_g["stadt_de"].isin(staedte_ok)]

    if len(df_g) == 0:
        st.info(f"Keine Stadt hat ≥ {min_jobs} Stellen im aktuellen Filter.")
    else:
        agg = (df_g.groupby("stadt_de")
               .agg(jobs_lohn=("gehalt_monat_chf", "mean"),
                    bfs_lohn =("bfs_medianlohn_chf", "mean"),
                    n        =("gehalt_monat_chf", "count"))
               .reset_index()
               .sort_values("jobs_lohn", ascending=False)
               .head(10))

        fig = go.Figure()
        fig.add_trace(go.Bar(
            name="jobs.ch Schätzung",
            x=agg["stadt_de"], y=agg["jobs_lohn"],
            marker_color=HSG_GRUEN,
            text=[f"CHF {v:,.0f}" for v in agg["jobs_lohn"]],
            textposition="outside",
            textfont=dict(color=HSG_GRAU, size=11),
        ))
        fig.add_trace(go.Bar(
            name="BFS Medianlohn (Referenz)",
            x=agg["stadt_de"], y=agg["bfs_lohn"],
            marker_color=HSG_HELLGRUEN,
            text=[f"CHF {v:,.0f}" if pd.notna(v) else "" for v in agg["bfs_lohn"]],
            textposition="outside",
            textfont=dict(color=HSG_GRAU, size=11),
        ))
        for _, row in agg.iterrows():
            fig.add_annotation(
                x=row["stadt_de"], y=0,
                text=f"n={int(row['n'])}",
                showarrow=False, yshift=-20,
                font=dict(size=9, color=HSG_GRAU),
            )
        fig.update_layout(
            barmode="group",
            height=550,
            yaxis_title="Monatslohn in CHF",
            xaxis_title="Stadt",
            plot_bgcolor="white",
            legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center"),
            margin=dict(l=20, r=20, t=60, b=60),
        )
        fig.update_yaxes(gridcolor="#E5E5E5", tickformat=",.0f", tickprefix="CHF ")
        st.plotly_chart(fig, use_container_width=True)

        st.markdown(
            '<div class="persona-box">👩 Für Lena: Wo kann sie als Einsteigerin am meisten verdienen? '
            'Zürich führt bei Inserats-Gehältern, aber die Lücke zum BFS-Median ist nicht überall gleich.</div>',
            unsafe_allow_html=True
        )


# -----------------------------------------------------------------------------
# CHART 3: SENIORITY VS. GEHALT
# -----------------------------------------------------------------------------
with tab3:
    st.subheader("Lohnt sich mehr Erfahrung? Seniority vs. Monatslohn")

    # Toggle: nur Hochlohn (PNG-Default) vs. alle Lohnkategorien
    c1, c2 = st.columns([1, 2])
    with c1:
        fokus = st.radio(
            "Fokus",
            ["Nur Hochlohn-Branchen", "Alle gefilterten Branchen"],
            key="sen_fokus",
            help="Statisches Chart zeigt nur Hochlohn - dort ist Lohn-Transparenz am höchsten."
        )
    with c2:
        min_n_sen = st.slider("Min. n pro Karrierestufe", 3, 20, 10, key="min_n_sen",
                              help="Stufen mit zu wenig Daten werden ausgeblendet.")

    df_s = df_f.dropna(subset=["gehalt_monat_chf"]).copy()
    if fokus == "Nur Hochlohn-Branchen":
        df_s = df_s[df_s["lohnkategorie"] == "Hochlohn"]

    df_s = df_s[df_s["seniority"].isin(SENIORITY_ORDER)]

    # Stufen mit n < min_n_sen filtern
    counts = df_s["seniority"].value_counts()
    valid_levels = [s for s in SENIORITY_ORDER if counts.get(s, 0) >= min_n_sen]
    df_s = df_s[df_s["seniority"].isin(valid_levels)]

    if len(df_s) == 0 or len(valid_levels) == 0:
        st.info(f"Keine Karrierestufe hat ≥ {min_n_sen} Einträge.")
    else:
        seniority_num = {s: i for i, s in enumerate(valid_levels)}
        df_s["x_num"] = df_s["seniority"].map(seniority_num)
        np.random.seed(99)
        df_s["x_jitter"] = df_s["x_num"] + np.random.uniform(-0.18, 0.18, len(df_s))

        fig = go.Figure()
        for level in valid_levels:
            sub = df_s[df_s["seniority"] == level]
            if len(sub) == 0:
                continue
            fig.add_trace(go.Scatter(
                x=sub["x_jitter"], y=sub["gehalt_monat_chf"],
                mode="markers", name=f"{level} (n={len(sub)})",
                marker=dict(color=SENIORITY_FARBEN[level], size=9,
                            opacity=0.6, line=dict(color="white", width=0.5)),
                hovertemplate=(
                    "<b>%{customdata[0]}</b><br>"
                    "%{customdata[1]}<br>"
                    "Lohnkategorie: %{customdata[2]}<br>"
                    "CHF %{y:,.0f}/Monat<extra></extra>"
                ),
                customdata=sub[["job_title", "company", "lohnkategorie"]].values,
            ))
            med = sub["gehalt_monat_chf"].median()
            n   = seniority_num[level]
            fig.add_shape(
                type="line",
                x0=n-0.35, x1=n+0.35, y0=med, y1=med,
                line=dict(color=SENIORITY_FARBEN[level], width=3),
            )
            fig.add_annotation(
                x=n+0.38, y=med,
                text=f"Median:<br>CHF {med:,.0f}<br>(n={len(sub)})",
                showarrow=False, xanchor="left",
                font=dict(color=SENIORITY_FARBEN[level], size=10),
            )

        fig.update_layout(
            height=550,
            xaxis=dict(
                tickvals=list(seniority_num.values()),
                ticktext=list(seniority_num.keys()),
                title="Karrierestufe",
                range=[-0.5, len(valid_levels) - 0.2],
            ),
            yaxis=dict(title="Monatslohn in CHF", gridcolor="#E5E5E5",
                       tickformat=",.0f", tickprefix="CHF "),
            plot_bgcolor="white",
            legend=dict(title="Karrierestufe", orientation="v", y=1, x=1.02),
            margin=dict(l=20, r=160, t=30, b=60),
        )
        st.plotly_chart(fig, use_container_width=True)

        note = ("Hinweis: 'Mid' = Default-Kategorie für Jobs ohne explizites Seniority-Keyword. "
                "Der flache Median-Verlauf (Mid → Senior → Lead) deutet darauf hin, dass "
                "Seniority weniger stark auf das Gehalt wirkt als die Branchen-Zugehörigkeit.")
        st.markdown(
            f'<div class="persona-box">👨 Für Marcus: Federt Senior-Erfahrung den Branchenwechsel ab? '
            f'<br><small>{note}</small></div>',
            unsafe_allow_html=True
        )


# -----------------------------------------------------------------------------
# CHART 4: ARBEITSMODELL NACH BRANCHE
# -----------------------------------------------------------------------------
with tab4:
    st.subheader("Arbeitsmodell nach Branche: Vor Ort / Hybrid / Remote")

    df_c = (df_f.groupby(["category", "contract_type"])
            .size().reset_index(name="anzahl"))
    df_tot = df_f.groupby("category").size().reset_index(name="total")
    df_c = df_c.merge(df_tot, on="category")
    df_c["pct"] = (df_c["anzahl"] / df_c["total"] * 100).round(1)

    if len(df_c) == 0:
        st.info("Keine Daten für Arbeitsmodell-Analyse.")
    else:
        pivot = df_c.pivot_table(index="category", columns="contract_type",
                                 values="pct", fill_value=0)
        for col in ["On-site", "Hybrid", "Remote"]:
            if col not in pivot.columns:
                pivot[col] = 0.0
        # Nach Flexibilitaet sortieren (Hybrid + Remote)
        pivot["_flex"] = pivot["Hybrid"] + pivot["Remote"]
        pivot = pivot.sort_values("_flex", ascending=True).drop(columns="_flex")

        fig = go.Figure()
        for col in ["On-site", "Hybrid", "Remote"]:
            fig.add_trace(go.Bar(
                name=LABEL_CONTRACT[col],
                y=pivot.index, x=pivot[col],
                orientation="h",
                marker_color=FARBEN_CONTRACT[col],
                text=[f"{v:.0f}%" if v > 6 else "" for v in pivot[col]],
                textposition="inside",
                insidetextanchor="middle",
                textfont=dict(color="white", size=11),
                hovertemplate="<b>%{y}</b><br>" + LABEL_CONTRACT[col] + ": %{x:.1f}%<extra></extra>",
            ))
        fig.update_layout(
            barmode="stack",
            height=max(400, 32 * len(pivot)),
            xaxis=dict(title="Anteil der Stelleninserate (%)", range=[0, 100]),
            yaxis=dict(title=""),
            plot_bgcolor="white",
            legend=dict(title="Arbeitsmodell", orientation="h", y=-0.08),
            margin=dict(l=20, r=20, t=20, b=60),
        )
        fig.update_xaxes(gridcolor="#E5E5E5")
        st.plotly_chart(fig, use_container_width=True)

        st.markdown(
            '<div class="persona-box">👨 Für Marcus: Welche Branche bietet die meiste Flexibilität? '
            'Beratung, Banken und IT führen bei Hybrid-Anteilen. Handwerk und Gastgewerbe bleiben on-site.</div>',
            unsafe_allow_html=True
        )


# -----------------------------------------------------------------------------
# CHART 5: LOHN-LUECKE HEATMAP
# -----------------------------------------------------------------------------
with tab5:
    st.subheader("Lohn-Lücke: Stelleninserate vs. BFS-Medianlohn (%)")

    df_h = df_f.dropna(subset=["lohn_diskrepanz_pct"]).copy()

    c1, c2 = st.columns([1, 3])
    with c1:
        min_n_cell = st.slider("Min. n pro Zelle", 1, 10, 3, key="min_n_cell",
                               help="Zellen mit zu wenig Daten werden ausgeblendet.")

    if len(df_h) == 0:
        st.info("Keine Diskrepanz-Daten für die aktuellen Filter.")
    else:
        # Counts pro Zelle
        cell_counts = (df_h.groupby(["category", "region_de"]).size()
                       .unstack("region_de").fillna(0))

        pivot_h = (df_h.groupby(["category", "region_de"])["lohn_diskrepanz_pct"]
                   .mean().unstack("region_de").round(1))

        # Regionen-Reihenfolge
        reihenfolge = ["Zürich", "Genferseeregion", "Mittelland",
                       "Nordwestschweiz", "Zentralschweiz", "Ostschweiz",
                       "Tessin", "Übrige"]
        region_cols = [c for c in reihenfolge if c in pivot_h.columns]
        pivot_h = pivot_h.reindex(columns=region_cols)
        cell_counts = cell_counts.reindex(columns=region_cols, fill_value=0)

        # Zellen mit zu wenig Daten maskieren
        mask = cell_counts < min_n_cell
        pivot_h = pivot_h.mask(mask)

        # Branchen nach Lohnkategorie sortieren (Hochlohn oben, Tieflohn unten)
        lohnkat_map = df.drop_duplicates("category").set_index("category")["lohnkategorie"].to_dict()
        sort_order = {"Hochlohn": 0, "Mittellohn": 1, "Tieflohn": 2, "Andere": 3}
        pivot_h["_sort_kat"] = pivot_h.index.map(lambda c: sort_order.get(lohnkat_map.get(c, "Andere"), 3))
        pivot_h["_sort_mean"] = pivot_h.drop(columns="_sort_kat").mean(axis=1)
        pivot_h = pivot_h.sort_values(["_sort_kat", "_sort_mean"], ascending=[True, False])
        pivot_h = pivot_h.drop(columns=["_sort_kat", "_sort_mean"])

        # Annotations mit n= kombiniert
        text_matrix = pivot_h.copy().astype(object)
        for col in text_matrix.columns:
            for idx in text_matrix.index:
                v = pivot_h.loc[idx, col]
                n = int(cell_counts.loc[idx, col]) if idx in cell_counts.index and col in cell_counts.columns else 0
                if pd.notna(v) and n >= min_n_cell:
                    text_matrix.loc[idx, col] = f"{v:+.1f}%<br>(n={n})"
                else:
                    text_matrix.loc[idx, col] = ""

        fig = go.Figure(data=go.Heatmap(
            z=pivot_h.values,
            x=pivot_h.columns, y=pivot_h.index,
            text=text_matrix.values, texttemplate="%{text}",
            textfont=dict(size=10),
            colorscale="RdYlGn", zmid=0, zmin=-55, zmax=55,
            colorbar=dict(title=dict(text="Diskrepanz %<br>(+ über BFS)", side="right")),
            hovertemplate="<b>%{y}</b><br>%{x}<br>Diskrepanz: %{z:+.1f}%<extra></extra>",
        ))
        fig.update_layout(
            height=max(450, 34 * len(pivot_h)),
            xaxis=dict(title="BFS-Grossregion", tickangle=-30),
            yaxis=dict(title="Branche", autorange="reversed"),
            margin=dict(l=20, r=20, t=20, b=60),
        )
        st.plotly_chart(fig, use_container_width=True)

        st.markdown(
            '<div class="persona-box">👨 Für Marcus: Grün = Inserate <b>über</b> BFS-Median, '
            'Rot = Inserate <b>unter</b> BFS-Median. <br><small>Wichtiger Befund: '
            'Hochlohn-Branchen (Chemie, Banken, IT) inserieren systematisch UNTER Median - '
            'Tieflohn-Branchen (Gesundheit, Gastgewerbe) ÜBER. Erklärung: Transparenz-Bias.</small></div>',
            unsafe_allow_html=True
        )


# -----------------------------------------------------------------------------
# TAB 6: ROHDATEN
# -----------------------------------------------------------------------------
with tab6:
    st.subheader(f"Gefilterte Rohdaten ({len(df_f):,} Zeilen)")

    df_display = df_f.copy()
    df_display["skills_liste"] = df_display["skills_liste"].apply(
        lambda x: " | ".join(x) if isinstance(x, list) else str(x))

    display_cols = [c for c in [
        "job_title", "company", "stadt_de", "category", "lohnkategorie",
        "seniority", "contract_type", "gehalt_monat_chf", "bfs_medianlohn_chf",
        "lohn_diskrepanz_pct", "skills_liste"
    ] if c in df_display.columns]

    st.dataframe(df_display[display_cols], use_container_width=True, height=500)

    csv = df_display[display_cols].to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Gefilterte Daten als CSV",
        csv, "swiss_jobs_filtered.csv", "text/csv",
    )


# =============================================================================
# FOOTER
# =============================================================================
st.divider()
st.markdown(
    f"<div style='text-align:center; color:{HSG_GRAU}; font-size: 0.8rem;'>"
    "<b>Schweizer Jobmarkt 2026</b> | HSG Data2Dollar FS 2026 | Robin D.<br>"
    f"Datensatz: {len(df):,} Inserate · 18 Branchen · April 2026 · "
    "Quellen: jobs.ch (Web Scraping) · BFS Lohnstrukturerhebung 2024"
    "</div>",
    unsafe_allow_html=True
)