"""
=============================================================================
cleaning.py - Datenbereinigung Schweizer Jobmarkt 2026
=============================================================================
Projekt : From Data2Dollar | HSG FS 2026
Beschreibung: Bereinigt rohdaten_jobs.csv und lohndaten_bfs.csv,
              extrahiert Skills und Seniority, normalisiert Staedte,
              merged beide Datensaetze.
Output  : merged_dataset.csv
=============================================================================
"""

import pandas as pd
import numpy as np
import re

# =============================================================================
# 1. DATEN EINLESEN
# =============================================================================

print("=" * 60)
print("SCHRITT 1: Daten einlesen")
print("=" * 60)

df_jobs = pd.read_csv("rohdaten_jobs.csv")
df_bfs  = pd.read_csv("lohndaten_bfs.csv")

print(f"Jobs-Datensatz : {df_jobs.shape[0]} Zeilen, {df_jobs.shape[1]} Spalten")
print(f"BFS-Datensatz  : {df_bfs.shape[0]} Zeilen, {df_bfs.shape[1]} Spalten")
print(f"\nFehlende Werte (Jobs):\n{df_jobs.isnull().sum()}")

# =============================================================================
# 2. JOBS - GRUNDBEREINIGUNG
# =============================================================================

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

for col in df_jobs.columns:
    if df_jobs[col].dtype == object:
        df_jobs[col] = df_jobs[col].astype(str).str.strip().replace("nan", "")

print(f"Nach Bereinigung: {df_jobs.shape[0]} Zeilen")

# =============================================================================
# 3. GEHALTSANGABEN PARSEN - JAHRESGEHALT -> MONATSGEHALT
# =============================================================================

print("\n" + "=" * 60)
print("SCHRITT 3: Gehaltsangaben parsen")
print("=" * 60)

def parse_gehalt(salary_str):
    """
    Parst 'CHF 95375 - 135375 (jobs.ch estimate)' -> 9590 CHF/Monat.
    Jahresgehalt (>25000) wird automatisch durch 12 geteilt.
    """
    if not isinstance(salary_str, str) or salary_str.strip() == "":
        return np.nan
    zahlen = re.findall(r"[\d']+", salary_str)
    zahlen = [int(z.replace("'", "")) for z in zahlen if len(z.replace("'", "")) >= 3]
    if len(zahlen) >= 2:
        mittelwert = np.mean(zahlen[:2])
    elif len(zahlen) == 1:
        mittelwert = float(zahlen[0])
    else:
        return np.nan
    # Jahresgehalt erkennen und auf Monat umrechnen
    if mittelwert > 25000:
        return round(mittelwert / 12, 0)
    return mittelwert

df_jobs["gehalt_monat_chf"] = df_jobs["salary_range"].apply(parse_gehalt)

# Plausibilitaet: 3000 - 25000 CHF/Monat
maske = (
    df_jobs["gehalt_monat_chf"].notna() &
    ((df_jobs["gehalt_monat_chf"] < 3000) | (df_jobs["gehalt_monat_chf"] > 25000))
)
df_jobs.loc[maske, "gehalt_monat_chf"] = np.nan
df_jobs["gehalt_jahr_chf"] = df_jobs["gehalt_monat_chf"] * 13

n_gehalt = df_jobs["gehalt_monat_chf"].notna().sum()
print(f"Gehaelter geparst: {n_gehalt} von {len(df_jobs)}")
if n_gehalt > 0:
    print(f"Bereich: CHF {df_jobs['gehalt_monat_chf'].min():.0f} - "
          f"{df_jobs['gehalt_monat_chf'].max():.0f} / Monat")

# =============================================================================
# 4. SENIORITY AUS JOBTITEL EXTRAHIEREN
# =============================================================================

print("\n" + "=" * 60)
print("SCHRITT 4: Seniority extrahieren")
print("=" * 60)

