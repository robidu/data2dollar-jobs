# KI-Deklaration - From Data2Dollar Projekt

**HSG FS 2026 | Robin D. | Swiss Job Market 2026**

---

## 1. Eingesetzte KI-Tools

| Tool | Hersteller | Einsatzzweck |
|---|---|---|
| **GitHub Copilot** | Microsoft / OpenAI | Auto-Completion, Boilerplate |
| **Claude (Opus 4.x)** | Anthropic | Architektur, Debugging, komplexe Regex, Code-Review, statistische Qualitätssicherung, Dashboard-Implementierung |

---

## 2. Kategorisierung der Code-Stellen

Der Code ist inline mit drei Tags markiert:

| Tag | Bedeutung | Beispiel |
|---|---|---|
| `# HUMAN:` | Eigenleistung - Konzept, Logik und Code vom Autor | Skill-Liste, Branchen-Mapping, Stadt-Mapping, Persona-Annotationen, Lohnkategorien |
| `# KI-ASSISTIERT:` | Iterativ mit KI entwickelt - Idee und Review vom Autor, Code-Details mit KI | Funktions-Grundgerüste, Standard-Pandas-Operationen |
| `# VIBE-CODED:` | Primär von KI generiert - komplexe technische Stellen, vom Autor verstanden und geprüft | JSON-LD Extraktion, React-State Regex, Scrapy Priority-System, BFS Excel-Parser, Heatmap-Annotation-Override, Streamlit-Dashboard |

---

## 3. Eigenleistung (HUMAN) - Konzeption und Logik

Folgende **konzeptionelle und inhaltliche Entscheidungen** wurden vollständig vom Autor getroffen:

### Projekt-Ebene
- Wahl des Use Cases (Schweizer Jobmarkt)
- Definition der 5 Forschungsfragen
- Entwicklung der beiden Personas (Lena und Marcus)
- Auswahl der Datenquellen (jobs.ch + BFS)
- Entscheidung v1: 8 Branchen × 40 Jobs = 320 Datenpunkte (Berufsfeld-Filter)
- Entscheidung v2 nach Coaching-Feedback: 18 Branchen × 100 Jobs = 1'800 Datenpunkte (Branche-Filter)
- Strategische Wahl der 18 von 24 verfügbaren Branchen (6 wegen zu wenig Jobs oder kein BFS-Match ausgelassen)
- Wechsel von `?category=X` auf `?industry=X` Filter, weil dieser direkt mit BFS-Wirtschaftszweigen matcht
- Gruppierung der 18 Branchen in 3 Lohnkategorien (Hochlohn / Mittellohn / Tieflohn) für visuelle Analyse
- Wahl der 5 Visualisierungen (welche Charts sinnvoll sind)
- HSG-Farbpalette und Design-Konzept
- Interpretation aller Ergebnisse und Business-Insights

### Daten- und Mapping-Entscheidungen
- **Skill-Liste** (`SKILL_LISTE` in cleaning.py): Auswahl der 50+ relevanten Skills für den Schweizer Markt
- **Stadt-Mapping** (`STADT_MAPPING` in cleaning.py): Zuordnung von Gemeinden und PLZ zu Hauptstädten, inklusive Agglomerationen (z.B. Rotkreuz → Zug, Burgdorf → Bern, Egerkingen → Solothurn)
- **Stadt → BFS-Region Mapping** (`STADT_ZU_REGION`): Zuordnung zu den 7 BFS-Grossregionen
- **Branchen-Mapping** (`CATEGORY_TO_BFS`): 18 jobs.ch Branchen → exakte BFS-Wirtschaftszweige
- **Lohnkategorien-Mapping** (`LOHNKATEGORIE`): Zuordnung jeder Branche zu Hochlohn / Mittellohn / Tieflohn
- **Seniority-Heuristik**: Keywords für Lead/Senior/Mid/Junior-Klassifikation
- **Plausibilitäts-Schwellen** für Gehaltsangaben (3'500-20'000 CHF/Monat)
- **Apprenti-Filter**: Ausschluss von Ausbildungsgehältern (Keywords: "apprenti", "lehrling", "stagiaire", "praktikant") um Parsing-Artefakte wie den CHF 23'400 Apprenti-Ausreisser zu eliminieren

