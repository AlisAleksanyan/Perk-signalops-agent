from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
SRC_PATH = ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from signalops.discovery import WebDiscovery
from signalops.llm import ReplayLLMProvider
from signalops.models import LeadInput
from signalops.pipeline import AccountQualificationPipeline
from signalops.storage import make_account_store

DB_PATH = ROOT / "data" / "signalops_crm.sqlite"
LOG_PATH = ROOT / "data" / "agent_runs.jsonl"
REPLAY_PATH = ROOT / "data" / "replay_llm_responses.json"
MAGIC_PEN_TARGET_COUNT = 3
MAGIC_PEN_CANDIDATE_COUNT = 8
MAGIC_PEN_MIN_SCORE = 60
MAGIC_PEN_MIN_CONFIDENCE = 0.65


DECISION_LABELS = {
    "auto_qualify": "Ready for Sales",
    "human_review": "Needs Review",
    "reject": "Not a Fit",
}

MOTION_LABELS = {
    "travel_led": "Travel-led",
    "finance_led": "Finance-led",
    "events_led": "Events-led",
    "general_outbound": "General Outbound",
}

SEGMENT_LABELS = {
    "enterprise": "Enterprise",
    "mid_market": "Mid-Market",
    "smb": "SMB",
    "unknown_segment": "Unknown Segment",
}

STEP_LABELS = {
    "pipeline": "Pipeline",
    "enrichment": "Account Enrichment",
    "research": "Research Brief",
    "scoring": "Fit Scoring",
    "routing": "Routing Decision",
    "crm_writeback": "CRM Update",
}

