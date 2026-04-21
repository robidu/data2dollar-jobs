"""
=============================================================================
cleaning.py - Datenbereinigung Schweizer Jobmarkt 2026
=============================================================================
Projekt      : From Data2Dollar | HSG FS 2026
Autor        : Robin D.
Beschreibung : Bereinigt rohdaten_jobs.csv und lohndaten_bfs.csv,
               extrahiert Skills und Seniority, normalisiert Staedte,
               merged beide Datensaetze.
Output       : merged_dataset.csv

-----------------------------------------------------------------------------
KI-DEKLARATION (vgl. KI_DEKLARATION.md)
-----------------------------------------------------------------------------
# HUMAN          = Konzept, Mappings und Logik vom Autor
# KI-ASSISTIERT  = iterativ mit Claude/Copilot entwickelt, Autor hat Review gemacht
# VIBE-CODED     = primaer von KI, vom Autor verstanden und getestet
=============================================================================
"""

import pandas as pd
import numpy as np
import re

# =============================================================================
# 1. DATEN EINLESEN
# =============================================================================
# HUMAN: Einfacher Einlese-Schritt, standard Pandas-Pattern

print("=" * 60)
print("SCHRITT 1: Daten einlesen")
print("=" * 60)

df_jobs = pd.read_csv("rohdaten_jobs.csv")
df_bfs  = pd.read_csv("lohndaten_bfs.csv")

print(f"Jobs-Datensatz : {df_jobs.shape[0]} Zeilen, {df_jobs.shape[1]} Spalten")
print(f"BFS-Datensatz  : {df_bfs.shape[0]} Zeilen, {df_bfs.shape[1]} Spalten")
print(f"\nFehlende Werte (Jobs):\n{df_jobs.isnull().sum()}")
print(f"\nBranchen im Datensatz:")
print(df_jobs["category"].value_counts())

# =============================================================================
# 2. JOBS - GRUNDBEREINIGUNG
# =============================================================================
# HUMAN: Duplikat-Strategie und NaN-Fuellwerte selbst definiert.
# Zuerst Duplikate per job_id (unique ID von jobs.ch), dann per title+company
# als Sicherheitsnetz fuer den Fall dass dieselbe Stelle unter 2 IDs gepostet wurde.

print("\n" + "=" * 60)
print("SCHRITT 2: Grundbereinigung Jobs")
print("=" * 60)

df_jobs = df_jobs.drop_duplicates(subset=["job_id"], keep="first")
df_jobs = df_jobs.drop_duplicates(subset=["job_title", "company"], keep="first")
df_jobs = df_jobs.dropna(subset=["job_title"])

df_jobs["company"]       = df_jobs["company"].fillna("Unbekannt")
df_jobs["location"]      = df_jobs["location"].fillna("Unbekannt")
df_jobs["salary_range"]  = df_jobs["salary_range"].fillna("")
df_jobs["skills_text"]   = df_jobs["skills_text"].fillna("")
df_jobs["contract_type"] = df_jobs["contract_type"].fillna("Nicht angegeben")
df_jobs["date_posted"]   = df_jobs["date_posted"].fillna("")

# KI-ASSISTIERT: Loop-Pattern zum trimmen aller Textspalten von Claude vorgeschlagen
for col in df_jobs.columns:
    if df_jobs[col].dtype == object:
        df_jobs[col] = df_jobs[col].astype(str).str.strip().replace("nan", "")

print(f"Nach Bereinigung: {df_jobs.shape[0]} Zeilen")

# =============================================================================
# 3. GEHALTSANGABEN PARSEN - JAHRESGEHALT -> MONATSGEHALT
# =============================================================================
# HUMAN: Konzept selbst entwickelt - wenn der geparste Wert > 25'000 ist, muss
# es ein Jahresgehalt sein (kein Monatslohn ist so hoch). Also durch 12 teilen.
# Die Schwelle 25'000 ist meine eigene Plausibilitaetsannahme.

print("\n" + "=" * 60)
print("SCHRITT 3: Gehaltsangaben parsen")
print("=" * 60)

