#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
=============================================================================
jobs_ch_scraper.py - Scrapy Spider für jobs.ch
=============================================================================
Projekt      : From Data2Dollar | HSG FS 2026
Autor        : Robin D.
Ziel         : 320 Stelleninserate aus 8 Branchen (40 pro Branche) scrapen
Output       : rohdaten_jobs.csv

-----------------------------------------------------------------------------
KI-DEKLARATION (vgl. KI_DEKLARATION.md)
-----------------------------------------------------------------------------
# HUMAN          = Konzeptionelle Entscheidungen (Branchen, Limits, Settings)
# KI-ASSISTIERT  = iterativ mit Claude/Copilot entwickelt
# VIBE-CODED     = primaer von KI, vom Autor verstanden (komplexe Regex/Parsing)

Dieser Spider ist der komplexeste Teil des Projekts. Die Multi-Strategy-
Extraktion (JSON-LD + React-State + Body-Fallback) wurde groesstenteils
in Zusammenarbeit mit Claude entwickelt, weil jobs.ch ein modernes Next.js-
Frontend nutzt bei dem Daten teils im HTML, teils im hydrated React-State liegen.
=============================================================================

Hinweis zu Rechtlichem (vgl. README.md Abschnitt Rechtliche Grundlage):
- DOWNLOAD_DELAY=3 Sekunden zwischen Requests
- CONCURRENT_REQUESTS=1 (keine parallelen Anfragen)
- Nur oeffentlich zugaengliche Inserate
- Nutzung im Rahmen Art. 24d URG (wissenschaftliche Forschung)

Ausführen:
    python3 jobs_ch_scraper.py
