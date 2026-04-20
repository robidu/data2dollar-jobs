# From Data2Dollar - Schweizer Jobmarkt 2026

**HSG Universität St. Gallen | FS 2026**
**Dozent:** Prof. Dr. Arne Grüttner
**Autor:** Robin D.

---

## 1. Projektbeschreibung

Analyse des Schweizer Jobmarkts 2026 anhand von 320 realen Stelleninseraten (jobs.ch)
kombiniert mit offiziellen Lohndaten des Bundesamts für Statistik (BFS).

### Forschungsfragen
1. **Welche Skills werden 2026 am häufigsten nachgefragt?**
2. **Wie unterscheiden sich Gehälter zwischen den Schweizer Städten?**
3. **Wie stark korreliert Seniority mit dem Monatsgehalt?**
4. **Welche Branchen bieten am meisten Remote- / Hybrid-Arbeit?**
5. **Wie gross ist die Lücke zwischen Inserats-Gehältern und dem BFS-Medianlohn?**

### Personas (Zielgruppe der Insights)
- **Lena (23)**: Wirtschaftsinformatik-Studentin im letzten Semester. Will wissen, welche Skills sich zu lernen lohnen und wo Einstiegsgehälter am höchsten sind.
- **Marcus (41)**: Senior Consultant mit Familie. Überlegt Branchenwechsel und braucht Transparenz über Löhne, Seniority-Effekte und Arbeitsmodelle.

---

## 2. Datenquellen

| Quelle | Methode | Umfang |
|---|---|---|
| **jobs.ch** | Web Scraping via Scrapy | 320 Stelleninserate, 8 Branchen × 40 Jobs |
| **BFS Lohnstrukturerhebung 2024** | CKAN API (opendata.swiss) | 368 Zeilen, 8 Grossregionen × 48 Wirtschaftszweige |

### Rechtliche Grundlage Web Scraping
Die Datenerhebung auf jobs.ch erfolgt im Rahmen des **Urheberrechtsgesetz Art. 24d URG** (Werknutzung zum Zweck der wissenschaftlichen Forschung). Es wurden ausschliesslich öffentlich zugängliche Inserate im Rahmen eines studentischen Forschungsprojekts gesammelt. Der Scraper verwendet `DOWNLOAD_DELAY=3` Sekunden sowie `CONCURRENT_REQUESTS=1`, um die Server nicht zu belasten.

---

## 3. Setup & Ausführung

### Voraussetzungen
- Python 3.10+
- Pakete aus `requirements.txt`

### Installation
```bash
pip install -r requirements.txt
```

### Pipeline-Reihenfolge
```bash
# Schritt 1: Rohdaten von jobs.ch scrapen (~20 Min. wegen Rate-Limiting)
python3 jobs_ch_scraper.py

# Schritt 2: BFS-Lohndaten via CKAN API laden
python3 bfs_lohndaten_ckan.py

# Schritt 3: Daten bereinigen, Skills extrahieren, Datensätze mergen
python3 cleaning.py

# Schritt 4: 5 Visualisierungen erzeugen
python3 visualisierungen.py
```

---

## 4. Dateien im Repository

### Code
| Datei | Zweck |
|---|---|
| `jobs_ch_scraper.py` | Scrapy-Spider für jobs.ch (Multi-Strategy Extraction) |
| `bfs_lohndaten_ckan.py` | BFS-Datenabruf via CKAN API von opendata.swiss |
| `cleaning.py` | Bereinigung, Skill-Extraktion, Seniority-Zuordnung, Merge |
| `visualisierungen.py` | Erzeugung von 5 Charts mit Matplotlib und Seaborn |

### Daten
| Datei | Zweck |
|---|---|
| `rohdaten_jobs.csv` | Rohe Scraping-Ausgabe (320 Jobs) |
| `lohndaten_bfs.csv` | BFS Medianlöhne (368 Zeilen) |
| `merged_dataset.csv` | Finaler bereinigter Datensatz (319 Zeilen, 20 Spalten) |

### Visualisierungen
| Datei | Zweck |
|---|---|
| `01_top15_skills.png` | Top 15 gefragte Skills |
| `02_gehalt_nach_stadt.png` | Gehaltsvergleich nach Schweizer Städten |
| `03_seniority_gehalt.png` | Seniority-Stufe vs. Monatsgehalt |
| `04_arbeitsmodell_branche.png` | Anteil Remote / Hybrid / On-site pro Branche |
| `05_lohn_diskrepanz_heatmap.png` | Lohn-Lücke Inserate vs. BFS nach Branche und Region |

