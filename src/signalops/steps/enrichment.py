from __future__ import annotations

from signalops.framework import AgentStep, RunContext
from signalops.models import EnrichedAccount, LeadInput


FIRMOGRAPHIC_LOOKUP = {
    "mistral.ai": ("AI software", "Paris, France"),
    "deepl.com": ("AI translation software", "Cologne, Germany"),
    "personio.com": ("HR software", "Munich, Germany"),
    "pleo.io": ("Spend management", "Copenhagen, Denmark"),
    "wefox.com": ("Insurance technology", "Berlin, Germany"),
    "typeform.com": ("SaaS", "Barcelona, Spain"),
}


class EnrichmentStep(AgentStep[LeadInput, EnrichedAccount]):
    name = "enrichment"

    def run(self, value: LeadInput, context: RunContext) -> EnrichedAccount:
        notes: list[str] = []
        industry, headquarters = FIRMOGRAPHIC_LOOKUP.get(
            value.domain.lower(),
            ("Unknown", value.country or "Unknown"),
        )
        if not value.domain:
            notes.append("missing domain")
        if not value.employee_count:
            notes.append("missing employee_count")
        if not value.country:
            notes.append("missing country")

        return EnrichedAccount(
            company_name=value.company_name,
            domain=value.domain,
            country=value.country or headquarters.split(",")[-1].strip(),
            employee_count=value.employee_count,
            industry=industry,
            headquarters=headquarters,
            signal_text=value.raw_signal,
            source_urls=[f"https://{value.domain}"] if value.domain else [],
            data_quality_notes=notes,
        )