"""

import json
import re
from urllib.parse import urlencode

import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.http import Response
from scrapy.spidermiddlewares.httperror import HttpError
from twisted.internet.error import DNSLookupError, TimeoutError, TCPTimedOutError


class JobsChSpider(scrapy.Spider):
    name = "jobs_ch_spider"

    # HUMAN: Auswahl der 8 Branchen komplett vom Autor.
    # Auswahlkriterien: (1) Relevanz fuer Schweizer Wirtschaft,
    # (2) Vielfalt (Finance, Tech, Industry, Services),
    # (3) ausreichende Inserats-Zahl pro Kategorie.
    # IDs entsprechen jobs.ch-interner Kategorisierung.
    categories = {
        "106": "IT/Telecom",
        "101": "Finance/Trusts/Real Estate",
        "102": "Banking/Insurance",
        "104": "Marketing/Communications",
        "124": "Consulting/Company Development",
        "108": "Engineering/Watches",
        "107": "Chemical/Pharma/Biotech",
        "110": "Construction/Architecture",
    }

    # HUMAN: Scrapy-Settings bewusst konservativ gewaehlt fuer respektvolles Scraping:
    # - DOWNLOAD_DELAY=3s (dreifacher Default)
    # - CONCURRENT_REQUESTS=1 (keine Parallelitaet)
    # - RETRY_TIMES=3 (Robustheit ohne Server-Stress)
    custom_settings = {
        "DOWNLOAD_DELAY": 3,
        "ROBOTSTXT_OBEY": False,
        "COOKIES_ENABLED": False,
        "RETRY_ENABLED": True,
        "RETRY_TIMES": 3,
        # HUMAN: Kritisch - CONCURRENT_REQUESTS=1 damit das Priority-System wirkt.
        # Bei parallelen Requests waeren Prioritaeten nicht strikt einhaltbar.
        "CONCURRENT_REQUESTS": 1,
        "LOG_LEVEL": "INFO",
        "DEFAULT_REQUEST_HEADERS": {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,de;q=0.8",
        },
        "USER_AGENT": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/123.0.0.0 Safari/537.36"
        ),
        # HUMAN: Feed-Konfiguration fuer direkte CSV-Ausgabe mit definierter Spaltenreihenfolge
        "FEEDS": {
            "rohdaten_jobs.csv": {
                "format": "csv",
                "encoding": "utf-8-sig",
                "overwrite": True,
                "fields": [
                    "category",
                    "category_id",
                    "job_title",
                    "company",
                    "location",
                    "salary_range",
                    "skills_text",
                    "contract_type",
                    "date_posted",
                    "job_url",
                    "job_id",
                ],
            }
        },
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # HUMAN: Limits selbst gesetzt - 40 pro Kategorie x 8 = 320 Total
        self.max_jobs_per_category = 40
        self.max_jobs_total = 320
        # HUMAN: Counter fuer Fortschritts-Tracking und harte Abbruchbedingung
        self.scraped_jobs_total = 0
        self.scraped_jobs_per_category = {cat_id: 0 for cat_id in self.categories}
        # HUMAN: Duplicate-Protection via URL-Set
        self.seen_urls = set()

    async def start(self):
        """
        HUMAN: Eine Kategorie nach der anderen starten - sequentiell.
        Alternative waere gleichzeitig alle 8 zu starten, aber das macht
        Debugging und Fortschrittskontrolle schwieriger.
        """
        base_url = "https://www.jobs.ch/en/vacancies/"
        self.logger.info("Starte Spider | 8 Kategorien x 40 Jobs = ~320 Inserate")

        for cat_id, cat_name in self.categories.items():
            url = f"{base_url}?{urlencode({'category': cat_id})}"
            yield scrapy.Request(
                url=url,
                callback=self.parse_search_results,
                errback=self.handle_error,
                meta={
                    "category_id": cat_id,
                    "category_name": cat_name,
                    "page_number": 1,
                },
                # VIBE-CODED: Priority-System. Problem war: ohne Prioritaeten
                # hat Scrapy zuerst ALLE Listen-Seiten der 8 Kategorien gecrawlt,
                # bevor auch nur ein einziger Detail-Request startete. Loesung:
                # priority=0 fuer Pagination, priority=10 fuer Detail-Requests.
                # Kombiniert mit CONCURRENT_REQUESTS=1 bedeutet das: innerhalb
                # einer Kategorie werden erst Details geparst, DANN naechste Seite.
                priority=0,
                dont_filter=True,
            )

    def parse_search_results(self, response: Response):
        """Parst eine Listen-Seite und folgt Detail-Links + Pagination."""
        cat_id = response.meta["category_id"]
        cat_name = response.meta["category_name"]
        page_number = response.meta.get("page_number", 1)

        # HUMAN: Harte Abbruchbedingungen
        if self.scraped_jobs_total >= self.max_jobs_total:
            return
        if self.scraped_jobs_per_category.get(cat_id, 0) >= self.max_jobs_per_category:
            return

        # KI-ASSISTIERT: Schutz gegen Redirect-Loop. Beobachtet: bei bestimmten
        # URLs redirected jobs.ch die Listen-URL auf ein Detail. Ohne diesen Check
        # wuerde der Spider crashen.
        if "/detail/" in response.url:
            self.logger.info("'%s': Redirect auf Detail -> stoppe", cat_name)
            return

        self.logger.info("Kategorie '%s' Seite %s", cat_name, page_number)

        # HUMAN: CSS-Selektor fuer Detail-Links selbst ausprobiert in Chrome DevTools
        detail_links = response.css(
            'a[href*="/en/vacancies/detail/"]::attr(href)'
        ).getall()

        # HUMAN: Deduplizierung pro Listen-Seite (gleicher Job kann mehrfach verlinkt sein)
        unique_links = []
        seen_on_page = set()
        for href in detail_links:
            if not href:
                continue
            full_url = response.urljoin(href)
            if full_url not in seen_on_page:
                seen_on_page.add(full_url)
                unique_links.append(full_url)

        self.logger.info("Links '%s' Seite %s: %s", cat_name, page_number, len(unique_links))

        if not unique_links:
            return

        # HUMAN: Detail-Requests mit HOHER Prioritaet = werden ZUERST verarbeitet
        for job_url in unique_links:
            if self.scraped_jobs_total >= self.max_jobs_total:
                return
            if self.scraped_jobs_per_category.get(cat_id, 0) >= self.max_jobs_per_category:
                return
            if job_url in self.seen_urls:
                continue
            self.seen_urls.add(job_url)

            yield scrapy.Request(
                url=job_url,
                callback=self.parse_job_detail,
                errback=self.handle_error,
                meta={"category_id": cat_id, "category_name": cat_name},
                # VIBE-CODED: priority=10 damit Details vor naechster Listen-Seite verarbeitet werden
                priority=10,
                dont_filter=True,
            )

        # HUMAN: Pagination mit NIEDRIGER Prioritaet = laueft erst nach Details
        already_scraped = self.scraped_jobs_per_category.get(cat_id, 0)
        if already_scraped < self.max_jobs_per_category:
            # KI-ASSISTIERT: Doppelte Pagination-Detection - erst CSS, dann XPath-Fallback
            next_href = response.css('a[aria-label="Next"]::attr(href)').get()
            if not next_href:
                next_href = response.xpath(
                    '//a[contains(normalize-space(.), "Next")]/@href'
                ).get()

            if next_href and "/detail/" not in next_href:
                yield response.follow(
                    next_href,
                    callback=self.parse_search_results,
                    errback=self.handle_error,
                    meta={
                        "category_id": cat_id,
                        "category_name": cat_name,
                        "page_number": page_number + 1,
                    },
                    priority=0,
                    dont_filter=True,
                )

    def parse_job_detail(self, response: Response):
        """
        HUMAN: Konzept selbst - Multi-Strategy-Extraktion.
        Reihenfolge: JSON-LD (strukturiert) -> React-State (hydrated) -> Body-Text (fallback).
        Fuer jedes Feld wird die beste Quelle genommen.
        """
        cat_id = response.meta.get("category_id", "")
        cat_name = response.meta.get("category_name", "")

        if self.scraped_jobs_total >= self.max_jobs_total:
            return
        if self.scraped_jobs_per_category.get(cat_id, 0) >= self.max_jobs_per_category:
            return

        # HUMAN: Drei Datenquellen, Kaskade von strukturiert zu unstrukturiert
        job_data = self.extract_jsonld_jobposting(response)
        react_data = self.extract_react_state(response)
        body_text = self.extract_clean_body_text(response)

        # HUMAN: Fallback-Chain fuer jedes Feld - elegantes OR-Pattern
        job_title = (job_data.get("title") or react_data.get("title")
                     or self.fallback_title(response))
        company = (job_data.get("company") or react_data.get("company"))
        location = (job_data.get("location") or react_data.get("location")
                    or self.fallback_location(body_text))
        salary_range = (job_data.get("salary") or react_data.get("salary")
                        or self.extract_salary(body_text))
        date_posted = (job_data.get("date_posted") or react_data.get("date_posted")
                       or self.extract_date_posted(body_text))
        contract_type = self.determine_contract_type(body_text, job_data)
        skills_text = (job_data.get("description") or react_data.get("description")
                       or self.fallback_description(response))

        item = {
            "category": cat_name,
            "category_id": cat_id,
            "job_title": self.clean_text(job_title),
            "company": self.clean_text(company),
            "location": self.clean_text(location),
            "salary_range": self.clean_text(salary_range),
            "skills_text": self.clean_text(skills_text),
            "contract_type": contract_type,
            "date_posted": self.clean_text(date_posted),
            "job_url": response.url,
            "job_id": self.extract_job_id(response.url),
        }

        # HUMAN: Mindest-Kriterium - ohne Titel kein gueltiges Inserat
        if not item["job_title"]:
            self.logger.warning("Kein Titel, überspringe: %s", response.url)
            return

        self.scraped_jobs_total += 1
        self.scraped_jobs_per_category[cat_id] += 1

        # KI-ASSISTIERT: Ausfuehrliches Logging fuer Fortschrittsanzeige
        self.logger.info(
            "✓ %s | %s @ %s | %s: %s/%s | Total: %s/%s",
            item["job_title"][:45],
            item["company"][:25] if item["company"] else "?",
            item["location"][:15] if item["location"] else "?",
            cat_name[:20],
            self.scraped_jobs_per_category[cat_id],
            self.max_jobs_per_category,
            self.scraped_jobs_total,
            self.max_jobs_total,
        )

        yield item

    # ------------------------------------------------------------------
    # JSON-LD Extraktion
    # ------------------------------------------------------------------

    # VIBE-CODED: Diese Methode wurde primaer von Claude generiert.
    # Hintergrund: jobs.ch betten Job-Metadaten als JSON-LD strukturiertes
    # Datenformat ein (schema.org/JobPosting Standard). Das sind <script>-Tags
    # mit type="application/ld+json". Diese enthalten alle wichtigen Felder
    # strukturiert - ideal zum Parsen weil zuverlaessig und stabil.
    # Der @graph-Handler ist wichtig weil Seiten manchmal mehrere JSON-LD
    # Objekte in einem @graph-Array bundeln.
    # Vom Autor verstanden, getestet und vom Autor bei Bedarf angepasst.
    def extract_jsonld_jobposting(self, response: Response) -> dict:
        result = {}
        scripts = response.xpath('//script[@type="application/ld+json"]/text()').getall()

        for script_content in scripts:
            try:
                data = json.loads(script_content)
            except (json.JSONDecodeError, ValueError):
                continue

            # VIBE-CODED: @graph-Pattern laut schema.org Standard
            candidates = []
            if isinstance(data, list):
                candidates = data
            elif isinstance(data, dict):
                candidates = data.get("@graph", [data])

            for candidate in candidates:
                if not isinstance(candidate, dict):
                    continue
                if candidate.get("@type") != "JobPosting":
                    continue

                # VIBE-CODED: schema.org/JobPosting Feld-Mapping
                result["title"] = candidate.get("title", "")
                result["description"] = self.strip_html(candidate.get("description", ""))
                result["date_posted"] = candidate.get("datePosted", "")
                result["employment_type"] = candidate.get("employmentType", "")

                org = candidate.get("hiringOrganization", {})
                if isinstance(org, dict):
                    result["company"] = org.get("name", "")

                loc = candidate.get("jobLocation", {})
                if isinstance(loc, list) and loc:
                    loc = loc[0]
                if isinstance(loc, dict):
                    addr = loc.get("address", {})
                    if isinstance(addr, dict):
                        city = addr.get("addressLocality", "")
                        region = addr.get("addressRegion", "")
                        result["location"] = ", ".join(p for p in [city, region] if p)

                salary = candidate.get("baseSalary", {})
                if isinstance(salary, dict):
                    value = salary.get("value", {})
                    currency = salary.get("currency", "CHF")
                    if isinstance(value, dict):
                        mn = value.get("minValue")
                        mx = value.get("maxValue")
                        val = value.get("value")
                        if mn and mx:
                            result["salary"] = f"{currency} {mn} - {mx}"
                        elif val:
                            result["salary"] = f"{currency} {val}"

                return result

        return result

    # ------------------------------------------------------------------
    # React Query State
    # ------------------------------------------------------------------

    # VIBE-CODED: Diese Methode wurde primaer von Claude generiert.
    # Hintergrund: jobs.ch nutzt Next.js (React SSR-Framework). Nach dem
    # initialen Server-Rendering wird ein hydrated State im HTML eingebettet,
    # typischerweise in einem __NEXT_DATA__ Script-Tag oder direkt inline als
    # JSON-Fragmente. Das sind quasi "versteckte" Daten, die nicht im
    # sichtbaren HTML stehen aber maschinenlesbar vorhanden sind.
    # Die Regex-Patterns wurden durch Analyse des jobs.ch HTML-Source mit Claude
    # erarbeitet. Vom Autor getestet und verstanden.
    def extract_react_state(self, response: Response) -> dict:
        result = {}
        html = response.text

        # VIBE-CODED: Company-Name aus React-State extrahieren
        company_match = re.search(
            r'"company"\s*:\s*\{[^}]*?"name"\s*:\s*"([^"]+)"', html)
        if company_match:
            name = company_match.group(1)
            # HUMAN: Filter damit nicht jobs.ch selbst als "Company" ausgelesen wird
            if name.lower() not in ("jobs.ch", "jobcloud ag"):
                result["company"] = name

        # VIBE-CODED: Title - Pattern matcht Title-Feld direkt vor trackingLinks-Objekt
        title_match = re.search(r'"title"\s*:\s*"([^"]+)"[^}]*?"trackingLinks"', html)
        if title_match:
            result["title"] = title_match.group(1)

        # VIBE-CODED: Location - erst aus "locations"-Array, dann Fallback auf "place"-Feld
        city_match = re.search(
            r'"locations"\s*:\s*\[\s*\{[^}]*?"city"\s*:\s*"([^"]+)"', html)
        if city_match:
            result["location"] = city_match.group(1)

        if not result.get("location"):
            place_match = re.search(r'"place"\s*:\s*"([^"]+)"', html)
            if place_match:
                result["location"] = place_match.group(1)

        # VIBE-CODED: ISO-Datum aus publicationDate, nur die ersten 10 Zeichen (YYYY-MM-DD)
        date_match = re.search(r'"publicationDate"\s*:\s*"([^"]+)"', html)
        if date_match:
            result["date_posted"] = date_match.group(1)[:10]

        # VIBE-CODED: jobs.ch-eigene Gehalts-Schaetzung aus "range" Objekt
        salary_match = re.search(
            r'"range"\s*:\s*\{\s*"min"\s*:\s*(\d+)\s*,\s*"max"\s*:\s*(\d+)', html)
        if salary_match:
            mn, mx = salary_match.group(1), salary_match.group(2)
            # HUMAN: Kennzeichnung "jobs.ch estimate" damit im cleaning.py unterscheidbar
            result["salary"] = f"CHF {mn} - {mx} (jobs.ch estimate)"

        # VIBE-CODED: Job-Description aus "template.text"-Feld mit Escape-Handling
        desc_match = re.search(
            r'"template"\s*:\s*\{[^}]*?"text"\s*:\s*"((?:[^"\\]|\\.)*)"', html)
        if desc_match:
            raw = desc_match.group(1)
            # VIBE-CODED: Escape-Sequenzen aus JSON-String dekodieren
            raw = raw.replace("\\u002F", "/").replace("\\n", " ").replace('\\"', '"')
            result["description"] = self.strip_html(raw)

        return result

    # ------------------------------------------------------------------
    # Body Text
    # ------------------------------------------------------------------

    def extract_clean_body_text(self, response: Response) -> str:
        """
        KI-ASSISTIERT: Extrahiert sauberen Body-Text als letzter Fallback.
        XPath schliesst script/style/noscript-Tags aus.
        """
        text_nodes = response.xpath(
            "//body//text()[not(ancestor::script) "
            "and not(ancestor::style) "
            "and not(ancestor::noscript)]"
        ).getall()

        # KI-ASSISTIERT: Filter fuer saubere Text-Knoten - keine JSON-Reste, keine
        # JS-Variablen-Deklarationen, maximale Laenge 500 (sonst wahrscheinlich kein echter Text)
        cleaned = []
        for node in text_nodes:
            t = self.clean_text(node)
            if (t
                and not t.startswith('{"')
                and not t.startswith('var ')
                and not t.startswith('__')
                and not t.startswith('window.')
                and len(t) < 500):
                cleaned.append(t)

        return " ".join(cleaned)

    # ------------------------------------------------------------------
    # Fallbacks
    # ------------------------------------------------------------------
    # HUMAN: Fallback-Funktionen sind einfache CSS-Selektoren und vom Autor geschrieben

    def fallback_title(self, response: Response) -> str:
        """HUMAN: Letzter Ausweg - Title aus h1, og:title oder <title>-Tag."""
        for sel in ["h1::text", 'meta[property="og:title"]::attr(content)', "title::text"]:
            val = response.css(sel).get()
            val = self.clean_text(val)
            if val:
                return val
        return ""

    def fallback_location(self, body_text: str) -> str:
        """HUMAN: Regex mit CH-Staedte-Liste als letzter Fallback fuer Location."""
        match = re.search(
            r"\b(Zurich|Zürich|Zug|Basel|Bern|Lausanne|Geneva|Genève|Genf|"
            r"Winterthur|St\. Gallen|St\.Gallen|Lucerne|Luzern|Lugano|Biel|Fribourg|"
            r"Neuchâtel|Sion|Thun|Schaffhausen|Chur|Aarau)\b",
            body_text, flags=re.IGNORECASE)
        return match.group(1) if match else ""

    def fallback_description(self, response: Response) -> str:
        """HUMAN: Meta-Description als letzter Fallback."""
        meta_desc = response.css('meta[name="description"]::attr(content)').get()
        return self.clean_text(meta_desc) if meta_desc else ""

    # ------------------------------------------------------------------
    # Feld-Extraktoren
    # ------------------------------------------------------------------

    def extract_salary(self, body_text: str) -> str:
        """
        KI-ASSISTIERT: Regex-Patterns fuer CH-Gehaltsformate.
        Drei Varianten: "CHF X - CHF Y", "CHF X - Y", "X - Y CHF".
        """
        patterns = [
            r"(CHF\s?\d[\d''\s]{2,}(?:\.\d+)?\s?(?:-|–|to|bis)\s?CHF?\s?\d[\d''\s]{2,}(?:\.\d+)?)",
            r"(CHF\s?\d[\d''\s]{2,}(?:\.\d+)?\s?(?:-|–|to|bis)\s?\d[\d''\s]{2,}(?:\.\d+)?)",
            r"(\d[\d''\s]{2,}(?:\.\d+)?\s?(?:-|–|to|bis)\s?\d[\d''\s]{2,}(?:\.\d+)?\s?CHF)",
        ]
        for pattern in patterns:
            match = re.search(pattern, body_text, flags=re.IGNORECASE)
            if match:
                return re.sub(r"\s+", " ", match.group(1)).strip()
        return ""

    def extract_date_posted(self, body_text: str) -> str:
        """HUMAN: Zwei Formate abgedeckt: absolutes Datum ("15 April 2026") und relatives ("3 days ago")."""
        absolute = re.search(
            r"\b(\d{1,2}\s+(?:January|February|March|April|May|June|July|"
            r"August|September|October|November|December)\s+\d{4})\b",
            body_text, flags=re.IGNORECASE)
        if absolute:
            return absolute.group(1)
        relative = re.search(
            r"\b(?:Today|Yesterday|\d+\s+(?:hours?|days?|weeks?|months?)\s+ago)\b",
            body_text, flags=re.IGNORECASE)
        return relative.group(0) if relative else ""

    def determine_contract_type(self, body_text: str, job_data: dict) -> str:
        """
        HUMAN: Arbeitsmodell-Klassifikation. Reihenfolge wichtig:
        1. schema.org TELECOMMUTE = Remote
        2. Spezifische Remote-Keywords = Remote
        3. Hybrid-Keywords = Hybrid
        4. Allgemeines "remote" = Remote
        5. Default = On-site
        """
        if "TELECOMMUTE" in str(job_data.get("employment_type", "")).upper():
            return "Remote"
        low = body_text.lower()
        if any(t in low for t in ["fully remote", "100% remote", "remote-first"]):
            return "Remote"
        if any(t in low for t in ["hybrid", "home office", "homeoffice"]):
            return "Hybrid"
        if "remote" in low:
            return "Remote"
        return "On-site"

    def extract_job_id(self, url: str) -> str:
        """HUMAN: jobs.ch nutzt UUIDs in URLs - per Regex extrahiert."""
        match = re.search(r"/detail/([a-f0-9\-]+)/?", url, flags=re.IGNORECASE)
        return match.group(1) if match else ""

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def clean_text(self, value) -> str:
        """HUMAN: Whitespace-Normalisierung - alle Mehrfach-Spaces zu einem."""
        if not value:
            return ""
        return re.sub(r"\s+", " ", str(value)).strip()

    def strip_html(self, html: str) -> str:
        """KI-ASSISTIERT: HTML-Tags entfernen plus haeufige Entity-Decodierung."""
        if not html:
            return ""
        text = re.sub(r"<[^>]+>", " ", str(html))
        text = (text.replace("&nbsp;", " ").replace("&amp;", "&")
                .replace("&lt;", "<").replace("&gt;", ">")
                .replace("&quot;", '"').replace("&#39;", "'"))
        return self.clean_text(text)

    def handle_error(self, failure):
        """KI-ASSISTIERT: Scrapy-Standard Error-Handling mit typspezifischen Messages."""
        request = failure.request
        if failure.check(HttpError):
            self.logger.error("HTTP %s bei %s", failure.value.response.status, request.url)
        elif failure.check(DNSLookupError):
            self.logger.error("DNS-Fehler bei %s", request.url)
        elif failure.check(TimeoutError, TCPTimedOutError):
            self.logger.error("Timeout bei %s", request.url)
        else:
            self.logger.error("Fehler bei %s: %r", request.url, failure)


if __name__ == "__main__":
    # HUMAN: Standardmaessiger Scrapy-Standalone-Einstiegspunkt
    process = CrawlerProcess()
    process.crawl(JobsChSpider)
    process.start()