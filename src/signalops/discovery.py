from __future__ import annotations

import html
import json
import re
import urllib.parse
from dataclasses import dataclass

from signalops.models import LeadInput
from signalops.tools.http import HttpClient


SEARCH_QUERIES = [
    '"finance operations" "hiring" "international offices" SaaS company',
    '"travel manager" OR "workplace operations" "hiring" SaaS',
    '"procurement" "finance transformation" "hiring" Europe startup',
    '"company offsite" "global teams" "hiring" software company',
]

SIGNAL_KEYWORDS = (
    "finance operations",
    "finance transformation",
    "procurement",
    "travel manager",
    "workplace",
    "offsite",
    "global",
    "international",
    "distributed",
    "hiring",
    "expansion",
    "events",
)

PRIORITY_TERMS = (
    "global",
    "international",
    "distributed",
    "finance operations",
    "procurement",
    "workplace",
    "travel",
    "events",
    "b2b",
    "saas",
    "software",
    "platform",
    "enterprise",
)

LOW_QUALITY_COMPANY_TERMS = (
    "recruiting",
    "talente",
    "beratung",
    "consulting",
    "agency",
    "humancapital",
    "personalvermittlung",
)

BLOCKED_DOMAINS = {
    "linkedin.com",
    "facebook.com",
    "twitter.com",
    "x.com",
    "youtube.com",
    "wikipedia.org",
    "crunchbase.com",
    "glassdoor.com",
    "indeed.com",
}

KNOWN_ACCOUNT_PROFILES = {
    "factorial": LeadInput(
        company_name="Factorial",
        domain="factorialhr.com",
        country="Spain",
        employee_count=1700,
        source="manual_web_enrichment",
        raw_signal=(
            "Barcelona-based AI business software company expanding internationally, including Germany. "
            "Signals include HR, finance, and IT workflows, growth hiring, multiple offices, company events, "
            "travel, expense, invoice, and spend-control needs."
        ),
    ),
    "legora": LeadInput(
        company_name="Legora",
        domain="legora.com",
        country="Sweden",
        employee_count=650,
        source="manual_web_enrichment",
        raw_signal=(
            "Fast-growing legal AI company with public rapid headcount growth and international enterprise demand. "
            "Likely needs sales travel, events, approvals, cross-border spend control, and finance operations visibility."
        ),
    ),
    "synthesia": LeadInput(
        company_name="Synthesia",
        domain="synthesia.io",
        country="United Kingdom",
        employee_count=550,
        source="manual_web_enrichment",
        raw_signal=(
            "AI video platform serving enterprise customers and expanding globally across North America, Europe, Japan, "
            "and Australia. Signals include enterprise sales travel, customer events, distributed teams, and expense workflows."
        ),
    ),
    "pigment": LeadInput(
        company_name="Pigment",
        domain="pigment.com",
        country="France",
        employee_count=900,
        source="manual_web_enrichment",
        raw_signal=(
            "Business planning SaaS company with finance buyer overlap, international enterprise growth, customer events, "
            "sales travel, expense, invoice, and spend visibility needs."
        ),
    ),
    "mistral ai": LeadInput(
        company_name="Mistral AI",
        domain="mistral.ai",
        country="France",
        employee_count=1000,
        source="manual_web_enrichment",
        raw_signal=(
            "European AI company expanding internationally with US sales presence. Signals include growth hiring, "
            "cross-border executive travel, customer events, and spend-management complexity."
        ),
    ),
    "helsing": LeadInput(
        company_name="Helsing",
        domain="helsing.ai",
        country="Germany",
        employee_count=900,
        source="manual_web_enrichment",
        raw_signal=(
            "Defense AI company operating across Europe with subsidiaries, manufacturing partnerships, procurement needs, "
            "policy-heavy travel, finance operations, and controlled spend workflows."
        ),
    ),
    "miro": LeadInput(
        company_name="Miro",
        domain="miro.com",
        country="Netherlands",
        employee_count=1800,
        source="manual_web_enrichment",
        raw_signal=(
            "Global collaboration software company with distributed teams, enterprise sales travel, customer events, "
            "offsites, and expense-management needs across offices."
        ),
    ),
    "qonto": LeadInput(
        company_name="Qonto",
        domain="qonto.com",
        country="France",
        employee_count=1600,
        source="manual_web_enrichment",
        raw_signal=(
            "European business finance platform operating across multiple countries. Signals include finance operations, "
            "international expansion, procurement, travel policy, and multi-country spend controls."
        ),
    ),
    "contentful": LeadInput(
        company_name="Contentful",
        domain="contentful.com",
        country="Germany",
        employee_count=750,
        source="manual_web_enrichment",
        raw_signal=(
            "B2B SaaS company with offices across the US, Europe, and Australia. Signals include enterprise sales travel, "
            "customer success travel, distributed teams, events, expenses, and spend-policy complexity."
        ),
    ),
    "alan": LeadInput(
        company_name="Alan",
        domain="alan.com",
        country="France",
        employee_count=650,
        source="manual_web_enrichment",
        raw_signal=(
            "Health insurance scaleup active across multiple countries. Signals include regulated multi-country operations, "
            "growth hiring, finance operations, travel, events, and spend visibility needs."
        ),
    ),
}


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str