### Statistische Qualitätssicherung (nach iterativer Review mit Claude)
- **Chart 2 - Mindest-Stichprobe pro Stadt**: n≥15, sonst statistisch nicht belastbar
- **Chart 3 - Filter auf Hochlohn-Branchen**: Verhindert das kontraintuitive Junior/Mid-Paradox durch Branchen-Mix. Zusätzlich Mindest-Stichprobe n≥10 pro Seniority-Stufe
- **Chart 5 - Mindest-Stichprobe pro Heatmap-Zelle**: n≥3, sonst leere Zelle (vorher verfälschten Zellen mit n=1 wie ein einzelner Apprenti-Job die ganze Heatmap mit +249% Ausreissern)

### Visualisierungs-Konzepte
- Gruppierter Barplot-Vergleich (jobs.ch vs. BFS) in Chart 2, mit Stichprobengrössen direkt unter Stadtnamen
- Jitter-Scatter mit Median-Bars in Chart 3, beschränkt auf Hochlohn-Branchen
- 100%-Stacked Horizontal Bars in Chart 4, sortiert nach Hybrid-Anteil
- Diverging Heatmap (RdYlGn) zentriert auf 0 in Chart 5, sortiert nach Lohnkategorie mit Trennlinien
- Persona-Annotationen ("Für Lena/Marcus") als Storytelling-Element in jedem Chart

### Dashboard-Konzept (`app.py`)
- **Idee eines interaktiven Dashboards** als Ergänzung zu den statischen Charts
- **Persona-Switcher-Logik**: Lena → Junior/Mid, Marcus → Hochlohn + Senior/Lead (basierend auf Lohnkategorie-Spalte, nicht auf brüchigem Keyword-Matching)
- **Filter-Hierarchie** in der Sidebar: Persona → Lohnkategorie → Branche → geografische Filter → Seniority → Gehaltsrange
- **Chart-3 Toggle**: "Nur Hochlohn-Branchen" (PNG-Default) vs. "Alle gefilterten Branchen" - ermöglicht explorative Analyse ohne den statistischen Default zu verlieren
- **Heatmap-Sortierung nach Lohnkategorie** identisch zum statischen PNG
- **KPI-Header mit Hoch/Mittel/Tief-Breakdown** als zentrale strukturelle Erkenntnis
- **Persona-Storytelling-Boxen** unter jedem Chart mit konkreten Insights (Transparenz-Bias etc.)

---

## 4. KI-Assistierte Stellen - Iterative Entwicklung

Folgende Stellen wurden iterativ mit KI entwickelt. Konzept und Review vom Autor, technische Umsetzung mit KI-Hilfe:

### `cleaning.py`
- **`parse_gehalt()` Funktion**: Idee (Jahresgehalt > 25k → /12) vom Autor, Regex-Details mit KI
- **`extrahiere_seniority()`**: Keyword-Logik vom Autor, Funktionsstruktur mit KI
- **`extrahiere_skills()`**: Skill-Liste und Normalisierung vom Autor, `re.escape()` Logik mit KI
- **`normalisiere_stadt()`**: Mapping-Tabellen vom Autor, längste-Keys-zuerst-Logik mit KI
- **Zweistufiger Merge** (Stufe 1: Region+Branche, Stufe 2: Schweiz-Fallback): Idee vom Autor, Pandas-Umsetzung mit KI

### `visualisierungen.py`
- **Alle 5 Charts**: Design und Layout vom Autor, spezifische Matplotlib-API-Calls mit KI
- **Farb-Kategorisierung** in Chart 1 (Top-Quartil vs. Standard vs. Sprachen)
- **100%-Stacked-Bar Implementierung** in Chart 4 (links-Offset-Logik)
- **Stichprobengrössen-Labels** unter Stadtnamen in Chart 2
- **Lohnkategorie-Sortierung und Trennlinien** in Chart 5 Heatmap