def parse_gehalt(salary_str):
    """
    Parst 'CHF 95375 - 135375 (jobs.ch estimate)' -> 9590 CHF/Monat.
    Jahresgehalt (>25000) wird automatisch durch 12 geteilt.
    """
    # HUMAN: Input-Validierung
    if not isinstance(salary_str, str) or salary_str.strip() == "":
        return np.nan

    # KI-ASSISTIERT: Regex-Pattern von Copilot. Findet alle Zahlen mit optionalem
    # Apostroph-Tausendertrenner (CH-Format: 95'000). Filtert auf Zahlen >= 100
    # damit keine Prozente oder 13. Monatslohn mitgeparst werden.
    zahlen = re.findall(r"[\d']+", salary_str)
    zahlen = [int(z.replace("'", "")) for z in zahlen if len(z.replace("'", "")) >= 3]

    # HUMAN: Mittelwert-Logik bei Range, sonst Einzelwert
    if len(zahlen) >= 2:
        mittelwert = np.mean(zahlen[:2])
    elif len(zahlen) == 1:
        mittelwert = float(zahlen[0])
    else:
        return np.nan

    # HUMAN: Plausibilitaets-Schwelle 25'000 ist meine eigene Annahme
    if mittelwert > 25000:
        return round(mittelwert / 12, 0)
    return mittelwert

df_jobs["gehalt_monat_chf"] = df_jobs["salary_range"].apply(parse_gehalt)

# HUMAN: Zweite Plausibilitaetspruefung (Monatslohn zwischen 3'500 und 20'000)
# Verschaerft gegenueber v1 weil bei 1800 Jobs ein paar Parsing-Fehler auftreten.
# Beispiel: "Apprenti.e CFC 3 ans" mit CHF 23'400 ist Ausbildungsgehalt ueber 3 Jahre,
# nicht Monatslohn -> wird rausgefiltert.
maske = (
    df_jobs["gehalt_monat_chf"].notna() &
    ((df_jobs["gehalt_monat_chf"] < 3500) | (df_jobs["gehalt_monat_chf"] > 20000))
)
df_jobs.loc[maske, "gehalt_monat_chf"] = np.nan

# HUMAN: Zusaetzlicher Apprenti/Stagiaire-Filter - Ausbildungsgehaelter sind
# keine regulaeren Monatsloehne und verfaelschen die Statistik
apprenti_keywords = ["apprenti", "lehrling", "stagiaire", "praktikant", "intern "]
for kw in apprenti_keywords:
    maske_app = (
        df_jobs["gehalt_monat_chf"].notna() &
        df_jobs["job_title"].str.lower().str.contains(kw, na=False)
    )
    df_jobs.loc[maske_app, "gehalt_monat_chf"] = np.nan

# HUMAN: Jahresgehalt mit 13 Monatsloehnen (CH-Standard), nicht 12
df_jobs["gehalt_jahr_chf"] = df_jobs["gehalt_monat_chf"] * 13

n_gehalt = df_jobs["gehalt_monat_chf"].notna().sum()
print(f"Gehaelter geparst: {n_gehalt} von {len(df_jobs)}")
if n_gehalt > 0:
    print(f"Bereich: CHF {df_jobs['gehalt_monat_chf'].min():.0f} - "
          f"{df_jobs['gehalt_monat_chf'].max():.0f} / Monat")

# =============================================================================
# 4. SENIORITY AUS JOBTITEL EXTRAHIEREN
# =============================================================================
# HUMAN: Keyword-Listen komplett selbst zusammengestellt.
# 4 Stufen gewaehlt (Junior, Mid, Senior, Lead/Manager) weil das die
# Standard-Karrierestufen in der Schweiz sind.
# Reihenfolge der Abfrage wichtig: Lead/Manager ueberschreibt Senior
# (ein "Senior Manager" zaehlt als Lead, nicht als Senior).

print("\n" + "=" * 60)
print("SCHRITT 4: Seniority extrahieren")
print("=" * 60)