def extrahiere_seniority(titel):
    if not isinstance(titel, str):
        return "Mid"
    t = titel.lower()
    if any(w in t for w in ["head of", "lead", "chief", "cto", "cfo", "cio",
                             "vp ", "vice president", "direktor", "director",
                             "manager", "leiter", "leiterin", "responsable"]):
        return "Lead/Manager"
    if any(w in t for w in ["senior", "sr.", "sr ", "principal",
                             "expert", "spezialist", "experienced"]):
        return "Senior"
    if any(w in t for w in ["junior", "jr.", "jr ", "trainee", "praktikum",
                             "werkstudent", "einstieg", "entry", "graduate",
                             "intern", "stagiaire", "apprentice"]):
        return "Junior"
    return "Mid"

df_jobs["seniority"] = df_jobs["job_title"].apply(extrahiere_seniority)
print("Seniority-Verteilung:")
print(df_jobs["seniority"].value_counts())

# =============================================================================
# 5. SKILLS AUS skills_text EXTRAHIEREN
# =============================================================================

print("\n" + "=" * 60)
print("SCHRITT 5: Skills extrahieren")
print("=" * 60)

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
    for skill in SKILL_LISTE:
        muster = r"\b" + re.escape(skill.lower()) + r"\b"
        if re.search(muster, text_lower):
            skill_norm = SKILL_NORMALISIERUNG.get(skill.lower(), skill)
            if skill_norm not in gefundene:
                gefundene.append(skill_norm)
    return gefundene

df_jobs["skills_liste"]  = df_jobs["skills_text"].apply(extrahiere_skills)
df_jobs["skills_anzahl"] = df_jobs["skills_liste"].apply(len)

alle_skills = [s for liste in df_jobs["skills_liste"] for s in liste]
print(f"Durchschnittliche Skills pro Inserat: {df_jobs['skills_anzahl'].mean():.1f}")
print(f"\nTop 10 Skills:\n{pd.Series(alle_skills).value_counts().head(10)}")

# =============================================================================
# 6. STADTNAME NORMALISIEREN
# =============================================================================

print("\n" + "=" * 60)
print("SCHRITT 6: Stadtname normalisieren")
print("=" * 60)

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
    "3000": "Bern", "3001": "Bern", "3010": "Bern",
    "3011": "Bern", "3012": "Bern", "3013": "Bern",
    # Genf
    "genf": "Genf", "geneva": "Genf", "geneve": "Genf",
    "genève": "Genf", "carouge": "Genf", "plan-les-ouates": "Genf",
    "lancy": "Genf", "meyrin": "Genf", "vernier": "Genf",
    "1201": "Genf", "1202": "Genf", "1203": "Genf", "1204": "Genf",
    "1205": "Genf", "1206": "Genf", "1207": "Genf", "1208": "Genf",
    "1209": "Genf", "1210": "Genf", "1211": "Genf", "1212": "Genf",
    "1213": "Genf", "1214": "Genf", "1215": "Genf", "1216": "Genf",
    "1217": "Genf", "1218": "Genf", "1219": "Genf", "1220": "Genf",
    "1222": "Genf", "1223": "Genf", "1224": "Genf", "1225": "Genf",
    "1226": "Genf", "1227": "Genf", "1228": "Genf",
    # Lausanne
    "lausanne": "Lausanne", "renens": "Lausanne",
    "ecublens": "Lausanne", "crissier": "Lausanne",
    "1000": "Lausanne", "1001": "Lausanne", "1002": "Lausanne",
    "1003": "Lausanne", "1004": "Lausanne", "1005": "Lausanne",
    "1006": "Lausanne", "1007": "Lausanne", "1010": "Lausanne",
    "1012": "Lausanne", "1015": "Lausanne", "1018": "Lausanne",
    # Zug
    "zug": "Zug", "baar": "Zug", "steinhausen": "Zug",
    "6300": "Zug", "6301": "Zug", "6302": "Zug", "6340": "Zug",
    # Luzern
    "luzern": "Luzern", "lucerne": "Luzern",
    "6000": "Luzern", "6002": "Luzern", "6003": "Luzern",
    "6004": "Luzern", "6005": "Luzern", "6006": "Luzern",
    # St. Gallen
    "st. gallen": "St. Gallen", "st gallen": "St. Gallen",
    "9000": "St. Gallen", "9001": "St. Gallen",
    # Lugano
    "lugano": "Lugano",
    "6900": "Lugano", "6901": "Lugano", "6902": "Lugano",
    # Weitere Staedte
    "aarau": "Aarau",
    "solothurn": "Solothurn",
    "fribourg": "Fribourg", "freiburg": "Fribourg",
    "neuchâtel": "Neuchatel", "neuchatel": "Neuchatel",
    "sion": "Sion", "sierre": "Sierre",
    "martigny": "Martigny", "1920": "Martigny", "1921": "Martigny",
    "visp": "Visp",
    "thun": "Thun",
    "biel": "Biel", "bienne": "Biel",
    "schaffhausen": "Schaffhausen",
    "chur": "Chur",
    "1026": "Lausanne",   # Denges -> Lausanne Region
    "1028": "Lausanne",   # Preverenges
    "1030": "Lausanne",   # Bussigny
}

