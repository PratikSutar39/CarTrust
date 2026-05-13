"""
CarTrust — AI Used Car Trust Assessment

Streamlit application. Run with: streamlit run app.py
"""

import logging
from datetime import date, datetime
from pathlib import Path

import pandas as pd
import streamlit as st

logging.basicConfig(level=logging.WARNING)

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="CarTrust — AI Used Car Assessment",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Constants ─────────────────────────────────────────────────────────────────

VERDICT_STYLES = {
    "BUY": {
        "bg": "#1a7a1a", "icon": "✅", "label": "GO AHEAD — BUY",
        "tagline": "This vehicle appears safe to purchase",
    },
    "NEGOTIATE": {
        "bg": "#b37000", "icon": "💰", "label": "NEGOTIATE FIRST",
        "tagline": "Some issues found — use them to negotiate a lower price",
    },
    "NEGOTIATE_WITH_SAFEGUARDS": {
        "bg": "#b35900", "icon": "⚠️", "label": "NEGOTIATE WITH SAFEGUARDS",
        "tagline": "Only proceed with strict payment safeguards in place",
    },
    "WALK_AWAY": {
        "bg": "#c0392b", "icon": "🚫", "label": "DO NOT BUY",
        "tagline": "Critical issues found — walk away from this deal",
    },
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

KNOWLEDGE_DOCS_DIR = Path(__file__).parent / "cartrust" / "knowledge" / "documents"
SAMPLES_DIR = Path(__file__).parent / "samples"


# ── Cached resources ──────────────────────────────────────────────────────────

@st.cache_resource(show_spinner="Loading knowledge base...")
def _get_kb():
    try:
        from cartrust.knowledge.rag import build_knowledge_base
        return build_knowledge_base()
    except Exception:
        return None


@st.cache_resource(show_spinner="Connecting to LLM...")
def _get_llm():
    try:
        from cartrust.reasoning.explainer import _get_llm as get
        return get()
    except Exception:
        return None


# ── Form → raw_inputs adapter ────────────────────────────────────────────────

def _build_inputs_from_form(form_data: dict) -> dict:
    """Convert form values into the raw_inputs dict expected by extractors."""

    # Service log: filter empty rows; convert items text → list
    service_log = []
    for entry in form_data.get("service_entries", []):
        d = (entry.get("date") or "").strip()
        odo = entry.get("odometer") or 0
        items_text = (entry.get("items") or "").strip()
        if d and odo > 0 and items_text:
            items_list = [x.strip() for x in items_text.split(",") if x.strip()]
            service_log.append({
                "date": d,
                "odometer": int(odo),
                "items": items_list,
                "center": entry.get("center") or "authorized",
            })

    # Insurance claims: filter empty
    claims = []
    for c in form_data.get("insurance_claims", []):
        d = (c.get("date") or "").strip()
        amt = c.get("amount") or 0
        if d and amt > 0:
            claims.append({
                "date": d,
                "amount": int(amt),
                "description": c.get("description") or "",
            })

    seller_claims = {
        "loan_status": form_data["seller_loan_status"],
        "no_loan": form_data["seller_no_loan"],
        "accidents": "none" if form_data["seller_no_accidents"] else "not stated",
        "seller_name": form_data["seller_name"],
        "owner_count": int(form_data["seller_claimed_owner_count"]),
    }
    if form_data.get("seller_closure_plan"):
        seller_claims["closure_plan"] = form_data["seller_closure_plan"]

    listing = {
        "make": form_data["make"],
        "model": form_data["model"],
        "year": int(form_data["year"]),
        "asking_price": int(form_data["asking_price"]),
        "odometer_reading": int(form_data["odometer_reading"]),
        "seller_name": form_data["seller_name"],
        "description": form_data["listing_description"],
        "seller_claims": seller_claims,
    }

    rc = {
        "registration_number": form_data["registration_number"],
        "owner_name": form_data["owner_name"],
        "owners_count": int(form_data["owner_count"]),
        "first_registration_date": form_data["first_registration_date"],
        "make": form_data["make"],
        "model": form_data["model"],
        "year": int(form_data["year"]),
        "hypothecation": {
            "active": form_data["hypothecation_active"],
            "lender": form_data["hypothecation_lender"] if form_data["hypothecation_active"] else None,
        },
        "rc_status": "active",
    }

    insurance = {"claims": claims}
    if form_data.get("insurance_declared_mileage"):
        insurance["declared_mileage"] = int(form_data["insurance_declared_mileage"])

    return {
        "listing": listing,
        "seller_claims": seller_claims,
        "rc": rc,
        "service_log": service_log,
        "insurance": insurance,
        "vehicle_age_years": datetime.now().year - int(form_data["year"]),
    }


def _run_form_assessment(form_data: dict):
    """Run the pipeline from form data."""
    from cartrust.extraction import (
        extract_accident, extract_financial, extract_odometer,
        extract_ownership, extract_service,
    )
    from cartrust.reasoning.pipeline import build_trust_report
    from cartrust.schemas import VehicleEvidence, VehicleMetadata

    inputs = _build_inputs_from_form(form_data)

    metadata = VehicleMetadata(
        make=form_data["make"],
        model=form_data["model"],
        year=int(form_data["year"]),
        registration_number=form_data["registration_number"],
        listing_price=int(form_data["asking_price"]),
    )

    evidence = VehicleEvidence(
        metadata=metadata,
        ownership=extract_ownership(inputs),
        odometer=extract_odometer(inputs),
        accident=extract_accident(inputs),
        financial=extract_financial(inputs),
        service=extract_service(inputs),
        extraction_timestamp=datetime.now(),
    )

    return build_trust_report(evidence, llm=_get_llm(), knowledge_collection=_get_kb())


def _run_sample_assessment(vehicle_dir: Path):
    from cartrust.orchestration import build_vehicle_evidence
    from cartrust.reasoning.pipeline import build_trust_report

    evidence = build_vehicle_evidence(str(vehicle_dir))
    return build_trust_report(evidence, llm=_get_llm(), knowledge_collection=_get_kb())


# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("# 🚗 CarTrust")
    st.caption("AI used car trust assessment for India")

    st.markdown("### 🎬 Try a Sample Vehicle")
    st.caption("Skip the form — load a pre-built example:")

    sample_options = [
        ("vehicle_01_clean", "✅ Clean Honda City"),
        ("vehicle_02_contradictions", "⚠️ Suspicious Maruti Swift"),
        ("vehicle_03_hard_stop", "🚫 Loan-encumbered Creta"),
    ]
    for vdir, label in sample_options:
        if st.button(label, key=f"sample_{vdir}", use_container_width=True):
            path = SAMPLES_DIR / vdir
            if path.exists():
                with st.spinner("Running full assessment..."):
                    try:
                        st.session_state["report"] = _run_sample_assessment(path)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed: {e}")
            else:
                st.error(f"Sample folder not found: {vdir}")

    st.divider()

    st.markdown("### 📚 Knowledge Base")
    if KNOWLEDGE_DOCS_DIR.exists():
        docs = sorted(KNOWLEDGE_DOCS_DIR.glob("*.txt"))
        st.caption(f"{len(docs)} documents indexed")
        for d in docs:
            st.markdown(f"• `{d.stem}`")
    else:
        st.caption("No knowledge base found")

    st.divider()
    st.caption(
        "Capstone AI project • "
        "[GitHub](https://github.com/PratikSutar39/CarTrust)"
    )


# ══════════════════════════════════════════════════════════════════════════════
# MAIN: show form OR show results
# ══════════════════════════════════════════════════════════════════════════════

if st.session_state.get("report"):
    # ── RESULTS VIEW ──────────────────────────────────────────────────────────

    report = st.session_state["report"]
    vstyle = VERDICT_STYLES.get(report.verdict, VERDICT_STYLES["WALK_AWAY"])

    # Big verdict banner
    st.markdown(
        f"""
        <div style="background:{vstyle['bg']};padding:36px 24px;border-radius:14px;
                    margin-bottom:20px;text-align:center;
                    box-shadow:0 4px 12px rgba(0,0,0,0.15)">
          <div style="color:white;font-size:13px;opacity:0.85;letter-spacing:3px">
            CARTRUST VERDICT
          </div>
          <div style="color:white;font-size:46px;font-weight:800;margin:14px 0">
            {vstyle['icon']} {vstyle['label']}
          </div>
          <div style="color:#ffffffdd;font-size:16px">{vstyle['tagline']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Vehicle header
    st.markdown(
        f"### {report.year} {report.make} {report.model}  \n"
        f"<span style='color:#888;font-size:14px'>Reg: {report.registration_number}</span>",
        unsafe_allow_html=True,
    )

    if report.verdict_explanation:
        st.info(f"**Why this verdict?**  \n{report.verdict_explanation}")

    # Score row
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Trust Score", f"{report.composite_score:.0%}")
    c2.metric("Confidence", report.confidence_level.title())
    c3.metric("Data Coverage", f"{report.coverage_ratio:.0%}")
    price = report.listing_price
    c4.metric("Listing Price", f"₹{price:,}" if price else "—")

    st.divider()

    # Dimensions + contradictions/checklist
    left, right = st.columns([1, 1], gap="large")

    with left:
        st.subheader("Trust Dimensions")
        for a in report.assessments:
            icon, _ = STATE_BADGES.get(a.state, ("⬜", "#666"))
            expand = a.state in ("critical", "verified_flagged", "active_resolvable")
            label = f"{icon} **{a.dimension.title()}** — {a.state.replace('_', ' ').title()} ({a.score:.0%})"
            with st.expander(label, expanded=expand):
                if a.summary:
                    st.markdown(f"**Summary:** {a.summary}")
                if a.reasoning:
                    st.markdown(f"_{a.reasoning}_")
                for f in a.flags:
                    fc = SEVERITY_COLOURS.get(f.severity, "#666")
                    st.markdown(
                        f'<span style="background:{fc};color:white;padding:2px 8px;'
                        f'border-radius:4px;font-size:11px;font-weight:700">'
                        f'{f.severity.upper()}</span>  `{f.flag_id}`',
                        unsafe_allow_html=True,
                    )
                    st.markdown(f.description or f.evidence_summary)
                if not a.flags:
                    st.success("No issues found in this dimension.")

    with right:
        if report.contradictions:
            st.subheader(f"⚡ Contradictions ({len(report.contradictions)})")
            for c in report.contradictions:
                with st.expander(
                    f"[{c.severity.upper()}] {c.contradiction_id}",
                    expanded=c.severity == "critical",
                ):
                    st.markdown(c.description or c.evidence_summary)

        if report.action_checklist:
            st.subheader("✅ Action Checklist")
            st.caption("Complete these before any payment")
            for i, action in enumerate(report.action_checklist, 1):
                st.checkbox(action, key=f"action_{i}_{i}", value=False)

    # Cost estimate
    if report.cost_estimate:
        st.divider()
        st.subheader("💰 3-Year Cost of Ownership")
        ce = report.cost_estimate
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Annual Maintenance", f"₹{ce.annual_maintenance_low:,}–{ce.annual_maintenance_high:,}")
        c2.metric("Annual Insurance", f"₹{ce.annual_insurance_estimate:,}")
        c3.metric("3-Year Total", f"₹{ce.total_3yr_low:,}–{ce.total_3yr_high:,}")
        c4.metric("Fair Market Value", f"₹{ce.fair_market_value_low:,}–{ce.fair_market_value_high:,}")
        st.caption(f"📚 Source: {ce.basis}")

    st.divider()

    # Actions
    c1, c2 = st.columns(2)
    try:
        from cartrust.output.pdf_report import generate_pdf_report
        pdf_bytes = generate_pdf_report(report)
        if pdf_bytes:
            fname = f"cartrust_{report.registration_number}_{report.make}_{report.model}.pdf".replace(" ", "_")
            c1.download_button(
                "📄 Download Full PDF Report",
                data=pdf_bytes,
                file_name=fname,
                mime="application/pdf",
                use_container_width=True,
            )
    except Exception:
        pass

    if c2.button("🔄 Assess Another Vehicle", use_container_width=True, type="primary"):
        st.session_state["report"] = None
        st.rerun()

    with st.expander("📋 View Raw Report JSON"):
        st.json(report.model_dump())

else:
    # ── FORM VIEW ─────────────────────────────────────────────────────────────

    st.title("🚗 CarTrust")
    st.markdown(
        "Enter the details of the used car you're considering. CarTrust analyses it "
        "across **5 trust dimensions** using a curated **knowledge base** of Indian "
        "used car data, a **deterministic rule engine**, and **LLM explanations** to "
        "tell you whether you should buy it."
    )

    with st.form("vehicle_form", clear_on_submit=False):

        # ── Basic info ────────────────────────────────────────────────────────
        st.subheader("📋 Basic Vehicle Information")

        c1, c2, c3 = st.columns(3)
        make = c1.selectbox(
            "Make *",
            ["Maruti Suzuki", "Maruti", "Honda", "Hyundai", "Toyota", "Tata",
             "Mahindra", "Ford", "Volkswagen", "Renault", "Other"],
        )
        model = c2.text_input("Model *", "Swift")
        year = c3.number_input("Year *", 2005, datetime.now().year, 2019)

        c1, c2, c3 = st.columns(3)
        registration_number = c1.text_input("Registration Number *", "MH12AB1234")
        asking_price = c2.number_input(
            "Asking Price (₹) *", 50000, 5000000, 450000, step=10000,
        )
        odometer_reading = c3.number_input(
            "Stated Odometer (km) *", 0, 500000, 45000, step=1000,
        )

        listing_description = st.text_area(
            "Listing Description",
            "Well maintained, single owner, all papers clear.",
            height=70,
        )

        # ── RC ────────────────────────────────────────────────────────────────
        st.subheader("📜 Registration Certificate (RC)")

        c1, c2 = st.columns(2)
        owner_name = c1.text_input("RC Owner Name", "Rakesh Sharma")
        owner_count = c2.number_input("Previous Owners (per RC)", 1, 10, 1)

        c1, c2 = st.columns(2)
        first_reg_date = c1.date_input(
            "First Registration Date",
            value=date(int(year), 6, 15),
            min_value=date(2005, 1, 1),
            max_value=date.today(),
        )
        hyp_status = c2.selectbox(
            "Loan / Hypothecation on RC?",
            ["No — vehicle is clear", "Yes — active loan"],
        )
        hypothecation_active = hyp_status.startswith("Yes")

        hypothecation_lender = st.text_input(
            "Lender Name (only if loan is active; leave blank otherwise)", "",
        )

        # ── Service history ───────────────────────────────────────────────────
        st.subheader("🛠️ Service History")
        st.caption(
            "Add service log entries. **Items** is a comma-separated list "
            "(e.g. `oil change, brake pads`). Leave blank rows if unknown."
        )

        default_service = pd.DataFrame({
            "date": ["2023-08-15", "2023-02-10", ""],
            "odometer": [38000, 30000, 0],
            "items": ["oil change, oil filter", "oil change", ""],
            "center": ["authorized", "authorized", "authorized"],
        })
        service_df = st.data_editor(
            default_service,
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "date": st.column_config.TextColumn(
                    "Date (YYYY-MM-DD)", help="e.g. 2023-08-15"
                ),
                "odometer": st.column_config.NumberColumn(
                    "Odometer (km)", min_value=0
                ),
                "items": st.column_config.TextColumn(
                    "Items / Work Done",
                    help="Comma-separated, e.g. 'oil change, brake pads'",
                ),
                "center": st.column_config.SelectboxColumn(
                    "Service Center",
                    options=["authorized", "local garage", "independent"],
                ),
            },
            key="service_editor",
        )

        # ── Insurance ─────────────────────────────────────────────────────────
        st.subheader("🚗 Insurance Claims History")
        st.caption("Add insurance claims found in records. Leave blank if none.")

        default_claims = pd.DataFrame({
            "date": [""],
            "amount": [0],
            "description": [""],
        })
        claims_df = st.data_editor(
            default_claims,
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "date": st.column_config.TextColumn("Date (YYYY-MM-DD)"),
                "amount": st.column_config.NumberColumn("Amount (₹)", min_value=0),
                "description": st.column_config.TextColumn("Description"),
            },
            key="claims_editor",
        )

        insurance_declared_mileage = st.number_input(
            "Mileage declared on insurance renewal (km) — optional, 0 = unknown",
            0, 500000, 0, step=1000,
        )

        # ── Seller claims ─────────────────────────────────────────────────────
        st.subheader("💬 Seller's Claims & Disclosures")
        st.caption("What the seller has told you")

        c1, c2 = st.columns(2)
        seller_name = c1.text_input("Seller's Name", "Rakesh Sharma")
        seller_claimed_owner_count = c2.number_input(
            "Owner count claimed by seller", 1, 10, 1,
        )

        seller_loan_status = st.selectbox(
            "Seller's stated loan position",
            ["free of dues", "active loan", "loan being closed", "not stated"],
            help="What did the seller say about a loan on the vehicle?",
        )

        c1, c2 = st.columns(2)
        seller_no_loan = c1.checkbox(
            "Seller explicitly says 'No loan'",
            value=False,
        )
        seller_no_accidents = c2.checkbox(
            "Seller explicitly says 'No accidents'",
            value=False,
        )

        seller_closure_plan = st.text_input(
            "Seller's loan closure plan (only if there's an active loan)",
            "",
        )

        # ── Submit ────────────────────────────────────────────────────────────
        st.divider()
        submitted = st.form_submit_button(
            "🔍 Run Trust Assessment",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        if not all([make, model, registration_number]):
            st.error("⚠️ Please fill in Make, Model, and Registration Number.")
        else:
            form_data = {
                "make": make,
                "model": model,
                "year": int(year),
                "asking_price": int(asking_price),
                "odometer_reading": int(odometer_reading),
                "registration_number": registration_number,
                "owner_name": owner_name,
                "owner_count": int(owner_count),
                "first_registration_date": first_reg_date.strftime("%Y-%m-%d"),
                "hypothecation_active": hypothecation_active,
                "hypothecation_lender": hypothecation_lender,
                "listing_description": listing_description,
                "service_entries": service_df.to_dict("records"),
                "insurance_claims": claims_df.to_dict("records"),
                "insurance_declared_mileage": (
                    int(insurance_declared_mileage)
                    if insurance_declared_mileage > 0 else None
                ),
                "seller_name": seller_name,
                "seller_claimed_owner_count": int(seller_claimed_owner_count),
                "seller_no_loan": seller_no_loan,
                "seller_no_accidents": seller_no_accidents,
                "seller_loan_status": seller_loan_status,
                "seller_closure_plan": seller_closure_plan,
            }

            try:
                with st.spinner("Analysing vehicle against the knowledge base..."):
                    report = _run_form_assessment(form_data)
                st.session_state["report"] = report
                st.rerun()
            except Exception as e:
                st.error(f"Assessment failed: {e}")
                st.exception(e)


# ══════════════════════════════════════════════════════════════════════════════
# KNOWLEDGE BASE BROWSER (always visible at bottom)
# ══════════════════════════════════════════════════════════════════════════════

st.divider()
with st.expander("📚 Browse the Knowledge Base", expanded=False):
    st.markdown(
        "CarTrust's analysis is grounded in these curated documents about the Indian "
        "used car market. The knowledge base powers cost estimates, mileage-pattern "
        "benchmarks, service-interval norms, and price references."
    )

    if KNOWLEDGE_DOCS_DIR.exists():
        docs = sorted(KNOWLEDGE_DOCS_DIR.glob("*.txt"))
        if docs:
            doc_tabs = st.tabs([d.stem.replace("_", " ").title() for d in docs])
            for tab, doc in zip(doc_tabs, docs):
                with tab:
                    content = doc.read_text(encoding="utf-8")
                    st.text_area(
                        "Document",
                        content,
                        height=400,
                        label_visibility="collapsed",
                        disabled=True,
                    )
        else:
            st.info("No documents found in the knowledge base folder.")
    else:
        st.warning(f"Knowledge base folder not found at: {KNOWLEDGE_DOCS_DIR}")