def extrahiere_seniority(titel):
    if not isinstance(titel, str):
        return "Mid"
    t = titel.lower()
    # HUMAN: Lead/Manager-Keywords - deutsch, englisch und franzoesisch fuer CH-Markt
    if any(w in t for w in ["head of", "lead", "chief", "cto", "cfo", "cio",
                             "vp ", "vice president", "direktor", "director",
                             "manager", "leiter", "leiterin", "responsable"]):
        return "Lead/Manager"
    # HUMAN: Senior-Keywords
    if any(w in t for w in ["senior", "sr.", "sr ", "principal",
                             "expert", "spezialist", "experienced"]):
        return "Senior"
    # HUMAN: Junior-Keywords inkl. Praktikum und Trainee
    if any(w in t for w in ["junior", "jr.", "jr ", "trainee", "praktikum",
                             "werkstudent", "einstieg", "entry", "graduate",
                             "intern", "stagiaire", "apprentice"]):
        return "Junior"
    # HUMAN: Default = Mid (haeufigste Stufe in den Daten)
    return "Mid"

df_jobs["seniority"] = df_jobs["job_title"].apply(extrahiere_seniority)
print("Seniority-Verteilung:")
print(df_jobs["seniority"].value_counts())

# =============================================================================
# 5. SKILLS AUS skills_text EXTRAHIEREN
# =============================================================================
# HUMAN: Die Skill-Liste ist 100% Eigenleistung - basiert auf meiner Recherche
# zu den relevantesten Skills fuer die 18 gewaehlten Branchen im CH-Markt 2026.
# Strukturiert nach: Programmiersprachen, BI/Analytics, Cloud, ML/AI, DB,
# Projektmanagement, Sprachen, Branchenspezifisch.

print("\n" + "=" * 60)
print("SCHRITT 5: Skills extrahieren")
print("=" * 60)

# HUMAN: Komplette Skill-Liste vom Autor zusammengestellt
SKILL_LISTE = [
    "Python", "SQL", "Java", "Scala", "R", "C++", "C#",
    "JavaScript", "TypeScript", "Go", "MATLAB",
    "Excel", "Power BI", "Tableau", "Looker", "SPSS", "SAS",
    "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Git", "Linux",
    "Machine Learning", "Deep Learning", "TensorFlow", "PyTorch",
    "NLP", "Pandas", "NumPy", "Scikit-learn",
    "PostgreSQL", "MySQL", "MongoDB", "Oracle", "Snowflake", "Databricks",
    "Projektmanagement", "Agile", "Scrum", "SAP", "Salesforce",
    "Deutsch", "Englisch", "Französisch", "Italienisch",
    "Bloomberg", "Risk Management", "Compliance", "Controlling",
    "CAD", "AutoCAD", "SolidWorks", "GMP", "ISO", "Lean", "Six Sigma",
]

# HUMAN: Normalisierungs-Mapping fuer Schreibvarianten
SKILL_NORMALISIERUNG = {
    "power bi":        "Power BI",
    "powerbi":         "Power BI",
    "ms excel":        "Excel",
    "microsoft excel": "Excel",
    "scikit-learn":    "Scikit-learn",
}

def extrahiere_skills(text):
    if not isinstance(text, str) or text.strip() == "":
        return []
    text_lower = text.lower()
    gefundene = []
    # KI-ASSISTIERT: re.escape() damit Sonderzeichen wie C++ korrekt geescaped werden.
    # Idee von Claude, weil mein erster Versuch ohne escape bei "C++" gescheitert ist.
    for skill in SKILL_LISTE:
        muster = r"\b" + re.escape(skill.lower()) + r"\b"
        if re.search(muster, text_lower):
            skill_norm = SKILL_NORMALISIERUNG.get(skill.lower(), skill)
            if skill_norm not in gefundene:
                gefundene.append(skill_norm)
    return gefundene

df_jobs["skills_liste"]  = df_jobs["skills_text"].apply(extrahiere_skills)
df_jobs["skills_anzahl"] = df_jobs["skills_liste"].apply(len)