HOT_ACCOUNTS = [
    LeadInput(
        company_name="Synthesia",
        domain="synthesia.io",
        country="United Kingdom",
        employee_count=450,
        source="magic_pen",
        raw_signal="AI video company scaling internationally; hiring finance operations and workplace roles while running customer events and distributed team offsites.",
    ),
    LeadInput(
        company_name="Lovable",
        domain="lovable.dev",
        country="Sweden",
        employee_count=180,
        source="magic_pen",
        raw_signal="Fast-growing AI software company with rapid hiring, international users, founder events, and likely scaling admin workload.",
    ),
    LeadInput(
        company_name="ElevenLabs",
        domain="elevenlabs.io",
        country="United Kingdom",
        employee_count=350,
        source="magic_pen",
        raw_signal="AI audio company expanding globally; job posts indicate finance operations, international teams, events, and cross-border travel needs.",
    ),
    LeadInput(
        company_name="Helsing",
        domain="helsing.ai",
        country="Germany",
        employee_count=500,
        source="magic_pen",
        raw_signal="European defense AI company growing across offices; hiring operations, procurement, and finance roles with strict policy and travel coordination needs.",
    ),
    LeadInput(
        company_name="Poolside",
        domain="poolside.ai",
        country="France",
        employee_count=250,
        source="magic_pen",
        raw_signal="AI company expanding between Europe and the United States; leadership hiring and distributed engineering offsites suggest travel and spend complexity.",
    ),
    LeadInput(
        company_name="Pigment",
        domain="pigment.com",
        country="France",
        employee_count=900,
        source="magic_pen",
        raw_signal="Business planning SaaS company with international offices, enterprise sales travel, finance buyer personas, and customer events.",
    ),
    LeadInput(
        company_name="Qonto",
        domain="qonto.com",
        country="France",
        employee_count=1600,
        source="magic_pen",
        raw_signal="European fintech operating across multiple countries; hiring procurement and finance transformation roles with cross-border spend policy needs.",
    ),
    LeadInput(
        company_name="Factorial",
        domain="factorialhr.com",
        country="Spain",
        employee_count=1000,
        source="magic_pen",
        raw_signal="Barcelona SaaS company scaling internationally; multiple offices, sales travel, finance operations, and company event coordination signals.",
    ),
    LeadInput(
        company_name="Monta",
        domain="monta.com",
        country="Denmark",
        employee_count=500,
        source="magic_pen",
        raw_signal="Climate tech platform expanding across European markets; field sales, partner events, and distributed teams create travel and expense policy needs.",
    ),
    LeadInput(
        company_name="Pennylane",
        domain="pennylane.com",
        country="France",
        employee_count=700,
        source="magic_pen",
        raw_signal="Finance software company growing headcount and hosting customer events; likely fit for travel, invoice, and spend visibility workflows.",
    ),
    LeadInput(
        company_name="Miro",
        domain="miro.com",
        country="Netherlands",
        employee_count=1800,
        source="magic_pen",
        raw_signal="Global collaboration software company with distributed teams, enterprise sales travel, customer events, and finance operations complexity.",
    ),
    LeadInput(
        company_name="Back Market",
        domain="backmarket.com",
        country="France",
        employee_count=1000,
        source="magic_pen",
        raw_signal="Marketplace company operating across Europe and the United States; hiring operations and finance roles with cross-border travel and spend policy needs.",
    ),
    LeadInput(
        company_name="Contentful",
        domain="contentful.com",
        country="Germany",
        employee_count=750,
        source="magic_pen",
        raw_signal="Enterprise SaaS company with international offices, customer events, sales travel, and distributed team coordination needs.",
    ),
    LeadInput(
        company_name="Celonis",
        domain="celonis.com",
        country="Germany",
        employee_count=3000,
        source="magic_pen",
        raw_signal="Large European enterprise software company with global offices, enterprise field sales, customer conferences, and complex travel policy needs.",
    ),
    LeadInput(
        company_name="Vinted",
        domain="vinted.com",
        country="Lithuania",
        employee_count=2000,
        source="magic_pen",
        raw_signal="European marketplace with international teams and growth across markets; likely travel, finance operations, and policy coordination needs.",
    ),
    LeadInput(
        company_name="GetYourGuide",
        domain="getyourguide.com",
        country="Germany",
        employee_count=900,
        source="magic_pen",
        raw_signal="Travel marketplace with global partners, distributed offices, events, and finance workflows that may require travel and spend visibility.",
    ),
    LeadInput(
        company_name="Remote",
        domain="remote.com",
        country="United States",
        employee_count=1500,
        source="magic_pen",
        raw_signal="Distributed workforce platform with global employee base, company events, finance operations, and cross-border policy complexity.",
    ),
    LeadInput(
        company_name="Too Good To Go",
        domain="toogoodtogo.com",
        country="Denmark",
        employee_count=1300,
        source="magic_pen",
        raw_signal="International impact company with local market operations, distributed teams, travel, events, and finance coordination needs.",
    ),
    LeadInput(
        company_name="Alan",
        domain="alan.com",
        country="France",
        employee_count=650,
        source="magic_pen",
        raw_signal="Healthtech company scaling across European markets; hiring finance and operations roles with cross-border team and event coordination needs.",
    ),
    LeadInput(
        company_name="Bolt",
        domain="bolt.eu",
        country="Estonia",
        employee_count=3500,
        source="magic_pen",
        raw_signal="Mobility company operating in many countries with distributed operations, field teams, finance workflows, and international travel needs.",
    ),
    LeadInput(
        company_name="Wolt",
        domain="wolt.com",
        country="Finland",
        employee_count=4000,
        source="magic_pen",
        raw_signal="Operations-heavy technology company across many countries with market launches, distributed teams, travel, and expense policy complexity.",
    ),
    LeadInput(
        company_name="Razor Group",
        domain="razor-group.com",
        country="Germany",
        employee_count=500,
        source="magic_pen",
        raw_signal="E-commerce aggregator with international operations, finance transformation, procurement, and cross-border spend management needs.",
    ),
]


