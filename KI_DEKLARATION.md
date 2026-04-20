# KI-Deklaration - From Data2Dollar Projekt

**HSG FS 2026 | Robin D. | Swiss Job Market 2026**

Dieses Dokument erfüllt die Selbstverpflichtung aus dem Projekt-Konzept:
> "Code wird in VS Code mit GitHub Copilot geschrieben - KI als aktiver Coding-Partner.
> Alle KI-generierten Codeabschnitte werden im GitHub Repository als solche deklariert."

---

## 1. Eingesetzte KI-Tools

| Tool | Hersteller | Einsatzzweck |
|---|---|---|
| **GitHub Copilot** | Microsoft / OpenAI | Auto-Completion, Boilerplate |
| **Claude (Opus 4.x)** | Anthropic | Architektur, Debugging, komplexe Regex, Code-Review |

---

## 2. Kategorisierung der Code-Stellen

Der Code ist inline mit drei Tags markiert:

| Tag | Bedeutung | Beispiel |
|---|---|---|
| `# HUMAN:` | Eigenleistung - Konzept, Logik und Code vom Autor | Skill-Liste, Branchen-Mapping, Stadt-Mapping, Persona-Annotationen |
| `# KI-ASSISTIERT:` | Iterativ mit KI entwickelt - Idee & Review vom Autor, Code-Details mit KI | Funktions-Grundgerüste, Standard-Pandas-Operationen |
| `# VIBE-CODED:` | Primär von KI generiert - komplexe technische Stellen, vom Autor verstanden und geprüft | JSON-LD Extraktion, React-State Regex, Scrapy Priority-System, BFS Excel-Parser |

---

## 3. Eigenleistung (HUMAN) - Konzeption und Logik

Folgende **konzeptionelle und inhaltliche Entscheidungen** wurden vollständig vom Autor getroffen:

### Projekt-Ebene
- Wahl des Use Cases (Schweizer Jobmarkt)
- Definition der 5 Forschungsfragen
- Entwicklung der beiden Personas (Lena & Marcus)
- Auswahl der Datenquellen (jobs.ch + BFS)
- Entscheidung für 8 Branchen × 40 Jobs = 320 Datenpunkte
- Wahl der 5 Visualisierungen (welche Charts sinnvoll sind)
- HSG-Farbpalette und Design-Konzept
- Interpretation aller Ergebnisse und Business-Insights

### Daten- und Mapping-Entscheidungen
- **Skill-Liste** (`SKILL_LISTE` in cleaning.py): Auswahl der 50+ relevanten Skills für den Schweizer Markt
- **Stadt-Mapping** (`STADT_MAPPING` in cleaning.py): Zuordnung von Gemeinden und PLZ zu Hauptstädten
- **Stadt → BFS-Region Mapping** (`STADT_ZU_REGION`): Zuordnung zu den 7 BFS-Grossregionen
- **Branchen-Mapping** (`BRANCHE_MAPPING`): jobs.ch Kategorien → BFS-Wirtschaftszweige
- **Seniority-Heuristik**: Keywords für Lead/Senior/Mid/Junior-Klassifikation
- **Plausibilitäts-Schwellen** für Gehaltsangaben (3000-25000 CHF/Monat)

### Visualisierungs-Konzepte
- Gruppierter Barplot-Vergleich (jobs.ch vs. BFS) in Chart 2
- Jitter-Scatter mit Median-Bars in Chart 3
- 100%-Stacked Horizontal Bars in Chart 4
- Diverging Heatmap (RdYlGn) zentriert auf 0 in Chart 5
- Persona-Annotationen ("Für Lena/Marcus") als Storytelling-Element

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

### `bfs_lohndaten_ckan.py`
- **CKAN Search Query Strategie**: 3 Queries in DE/FR vom Autor definiert
- **Scoring-Funktion** zur Auswahl des besten Datensatzes: Kriterien vom Autor

---

## 5. Vibe-Coded Stellen - Komplexe Technik mit KI

Diese Stellen wurden **primär von KI generiert**. Der Autor hat sie verstanden, getestet und angepasst, aber die initiale Implementierung kam aus KI-Output. Dies ist entsprechend im Code markiert.