# HUMAN: Top-Skills fuer Konsolen-Output (hilft beim Debugging und Plausibilitaetscheck)
alle_skills = [s for liste in df_jobs["skills_liste"] for s in liste]
print(f"Durchschnittliche Skills pro Inserat: {df_jobs['skills_anzahl'].mean():.1f}")
print(f"\nTop 10 Skills:\n{pd.Series(alle_skills).value_counts().head(10)}")

# =============================================================================
# 6. STADTNAME NORMALISIEREN
# =============================================================================
# HUMAN: Komplettes Mapping von Gemeinden und PLZ zu Hauptstaedten selbst erstellt.
# Hintergrund: jobs.ch Angaben sind inkonsistent ("Zuerich", "8001 Zuerich",
# "Wallisellen", "ZH"). Fuer die Analyse wollte ich Agglomerationen zusammenfassen
# (Wallisellen und Schlieren sind effektiv Zuerich-Jobs).

print("\n" + "=" * 60)
print("SCHRITT 6: Stadtname normalisieren")
print("=" * 60)

# HUMAN: Mapping komplett vom Autor - basierend auf CH-Geografie und Pendler-Regionen
STADT_MAPPING = {
    # Zuerich
    "zürich": "Zuerich", "zurich": "Zuerich", "zuerich": "Zuerich",
    "wallisellen": "Zuerich", "schlieren": "Zuerich", "opfikon": "Zuerich",
    "regensdorf": "Zuerich", "dietikon": "Zuerich", "uster": "Zuerich",
    "winterthur": "Zuerich", "volketswil": "Zuerich", "kloten": "Zuerich",
    "adliswil": "Zuerich", "horgen": "Zuerich", "thalwil": "Zuerich",
    "8000": "Zuerich", "8001": "Zuerich", "8002": "Zuerich",
    "8003": "Zuerich", "8004": "Zuerich", "8005": "Zuerich",
    "8006": "Zuerich", "8008": "Zuerich", "8048": "Zuerich",
    "8050": "Zuerich", "8051": "Zuerich", "8052": "Zuerich",
    "8053": "Zuerich", "8055": "Zuerich",
    # Basel
    "basel": "Basel", "basle": "Basel", "bâle": "Basel",
    "muttenz": "Basel", "pratteln": "Basel", "allschwil": "Basel",
    "4000": "Basel", "4001": "Basel", "4051": "Basel",
    "4052": "Basel", "4053": "Basel", "4054": "Basel",
    # Bern
    "bern": "Bern", "berne": "Bern",
    "koeniz": "Bern", "ostermundigen": "Bern", "zollikofen": "Bern",
    "ittigen": "Bern", "muri bei bern": "Bern", "liebefeld": "Bern",
    "burgdorf": "Bern", "langenthal": "Bern",
    "3000": "Bern", "3001": "Bern", "3003": "Bern",
    "3005": "Bern", "3006": "Bern", "3008": "Bern",
    "3400": "Bern", "3401": "Bern", "3402": "Bern",  # Burgdorf PLZ
    # Genf
    "genf": "Genf", "geneva": "Genf", "genève": "Genf", "geneve": "Genf",
    "meyrin": "Genf", "vernier": "Genf", "carouge": "Genf",
    "1200": "Genf", "1201": "Genf", "1202": "Genf",
    "1203": "Genf", "1204": "Genf", "1205": "Genf", "1206": "Genf",
    # Lausanne
    "lausanne": "Lausanne", "renens": "Lausanne", "ecublens": "Lausanne",
    "1000": "Lausanne", "1003": "Lausanne", "1004": "Lausanne",
    "1005": "Lausanne", "1006": "Lausanne", "1007": "Lausanne",
    # Zug
    "zug": "Zug", "baar": "Zug", "cham": "Zug", "steinhausen": "Zug",
    "rotkreuz": "Zug", "risch": "Zug", "hünenberg": "Zug", "huenenberg": "Zug",
    "6300": "Zug", "6301": "Zug", "6302": "Zug", "6303": "Zug", "6304": "Zug",
    "6340": "Zug", "6341": "Zug", "6343": "Zug",
    # Luzern
    "luzern": "Luzern", "lucerne": "Luzern", "emmen": "Luzern", "kriens": "Luzern",
    "6000": "Luzern", "6003": "Luzern", "6004": "Luzern", "6005": "Luzern",
    # St. Gallen
    "st. gallen": "St. Gallen", "st.gallen": "St. Gallen", "sankt gallen": "St. Gallen",
    "9000": "St. Gallen", "9001": "St. Gallen", "9004": "St. Gallen", "9006": "St. Gallen",
    # Lugano
    "lugano": "Lugano",
    "6900": "Lugano", "6901": "Lugano", "6902": "Lugano",
    # Weitere
    "neuchatel": "Neuchatel", "neuchâtel": "Neuchatel",
    "fribourg": "Fribourg", "freiburg": "Fribourg", "bulle": "Fribourg",
    "sion": "Sion", "sierre": "Sierre",
    "biel": "Biel", "bienne": "Biel",
    "schaffhausen": "Schaffhausen", "chur": "Chur", "aarau": "Aarau",
    "solothurn": "Solothurn", "egerkingen": "Solothurn", "olten": "Solothurn",
    "thun": "Thun",
    "visp": "Visp", "martigny": "Martigny", "montreux": "Montreux",
    "frauenfeld": "Frauenfeld", "winterthur": "Winterthur",
}