def main() -> None:
    import streamlit as st

    st.set_page_config(page_title="Perk SignalOps", layout="wide", initial_sidebar_state="expanded")
    inject_css(st)

    accounts = load_accounts()
    logs = load_logs()

    st.markdown(
        """
        <section class="hero">
          <div>
            <div class="eyebrow">Perk SignalOps</div>
            <h1>Find the right accounts. Route uncertain cases for human review.</h1>
            <p>
              Turn Clay-style signals into researched, scored, and routed account decisions
              with a human review lane for uncertain cases.
            </p>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    render_operator_actions(st)
    accounts = load_accounts()
    logs = load_logs()

    if not accounts:
        st.markdown(
            '<div class="empty-state">No accounts yet. Add one company or use Magic Pen to discover a starter list.</div>',
            unsafe_allow_html=True,
        )
        return

    render_metrics(st, accounts)
    render_account_index(st, accounts)

    left, right = st.columns([1.35, 0.9], gap="large")
    with left:
        st.markdown('<h2 class="section-title">Qualified Accounts</h2>', unsafe_allow_html=True)
        for row in sorted(accounts, key=lambda item: item["perk_fit_score"], reverse=True):
            render_account_card(st, row)

    with right:
        st.markdown('<h2 class="section-title">Review Queue</h2>', unsafe_allow_html=True)
        review_rows = [row for row in accounts if row["route_decision"] == "human_review"]
        if review_rows:
            for row in sorted(review_rows, key=lambda item: item["perk_fit_score"], reverse=True):
                render_review_card(st, row)
        else:
            st.markdown('<div class="empty-state">No accounts currently need review.</div>', unsafe_allow_html=True)

        st.markdown('<h2 class="section-title top-space">Activity</h2>', unsafe_allow_html=True)
        for event in simplify_logs(logs)[-10:][::-1]:
            render_activity_item(st, event)


def render_operator_actions(st: Any) -> None:
    sidebar = st.sidebar
    sidebar.markdown(
        """
        <div class="sidebar-agent">
          <span>Revenue Systems Agent</span>
          <strong>Research -> Score -> Route -> Update CRM</strong>
        </div>
        """,
        unsafe_allow_html=True,
    )
    sidebar.markdown(
        """
        <div class="sidebar-brand">
          <span>Workspace</span>
          <strong>Account Actions</strong>
          <p>Add one company or let the agent discover a fresh batch.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with sidebar.expander("Analyze a company now", expanded=False):
        st.caption("Type one company name. The agent will search, enrich, score, route, and update the CRM view.")
        with st.form("single_company_form", clear_on_submit=True):
            company_name = st.text_input("Company Name", placeholder="Example: Legora")
            submitted = st.form_submit_button("Analyze Account", type="primary")

        if submitted:
            if not company_name.strip():
                st.warning("Add a company name first.")
            else:
                with st.spinner(f"Researching and analyzing {company_name.strip()}..."):
                    lead = enrich_manual_company(company_name)
                    run = run_lead(lead)
                if run.errors:
                    st.error(f"Could not analyze {lead.company_name}: {run.errors[0]}")
                else:
                    st.success(f"{lead.company_name} analyzed and added to the dashboard.")
                    st.rerun()

    sidebar.markdown(
        """
        <div class="sidebar-magic">
          <span>Magic Pen</span>
          <strong>Research 3 new accounts</strong>
          <p>Instantly suggests high-fit accounts from the curated signal library.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if sidebar.button("Run Magic Pen", type="primary", width="stretch"):
        leads = next_magic_accounts(limit=MAGIC_PEN_CANDIDATE_COUNT)
        if not leads:
            st.info("Magic Pen has no new companies left in its current discovery pool.")
            return
        accepted = []
        skipped = []
        with st.spinner(f"Researching candidates and saving the best {MAGIC_PEN_TARGET_COUNT}..."):
            for lead in leads:
                run = run_lead(lead, writeback_filter=is_magic_pen_qualified)
                if run.errors:
                    skipped.append(lead.company_name)
                    continue
                if run.crm_record:
                    accepted.append(lead.company_name)
                else:
                    skipped.append(lead.company_name)
                if len(accepted) >= MAGIC_PEN_TARGET_COUNT:
                    break
        if accepted:
            st.success(f"Magic Pen added: {', '.join(accepted)}.")
            if skipped:
                st.caption(f"Skipped weak-fit candidates: {', '.join(skipped[:6])}.")
        else:
            st.info("Magic Pen researched candidates, but none passed the quality bar for the CRM.")
        st.rerun()


def run_lead(lead: LeadInput, writeback_filter=None):
    pipeline = AccountQualificationPipeline(
        llm=ReplayLLMProvider(REPLAY_PATH),
        db_path=DB_PATH,
        log_path=LOG_PATH,
    )
    return pipeline.run_one(lead, writeback_filter=writeback_filter)


def enrich_manual_company(company_name: str) -> LeadInput:
    return WebDiscovery().enrich_company(company_name)


def is_magic_pen_qualified(run) -> bool:
    if not run.score or not run.route:
        return False
    weak_text = " ".join(
        [
            run.score.primary_pain,
            run.score.rationale,
            *(run.research.recent_signals if run.research else []),
            *(run.research.likely_pains if run.research else []),
        ]
    ).lower()
    if "unclear fit" in weak_text or "weak or generic" in weak_text or "weak or conflicting" in weak_text:
        return False
    return run.score.score >= MAGIC_PEN_MIN_SCORE and run.score.confidence >= MAGIC_PEN_MIN_CONFIDENCE


def next_magic_accounts(limit: int = 3) -> list[LeadInput]:
    existing = load_existing_domains()
    candidates = [lead for lead in HOT_ACCOUNTS if lead.domain.lower() not in existing]
    return candidates[:limit]


def load_existing_domains() -> set[str]:
    return get_account_store().list_domains()


def render_metrics(st: Any, accounts: list[dict[str, Any]]) -> None:
    total = len(accounts)
    auto = sum(1 for row in accounts if row["route_decision"] == "auto_qualify")
    review = sum(1 for row in accounts if row["route_decision"] == "human_review")
    avg_score = round(sum(row["perk_fit_score"] for row in accounts) / total)

    c1, c2, c3, c4 = st.columns(4)
    metric_card(c1, "Accounts Processed", str(total), "Clay-style leads analyzed")
    metric_card(c2, "Ready for Sales", str(auto), "High fit, high confidence")
    metric_card(c3, "Needs Review", str(review), "Human judgment required")
    metric_card(c4, "Average Fit Score", f"{avg_score}", "Across this batch")


def render_account_index(st: Any, accounts: list[dict[str, Any]]) -> None:
    sorted_accounts = sorted(accounts, key=lambda item: item["perk_fit_score"], reverse=True)
    links = [
        f'<a href="#{account_anchor(row)}">{row["company_name"]}</a>'
        for row in sorted_accounts
    ]
    st.markdown(
        f"""
        <div class="account-index">
          <span>Analyzed accounts</span>
          <div>{", ".join(links)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def metric_card(column: Any, label: str, value: str, caption: str) -> None:
    column.markdown(
        f"""
        <div class="metric-card">
          <span>{label}</span>
          <strong>{value}</strong>
          <small>{caption}</small>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_account_card(st: Any, row: dict[str, Any]) -> None:
    decision = row["route_decision"]
    score = row["perk_fit_score"]
    confidence = int(round(row["confidence"] * 100))
    decision_class = decision.replace("_", "-")
    pain = sentence_case(row["primary_pain"])
    sales_motion = MOTION_LABELS.get(row["sales_motion"], sentence_case(row["sales_motion"]))
    segment = SEGMENT_LABELS.get(row["segment"], sentence_case(row["segment"]))
    region = row["region"].upper()
    review_note = row["human_review_reason"] or "No review needed."
    score_tooltip = "Fit score = headcount + international/distributed signal + spend pain + events + growth, minus data gaps."
    confidence_tooltip = "Confidence reflects research evidence strength, then is capped when core firmographic data is missing."

    st.markdown(
        f"""
        <div id="{account_anchor(row)}" class="account-anchor"></div>
        <article class="account-card">
          <div class="account-head">
            <div>
              <h3>{row["company_name"]}</h3>
              <p>{row["domain"]}</p>
            </div>
            <span class="pill {decision_class}">{DECISION_LABELS.get(decision, sentence_case(decision))}</span>
          </div>
          <div class="score-row">
            <div>
              <span>Perk Fit Score <b class="info-dot" title="{score_tooltip}">?</b></span>
              <strong>{score}</strong>
            </div>
            <div>
              <span>Confidence <b class="info-dot" title="{confidence_tooltip}">?</b></span>
              <strong>{confidence}%</strong>
            </div>
            <div>
              <span>Sales Motion</span>
              <strong>{sales_motion}</strong>
            </div>
          </div>
          <div class="progress-track"><div style="width:{score}%"></div></div>
          <div class="detail-grid">
            <div><span>Main Pain</span><strong>{pain}</strong></div>
            <div><span>Segment</span><strong>{segment}</strong></div>
            <div><span>Region</span><strong>{region}</strong></div>
            <div><span>Sales Handoff</span><strong>{humanize_queue(row["owner_queue"])}</strong></div>
          </div>
          <div class="next-action">
            <span>Next Best Action</span>
            <p>{row["next_best_action"]}</p>
          </div>
          <details>
            <summary>Why this decision?</summary>
            <p>{row["research_summary"]}</p>
            <p><strong>Review note:</strong> {review_note}</p>
          </details>
          <details>
            <summary>How were score and confidence calculated?</summary>
            <p><strong>Perk Fit Score:</strong> {score_explanation(row)}</p>
            <p><strong>Confidence:</strong> {confidence_explanation(row)}</p>
          </details>
        </article>
        """,
        unsafe_allow_html=True,
    )
    with st.expander(f"Account tools: {row['company_name']}", expanded=False):
        confirm_delete = st.checkbox(
            f"Confirm deletion of {row['company_name']}",
            key=f"confirm_delete_{row['account_id']}",
        )
        if st.button(
            "Delete Account",
            key=f"delete_{row['account_id']}",
            disabled=not confirm_delete,
            width="stretch",
        ):
            delete_account(row["account_id"])
            st.success(f"{row['company_name']} deleted.")
            st.rerun()


def render_review_card(st: Any, row: dict[str, Any]) -> None:
    reason = row["human_review_reason"] or "Needs confirmation before handoff."
    st.markdown(
        f"""
        <div class="review-card">
          <div>
            <strong>{row["company_name"]}</strong>
            <span>{row["perk_fit_score"]} score · {int(round(row["confidence"] * 100))}% confidence</span>
          </div>
          <p>{reason}</p>
          <small>{sentence_case(row["primary_pain"])}</small>
        </div>
        """,
        unsafe_allow_html=True,
    )
    approve_col, reject_col = st.columns(2)
    if approve_col.button("Approve", key=f"approve_{row['account_id']}", width="stretch"):
        update_review_decision(
            row["account_id"],
            decision="auto_qualify",
            reason="Approved by RevOps from review queue.",
            next_action=f"Create Salesforce task: enrich contacts and draft outreach around {row['primary_pain']}.",
        )
        st.success(f"{row['company_name']} approved for Sales.")
        st.rerun()
    if reject_col.button("Mark Not Fit", key=f"reject_{row['account_id']}", width="stretch"):
        update_review_decision(
            row["account_id"],
            decision="reject",
            reason="Marked not a fit by RevOps from review queue.",
            next_action="Remove from active outbound; keep in nurture if stronger signals appear.",
        )
        st.success(f"{row['company_name']} marked as not a fit.")
        st.rerun()


def render_activity_item(st: Any, event: dict[str, str]) -> None:
    st.markdown(
        f"""
        <div class="activity-item">
          <span>{event["time"]}</span>
          <strong>{event["step"]}</strong>
          <p>{event["message"]}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def load_accounts() -> list[dict[str, Any]]:
    return get_account_store().list_accounts()


def update_review_decision(account_id: str, *, decision: str, reason: str, next_action: str) -> None:
    get_account_store().update_review_decision(account_id, decision=decision, reason=reason, next_action=next_action)


def delete_account(account_id: str) -> None:
    get_account_store().delete_account(account_id)


def get_account_store():
    return make_account_store(DB_PATH)


def load_logs() -> list[dict[str, Any]]:
    if not LOG_PATH.exists():
        return []
    events = []
    with LOG_PATH.open("r", encoding="utf-8") as handle:
        for line in handle:
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return events


def simplify_logs(logs: list[dict[str, Any]]) -> list[dict[str, str]]:
    simplified = []
    for event in logs:
        event_type = event.get("event_type", "")
        if event_type not in {"finished", "failed"}:
            continue
        step = event.get("step", "")
        payload = event.get("payload", {})
        simplified.append(
            {
                "time": event.get("timestamp", "")[11:19],
                "step": STEP_LABELS.get(step, sentence_case(step)),
                "message": activity_message(step, event_type, payload),
            }
        )
    return simplified


def activity_message(step: str, event_type: str, payload: dict[str, Any]) -> str:
    if event_type == "failed":
        return "A step failed and was captured for troubleshooting."
    output = payload.get("output") or {}
    if step == "routing" and isinstance(output, dict):
        decision = DECISION_LABELS.get(output.get("decision", ""), "Decision recorded")
        return f"{decision} route selected."
    if step == "scoring" and isinstance(output, dict):
        return f"Fit score calculated: {output.get('score', 'N/A')}."
    if step == "crm_writeback":
        return "CRM record updated."
    if step == "research":
        return "Research brief generated."
    if step == "enrichment":
        return "Account details enriched."
    if step == "pipeline":
        return "Account run completed."
    return "Step completed."


def score_explanation(row: dict[str, Any]) -> str:
    return (
        "The model adds points for target headcount, international or distributed-team signals, "
        "travel/spend/invoice pain, events or offsites, and growth or hiring momentum. "
        "It subtracts points when core data is missing, then caps the result from 0 to 100. "
        f"This account landed at {row['perk_fit_score']}/100."
    )


def confidence_explanation(row: dict[str, Any]) -> str:
    confidence = int(round(row["confidence"] * 100))
    return (
        "Confidence starts from the strength of the research evidence: multiple clear signal groups score higher, "
        "generic evidence scores lower, and weak or conflicting evidence is routed toward review. "
        "The final confidence is capped lower when domain, country, or headcount data is missing. "
        f"This account's final confidence is {confidence}%."
    )


def sentence_case(value: str) -> str:
    return value.replace("_", " ").replace("-", " ").strip().capitalize()


def humanize_queue(value: str) -> str:
    return value.replace("_", " ").title()


def account_anchor(row: dict[str, Any]) -> str:
    raw = row.get("account_id") or row.get("company_name", "")
    slug = "".join(char.lower() if char.isalnum() else "-" for char in raw).strip("-")
    return f"account-{slug}"


def inject_css(st: Any) -> None:
    st.markdown(
        """
        <style>
        :root {
          --ink: #17201c;
          --muted: #66736d;
          --line: #dce5df;
          --surface: #ffffff;
          --wash: #f3f8f4;
          --mint: #d9f6e6;
          --green: #0a7f53;
          --amber: #a45b00;
          --red: #ad3434;
          --blue: #285a7a;
        }

        .stApp {
          background:
            linear-gradient(180deg, #eef8f0 0%, #fbfcf8 34%, #f8faf7 100%);
          color: var(--ink);
        }

        .block-container {
          max-width: 1260px;
          padding-top: 28px;
          padding-bottom: 56px;
        }

        .hero {
          min-height: 260px;
          border: 1px solid rgba(23, 32, 28, 0.08);
          border-radius: 8px;
          padding: 34px;
          background:
            linear-gradient(135deg, rgba(11, 124, 82, 0.16), rgba(249, 252, 248, 0.9)),
            radial-gradient(circle at 88% 18%, rgba(255, 203, 107, 0.38), transparent 28%),
            #fbfff9;
          margin-bottom: 22px;
        }

        .eyebrow {
          color: var(--green);
          font-weight: 800;
          text-transform: uppercase;
          font-size: 12px;
          letter-spacing: 0;
          margin-bottom: 12px;
        }

        .hero h1 {
          max-width: 780px;
          font-size: 44px;
          line-height: 1.04;
          letter-spacing: 0;
          margin: 0 0 14px;
          color: var(--ink);
        }

        .hero p {
          max-width: 720px;
          color: #4e5c55;
          font-size: 17px;
          line-height: 1.45;
          margin: 0;
        }

        .metric-card, .account-card, .review-card, .activity-item, .empty-state {
          background: var(--surface);
          border: 1px solid var(--line);
          border-radius: 8px;
          box-shadow: 0 10px 28px rgba(23, 32, 28, 0.04);
        }

        [data-testid="stSidebar"] {
          background: #f6fbf5;
          border-right: 1px solid var(--line);
        }

        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
          color: var(--muted);
        }

        .sidebar-agent, .sidebar-brand, .sidebar-magic {
          background: #ffffff;
          border: 1px solid var(--line);
          border-radius: 8px;
          padding: 16px;
          margin: 12px 0;
          box-shadow: 0 10px 24px rgba(23, 32, 28, 0.04);
        }

        .sidebar-agent {
          background:
            linear-gradient(135deg, rgba(11, 124, 82, 0.12), rgba(255, 255, 255, 0.96)),
            #ffffff;
        }

        .sidebar-agent span, .sidebar-brand span, .sidebar-magic span {
          display: block;
          color: var(--green);
          font-size: 12px;
          font-weight: 800;
          text-transform: uppercase;
          letter-spacing: 0;
          margin-bottom: 7px;
        }

        .sidebar-agent strong, .sidebar-brand strong, .sidebar-magic strong {
          display: block;
          color: var(--ink);
          font-size: 18px;
          margin-bottom: 7px;
          line-height: 1.24;
        }

        .sidebar-brand p, .sidebar-magic p {
          color: var(--muted);
          margin: 0;
          line-height: 1.42;
        }

        .sidebar-magic {
          background:
            linear-gradient(135deg, rgba(255, 209, 102, 0.2), rgba(255, 255, 255, 0.94)),
            #ffffff;
          border-color: #ead8a8;
        }

        [data-testid="stExpander"] {
          background: #ffffff;
          border: 1px solid var(--line);
          border-radius: 8px;
          box-shadow: 0 10px 24px rgba(23, 32, 28, 0.04);
        }

        .metric-card {
          padding: 18px;
          min-height: 122px;
        }

        .metric-card span, .detail-grid span, .score-row span, .next-action span {
          display: block;
          color: var(--muted);
          font-size: 12px;
          font-weight: 700;
          text-transform: uppercase;
          letter-spacing: 0;
        }

        .info-dot {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          width: 16px;
          height: 16px;
          margin-left: 4px;
          border-radius: 50%;
          background: #e8f2ec;
          color: var(--green);
          font-size: 11px;
          font-weight: 900;
          text-transform: none;
          cursor: help;
        }

        .metric-card strong {
          display: block;
          font-size: 34px;
          margin: 8px 0 2px;
          color: var(--ink);
        }

        .metric-card small {
          color: var(--muted);
        }

        .account-index {
          background: rgba(255, 255, 255, 0.82);
          border: 1px solid var(--line);
          border-radius: 8px;
          padding: 14px 16px;
          margin: 14px 0 6px;
          box-shadow: 0 10px 28px rgba(23, 32, 28, 0.035);
        }

        .account-index span {
          display: block;
          color: var(--muted);
          font-size: 12px;
          font-weight: 800;
          text-transform: uppercase;
          letter-spacing: 0;
          margin-bottom: 8px;
        }

        .account-index div {
          color: var(--muted);
          line-height: 1.8;
        }

        .account-index a {
          color: var(--green);
          font-weight: 800;
          text-decoration: none;
          white-space: nowrap;
        }

        .account-index a:hover {
          text-decoration: underline;
        }

        .section-title {
          font-size: 20px;
          margin: 30px 0 12px;
          color: var(--ink);
        }

        .top-space {
          margin-top: 30px;
        }

        .account-card {
          padding: 20px;
          margin-bottom: 14px;
        }

        .account-anchor {
          scroll-margin-top: 24px;
        }

        .account-head {
          display: flex;
          justify-content: space-between;
          gap: 16px;
          align-items: flex-start;
        }

        .account-head h3 {
          margin: 0;
          font-size: 23px;
          color: var(--ink);
        }

        .account-head p {
          color: var(--muted);
          margin: 4px 0 0;
        }

        .pill {
          border-radius: 999px;
          padding: 7px 11px;
          font-size: 12px;
          font-weight: 800;
          white-space: nowrap;
        }

        .pill.auto-qualify {
          color: var(--green);
          background: #ddf8e9;
        }

        .pill.human-review {
          color: var(--amber);
          background: #fff0d6;
        }

        .pill.reject {
          color: var(--red);
          background: #fde2e2;
        }

        .score-row {
          display: grid;
          grid-template-columns: repeat(3, minmax(0, 1fr));
          gap: 12px;
          margin-top: 18px;
        }

        .score-row strong {
          display: block;
          font-size: 22px;
          margin-top: 3px;
          color: var(--ink);
        }

        .progress-track {
          height: 8px;
          background: #edf1ec;
          border-radius: 999px;
          overflow: hidden;
          margin: 16px 0;
        }

        .progress-track div {
          height: 100%;
          background: linear-gradient(90deg, #11a86d, #ffd166);
        }

        .detail-grid {
          display: grid;
          grid-template-columns: repeat(2, minmax(0, 1fr));
          gap: 12px;
          margin: 14px 0;
        }

        .detail-grid div {
          background: var(--wash);
          border-radius: 8px;
          padding: 12px;
        }

        .detail-grid strong {
          display: block;
          color: var(--ink);
          font-size: 14px;
          margin-top: 5px;
        }

        .next-action {
          background: #f7f2df;
          border-left: 4px solid #f0b84b;
          border-radius: 8px;
          padding: 12px 14px;
          margin-top: 14px;
        }

        .next-action p {
          color: var(--ink);
          margin: 5px 0 0;
          line-height: 1.4;
        }

        details {
          margin-top: 12px;
          color: var(--muted);
        }

        summary {
          cursor: pointer;
          color: var(--green);
          font-weight: 800;
        }

        .review-card {
          padding: 15px;
          margin-bottom: 12px;
        }

        .review-card strong {
          display: block;
          color: var(--ink);
          font-size: 16px;
        }

        .review-card span, .review-card small {
          display: block;
          color: var(--muted);
          margin-top: 3px;
        }

        .review-card p {
          margin: 10px 0;
          color: var(--ink);
          line-height: 1.38;
        }

        .activity-item {
          padding: 12px 14px;
          margin-bottom: 9px;
        }

        .activity-item span {
          color: var(--muted);
          font-size: 12px;
        }

        .activity-item strong {
          display: block;
          color: var(--ink);
          margin-top: 2px;
        }

        .activity-item p {
          color: var(--muted);
          margin: 2px 0 0;
          font-size: 13px;
        }

        .empty-state {
          padding: 18px;
          color: var(--muted);
        }

        [data-testid="stHeader"] {
          background: transparent;
        }

        @media (max-width: 860px) {
          .hero {
            padding: 24px;
          }

          .hero h1 {
            font-size: 34px;
          }

          .score-row, .detail-grid {
            grid-template-columns: 1fr;
          }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
