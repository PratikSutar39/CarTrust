"""
CarTrust — Streamlit Demo Application

Run with: streamlit run app.py
"""

import json
import logging
import os
from pathlib import Path
from typing import Optional

import streamlit as st

logging.basicConfig(level=logging.WARNING)

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="CarTrust — AI Used Car Assessment",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Styling ───────────────────────────────────────────────────────────────────

VERDICT_STYLES = {
    "BUY": {"bg": "#1a7a1a", "icon": "✅", "label": "BUY"},
    "NEGOTIATE": {"bg": "#b37000", "icon": "🟡", "label": "NEGOTIATE"},
    "NEGOTIATE_WITH_SAFEGUARDS": {"bg": "#b35900", "icon": "⚠️", "label": "NEGOTIATE WITH SAFEGUARDS"},
    "WALK_AWAY": {"bg": "#c0392b", "icon": "🚫", "label": "WALK AWAY"},
}

STATE_BADGES = {
    "verified_clean": ("✅", "#1a7a1a"),
    "verified_flagged": ("🟠", "#b35900"),
    "active_resolvable": ("🔵", "#1a4a8a"),
    "critical": ("🔴", "#c0392b"),
    "unverifiable": ("⬜", "#666666"),
}

SEVERITY_COLOURS = {
    "critical": "#c0392b",
    "high": "#d35400",
    "medium": "#b7950b",
    "low": "#1e8449",
}


# ── Sidebar: vehicle selection ────────────────────────────────────────────────

def _list_sample_vehicles():
    samples_dir = Path(__file__).parent / "samples"
    if not samples_dir.exists():
        return {}
    return {
        p.name: p for p in sorted(samples_dir.iterdir()) if p.is_dir()
    }


def _load_listing_preview(vehicle_dir: Path) -> str:
    listing_path = vehicle_dir / "listing.json"
    if not listing_path.exists():
        return vehicle_dir.name
    try:
        data = json.loads(listing_path.read_text())
        return f"{data.get('year', '')} {data.get('make', '')} {data.get('model', '')} — Rs. {data.get('listing_price', 'N/A'):,}" if isinstance(data.get('listing_price'), int) else f"{data.get('year', '')} {data.get('make', '')} {data.get('model', '')}"
    except Exception:
        return vehicle_dir.name


with st.sidebar:
    st.title("🚗 CarTrust")
    st.caption("AI-Powered Used Car Trust Assessment")
    st.divider()

    sample_vehicles = _list_sample_vehicles()
    if sample_vehicles:
        st.subheader("Sample Vehicles")
        vehicle_labels = {name: _load_listing_preview(path) for name, path in sample_vehicles.items()}
        selected_name = st.radio(
            "Select a vehicle:",
            options=list(sample_vehicles.keys()),
            format_func=lambda x: vehicle_labels.get(x, x),
        )
        selected_dir = sample_vehicles[selected_name]
    else:
        st.warning("No sample vehicles found in /samples/")
        selected_dir = None

    st.divider()
    st.caption("LLM API keys are read from .env")
    run_btn = st.button("Run Assessment", type="primary", use_container_width=True, disabled=selected_dir is None)


# ── Main content ──────────────────────────────────────────────────────────────

st.title("CarTrust Assessment")
st.caption("Deterministic rule engine + RAG knowledge + LLM explanations")

if not run_btn and "report" not in st.session_state:
    st.info("Select a vehicle from the sidebar and click **Run Assessment** to begin.")
    st.stop()


@st.cache_resource(show_spinner="Loading knowledge base...")
def _get_knowledge_collection():
    try:
        from cartrust.knowledge.rag import build_knowledge_base
        return build_knowledge_base()
    except Exception as e:
        st.warning(f"Knowledge base unavailable: {e}")
        return None


@st.cache_resource(show_spinner="Initializing LLM...")
def _get_llm():
    try:
        from cartrust.reasoning.explainer import _get_llm as get
        return get()
    except Exception:
        return None


def _run_assessment(vehicle_dir: Path):
    from cartrust.orchestration import build_vehicle_evidence
    from cartrust.reasoning.pipeline import build_trust_report

    with st.spinner("Extracting evidence..."):
        evidence = build_vehicle_evidence(str(vehicle_dir))

    knowledge_collection = _get_knowledge_collection()
    llm = _get_llm()

    with st.spinner("Running rule engine + LLM explanations..."):
        report = build_trust_report(evidence, llm=llm, knowledge_collection=knowledge_collection)

    return report