### `bfs_lohndaten_ckan.py`
- **CKAN Search Query Strategie**: 3 Queries in DE/FR vom Autor definiert
- **Scoring-Funktion** zur Auswahl des besten Datensatzes: Kriterien vom Autor

---

## 5. Vibe-Coded Stellen - Komplexe Technik mit KI

Diese Stellen wurden **primär von KI generiert**. Der Autor hat sie verstanden, getestet und angepasst, aber die initiale Implementierung kam aus KI-Output. Dies ist entsprechend im Code markiert.

### `jobs_ch_scraper.py`
- **`extract_jsonld_jobposting()`**: JSON-LD Parsing mit `@graph`-Handling
  - Grund: Strukturierte Metadaten-Extraktion aus `<script type="application/ld+json">`
  - Kenntnis-Level vorher: Nicht bekannt, durch KI-Erklärung gelernt
- **`extract_react_state()`**: Regex-Patterns für React Query State im HTML
  - Grund: jobs.ch nutzt Next.js mit React Server Components, Daten sind im `__NEXT_DATA__` JSON
  - Kenntnis-Level vorher: Regex-Grundlagen ja, aber nicht diese Pattern-Tiefe
- **Scrapy Priority-System**: `priority=10` für Detail-Requests, `priority=0` für Pagination
  - Grund: Ohne dieses System wurden zuerst alle Listenseiten geladen, dann erst Details
  - Debuggt mit Claude, die Lösung kam aus dem Dialog

### `bfs_lohndaten_ckan.py`
- **`parse_bfs_excel()`**: Zweizeiler-Header-Parsing des T1-GR Excel
  - Grund: BFS-Excel hat komplexe Struktur mit kombinierten Headern über zwei Zeilen
  - Kenntnis-Level vorher: `pd.read_excel` ja, aber nicht multi-row-header-Handling

### `cleaning.py`
- Der Code ist insgesamt für den Autor nachvollziehbar

### `visualisierungen.py`
- **Seaborn Heatmap Annotation-Override** in Chart 5: `annot_df` als String-DataFrame für benutzerdefinierte Labels
  - Grund: Standard-Heatmap zeigt nur Zahlen, gewollt war `+12.5%\n(n=7)`-Format mit Vorzeichen und Stichprobengrösse
  - Kenntnis-Level vorher: Heatmap ja, aber nicht dieser Annotation-Trick
- **Stacked-Bar-Implementierung** in Chart 4: Standard-Pattern für horizontale Stacked-Bars mit kumulativem `links`-Offset

### `app.py` - Streamlit Dashboard (komplett vibe-coded)

**Das gesamte Dashboard-File ist vibe-coded.** Die Konzeption (welche Filter, welches Layout, Persona-Logik, KPI-Auswahl) kam vollständig vom Autor. Die Streamlit- und Plotly-Implementierung kam primär aus dem KI-Dialog mit Claude. Der Autor hat jede Zeile verstanden, das Layout mehrfach iteriert und die App lokal getestet.

- **Streamlit-Scaffold**: Page-Config, Tab-Struktur, Sidebar-Layout, Custom-CSS für HSG-Styling
- **Plotly-Umsetzung der 5 Charts** (Übersetzung von Matplotlib/Seaborn auf Plotly)
  - `go.Bar` mit `barmode="group"` für Chart 2
  - `go.Scatter` mit Jitter-Berechnung + `add_shape` für Median-Linien in Chart 3
  - `go.Bar` mit `barmode="stack"` und `insidetextanchor="middle"` für Chart 4
  - `go.Heatmap` mit `texttemplate` für annotierte Heatmap in Chart 5