# HUMAN: Zuordnung Stadt -> BFS-Grossregion (7 Regionen + "Andere")
# Basis: offizielle BFS NUTS-2 Regionenklassifikation
STADT_ZU_REGION = {
    "Zuerich":      "Zürich",
    "Winterthur":   "Zürich",
    "Basel":        "Nordwestschweiz",
    "Aarau":        "Nordwestschweiz",
    "Bern":         "Espace Mittelland",
    "Solothurn":    "Espace Mittelland",
    "Fribourg":     "Espace Mittelland",
    "Neuchatel":    "Espace Mittelland",
    "Thun":         "Espace Mittelland",
    "Biel":         "Espace Mittelland",
    "Genf":         "Genferseeregion",
    "Lausanne":     "Genferseeregion",
    "Sion":         "Genferseeregion",
    "Sierre":       "Genferseeregion",
    "Martigny":     "Genferseeregion",
    "Montreux":     "Genferseeregion",
    "Visp":         "Genferseeregion",
    "Zug":          "Zentralschweiz",
    "Luzern":       "Zentralschweiz",
    "St. Gallen":   "Ostschweiz",
    "Schaffhausen": "Ostschweiz",
    "Chur":         "Ostschweiz",
    "Frauenfeld":   "Ostschweiz",
    "Lugano":       "Tessin",
}

def normalisiere_stadt(location_str):
    """HUMAN: Drei-Stufen-Matching: 1. PLZ, 2. Text-Match, 3. Fallback."""
    if not isinstance(location_str, str) or location_str.strip() == "":
        return "Andere"
    loc = location_str.lower().strip()

    # HUMAN: Stufe 1 - PLZ am String-Anfang
    plz_match = re.match(r"^(\d{4})", loc)
    if plz_match:
        plz = plz_match.group(1)
        if plz in STADT_MAPPING:
            return STADT_MAPPING[plz]

    # KI-ASSISTIERT: Laengste Keys zuerst sortieren - wichtig damit "st. gallen"
    # vor "gallen" gematcht wird. Trick von Claude empfohlen.
    for key in sorted(STADT_MAPPING.keys(), key=len, reverse=True):
        if key in loc:
            return STADT_MAPPING[key]

    # HUMAN: Fallback - ersten Teil vor Komma/Slash nehmen
    erster_teil = location_str.split(",")[0].split("/")[0].strip()
    return erster_teil if erster_teil else "Andere"

df_jobs["stadt_normalisiert"] = df_jobs["location"].apply(normalisiere_stadt)
df_jobs["bfs_region"]         = df_jobs["stadt_normalisiert"].map(STADT_ZU_REGION).fillna("Andere")