class WebDiscovery:
    def __init__(self, http: HttpClient | None = None):
        self.http = http or HttpClient(timeout_seconds=7.0, retries=2)

    def discover(self, *, existing_domains: set[str], limit: int = 3) -> list[LeadInput]:
        candidates: dict[str, LeadInput] = {}
        for lead in self.discover_from_jobs(existing_domains=existing_domains, limit=limit):
            candidates[lead.domain.lower()] = lead
            if len(candidates) >= limit:
                return list(candidates.values())
        for query in SEARCH_QUERIES:
            for result in self.search(query):
                domain = normalize_domain(result.url)
                if not domain or domain in existing_domains or is_blocked_domain(domain):
                    continue
                if domain in candidates:
                    continue
                lead = self.result_to_lead(result, domain)
                if lead:
                    candidates[domain] = lead
                if len(candidates) >= limit:
                    return list(candidates.values())
        return list(candidates.values())

    def enrich_company(self, company_name: str) -> LeadInput:
        company = clean_text(company_name)
        known = KNOWN_ACCOUNT_PROFILES.get(normalize_company_key(company))
        if known:
            return known

        results: list[SearchResult] = []
        for query in (
            f'"{company}" official website company',
            f'"{company}" careers jobs finance operations international expansion',
        ):
            results.extend(self.search(query))

        best_result = next(
            (
                result
                for result in results
                if normalize_domain(result.url) and not is_blocked_domain(normalize_domain(result.url))
            ),
            None,
        )
        domain = normalize_domain(best_result.url) if best_result else infer_domain_from_company(company)
        website_text = self.fetch_company_text(domain) if domain else ""
        evidence = " ".join(
            part
            for part in [
                *(f"{result.title}. {result.snippet}" for result in results[:4]),
                website_text,
            ]
            if part
        )
        signal = build_signal(evidence) if evidence else ""
        if not signal:
            signal = (
                f"{company} was submitted for autonomous qualification. Web enrichment found limited public "
                "signal, so the agent should be conservative and route uncertain cases to review."
            )

        return LeadInput(
            company_name=company,
            domain=domain,
            country=infer_country(evidence),
            employee_count=infer_employee_count(evidence),
            source="manual_web_enrichment",
            raw_signal=signal,
        )

    def discover_from_jobs(self, *, existing_domains: set[str], limit: int = 3) -> list[LeadInput]:
        url = "https://www.arbeitnow.com/api/job-board-api"
        try:
            response = self.http.get_text(url, max_bytes=2_500_000)
            payload = json.loads(response.text)
        except Exception:
            return []

        leads: dict[str, LeadInput] = {}
        items = sorted(
            payload.get("data", [])[:180],
            key=lambda item: signal_priority_score(
                " ".join(
                    [
                        item.get("company_name", ""),
                        item.get("title", ""),
                        html_to_text(item.get("description", ""))[:1200],
                        item.get("location", ""),
                    ]
                )
            ),
            reverse=True,
        )
        for item in items:
            company = clean_text(item.get("company_name", ""))
            company = normalize_company_name(company)
            title = clean_text(item.get("title", ""))
            description = html_to_text(item.get("description", ""))
            location = clean_text(item.get("location", ""))
            tags = " ".join(item.get("tags") or [])
            text = " ".join([company, title, description, location, tags])
            if not company or is_low_quality_company(company) or not is_relevant_signal(text):
                continue

            domain = infer_domain_from_company(company)
            if domain in existing_domains or domain in leads:
                continue

            website_text = self.fetch_company_text(domain)
            evidence = " ".join(part for part in (title, location, tags, description[:900], website_text[:700]) if part)
            leads[domain] = LeadInput(
                company_name=company,
                domain=domain,
                country=infer_country(evidence),
                employee_count=infer_employee_count(evidence),
                source="job_post_discovery",
                raw_signal=build_signal(evidence),
            )
            if len(leads) >= limit:
                break
        return list(leads.values())

    def search(self, query: str) -> list[SearchResult]:
        encoded = urllib.parse.urlencode({"q": query})
        url = f"https://duckduckgo.com/html/?{encoded}"
        try:
            response = self.http.get_text(url)
        except Exception:
            return []
        return parse_duckduckgo_results(response.text)

    def result_to_lead(self, result: SearchResult, domain: str) -> LeadInput | None:
        title = clean_text(result.title)
        snippet = clean_text(result.snippet)
        company = infer_company_name(title, domain)
        page_text = self.fetch_company_text(domain)
        evidence = " ".join(part for part in (title, snippet, page_text) if part)
        if not any(keyword in evidence.lower() for keyword in SIGNAL_KEYWORDS):
            return None
        country = infer_country(evidence)
        employee_count = infer_employee_count(evidence)
        signal = build_signal(evidence)
        return LeadInput(
            company_name=company,
            domain=domain,
            country=country,
            employee_count=employee_count,
            source="web_discovery",
            raw_signal=signal,
        )

    def fetch_company_text(self, domain: str) -> str:
        for url in (f"https://{domain}", f"https://{domain}/careers", f"https://{domain}/jobs"):
            try:
                response = self.http.get_text(url)
            except Exception:
                continue
            text = html_to_text(response.text)
            if text:
                return text[:1600]
        return ""