### Dokumentation
| Datei | Zweck |
|---|---|
| `README.md` | Diese Datei |
| `KI_DEKLARATION.md` | Transparente Auflistung aller KI-unterstützten Code-Stellen |
| `requirements.txt` | Python-Dependencies |

---

## 5. Key Findings

1. **Python, SQL und Englisch** sind die meistgefragten Skills (zusammen in über 40% der Inserate).
2. **Zürich führt bei Inserats-Gehältern** deutlich vor Genf und Basel. BFS-Medianlöhne liegen in Zürich ebenfalls an der Spitze, die Lücke ist jedoch kleiner als erwartet.
3. **Seniority zahlt sich aus**: Der Sprung vom Mid- zum Senior-Level bringt im Median einen deutlich höheren Gehaltssprung als der Sprung vom Junior- zum Mid-Level.
4. **IT/Telecom bietet am meisten Flexibilität**: Höchster Anteil an Hybrid- und Remote-Stellen. Bau- und Ingenieurbranchen bleiben stark On-site.
5. **Inserats-Gehälter liegen systematisch über BFS-Medianlöhnen**, besonders im Consulting- und IT-Sektor. Dies deutet auf eine Positiv-Selektion hin (Arbeitgeber mit höheren Löhnen inserieren eher transparent).

---

## 6. Limitationen

- **Gehaltstransparenz nur bei 42% der Inserate** (138 von 320). Die übrigen Inserate enthalten keine Gehaltsangabe → Analysen zu Gehalt basieren auf dieser Teilmenge.
- **Jobs.ch Schätzungen**: Ein Teil der angegebenen Gehälter sind von jobs.ch berechnete Schätzungen, keine offiziellen Arbeitgeberangaben. Dies wird im Chart 2 transparent mit "jobs.ch Schätzung" kommuniziert.
- **Branchen-Mapping vereinfacht**: Die 8 jobs.ch-Kategorien wurden auf BFS-Wirtschaftszweige gemappt, was stellenweise Vereinfachungen bedeutet (z.B. wurde "Finance/Trusts/Real Estate" der BFS-Kategorie "Finanz- u. Versicherungsdienstleistungen" zugeordnet).
- **Snapshot**: Daten wurden im April 2026 erhoben und reflektieren eine Momentaufnahme.

---

## 7. KI-Nutzung

Dieses Projekt wurde unter aktivem Einsatz von KI-Coding-Assistenten erstellt (GitHub Copilot und Claude). Die konzeptionelle Planung, die Wahl der Forschungsfragen, die Datenquellen-Auswahl, das Branchen-Mapping, die Visualisierungs-Strategie und die inhaltliche Interpretation der Ergebnisse wurden vollständig vom Autor selbst erarbeitet.

KI wurde primär eingesetzt für:
- Generierung von Boilerplate-Code (z.B. Grundstruktur des Scrapy-Spiders)
- Komplexe Regex-Patterns (JSON-LD und React-State Extraktion)
- Debugging von Pipeline-Problemen (z.B. Prioritäten-Konflikt bei Scrapy)
- Code-Review und Formatierung

**Eine detaillierte Auflistung aller KI-unterstützten Stellen findet sich in `KI_DEKLARATION.md`.**

---

## 8. Stack Overflow Fragen

Im Rahmen dieses Projekts wurden folgende Stack Overflow Fragen konsultiert bzw. gestellt:

1. [Scrapy priority system for sequential vs parallel requests](https://stackoverflow.com/questions/...) *(Link einfügen)*
2. [Pandas merge with fallback strategy](https://stackoverflow.com/questions/...) *(Link einfügen)*
3. [Seaborn heatmap annotations with formatting](https://stackoverflow.com/questions/...) *(Link einfügen)*

---

## 9. Abgaben & Termine

| Was | Wann |
|---|---|
| Coaching Call (Zwischenstand + Visualisierungen) | 20.04.2026 |
| Video-Präsentation + GitHub + Datensatz (Canvas) | 24.04.2026 |
| Online-Diskussion (Zoom, 15 Min.) | 27.04.2026 |
| Schriftliche Hausarbeit (5 Seiten, Paper-Stil) | 01.05.2026 |

---

## 10. Kontakt

**Robin D.** | HSG Universität St. Gallen | FS 2026
GitHub: [github.com/robidu/data2dollar-jobs](https://github.com/robidu/data2dollar-jobs)