print("Stadtverteilung (Top 10):")
print(df_jobs["stadt_normalisiert"].value_counts().head(10))
print("\nBFS-Regionen:")
print(df_jobs["bfs_region"].value_counts())

# =============================================================================
# 7. BRANCHE -> BFS-WIRTSCHAFTSZWEIG (18 BRANCHEN - NEUER SCRAPER)
# =============================================================================
# HUMAN: Dieses Mapping ist eine bewusste konzeptionelle Entscheidung des Autors.
# jobs.ch arbeitet mit eigenen Kategorie-IDs, BFS mit NOGA-Klassifikation.
# Ich habe manuell die beste Entsprechung pro Branche gewaehlt.
# 18 Branchen in 3 Lohnkategorien gruppiert fuer bessere Visualisierung.

print("\n" + "=" * 60)
print("SCHRITT 7: Branche -> BFS-Wirtschaftszweig (18 Branchen)")
print("=" * 60)

# HUMAN: Mapping komplett vom Autor - exakte BFS-Bezeichnungen verwendet
# Hochlohn-Branchen: typisch >8000 CHF/Monat
# Mittellohn: 6000-8000 CHF/Monat
# Tieflohn: <6000 CHF/Monat
CATEGORY_TO_BFS = {
    # Hochlohn
    "Banken / Finanzinstitute":       "Finanz- u. Versicherungsdienstleistungen",
    "Chemie / Pharma":                "Herst. v. pharmazeutischen Erzeugnissen",
    "Informatik / Telekommunikation": "Informationstechnologie u. Informationsdienstl.",
    "Rechts- / Wirtschaftsberatung":  "Freiberufliche, wissenschaftliche und technische Dienstl.",
    "Versicherungen":                 "Versicherungen",
    "Medizinaltechnik":               "Herst. v. Datenverarbeitungsge., elektron. u. opt. Erz.; Uhren",
    # Mittellohn
    "Baugewerbe / Immobilien":        "Baugewerbe",
    "Beratung diverse":               "Freiberufliche, wissenschaftliche und technische Dienstl.",
    "Bildungswesen":                  "Erziehung und Unterricht",
    "Energie / Wasserwirtschaft":     "Energieversorgung",
    "Gewerbe / Handwerk allgemein":   "Verarbeitendes Gewerbe/Herst. v. Waren",
    "Oeffentliche Verwaltung":        "Öffentl. Verwaltung, Verteidigung; Sozialvers.",
    "Transport / Logistik":           "Verkehr u. Lagerei",
    "Maschinen / Anlagenbau":         "Maschinenbau",
    # Tieflohn
    "Detail / Grosshandel":           "Handel; Instandhaltung u. Rep. von Motorfahrz.",
    "Gastgewerbe / Hotellerie":       "Gastgewerbe/Beherbergung u. Gastronomie",
    "Gesundheits / Sozialwesen":      "Gesundheits- u. Sozialwesen",
    "Industrie diverse":              "Verarbeitendes Gewerbe/Herst. v. Waren",
}

# HUMAN: Lohnkategorie fuer Farbkodierung in Visualisierungen
LOHNKATEGORIE = {
    "Banken / Finanzinstitute":       "Hochlohn",
    "Chemie / Pharma":                "Hochlohn",
    "Informatik / Telekommunikation": "Hochlohn",
    "Rechts- / Wirtschaftsberatung":  "Hochlohn",
    "Versicherungen":                 "Hochlohn",
    "Medizinaltechnik":               "Hochlohn",
    "Baugewerbe / Immobilien":        "Mittellohn",
    "Beratung diverse":               "Mittellohn",
    "Bildungswesen":                  "Mittellohn",
    "Energie / Wasserwirtschaft":     "Mittellohn",
    "Gewerbe / Handwerk allgemein":   "Mittellohn",
    "Oeffentliche Verwaltung":        "Mittellohn",
    "Transport / Logistik":           "Mittellohn",
    "Maschinen / Anlagenbau":         "Mittellohn",
    "Detail / Grosshandel":           "Tieflohn",
    "Gastgewerbe / Hotellerie":       "Tieflohn",
    "Gesundheits / Sozialwesen":      "Tieflohn",
    "Industrie diverse":              "Tieflohn",
}

