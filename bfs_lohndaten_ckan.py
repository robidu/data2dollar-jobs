#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
=============================================================================
bfs_lohndaten_ckan.py - BFS Lohnstrukturerhebung via CKAN API
=============================================================================
Projekt      : From Data2Dollar | HSG FS 2026
Autor        : Robin D.
Ziel         : Medianloehne nach Grossregion und Wirtschaftszweig
               von opendata.swiss abrufen und als CSV speichern.
Output       : lohndaten_bfs.csv

-----------------------------------------------------------------------------
KI-DEKLARATION (vgl. KI_DEKLARATION.md)
-----------------------------------------------------------------------------
# HUMAN          = Konzeptionelle Entscheidungen (Queries, Scoring)
# KI-ASSISTIERT  = iterativ mit Claude/Copilot entwickelt
# VIBE-CODED     = primaer von KI, vom Autor verstanden (Excel-Parser)

Datensatz: T1-GR - Monatlicher Bruttolohn nach Wirtschaftszweigen
und Grossregionen (Privater und oeffentlicher Sektor zusammen)

Excel-Struktur (bekannt):
- Zeilen 0-2: Metadaten
- Zeile 3: Erste Header-Zeile (Regionen, Teil 1)
- Zeile 4: Zweite Header-Zeile (Regionen, Teil 2)
- Zeile 5: Leer
- Zeile 6+: Daten (NOGA-Code | Wirtschaftszweig | leer | CH | Reg1 | ...)

Ausführen:
    python3 bfs_lohndaten_ckan.py
