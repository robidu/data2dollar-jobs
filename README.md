# From Data2Dollar - Schweizer Jobmarkt 2026

**HSG Universität St. Gallen | FS 2026**
**Dozent:** Prof. Dr. Arne Grüttner
**Autor:** Robin D.

---

## 1. Projektbeschreibung

Analyse des Schweizer Jobmarkts 2026 anhand von 1'762 realen Stelleninseraten (jobs.ch)
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
| **jobs.ch** | Web Scraping via Scrapy | 1'800 Stelleninserate gescrapt, 1'762 nach Duplikat-Bereinigung, 18 Branchen × 100 Jobs |
| **BFS Lohnstrukturerhebung 2024** | CKAN API (opendata.swiss) | 368 Zeilen, 8 Grossregionen × 48 Wirtschaftszweige |

### Gescrapte Branchen (18)

| Lohnkategorie | Branchen |
|---|---|
| **Hochlohn** | Banken / Finanzinstitute, Chemie / Pharma, Informatik / Telekommunikation, Rechts- / Wirtschaftsberatung, Versicherungen, Medizinaltechnik |
| **Mittellohn** | Baugewerbe / Immobilien, Beratung diverse, Bildungswesen, Energie / Wasserwirtschaft, Gewerbe / Handwerk allgemein, Öffentliche Verwaltung, Transport / Logistik, Maschinen / Anlagenbau |
| **Tieflohn** | Detail / Grosshandel, Gastgewerbe / Hotellerie, Gesundheits / Sozialwesen, Industrie diverse |

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
# Schritt 1: Rohdaten von jobs.ch scrapen (~2h wegen Rate-Limiting, 0 Fehler)
python3 jobs_ch_scraper.py

# Schritt 2: BFS-Lohndaten via CKAN API laden (~1 Min.)
python3 bfs_lohndaten_ckan.py

# Schritt 3: Daten bereinigen, Skills extrahieren, Datensätze mergen
python3 cleaning.py

# Schritt 4: 5 Visualisierungen erzeugen
python3 visualisierungen.py

# Schritt 5 (optional): Interaktives Dashboard lokal starten
streamlit run app.py
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
| `app.py` | Interaktives Streamlit-Dashboard (Bonus, siehe §10) |