df_jobs["wirtschaftszweig_bfs"] = df_jobs["category"].map(CATEGORY_TO_BFS).fillna("Andere")
df_jobs["lohnkategorie"]        = df_jobs["category"].map(LOHNKATEGORIE).fillna("Andere")

print("Branchen-Mapping:")
print(df_jobs.groupby("category")["wirtschaftszweig_bfs"].first().to_string())

# =============================================================================
# 8. BFS-DATENSATZ BEREINIGEN
# =============================================================================
# HUMAN: Standard Pandas-Bereinigung

print("\n" + "=" * 60)
print("SCHRITT 8: BFS-Datensatz bereinigen")
print("=" * 60)

df_bfs.columns = df_bfs.columns.str.strip().str.lower()
df_bfs["medianlohn_chf"] = pd.to_numeric(df_bfs["medianlohn_chf"], errors="coerce")
df_bfs = df_bfs.dropna(subset=["medianlohn_chf"])

for col in df_bfs.columns:
    if df_bfs[col].dtype == object:
        df_bfs[col] = df_bfs[col].astype(str).str.strip()

# KI-ASSISTIERT: groupby-Aggregation mit Rename - Standard Pandas-Pattern,
# aber von Claude strukturiert empfohlen
df_bfs_agg = (
    df_bfs
    .groupby(["region", "wirtschaftszweig"], as_index=False)["medianlohn_chf"]
    .median()
    .rename(columns={
        "region":           "bfs_region",
        "wirtschaftszweig": "wirtschaftszweig_bfs",
        "medianlohn_chf":   "bfs_medianlohn_chf",
    })
)

# HUMAN: Fallback-Idee selbst: Wenn Region+Branche keinen Match gibt,
# nimm Schweiz-Gesamtmedian pro Branche. Wichtig damit kein Job unmapped bleibt.
df_bfs_fallback = (
    df_bfs[df_bfs["region"] == "Schweiz"]
    .rename(columns={
        "wirtschaftszweig": "wirtschaftszweig_bfs",
        "medianlohn_chf":   "bfs_medianlohn_fallback",
    })[["wirtschaftszweig_bfs", "bfs_medianlohn_fallback"]]
)

print(f"BFS aggregiert (Region+Branche): {df_bfs_agg.shape[0]} Eintraege")
print(f"BFS Fallback (Schweiz-Gesamt)  : {df_bfs_fallback.shape[0]} Eintraege")

# HUMAN: Debug-Output aller verfuegbaren Wirtschaftszweige (geholfen beim Mapping erstellen)
print("\nBFS Wirtschaftszweige verfuegbar:")
for w in sorted(df_bfs["wirtschaftszweig"].unique()):
    print(f"  {w}")

# =============================================================================
# 9. MERGE: JOBS + BFS (ZWEISTUFIG)
# =============================================================================
# HUMAN: Der zweistufige Merge ist eine konzeptionelle Entscheidung des Autors.
# Ziel: 100% BFS-Match-Rate. Stufe 1 matched exakt (Region+Branche), Stufe 2
# faengt alles andere ueber Schweiz-Gesamtwerte pro Branche auf.

print("\n" + "=" * 60)
print("SCHRITT 9: Merge Jobs + BFS")
print("=" * 60)

# HUMAN: Stufe 1 - Praeziser Match
df_merged = df_jobs.merge(
    df_bfs_agg,
    on=["bfs_region", "wirtschaftszweig_bfs"],
    how="left",
)

# HUMAN: Stufe 2 - Fallback ueber Schweiz-Gesamt
df_merged = df_merged.merge(
    df_bfs_fallback,
    on="wirtschaftszweig_bfs",
    how="left",
)
df_merged["bfs_medianlohn_chf"] = df_merged["bfs_medianlohn_chf"].fillna(
    df_merged["bfs_medianlohn_fallback"]
)
df_merged = df_merged.drop(columns=["bfs_medianlohn_fallback"])

