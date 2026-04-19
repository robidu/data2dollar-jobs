#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
jobs_ch_scraper.py - Scrapy Spider für jobs.ch

Projekt: Swiss Job Market 2026 (HSG, From Data2Dollar)
Ziel: ~320 Stelleninserate aus 8 Branchen.

Fix: Detail-Requests haben höhere Priorität als Pagination-Requests.
Das verhindert dass der Spider erst alle Seiten sammelt bevor er
Detailseiten verarbeitet.

Ausführen:
    python3 jobs_ch_scraper.py

Output: rohdaten_jobs.csv
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

    # 8 Branchen - entspricht Projektkonzept
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

    custom_settings = {
        "DOWNLOAD_DELAY": 3,
        "ROBOTSTXT_OBEY": False,
        "COOKIES_ENABLED": False,
        "RETRY_ENABLED": True,
        "RETRY_TIMES": 3,
        # WICHTIG: Nur 1 concurrent request damit Prioritäten korrekt greifen
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
        self.max_jobs_per_category = 40
        self.max_jobs_total = 320
        self.scraped_jobs_total = 0
        self.scraped_jobs_per_category = {cat_id: 0 for cat_id in self.categories}
        self.seen_urls = set()

    async def start(self):
        """Eine Kategorie nach der anderen - sequentiell."""
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
                # Niedrige Priorität - Pagination wartet auf Detail-Requests
                priority=0,
                dont_filter=True,
            )

    def parse_search_results(self, response: Response):
        cat_id = response.meta["category_id"]
        cat_name = response.meta["category_name"]
        page_number = response.meta.get("page_number", 1)

        if self.scraped_jobs_total >= self.max_jobs_total:
            return
        if self.scraped_jobs_per_category.get(cat_id, 0) >= self.max_jobs_per_category:
            return

        # Schutz gegen Pagination-Loop
        if "/detail/" in response.url:
            self.logger.info("'%s': Redirect auf Detail -> stoppe", cat_name)
            return

        self.logger.info("Kategorie '%s' Seite %s", cat_name, page_number)

        # Detail-Links finden
        detail_links = response.css(
            'a[href*="/en/vacancies/detail/"]::attr(href)'
        ).getall()

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

        # Detail-Requests mit HOHER Priorität - werden zuerst verarbeitet
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
                # HOHE Priorität - Detailseiten werden vor Pagination verarbeitet
                priority=10,
                dont_filter=True,
            )

        # Pagination mit NIEDRIGER Priorität - erst nach Detail-Requests
        already_scraped = self.scraped_jobs_per_category.get(cat_id, 0)
        if already_scraped < self.max_jobs_per_category:
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
                    # Niedrige Priorität
                    priority=0,
                    dont_filter=True,
                )

    def parse_job_detail(self, response: Response):
        cat_id = response.meta.get("category_id", "")
        cat_name = response.meta.get("category_name", "")

        if self.scraped_jobs_total >= self.max_jobs_total:
            return
        if self.scraped_jobs_per_category.get(cat_id, 0) >= self.max_jobs_per_category:
            return

        job_data = self.extract_jsonld_jobposting(response)
        react_data = self.extract_react_state(response)
        body_text = self.extract_clean_body_text(response)

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

        if not item["job_title"]:
            self.logger.warning("Kein Titel, überspringe: %s", response.url)
            return

        self.scraped_jobs_total += 1
        self.scraped_jobs_per_category[cat_id] += 1

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

    def extract_jsonld_jobposting(self, response: Response) -> dict:
        result = {}
        scripts = response.xpath('//script[@type="application/ld+json"]/text()').getall()

        for script_content in scripts:
            try:
                data = json.loads(script_content)
            except (json.JSONDecodeError, ValueError):
                continue

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

    def extract_react_state(self, response: Response) -> dict:
        result = {}
        html = response.text

        company_match = re.search(
            r'"company"\s*:\s*\{[^}]*?"name"\s*:\s*"([^"]+)"', html)
        if company_match:
            name = company_match.group(1)
            if name.lower() not in ("jobs.ch", "jobcloud ag"):
                result["company"] = name

        title_match = re.search(r'"title"\s*:\s*"([^"]+)"[^}]*?"trackingLinks"', html)
        if title_match:
            result["title"] = title_match.group(1)

        city_match = re.search(
            r'"locations"\s*:\s*\[\s*\{[^}]*?"city"\s*:\s*"([^"]+)"', html)
        if city_match:
            result["location"] = city_match.group(1)

        if not result.get("location"):
            place_match = re.search(r'"place"\s*:\s*"([^"]+)"', html)
            if place_match:
                result["location"] = place_match.group(1)

        date_match = re.search(r'"publicationDate"\s*:\s*"([^"]+)"', html)
        if date_match:
            result["date_posted"] = date_match.group(1)[:10]

        salary_match = re.search(
            r'"range"\s*:\s*\{\s*"min"\s*:\s*(\d+)\s*,\s*"max"\s*:\s*(\d+)', html)
        if salary_match:
            mn, mx = salary_match.group(1), salary_match.group(2)
            result["salary"] = f"CHF {mn} - {mx} (jobs.ch estimate)"

        desc_match = re.search(
            r'"template"\s*:\s*\{[^}]*?"text"\s*:\s*"((?:[^"\\]|\\.)*)"', html)
        if desc_match:
            raw = desc_match.group(1)
            raw = raw.replace("\\u002F", "/").replace("\\n", " ").replace('\\"', '"')
            result["description"] = self.strip_html(raw)

        return result

    # ------------------------------------------------------------------
    # Body Text
    # ------------------------------------------------------------------

    def extract_clean_body_text(self, response: Response) -> str:
        text_nodes = response.xpath(
            "//body//text()[not(ancestor::script) "
            "and not(ancestor::style) "
            "and not(ancestor::noscript)]"
        ).getall()

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

    def fallback_title(self, response: Response) -> str:
        for sel in ["h1::text", 'meta[property="og:title"]::attr(content)', "title::text"]:
            val = response.css(sel).get()
            val = self.clean_text(val)
            if val:
                return val
        return ""

    def fallback_location(self, body_text: str) -> str:
        match = re.search(
            r"\b(Zurich|Zürich|Zug|Basel|Bern|Lausanne|Geneva|Genève|Genf|"
            r"Winterthur|St\. Gallen|St\.Gallen|Lucerne|Luzern|Lugano|Biel|Fribourg|"
            r"Neuchâtel|Sion|Thun|Schaffhausen|Chur|Aarau)\b",
            body_text, flags=re.IGNORECASE)
        return match.group(1) if match else ""

    def fallback_description(self, response: Response) -> str:
        meta_desc = response.css('meta[name="description"]::attr(content)').get()
        return self.clean_text(meta_desc) if meta_desc else ""

    # ------------------------------------------------------------------
    # Feld-Extraktoren
    # ------------------------------------------------------------------

    def extract_salary(self, body_text: str) -> str:
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
        match = re.search(r"/detail/([a-f0-9\-]+)/?", url, flags=re.IGNORECASE)
        return match.group(1) if match else ""

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def clean_text(self, value) -> str:
        if not value:
            return ""
        return re.sub(r"\s+", " ", str(value)).strip()

    def strip_html(self, html: str) -> str:
        if not html:
            return ""
        text = re.sub(r"<[^>]+>", " ", str(html))
        text = (text.replace("&nbsp;", " ").replace("&amp;", "&")
                .replace("&lt;", "<").replace("&gt;", ">")
                .replace("&quot;", '"').replace("&#39;", "'"))
        return self.clean_text(text)

    def handle_error(self, failure):
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
    process = CrawlerProcess()
    process.crawl(JobsChSpider)
    process.start()