### Daten
| Datei | Zweck |
|---|---|
| `rohdaten_jobs.csv` | Rohe Scraping-Ausgabe (1'800 Jobs) |
| `lohndaten_bfs.csv` | BFS Medianlöhne (368 Zeilen) |
| `merged_dataset.csv` | Finaler bereinigter Datensatz (1'762 Zeilen) |
| `merged_dataset_mit_gehalt.csv` | Subset mit Gehaltsangaben (652 Zeilen) |

### Visualisierungen
| Datei | Zweck |
|---|---|
| `01_top15_skills.png` | Top 15 gefragte Skills |
| `02_gehalt_nach_stadt.png` | Gehaltsvergleich nach Schweizer Städten (min n=15 pro Stadt) |
| `03_seniority_gehalt.png` | Seniority-Stufe vs. Monatsgehalt (Hochlohn-Branchen, min n=10) |
| `04_arbeitsmodell_branche.png` | Anteil Remote / Hybrid / On-site pro Branche |
| `05_lohn_diskrepanz_heatmap.png` | Lohn-Lücke Inserate vs. BFS nach Branche und Region (min n=3 pro Zelle) |

### Dokumentation
| Datei | Zweck |
|---|---|
| `README.md` | Diese Datei |
| `KI_DEKLARATION.md` | Transparente Auflistung aller KI-unterstützten Code-Stellen |
| `requirements.txt` | Python-Dependencies |

---

## 5. Datensatz-Versionen

| Version | Branchen | Jobs | Filter-Typ | Datum |
|---|---|---|---|---|
| v1 | 8 (Berufsfeld) | 320 | `?category=X` | April 2026 |
| v2 | 18 (Branche) | 1'762 | `?industry=X` | April 2026 |

**Warum v2?** Feedback Coaching Call: Datensatz zu klein (min. 1'000 Jobs). Ausserdem matcht der `industry`-Filter von jobs.ch direkt mit den BFS-Wirtschaftszweigen, was den Merge sauberer macht als der alte `category`-Filter.

---

## 6. Key Findings

1. **Sprachkenntnisse dominieren die Skill-Anforderungen**: Deutsch wird in 450 der 1'762 Inserate verlangt (26%), Englisch in 213 (12%), Französisch in 129 (7%). Unter den Tech-Skills führt SAP (129) vor Excel (99) und R (86).

2. **Zürich führt bei Inserats-Gehältern** mit CHF 8'098/Monat (n=102), gefolgt von Genf (CHF 7'673, n=27) und Bern (CHF 7'527, n=66). In Basel, Luzern und Lausanne liegen die Inserats-Gehälter **unter** dem BFS-Medianlohn der jeweiligen Region.

3. **Seniority zahlt sich aus** (in Hochlohn-Branchen): Mid CHF 7'083 (n=145) → Senior CHF 7'958 (n=20, +12%) → Lead/Manager CHF 8'167 (n=45, +15% gegenüber Mid). Der grösste Gehaltssprung erfolgt bei der Beförderung zum Senior-Level.

4. **Beratung und Banken bieten am meisten Flexibilität**: Beratung diverse (36% Hybrid) und Banken / Finanzinstitute (33% Hybrid) führen. IT / Telekommunikation folgt mit 26% Hybrid und zusätzlich 4% Remote. Detail / Grosshandel, Gewerbe / Handwerk und Gastgewerbe bleiben zu über 95% On-site.

5. **Umgekehrte Lohn-Logik**: Hochlohn-Branchen inserieren systematisch **unter** dem BFS-Median (z.B. Chemie/Pharma Nordwestschweiz -43%, Banken Genferseeregion -25.5%, Versicherungen Mittelland -17.3%), während Tieflohn-Branchen oft **über** dem Median zahlen (Detail/Grosshandel Zürich +32.8%, Gesundheits/Sozialwesen Mittelland +63%, Gastgewerbe Mittelland +32.8%). Interpretation: jobs.ch zeigt in Hochlohn-Branchen eher Einstiegs-/Durchschnittspositionen, in Tieflohn-Branchen eher qualifizierte Fachstellen.

---

## 7. Limitationen

- **Gehaltstransparenz nur bei 37% der Inserate** (652 von 1'762). Die übrigen enthalten keine Gehaltsangabe, sodass alle Gehalts-Analysen auf dieser Teilmenge basieren.
- **Jobs.ch Schätzungen**: Ein Teil der angegebenen Gehälter sind von jobs.ch berechnete Schätzungen, keine offiziellen Arbeitgeberangaben. Dies wird in Chart 2 transparent kommuniziert.
- **Ausbildungsgehälter gefiltert**: Inserate mit Keywords wie "Apprenti", "Lehrling", "Stagiaire" und "Praktikum" wurden aus der Gehalts-Analyse ausgeschlossen, um Verzerrungen zu vermeiden. Zusätzlich gilt ein Plausibilitätsfilter von CHF 3'500-20'000/Monat.
- **Seniority-Heuristik**: Die Klassifikation basiert auf Keywords im Jobtitel. "Mid" ist die Default-Kategorie für Inserate ohne explizites Seniority-Keyword und enthält daher eine heterogene Mischung. Seniority-Analyse (Chart 3) beschränkt sich auf Hochlohn-Branchen, wo Seniority ein klarer Gehaltstreiber ist.
- **Statistische Filter**: Chart 2 zeigt nur Städte mit n≥15, Chart 3 nur Stufen mit n≥10, Chart 5 nur Zellen mit n≥3. Dies führt zu leeren Zellen in der Heatmap, wo die Stichprobengrösse zu klein für belastbare Aussagen ist.
- **Branchen-Mapping vereinfacht**: Die 18 jobs.ch-Branchen wurden auf BFS-Wirtschaftszweige gemappt, was stellenweise Vereinfachungen bedeutet (z.B. Industrie diverse und Gewerbe / Handwerk allgemein → beide "Verarbeitendes Gewerbe").
- **Mehrsprachigkeit**: jobs.ch enthält Inserate auf Deutsch, Französisch und Englisch. Skill-Extraktion wurde für alle drei Sprachen optimiert.
- **Snapshot**: Daten wurden im April 2026 erhoben und reflektieren eine Momentaufnahme.

---

## 8. KI-Nutzung

Dieses Projekt wurde unter aktivem Einsatz von KI-Coding-Assistenten erstellt (GitHub Copilot und Claude). Die konzeptionelle Planung, die Wahl der Forschungsfragen, die Datenquellen-Auswahl, das Branchen-Mapping, die Visualisierungs-Strategie und die inhaltliche Interpretation der Ergebnisse wurden vollständig vom Autor selbst erarbeitet.

KI wurde primär eingesetzt für:
- Generierung von Boilerplate-Code (z.B. Grundstruktur des Scrapy-Spiders)
- Komplexe Regex-Patterns (JSON-LD und React-State Extraktion)
- Debugging von Pipeline-Problemen (z.B. Prioritäten-Konflikt bei Scrapy)
- Statistische Qualitätssicherung (Mindest-Stichprobengrössen, Ausreisser-Filter)
- Code-Review und Formatierung
- **Umsetzung des interaktiven Dashboards (`app.py`, §10)** - primär vibe-coded

**Eine detaillierte Auflistung aller KI-unterstützten Stellen findet sich in `KI_DEKLARATION.md`.**

---

## 9. Stack Overflow Fragen

1. [scrapy CONCURRENT_REQUESTS ignored when DOWNLOAD_DELAY set?](https://stackoverflow.com/questions/37461327)
2. [Pandas Merging 101](https://stackoverflow.com/questions/53645882)
3. [Custom Annotation Seaborn Heatmap](https://stackoverflow.com/questions/33158075)
4. [How to write text above the bars on a bar plot](https://stackoverflow.com/questions/40489821)
5. [How to pass another entire column as argument to pandas fillna()](https://stackoverflow.com/questions/30239152)
6. [Extract both href and link using css selectors in scrapy](https://stackoverflow.com/questions/67480652)

---

## 10. Interaktives Dashboard (Bonus)

Zusätzlich zur statischen Analyse (5 PNGs aus `visualisierungen.py`) wurde ein interaktives Streamlit-Dashboard gebaut, das alle 5 Visualisierungen mit Echtzeit-Filtern zugänglich macht. Damit kann der Datensatz frei exploriert werden, ohne dass Code ausgeführt werden muss.

**Live-App:** https://data2dollar-jobs.streamlit.app *(Link nach Deployment aktualisieren)*

### Features
- Alle 5 Charts interaktiv (zoom, hover, tooltips)
- **Persona-Switcher**: Lena (Einstieg) / Marcus (Senior Hochlohn) setzt passende Filter automatisch
- **Filter**: Lohnkategorie (Hoch/Mittel/Tief), Branche, Stadt, Grossregion, Seniority, Arbeitsmodell, Gehaltsrange
- **KPI-Header** mit Stichprobengrösse, Ø Monatslohn, Median-Diskrepanz, Hoch/Mittel/Tief-Breakdown
- **CSV-Export** der gefilterten Daten

### Ausführung lokal
```bash
pip install -r requirements.txt
streamlit run app.py
```

Browser öffnet automatisch auf `http://localhost:8501`.

### Deployment
Das Dashboard ist gratis auf **Streamlit Community Cloud** gehostet. Deployment erfolgt automatisch bei jedem GitHub-Push.

### Abgrenzung
Die statischen Charts aus `visualisierungen.py` bleiben die **primäre Abgabe** (Video, Hausarbeit). Das Dashboard ist eine ergänzende interaktive Aufbereitung derselben Daten für die explorative Analyse.

### KI-Nutzung `app.py`
Das gesamte Dashboard wurde **primär vibe-coded** mit Claude als Coding-Partner. Konzeption (welche Filter, welches Layout, Persona-Logik basierend auf Lohnkategorie) kam vom Autor, die Streamlit- und Plotly-Implementierung primär von KI. Siehe `KI_DEKLARATION.md` §5 für Details.

---

## 11. Kontakt

**Robin D.** | HSG Universität St. Gallen | FS 2026
GitHub: [github.com/robidu/data2dollar-jobs](https://github.com/robidu/data2dollar-jobs)