if run_btn:
    try:
        report = _run_assessment(selected_dir)
        st.session_state["report"] = report
    except Exception as e:
        st.error(f"Assessment failed: {e}")
        st.exception(e)
        st.stop()


if "report" not in st.session_state:
    st.stop()

report = st.session_state["report"]

# ── Verdict banner ────────────────────────────────────────────────────────────

vstyle = VERDICT_STYLES.get(report.verdict, VERDICT_STYLES["WALK_AWAY"])
st.markdown(
    f"""
    <div style="background:{vstyle['bg']};padding:18px 24px;border-radius:8px;margin-bottom:16px">
      <span style="color:white;font-size:28px;font-weight:700">{vstyle['icon']} {vstyle['label']}</span>
      <br><span style="color:#ffffffcc;font-size:14px">{report.verdict_explanation}</span>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Score row ─────────────────────────────────────────────────────────────────

col1, col2, col3, col4 = st.columns(4)
col1.metric("Trust Score", f"{report.composite_score:.0%}")
col2.metric("Confidence", report.confidence_level.title())
col3.metric("Data Coverage", f"{report.coverage_ratio:.0%}")
price_str = f"Rs. {report.listing_price:,}" if report.listing_price else "N/A"
col4.metric("Listing Price", price_str)

st.divider()

# ── Two-column layout: dimensions + contradictions/flags ──────────────────────

left, right = st.columns([1, 1], gap="large")

with left:
    st.subheader("Dimension Assessments")
    for a in report.assessments:
        icon, colour = STATE_BADGES.get(a.state, ("⬜", "#666"))
        score_pct = f"{a.score:.0%}"
        with st.expander(f"{icon} **{a.dimension.title()}** — {a.state.replace('_', ' ').title()} ({score_pct})", expanded=(a.state in ("critical", "verified_flagged"))):
            if a.summary:
                st.markdown(f"**Summary:** {a.summary}")
            if a.reasoning:
                st.markdown(f"*{a.reasoning}*")
            if a.flags:
                st.markdown("**Flags:**")
                for flag in a.flags:
                    fc = SEVERITY_COLOURS.get(flag.severity, "#666")
                    desc = flag.description or flag.evidence_summary
                    st.markdown(
                        f'<span style="color:{fc};font-weight:700">[{flag.severity.upper()}]</span> '
                        f'`{flag.flag_id}` — {desc}',
                        unsafe_allow_html=True,
                    )
            else:
                st.success("No flags for this dimension.")

with right:
    # Contradictions
    if report.contradictions:
        st.subheader(f"Contradictions ({len(report.contradictions)})")
        for c in report.contradictions:
            fc = SEVERITY_COLOURS.get(c.severity, "#666")
            with st.expander(f"[{c.severity.upper()}] {c.contradiction_id}", expanded=c.severity == "critical"):
                st.markdown(c.description or c.evidence_summary)

    # Action checklist
    if report.action_checklist:
        st.subheader("Action Checklist")
        for i, action in enumerate(report.action_checklist, 1):
            st.checkbox(action, key=f"action_{i}", value=False)

# ── Cost estimate ─────────────────────────────────────────────────────────────

if report.cost_estimate:
    st.divider()
    st.subheader("3-Year Cost Estimate")
    c = report.cost_estimate
    cc1, cc2, cc3, cc4 = st.columns(4)
    cc1.metric("Annual Maintenance", f"Rs. {c.annual_maintenance_low:,}–{c.annual_maintenance_high:,}")
    cc2.metric("Annual Insurance", f"Rs. {c.annual_insurance_estimate:,}")
    cc3.metric("3-Year Total (Low)", f"Rs. {c.total_3yr_low:,}")
    cc4.metric("Fair Market Value", f"Rs. {c.fair_market_value_low:,}–{c.fair_market_value_high:,}")
    st.caption(f"Basis: {c.basis}")

# ── PDF download ──────────────────────────────────────────────────────────────

st.divider()
try:
    from cartrust.output.pdf_report import generate_pdf_report
    pdf_bytes = generate_pdf_report(report)
    if pdf_bytes:
        fname = f"cartrust_{report.registration_number}_{report.make}_{report.model}.pdf".replace(" ", "_")
        st.download_button(
            label="Download PDF Report",
            data=pdf_bytes,
            file_name=fname,
            mime="application/pdf",
        )
    else:
        st.caption("PDF generation unavailable (fpdf2 not installed).")
except Exception as e:
    st.caption(f"PDF generation unavailable: {e}")

# ── Raw JSON (collapsed) ──────────────────────────────────────────────────────

with st.expander("Raw JSON Report"):
    st.json(report.model_dump())