# HUMAN: Diskrepanz-Metriken - Kern-Insight fuer die finale Heatmap.
# Positive Werte = Inserat zahlt mehr als BFS-Median (= Positiv-Selektion)
# Negative Werte = Inserat zahlt weniger (= Benchmark-Unterschreitung)
df_merged["lohn_diskrepanz_chf"] = (
    df_merged["gehalt_monat_chf"] - df_merged["bfs_medianlohn_chf"]
).round(0)
df_merged["lohn_diskrepanz_pct"] = (
    df_merged["lohn_diskrepanz_chf"] / df_merged["bfs_medianlohn_chf"] * 100
).round(1)

print(f"Merge-Ergebnis     : {df_merged.shape[0]} Zeilen")
print(f"BFS-Matches gesamt : {df_merged['bfs_medianlohn_chf'].notna().sum()}")
print(f"Diskrepanz-Daten   : {df_merged['lohn_diskrepanz_chf'].notna().sum()}")

# =============================================================================
# 10. FINALER DATENSATZ SPEICHERN
# =============================================================================
# HUMAN: Spalten-Reihenfolge und Auswahl bewusst gewaehlt fuer bessere
# Lesbarkeit im finalen CSV (erst Identifikation, dann Kategorisierung,
# dann Kernmetriken, dann Rohdaten).

print("\n" + "=" * 60)
print("SCHRITT 10: merged_dataset.csv speichern")
print("=" * 60)

# KI-ASSISTIERT: Liste-zu-String-Serialisierung fuer CSV - kleine technische Hilfe
df_merged["skills_liste"] = df_merged["skills_liste"].apply(
    lambda x: " | ".join(x) if isinstance(x, list) else ""
)

# HUMAN: Spalten-Reihenfolge selbst bestimmt
spalten_final = [
    "job_id", "job_title", "company", "location",
    "stadt_normalisiert", "bfs_region",
    "category", "lohnkategorie", "wirtschaftszweig_bfs",
    "seniority", "contract_type",
    "salary_range", "gehalt_monat_chf", "gehalt_jahr_chf",
    "bfs_medianlohn_chf", "lohn_diskrepanz_chf", "lohn_diskrepanz_pct",
    "skills_liste", "skills_anzahl",
    "date_posted", "job_url",
]
spalten_final = [s for s in spalten_final if s in df_merged.columns]
df_final = df_merged[spalten_final].copy()

df_final.to_csv("merged_dataset.csv", index=False, encoding="utf-8-sig")

# HUMAN: Separater Datensatz nur mit Gehaltsangaben fuer Gehalts-Analysen
df_mit_gehalt = df_final[df_final["gehalt_monat_chf"].notna()].copy()
df_mit_gehalt.to_csv("merged_dataset_mit_gehalt.csv", index=False, encoding="utf-8-sig")

print(f"Gespeichert: merged_dataset.csv")
print(f"  Zeilen              : {df_final.shape[0]}")
print(f"  Spalten             : {df_final.shape[1]}")
print(f"  Gehaelter           : {df_final['gehalt_monat_chf'].notna().sum()}")
print(f"  BFS-Matches         : {df_final['bfs_medianlohn_chf'].notna().sum()}")
print(f"  Diskrepanz-Daten    : {df_final['lohn_diskrepanz_chf'].notna().sum()}")
print(f"  Mit Gehalt (separat): {len(df_mit_gehalt)}")

print("\nVorschau:")
print(df_final[[
    "job_title", "category", "stadt_normalisiert", "seniority",
    "gehalt_monat_chf", "bfs_medianlohn_chf", "lohn_diskrepanz_pct"
]].head(5).to_string())

print("\n" + "=" * 60)
print("Fertig. Output: merged_dataset.csv + merged_dataset_mit_gehalt.csv")
print("=" * 60)