=============================================================================
"""

import io
import re
import sys

import pandas as pd
import requests

# HUMAN: Konfiguration - CKAN-Endpoint und Query-Strategie vom Autor
CKAN_SEARCH_URL = "https://ckan.opendata.swiss/api/3/action/package_search"
OUTPUT_FILE = "lohndaten_bfs.csv"
TIMEOUT = 60

# HUMAN: Drei Queries in DE und FR um robusten Match zu erzielen. Die CKAN-API
# sucht nur mit dem angegebenen Text, also lohnt es sich mehrere Varianten zu
# probieren - manche BFS-Datensaetze sind nur auf Franzoesisch indexiert.
SEARCH_QUERIES = [
    'monatlicher Bruttolohn Grossregion',
    'Lohnstrukturerhebung Grossregion Wirtschaftszweig',
    'salaire mensuel brut grande région',
]

# HUMAN: BFS-Grossregionen in Standard-Reihenfolge wie im BFS Excel
REGION_NAMES = [
    "Schweiz",
    "Genferseeregion",
    "Espace Mittelland",
    "Nordwestschweiz",
    "Zürich",
    "Ostschweiz",
    "Zentralschweiz",
    "Tessin",
]


def flatten_lang(value) -> str:
    """
    KI-ASSISTIERT: Helper zum Abflachen von CKAN's Multi-Language-Dicts.
    CKAN gibt manchmal {"de": "...", "fr": "...", "en": "..."} zurueck.
    Nimm die erste verfuegbare Sprache in Reihenfolge DE > EN > FR > IT.
    """
    if isinstance(value, dict):
        for lang in ["de", "en", "fr", "it"]:
            v = value.get(lang)
            if v:
                return str(v)
        return ""
    return str(value) if value else ""


def search_and_download() -> pd.DataFrame:
    """Sucht Datensatz und laedt Excel herunter."""
    seen_ids = set()
    all_results = []

    # HUMAN: Suche mit allen 3 Query-Varianten, Deduplizierung per Package-ID
    for query in SEARCH_QUERIES:
        print(f"[INFO] CKAN-Suche: {query}")
        try:
            resp = requests.get(
                CKAN_SEARCH_URL,
                params={"q": query, "rows": 20},
                timeout=TIMEOUT,
            )
            resp.raise_for_status()
            data = resp.json()
            if not data.get("success"):
                continue
            for pkg in data["result"]["results"]:
                pid = pkg.get("id")
                if pid and pid not in seen_ids:
                    seen_ids.add(pid)
                    all_results.append(pkg)
        except requests.RequestException as e:
            # KI-ASSISTIERT: Fehlerbehandlung - bei Timeout einfach weiter machen
            print(f"[WARN] {e}")

    print(f"[INFO] Datensätze gefunden: {len(all_results)}")

    # HUMAN: Scoring-Funktion komplett vom Autor. Hintergrund: CKAN liefert
    # mehrere treffende Datensaetze, aber nicht alle haben die gewuenschte
    # Granularitaet (Region + Wirtschaftszweig). Scoring-Logik:
    # +20 wenn "grossregion" in Titel/Beschreibung
    # +10 wenn "wirtschaftszweig" oder "branche"
    # +10 wenn "bruttolohn"
    # -20 wenn "betriebe" (das waere ein Betriebsdatensatz, nicht Loehne)
    def score(pkg):
        text = (flatten_lang(pkg.get("title", "")) + " " +
                flatten_lang(pkg.get("notes", ""))).lower()
        s = 0
        if "grossregion" in text or "grande région" in text:
            s += 20
        if "wirtschaftszweig" in text or "branche" in text:
            s += 10
        if "bruttolohn" in text or "salaire" in text:
            s += 10
        if "betriebe" in text:
            s -= 20
        return s

    ranked = sorted(all_results, key=score, reverse=True)

    # HUMAN: Top-5 Datensaetze durchprobieren bis einer passt
    for dataset in ranked[:5]:
        title = flatten_lang(dataset.get("title", ""))
        resources = dataset.get("resources", [])

        for resource in resources:
            fmt = str(resource.get("format", "")).lower()
            if fmt not in ("xls", "xlsx", "csv"):
                continue

            url = resource.get("url", "")
            if not url:
                continue

            print(f"[INFO] Datensatz: {title}")
            print(f"[INFO] Format: {fmt.upper()} | URL: {url}")

            try:
                r = requests.get(url, timeout=TIMEOUT)
                r.raise_for_status()

                # KI-ASSISTIERT: CSV-Parsing mit Encoding/Separator-Fallback
                if fmt == "csv":
                    for enc in ["utf-8", "latin-1"]:
                        for sep in [";", ","]:
                            try:
                                df = pd.read_csv(
                                    io.BytesIO(r.content),
                                    encoding=enc, sep=sep, header=None
                                )
                                if df.shape[1] >= 3:
                                    print(f"[INFO] CSV geladen: {df.shape}")
                                    return df
                            except Exception:
                                continue
                else:
                    # VIBE-CODED: Excel mit multiplen Sheets - nimm das groesste Sheet.
                    # Idee war: Daten-Sheet ist immer das groesste. Alternative (nach
                    # Name suchen) waere fragil weil BFS Sheet-Namen teils aendert.
                    sheets = pd.read_excel(
                        io.BytesIO(r.content),
                        sheet_name=None,
                        header=None
                    )
                    best = max(
                        sheets.items(),
                        key=lambda x: x[1].size if x[1] is not None else 0
                    )
                    print(f"[INFO] Excel Sheet: {best[0]}, Shape: {best[1].shape}")
                    return best[1]

            except Exception as e:
                print(f"[WARN] Download fehlgeschlagen: {e}")
                continue

    raise RuntimeError("Kein Datensatz heruntergeladen.")


# VIBE-CODED: Diese gesamte Parser-Funktion wurde primaer von Claude generiert.
# Hintergrund: Die BFS T1-GR Excel-Datei hat eine sehr spezifische Struktur:
# - Zeilen 0-2: Metadaten (Titel, Quelle, etc.)
# - Zeile 3: Erste Header-Zeile (Regionennamen, Teil 1 - z.B. " Genfersee-")
# - Zeile 4: Zweite Header-Zeile (Regionennamen, Teil 2 - z.B. " region")
# - Zeile 5: Leer
# - Zeile 6+: Daten
# Der Parser kombiniert Zeile 3+4 zu finalen Headers, skippt Aggregate
# (SEKTOR, TOTAL), und normalisiert BFS-Wertformate (eckige Klammern fuer
# Schaetzwerte, non-breaking spaces, Apostrophe als Tausendertrenner).
# Vom Autor verstanden, getestet und angepasst (Plausibilitaetsschwellen sind vom Autor).
def parse_bfs_excel(df: pd.DataFrame) -> pd.DataFrame:
    """Verarbeitet das T1-GR Excel mit bekannter Struktur."""
    print("[INFO] Verarbeite Excel-Struktur...")

    # VIBE-CODED: Zeilen 3+4 kombinieren zu finalen Column-Headers
    row3 = [str(v).strip() for v in df.iloc[3].tolist()]
    row4 = [str(v).strip() for v in df.iloc[4].tolist()]

    combined_headers = []
    for r3, r4 in zip(row3, row4):
        r3 = r3 if r3.lower() != "nan" else ""
        r4 = r4 if r4.lower() != "nan" else ""
        combined = f"{r3} {r4}".strip()
        combined_headers.append(combined)

    print(f"[INFO] Kombinierte Headers: {combined_headers}")

    # VIBE-CODED: Daten ab Zeile 6
    data = df.iloc[6:].copy()
    data.columns = range(len(data.columns))
    data = data.reset_index(drop=True)

    # HUMAN: Spalten-Mapping selbst definiert - basierend auf manueller Analyse
    # der BFS-Excel in Excel-Vorschau
    col_wirtschaft = 1
    col_regionen = {
        "Schweiz": 3,
        "Genferseeregion": 4,
        "Espace Mittelland": 5,
        "Nordwestschweiz": 6,
        "Zürich": 7,
        "Ostschweiz": 8,
        "Zentralschweiz": 9,
        "Tessin": 10,
    }

    records = []
    for _, row in data.iterrows():
        wirtschaft = str(row[col_wirtschaft]).strip()

        # HUMAN: Filter - leere Zeilen, Aggregate (SEKTOR, TOTAL) und
        # zu kurze Eintraege ueberspringen
        if not wirtschaft or wirtschaft.lower() in ("nan", "", "none"):
            continue
        if wirtschaft.upper().startswith("SEKTOR") or wirtschaft.upper().startswith("TOTAL"):
            continue
        if len(wirtschaft) < 3:
            continue

        for region_name, col_idx in col_regionen.items():
            if col_idx >= len(row):
                continue

            raw_val = str(row[col_idx]).strip()

            # VIBE-CODED: BFS-spezifische Value-Normalisierung:
            # - Eckige Klammern fuer Schaetzwerte entfernen: [6 522] -> 6522
            # - Non-breaking spaces und normale Spaces entfernen
            # - CH-Apostrophe entfernen
            raw_val = re.sub(r"[\[\]]", "", raw_val)
            raw_val = raw_val.replace("\xa0", "").replace(" ", "").replace("'", "")

            # HUMAN: Not-Available-Marker die BFS verwendet: "-", "*", "..."
            if raw_val in ("-", "*", "...", "", "nan", "none"):
                continue

            try:
                lohn = float(raw_val.replace(",", "."))
                # HUMAN: Plausibilitaetsschwelle 1000-30000 CHF/Monat
                # vom Autor definiert (gleiche Logik wie in cleaning.py)
                if 1000 < lohn < 30000:
                    records.append({
                        "region": region_name,
                        "wirtschaftszweig": wirtschaft,
                        "medianlohn_chf": lohn,
                    })
            except ValueError:
                continue

    result = pd.DataFrame(records)
    result = result.drop_duplicates().reset_index(drop=True)
    return result


def main():
    """HUMAN: Orchestrierung - Download, Parse, Speichern, Zusammenfassung."""
    try:
        raw_df = search_and_download()

        print(f"\n[INFO] Rohformat: {raw_df.shape[0]} Zeilen x {raw_df.shape[1]} Spalten")
        print("[INFO] Erste 8 Zeilen:")
        for i in range(min(8, len(raw_df))):
            vals = [str(v)[:25] for v in raw_df.iloc[i].tolist()]
            print(f"  Zeile {i}: {vals}")

        clean_df = parse_bfs_excel(raw_df)

        if clean_df.empty:
            raise RuntimeError("Keine Daten nach Bereinigung.")

        clean_df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")

        print(f"\n✅ CSV gespeichert: {OUTPUT_FILE}")
        print(f"[INFO] Zeilen total: {len(clean_df)}")
        print(f"[INFO] Regionen ({clean_df['region'].nunique()}): "
              f"{sorted(clean_df['region'].unique().tolist())}")
        print(f"[INFO] Wirtschaftszweige: {clean_df['wirtschaftszweig'].nunique()}")
        print(f"[INFO] Lohn-Range: "
              f"CHF {clean_df['medianlohn_chf'].min():.0f} - "
              f"{clean_df['medianlohn_chf'].max():.0f}")
        print(f"\n[INFO] Vorschau:")
        print(clean_df.head(15).to_string())

    except Exception as e:
        # KI-ASSISTIERT: Traceback-Print fuer besseres Debugging
        print(f"\n❌ Fehler: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()