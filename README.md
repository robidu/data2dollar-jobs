# From Data2Dollar - Schweizer Jobmarkt 2026

**HSG Universität St. Gallen | FS 2026**

## Projektbeschreibung
Analyse des Schweizer Jobmarkts 2026: Welche Skills zahlen sich aus und wo bezahlt die Schweiz am besten?

## Datenquellen
- **jobs.ch** (Web Scraping mit Scrapy) - 320 Stelleninserate aus 8 Branchen
- **BFS Lohnstrukturerhebung 2024** (CKAN API via opendata.swiss)

## Dateien
- `jobs_ch_scraper.py` - Scrapy Spider für jobs.ch
- `bfs_lohndaten_ckan.py` - BFS API Abfrage
- `cleaning.py` - Datenbereinigung und Merge
- `visualisierungen.py` - 5 Visualisierungen
- `rohdaten_jobs.csv` - Rohdaten jobs.ch
- `lohndaten_bfs.csv` - BFS Medianlöhne
- `merged_dataset.csv` - Bereinigter Datensatz

## KI-Nutzung
Code wurde mit GitHub Copilot und Claude (Anthropic) als KI-Assistenten erstellt.
Alle KI-generierten Abschnitte sind als solche deklariert.

## Resultate
5 Visualisierungen: Top Skills, Gehalt nach Stadt, Seniority vs. Gehalt,
Arbeitsmodell nach Branche, Lohn-Lücke BFS vs. Inserate