def parse_duckduckgo_results(page: str) -> list[SearchResult]:
    results: list[SearchResult] = []
    pattern = re.compile(
        r'<a rel="nofollow" class="result__a" href="(?P<url>.*?)".*?>(?P<title>.*?)</a>.*?'
        r'<a class="result__snippet".*?>(?P<snippet>.*?)</a>',
        re.DOTALL,
    )
    for match in pattern.finditer(page):
        url = decode_duckduckgo_url(html.unescape(match.group("url")))
        results.append(
            SearchResult(
                title=html_to_text(match.group("title")),
                url=url,
                snippet=html_to_text(match.group("snippet")),
            )
        )
    return results


def decode_duckduckgo_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    query = urllib.parse.parse_qs(parsed.query)
    if "uddg" in query:
        return query["uddg"][0]
    return url


def normalize_domain(url: str) -> str:
    parsed = urllib.parse.urlparse(url if "://" in url else f"https://{url}")
    host = parsed.netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    return host.split(":")[0]


def is_blocked_domain(domain: str) -> bool:
    return any(domain == blocked or domain.endswith(f".{blocked}") for blocked in BLOCKED_DOMAINS)


def is_relevant_signal(text: str) -> bool:
    lowered = text.lower()
    strong_terms = (
        "finance",
        "procurement",
        "operations",
        "workplace",
        "office manager",
        "travel",
        "events",
        "people operations",
        "sales operations",
        "business operations",
        "expansion",
        "international",
        "global",
    )
    return any(term in lowered for term in strong_terms)


