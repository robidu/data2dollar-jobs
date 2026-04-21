#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
bfs_lohndaten_ckan.py - BFS Lohnstrukturerhebung via CKAN API

Projekt: Swiss Job Market 2026 (HSG, From Data2Dollar)
Ziel: Medianlohn nach Grossregion und Wirtschaftszweig.

Datensatz: T1-GR - Monatlicher Bruttolohn nach Wirtschaftszweigen
und Grossregionen (Privater und öffentlicher Sektor zusammen)

Excel-Struktur (bekannt):
- Zeilen 0-2: Metadaten
- Zeile 3: Erste Header-Zeile (Regionen, Teil 1)
- Zeile 4: Zweite Header-Zeile (Regionen, Teil 2)
- Zeile 5: Leer
- Zeile 6+: Daten (NOGA-Code | Wirtschaftszweig | leer | CH | Reg1 | ...)

Ausführen:
    python3 bfs_lohndaten_ckan.py

Output: lohndaten_bfs.csv
"""

import io
import re
import sys

import pandas as pd
import requests

CKAN_SEARCH_URL = "https://ckan.opendata.swiss/api/3/action/package_search"
OUTPUT_FILE = "lohndaten_bfs.csv"
TIMEOUT = 60

SEARCH_QUERIES = [
    'monatlicher Bruttolohn Grossregion',
    'Lohnstrukturerhebung Grossregion Wirtschaftszweig',
    'salaire mensuel brut grande région',
]

# Bekannte URL der deutschen Excel-Version (T1-GR).
# BFS liefert manchmal die französische Version - diese URL ist die deutsche.
# Wird als direkter Download verwendet statt CKAN-Suche.
BFS_DEUTSCHE_URL = "https://dam-api.bfs.admin.ch/hub/api/dam/assets/21224998/master"

# Grossregionen in der richtigen Reihenfolge (aus Excel-Struktur bekannt)
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
    if isinstance(value, dict):
        for lang in ["de", "en", "fr", "it"]:
            v = value.get(lang)
            if v:
                return str(v)
        return ""
    return str(value) if value else ""


def search_and_download() -> pd.DataFrame:
    """Sucht Datensatz und lädt Excel herunter."""
    seen_ids = set()
    all_results = []

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
            print(f"[WARN] {e}")

    print(f"[INFO] Datensätze gefunden: {len(all_results)}")

    # Besten Datensatz wählen
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
                    # Excel: grössten Sheet nehmen
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


def parse_bfs_excel(df: pd.DataFrame) -> pd.DataFrame:
    """Verarbeitet das T1-GR Excel mit bekannter Struktur.

    Struktur:
    Zeile 3: ' T1_gr' | nan | nan | ' Schweiz' | ' Genfersee-' | ...
    Zeile 4: ' Wirtschaftszweige' | nan | nan | nan | ' region' | ...
    Zeile 6+: NOGA-Code | Bezeichnung | nan | Wert_CH | Wert_GS | ...
    """
    print("[INFO] Verarbeite Excel-Struktur...")

    # Zeilen 3+4 kombinieren für Spaltenheader
    row3 = [str(v).strip() for v in df.iloc[3].tolist()]
    row4 = [str(v).strip() for v in df.iloc[4].tolist()]

    # Kombinierte Spaltenbezeichnungen
    combined_headers = []
    for r3, r4 in zip(row3, row4):
        r3 = r3 if r3.lower() != "nan" else ""
        r4 = r4 if r4.lower() != "nan" else ""
        combined = f"{r3} {r4}".strip()
        combined_headers.append(combined)

    print(f"[INFO] Kombinierte Headers: {combined_headers}")

    # Daten ab Zeile 6
    data = df.iloc[6:].copy()
    data.columns = range(len(data.columns))
    data = data.reset_index(drop=True)

    # Spalten 0=NOGA-Code, 1=Wirtschaftszweig, 2=leer, 3=CH, 4=GS, 5=EM, 6=NW, 7=ZH, 8=OS, 9=ZS, 10=TI
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

        # Leere Zeilen und Aggregate überspringen
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

            # BFS verwendet eckige Klammern für Schätzwerte: [6 522]
            raw_val = re.sub(r"[\[\]]", "", raw_val)
            # Non-breaking spaces und normale Spaces entfernen
            raw_val = raw_val.replace("\xa0", "").replace(" ", "").replace("'", "")

            # Nicht verfügbare Werte überspringen
            if raw_val in ("-", "*", "...", "", "nan", "none"):
                continue

            try:
                lohn = float(raw_val.replace(",", "."))
                if 1000 < lohn < 30000:  # Plausibilitätsprüfung CHF/Monat
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


def download_direct(url: str) -> pd.DataFrame:
    """Lädt Excel direkt von bekannter BFS-URL (deutsche Version)."""
    print(f"[INFO] Lade deutsche Version direkt von: {url}")
    r = requests.get(url, timeout=TIMEOUT)
    r.raise_for_status()
    sheets = pd.read_excel(io.BytesIO(r.content), sheet_name=None, header=None)
    best = max(sheets.items(), key=lambda x: x[1].size if x[1] is not None else 0)
    print(f"[INFO] Excel Sheet: {best[0]}, Shape: {best[1].shape}")
    return best[1]


def is_german(df: pd.DataFrame) -> bool:
    """Prüft ob das Excel auf Deutsch ist (nicht Französisch/Italienisch)."""
    sample = " ".join(str(v) for v in df.iloc[:8].values.flatten()).lower()
    french_indicators = ["secteur", "branches économiques", "salaire", "suisse romande"]
    german_indicators = ["wirtschaftszweig", "sektor", "schweiz", "bruttolohn"]
    fr_count = sum(1 for w in french_indicators if w in sample)
    de_count = sum(1 for w in german_indicators if w in sample)
    return de_count >= fr_count


def main():
    try:
        # Zuerst direkt die bekannte deutsche URL versuchen
        raw_df = download_direct(BFS_DEUTSCHE_URL)

        # Sprachprüfung - falls nicht Deutsch, CKAN-Suche als Fallback
        if not is_german(raw_df):
            print("[WARN] Deutsche URL lieferte nicht-deutsche Version - versuche CKAN-Suche")
            raw_df = search_and_download()
            if not is_german(raw_df):
                print("[WARN] Auch CKAN lieferte nicht-deutsche Version - fahre trotzdem fort")

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
        print(f"\n❌ Fehler: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()