### `jobs_ch_scraper.py`
- **`extract_jsonld_jobposting()`** (Z. 261-317): JSON-LD Parsing mit `@graph`-Handling
  - Grund: Strukturierte Metadaten-Extraktion aus `<script type="application/ld+json">`
  - Kenntnis-Level vorher: Nicht bekannt, durch KI-Erklärung gelernt
- **`extract_react_state()`** (Z. 323-365): Regex-Patterns für React Query State im HTML
  - Grund: jobs.ch nutzt Next.js mit React Server Components, Daten sind im `__NEXT_DATA__` JSON
  - Kenntnis-Level vorher: Regex-Grundlagen ja, aber nicht diese Pattern-Tiefe
- **Scrapy Priority-System** (Z. 110-169): `priority=10` für Detail-Requests, `priority=0` für Pagination
  - Grund: Ohne dieses System wurden zuerst alle Listenseiten geladen, dann erst Details
  - Debuggt mit Claude, die Lösung kam aus dem Dialog

### `bfs_lohndaten_ckan.py`
- **`parse_bfs_excel()`** (Z. 127-193): Zweizeiler-Header-Parsing des T1-GR Excel
  - Grund: BFS-Excel hat komplexe Struktur mit kombinierten Headern über zwei Zeilen
  - Kenntnis-Level vorher: `pd.read_excel` ja, aber nicht multi-row-header-Handling

### `cleaning.py`
- Keine vibe-coded Stellen - der Code ist insgesamt für den Autor nachvollziehbar

### `visualisierungen.py`
- **Seaborn Heatmap Annotation-Override** in Chart 5 (Z. 402-416): `annot_df` als String-DataFrame für benutzerdefinierte Labels
  - Grund: Standard-Heatmap zeigt nur Zahlen, gewollt war `+12.5%`-Format mit Vorzeichen
  - Kenntnis-Level vorher: Heatmap ja, aber nicht dieser Annotation-Trick

---

## 6. Lernprozess & Verstehen

Alle KI-unterstützten und vibe-coded Stellen wurden vom Autor **gelesen, nachvollzogen und getestet**. Bei den komplexen Stellen wurde KI als Sparringpartner im Sinne der Kursmaterialien genutzt (vgl. Slides Woche 2 "AI-Tools als Sparringspartner"):

> *"Man muss nicht jedes technische Detail verstehen - KI-Tools helfen bei der Erklärung und Anleitung der Codierung - Nutzung von KI zum Lernen und Experimentieren mit Code"*

Konkret wurde KI gebeten, komplexe Stellen (z.B. das Scrapy Priority-System oder die Next.js React-State-Regex) in einfachen Worten zu erklären, bevor der Code übernommen wurde.

---

## 7. Beispielhafte Prompts

Zur Transparenz hier einige reale Prompts, die an Claude gerichtet wurden:

**Prompt zu Scrapy Priority-Problem:**
> "Mein Scrapy Spider lädt zuerst alle Pagination-Seiten und startet erst danach mit den Detail-Requests. Ich will aber pro Kategorie sequentiell arbeiten: erst Details einer Seite, dann nächste Seite. Wie löse ich das?"

**Prompt zu BFS-Excel:**
> "Ich habe ein Excel vom BFS mit zweizeiligem Header (Zeile 3 und 4 kombiniert). Die Daten starten ab Zeile 6. Wie parse ich das sauber mit pandas?"

**Prompt zu Seaborn Heatmap:**
> "Ich will in sns.heatmap Zellen mit '+12.5%' Format annotieren, nicht nur mit Zahlen. Wie geht das?"

Diese iterative Prompting-Strategie entspricht dem im Kurs empfohlenen Vibe-Coding-Vorgehen.

---

## 8. Zusammenfassung

| Kategorie | Anteil am Code (geschätzt) | Rolle Autor |
|---|---|---|
| HUMAN (Eigenleistung) | ~35% | Alle konzeptionellen Entscheidungen, Mappings, Design |
| KI-ASSISTIERT | ~45% | Idee und Review vom Autor, technische Details mit KI |
| VIBE-CODED | ~20% | Primär KI-generiert, vom Autor verstanden und getestet |

**Der Autor steht hinter jedem Code-Abschnitt und kann jede Entscheidung begründen.**