def signal_priority_score(text: str) -> int:
    lowered = text.lower()
    return sum(1 for term in PRIORITY_TERMS if term in lowered)


def is_low_quality_company(company: str) -> bool:
    lowered = company.lower()
    return any(term in lowered for term in LOW_QUALITY_COMPANY_TERMS)


def normalize_company_name(company: str) -> str:
    company = re.sub(r"\s+-\s+(english|deutsch|german|remote)$", "", company, flags=re.IGNORECASE)
    company = re.sub(r"\s+\([^)]*\)$", "", company)
    return company.strip()


def normalize_company_key(company: str) -> str:
    normalized = company.lower().replace("&", "and")
    normalized = re.sub(r"\b(gmbh|ltd|limited|inc|corp|corporation|s\.?a\.?|ag|bv|plc)\b", "", normalized)
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized)
    return normalized.strip()


def infer_domain_from_company(company: str) -> str:
    aliases = {
        "wolt": "wolt.com",
        "tulip interfaces": "tulip.co",
        "flix": "flix.com",
    }
    normalized = company.lower()
    if normalized in aliases:
        return aliases[normalized]
    normalized = normalized.replace("&", "and")
    normalized = re.sub(r"\b(gmbh|ltd|limited|inc|corp|corporation|s\.?a\.?|ag|bv|plc)\b", "", normalized)
    normalized = re.sub(r"[^a-z0-9]+", "", normalized)
    return f"{normalized}.com" if normalized else ""


def infer_company_name(title: str, domain: str) -> str:
    clean_title = re.split(r"[-|:]", title)[0].strip()
    if clean_title and len(clean_title) <= 40:
        return clean_title
    return domain.split(".")[0].replace("-", " ").title()


def infer_country(text: str) -> str:
    lowered = text.lower()
    countries = {
        "united states": "United States",
        "usa": "United States",
        "new york": "United States",
        "san francisco": "United States",
        "united kingdom": "United Kingdom",
        "london": "United Kingdom",
        "germany": "Germany",
        "berlin": "Germany",
        "france": "France",
        "paris": "France",
        "spain": "Spain",
        "barcelona": "Spain",
        "netherlands": "Netherlands",
        "amsterdam": "Netherlands",
        "denmark": "Denmark",
        "copenhagen": "Denmark",
        "sweden": "Sweden",
        "stockholm": "Sweden",
    }
    for token, country in countries.items():
        if token in lowered:
            return country
    return ""


def infer_employee_count(text: str) -> int | None:
    lowered = text.lower()
    patterns = [
        (r"(\d{1,3}(?:,\d{3})?)\+?\s+employees", 1),
        (r"team of\s+(\d{1,3}(?:,\d{3})?)", 1),
        (r"(\d{1,3}(?:,\d{3})?)\+?\s+people", 1),
    ]
    for pattern, group in patterns:
        match = re.search(pattern, lowered)
        if match:
            return int(match.group(group).replace(",", ""))
    return None


def build_signal(text: str) -> str:
    compact = clean_text(text)
    sentences = re.split(r"(?<=[.!?])\s+", compact)
    useful = [sentence for sentence in sentences if any(keyword in sentence.lower() for keyword in SIGNAL_KEYWORDS)]
    signal = " ".join(useful[:3]) or compact[:500]
    return signal[:900]


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(value)).strip()


def html_to_text(value: str) -> str:
    without_tags = re.sub(r"<script.*?</script>|<style.*?</style>", " ", value, flags=re.DOTALL | re.IGNORECASE)
    without_tags = re.sub(r"<[^>]+>", " ", without_tags)
    return clean_text(without_tags)