- **Cache-Strategie**: `@st.cache_data` für `load_data()` - wesentlich für Performance bei Filter-Änderungen
- **Filter-Anwendungs-Logik** in `apply_filters()`: Defensive Handhabung von NaN-Werten beim Gehalts-Slider
- **Persona-Logik-Mapping**: Automatische Filter-Defaults basierend auf `lohnkategorie`-Spalte (sauberer als Keyword-Matching über `category`)
- **Chart-3 Toggle**: `radio` für "Nur Hochlohn / Alle Branchen" kombiniert mit dynamischem `min_n`-Slider
- **Heatmap-Maskierung**: Zellen mit n<min_n werden maskiert, Sortierung nach Lohnkategorie + Mittelwert
- **CSS Custom-Properties**: HSG-Farbpalette als CSS-Variablen, Persona-Boxen mit `border-left`-Accent

**Design-Entscheidung des Autors** (nicht vibe-coded): Farbschema identisch zu `visualisierungen.py` (`HSG_GRUEN = #00694E`, Seniority-Gradient etc.), damit Dashboard und statische PNGs visuell konsistent wirken.

---

## 6. Iteratives Debugging und Qualitätssicherung mit KI

Nach der ersten Version der Visualisierungen wurde mit Claude ein kritischer Review durchgeführt. Identifizierte Probleme und Lösungen:

| Problem (v1) | Lösung (v2) |
|---|---|
| Chart 2: Einzel-Jobs verzerren Stadt-Vergleich (Rotkreuz n=5 als #1) | Mindest-Stichprobe n≥15, Agglomerationen zusammengefasst |
| Chart 3: Junior (CHF 7'416) > Mid (CHF 6'684) durch Branchen-Mix | Filter auf Hochlohn-Branchen, Mindest-Stichprobe n≥10 pro Stufe |
| Chart 5: Gewerbe/Handwerk Genferseeregion mit +249.6% (Einzelner Apprenti-Job) | Mindest-Stichprobe n≥3 pro Zelle, Apprenti-Filter in cleaning.py |
| Cleaning: Ausbildungsgehälter als CHF 23'400 geparst | Keyword-Filter für Apprenti/Lehrling/Stagiaire, Plausibilitätsgrenze verschärft auf 3'500-20'000 |
| Dashboard: Persona-Matching für Marcus über Keywords `"tech"`, `"finance"` war brüchig (fand Chemie/Medizinaltechnik/Versicherungen nicht) | Umstellung auf `lohnkategorie == "Hochlohn"` als sauberes Filter-Kriterium |

---

## 7. Lernprozess und Verstehen

Alle KI-unterstützten und vibe-coded Stellen wurden vom Autor **gelesen, nachvollzogen und getestet**. Bei den komplexen Stellen wurde KI als Sparringpartner im Sinne der Kursmaterialien genutzt (vgl. Slides Woche 2 "AI-Tools als Sparringspartner"):

> *"Man muss nicht jedes technische Detail verstehen - KI-Tools helfen bei der Erklärung und Anleitung der Codierung - Nutzung von KI zum Lernen und Experimentieren mit Code"*

---

## 8. Zusammenfassung

| Kategorie | Anteil am Code (geschätzt) | Rolle Autor |
|---|---|---|
| HUMAN (Eigenleistung) | ~30% | Alle konzeptionellen Entscheidungen, Mappings, Design, statistische Filter, Persona-Storytelling, Dashboard-Konzept |
| KI-ASSISTIERT | ~40% | Idee und Review vom Autor, technische Details mit KI |
| VIBE-CODED | ~30% | Primär KI-generiert, vom Autor verstanden und getestet (jobs.ch Scraper Extraktionen, BFS-Excel-Parser, Heatmap-Annotations, **komplettes Streamlit-Dashboard**) |

*Hinweis: Durch die Ergänzung des Streamlit-Dashboards (ca. 700 Zeilen, primär vibe-coded) verschiebt sich der Code-Anteil in Richtung vibe-coded gegenüber der v1-Version des Projekts.*