STADT_ZU_REGION = {
    "Zuerich":      "Zürich",
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
    "Visp":         "Genferseeregion",
    "Zug":          "Zentralschweiz",
    "Luzern":       "Zentralschweiz",
    "St. Gallen":   "Ostschweiz",
    "Schaffhausen": "Ostschweiz",
    "Chur":         "Ostschweiz",
    "Lugano":       "Tessin",
}

def normalisiere_stadt(location_str):
    if not isinstance(location_str, str) or location_str.strip() == "":
        return "Andere"
    loc = location_str.lower().strip()
    # PLZ am Anfang (z.B. "1920 Martigny")
    plz_match = re.match(r"^(\d{4})", loc)
    if plz_match:
        plz = plz_match.group(1)
        if plz in STADT_MAPPING:
            return STADT_MAPPING[plz]
    # Text-Matching (laengste Keys zuerst)
    for key in sorted(STADT_MAPPING.keys(), key=len, reverse=True):
        if key in loc:
            return STADT_MAPPING[key]
    # Fallback: ersten Textteil nehmen
    erster_teil = location_str.split(",")[0].split("/")[0].strip()
    return erster_teil if erster_teil else "Andere"

df_jobs["stadt_normalisiert"] = df_jobs["location"].apply(normalisiere_stadt)
df_jobs["bfs_region"]         = df_jobs["stadt_normalisiert"].map(STADT_ZU_REGION).fillna("Andere")

print("Stadtverteilung (Top 10):")
print(df_jobs["stadt_normalisiert"].value_counts().head(10))
print("\nBFS-Regionen:")
print(df_jobs["bfs_region"].value_counts())

# =============================================================================
# 7. BRANCHE -> BFS-WIRTSCHAFTSZWEIG (EXAKTE BFS-NAMEN)
# =============================================================================

print("\n" + "=" * 60)
print("SCHRITT 7: Branche -> BFS-Wirtschaftszweig")
print("=" * 60)

# WICHTIG: Exakte Bezeichnungen aus lohndaten_bfs.csv verwenden
BRANCHE_MAPPING = {
    "IT/Telecom":
        "Informationstechnologie u. Informationsdienstl.",
    "Finance/Trusts/Real Estate":
        "Finanz- u. Versicherungsdienstleistungen",
    "Banking/Insurance":
        "Finanz- u. Versicherungsdienstleistungen",
    "Marketing/Communications":
        "Sonst. wirtschaftliche Dienstleistungen",
    "Consulting/Company Development":
        "Freiberufliche, wissenschaftliche und technische Dienstl.",
    "Engineering/Watches":
        "Herst. v. Datenverarbeitungsge., elektron. u. opt. Erz.; Uhren",
    "Chemical/Pharma/Biotech":
        "Herst. v. pharmazeutischen Erzeugnissen",
    "Construction/Architecture":
        "Baugewerbe",
}

df_jobs["wirtschaftszweig_bfs"] = df_jobs["category"].map(BRANCHE_MAPPING).fillna("Andere")
print("Branchen-Mapping:")
print(df_jobs.groupby("category")["wirtschaftszweig_bfs"].first().to_string())

# =============================================================================
# 8. BFS-DATENSATZ BEREINIGEN
# =============================================================================

print("\n" + "=" * 60)
print("SCHRITT 8: BFS-Datensatz bereinigen")
print("=" * 60)

df_bfs.columns = df_bfs.columns.str.strip().str.lower()
df_bfs["medianlohn_chf"] = pd.to_numeric(df_bfs["medianlohn_chf"], errors="coerce")
df_bfs = df_bfs.dropna(subset=["medianlohn_chf"])

for col in df_bfs.columns:
    if df_bfs[col].dtype == object:
        df_bfs[col] = df_bfs[col].astype(str).str.strip()

# Aggregieren: Medianlohn pro Region + Wirtschaftszweig
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

# Fallback: Schweiz-Gesamt pro Wirtschaftszweig
df_bfs_fallback = (
    df_bfs[df_bfs["region"] == "Schweiz"]
    .rename(columns={
        "wirtschaftszweig": "wirtschaftszweig_bfs",
        "medianlohn_chf":   "bfs_medianlohn_fallback",
    })[["wirtschaftszweig_bfs", "bfs_medianlohn_fallback"]]
)

print(f"BFS aggregiert (Region+Branche): {df_bfs_agg.shape[0]} Eintraege")
print(f"BFS Fallback (Schweiz-Gesamt)  : {df_bfs_fallback.shape[0]} Eintraege")

# Verfuegbare Wirtschaftszweige in BFS ausgeben (zum Debuggen)
print("\nBFS Wirtschaftszweige verfuegbar:")
for w in sorted(df_bfs["wirtschaftszweig"].unique()):
    print(f"  {w}")

# =============================================================================
# 9. MERGE: JOBS + BFS (ZWEISTUFIG)
# =============================================================================

print("\n" + "=" * 60)
print("SCHRITT 9: Merge Jobs + BFS")
print("=" * 60)

# Stufe 1: Praeziser Merge mit Region + Branche
df_merged = df_jobs.merge(
    df_bfs_agg,
    on=["bfs_region", "wirtschaftszweig_bfs"],
    how="left",
)

# Stufe 2: Fallback auf Schweiz-Gesamt fuer nicht gematchte Zeilen
df_merged = df_merged.merge(
    df_bfs_fallback,
    on="wirtschaftszweig_bfs",
    how="left",
)
df_merged["bfs_medianlohn_chf"] = df_merged["bfs_medianlohn_chf"].fillna(
    df_merged["bfs_medianlohn_fallback"]
)
df_merged = df_merged.drop(columns=["bfs_medianlohn_fallback"])

# Diskrepanz berechnen (nur wo beide Werte vorhanden)
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

print("\n" + "=" * 60)
print("SCHRITT 10: merged_dataset.csv speichern")
print("=" * 60)

df_merged["skills_liste"] = df_merged["skills_liste"].apply(
    lambda x: " | ".join(x) if isinstance(x, list) else ""
)

spalten_final = [
    "job_id", "job_title", "company", "location",
    "stadt_normalisiert", "bfs_region",
    "category", "wirtschaftszweig_bfs",
    "seniority", "contract_type",
    "salary_range", "gehalt_monat_chf", "gehalt_jahr_chf",
    "bfs_medianlohn_chf", "lohn_diskrepanz_chf", "lohn_diskrepanz_pct",
    "skills_liste", "skills_anzahl",
    "date_posted", "job_url",
]
spalten_final = [s for s in spalten_final if s in df_merged.columns]
df_final = df_merged[spalten_final].copy()

df_final.to_csv("merged_dataset.csv", index=False, encoding="utf-8-sig")

print(f"Gespeichert: merged_dataset.csv")
print(f"  Zeilen            : {df_final.shape[0]}")
print(f"  Spalten           : {df_final.shape[1]}")
print(f"  Gehaelter         : {df_final['gehalt_monat_chf'].notna().sum()}")
print(f"  BFS-Matches       : {df_final['bfs_medianlohn_chf'].notna().sum()}")
print(f"  Diskrepanz-Daten  : {df_final['lohn_diskrepanz_chf'].notna().sum()}")

print("\nVorschau:")
print(df_final[[
    "job_title", "stadt_normalisiert", "seniority",
    "gehalt_monat_chf", "bfs_medianlohn_chf", "lohn_diskrepanz_pct"
]].head(5).to_string())

print("\n" + "=" * 60)
print("Fertig. Output: merged_dataset.csv")
print("=" * 60)