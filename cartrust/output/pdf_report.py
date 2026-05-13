"""
Phase 4: PDF Report Generator

Generates a structured PDF trust report using FPDF2.
Gracefully degrades if fpdf2 is not installed.
"""

import logging
from pathlib import Path
from typing import Optional

from cartrust.reasoning.schemas import TrustReport

logger = logging.getLogger(__name__)

# Verdict colour map (R, G, B)
VERDICT_COLOURS = {
    "BUY": (34, 139, 34),
    "NEGOTIATE": (255, 165, 0),
    "NEGOTIATE_WITH_SAFEGUARDS": (255, 140, 0),
    "WALK_AWAY": (200, 30, 30),
}

SEVERITY_COLOURS = {
    "critical": (200, 30, 30),
    "high": (220, 100, 0),
    "medium": (200, 160, 0),
    "low": (80, 130, 80),
}

STATE_LABELS = {
    "verified_clean": "Verified Clean",
    "verified_flagged": "Issues Found",
    "active_resolvable": "Resolvable Issue",
    "critical": "CRITICAL",
    "unverifiable": "Unverifiable",
}


def generate_pdf_report(report: TrustReport, output_path: Optional[str] = None) -> Optional[bytes]:
    """
    Generate a PDF trust report.

    If output_path is given, writes to disk and returns None.
    Otherwise returns the PDF as bytes (suitable for Streamlit download).
    Returns None on any error.
    """
    try:
        from fpdf import FPDF
    except ImportError:
        logger.warning("fpdf2 not installed. PDF generation unavailable.")
        return None

    try:
        pdf = _build_pdf(report, FPDF)
        if output_path:
            pdf.output(output_path)
            return None
        return bytes(pdf.output())
    except Exception as e:
        logger.error(f"PDF generation failed: {e}")
        return None


# ── Builder ────────────────────────────────────────────────────────────────────

def _build_pdf(report: TrustReport, FPDF):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    _header(pdf, report)
    _verdict_banner(pdf, report)
    _vehicle_summary(pdf, report)
    _dimension_table(pdf, report)

    if report.contradictions:
        _contradictions_section(pdf, report)

    _flags_section(pdf, report)

    if report.action_checklist:
        _action_checklist(pdf, report)

    if report.cost_estimate:
        _cost_estimate(pdf, report)

    _footer(pdf)
    return pdf


def _header(pdf, report: TrustReport):
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 12, "CarTrust Assessment Report", ln=True, align="C")
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 6, f"{report.year} {report.make} {report.model}  |  Reg: {report.registration_number}", ln=True, align="C")
    pdf.ln(4)
    pdf.set_draw_color(200, 200, 200)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)


def _verdict_banner(pdf, report: TrustReport):
    r, g, b = VERDICT_COLOURS.get(report.verdict, (80, 80, 80))
    pdf.set_fill_color(r, g, b)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 14, f"  VERDICT: {report.verdict.replace('_', ' ')}", ln=True, fill=True)
    pdf.ln(2)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(30, 30, 30)
    pdf.multi_cell(0, 5, report.verdict_explanation or "")
    pdf.ln(4)


def _vehicle_summary(pdf, report: TrustReport):
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 8, "Overall Score", ln=True)
    pdf.set_font("Helvetica", "", 10)

    price_str = f"Rs. {report.listing_price:,}" if report.listing_price else "N/A"
    rows = [
        ("Composite Trust Score", f"{report.composite_score:.1%}"),
        ("Confidence Level", report.confidence_level.title()),
        ("Data Coverage", f"{report.coverage_ratio:.0%}"),
        ("Listing Price", price_str),
    ]
    _two_col_table(pdf, rows)
    pdf.ln(3)


def _dimension_table(pdf, report: TrustReport):
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 8, "Dimension Assessments", ln=True)

    # Table header
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(45, 7, "Dimension", border=1, fill=True)
    pdf.cell(50, 7, "State", border=1, fill=True)
    pdf.cell(20, 7, "Score", border=1, fill=True, align="C")
    pdf.cell(75, 7, "Summary", border=1, fill=True)
    pdf.ln()

    pdf.set_font("Helvetica", "", 9)
    for a in report.assessments:
        r, g, b = _state_colour(a.state)
        pdf.set_fill_color(r, g, b)
        pdf.set_text_color(255, 255, 255) if a.state == "critical" else pdf.set_text_color(30, 30, 30)
        fill = a.state == "critical"
        pdf.cell(45, 6, a.dimension.title(), border=1, fill=fill)
        pdf.set_text_color(r, g, b)
        pdf.cell(50, 6, STATE_LABELS.get(a.state, a.state), border=1)
        pdf.set_text_color(30, 30, 30)
        pdf.cell(20, 6, f"{a.score:.0%}", border=1, align="C")
        summary = (a.summary or "")[:80]
        pdf.cell(75, 6, summary, border=1)
        pdf.ln()
    pdf.ln(4)


def _contradictions_section(pdf, report: TrustReport):
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(180, 30, 30)
    pdf.cell(0, 8, f"Contradictions Detected ({len(report.contradictions)})", ln=True)
    pdf.set_text_color(30, 30, 30)
    pdf.set_font("Helvetica", "", 9)
    for c in report.contradictions:
        r, g, b = SEVERITY_COLOURS.get(c.severity, (80, 80, 80))
        pdf.set_text_color(r, g, b)
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(0, 5, f"[{c.severity.upper()}] {c.contradiction_id}", ln=True)
        pdf.set_text_color(30, 30, 30)
        pdf.set_font("Helvetica", "", 9)
        pdf.multi_cell(0, 5, c.description or c.evidence_summary)
        pdf.ln(2)
    pdf.ln(2)


def _flags_section(pdf, report: TrustReport):
    all_flags = [(a.dimension, f) for a in report.assessments for f in a.flags]
    if not all_flags:
        return

    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 8, f"Flags ({len(all_flags)})", ln=True)

    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    all_flags.sort(key=lambda x: severity_order.get(x[1].severity, 9))

    for dim, flag in all_flags:
        r, g, b = SEVERITY_COLOURS.get(flag.severity, (80, 80, 80))
        pdf.set_fill_color(r, g, b)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 8)
        badge = f" {flag.severity.upper()} "
        pdf.cell(len(badge) * 2.5, 5, badge, fill=True, align="C")
        pdf.set_text_color(30, 30, 30)
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(0, 5, f"  [{dim.title()}] {flag.flag_id}", ln=True)
        pdf.set_font("Helvetica", "", 9)
        desc = flag.description or flag.evidence_summary
        pdf.multi_cell(0, 5, desc)
        pdf.ln(1)
    pdf.ln(3)


def _action_checklist(pdf, report: TrustReport):
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 8, "Action Checklist", ln=True)
    pdf.set_font("Helvetica", "", 9)
    for i, action in enumerate(report.action_checklist, 1):
        pdf.multi_cell(0, 5, f"{i}. {action}")
    pdf.ln(4)


def _cost_estimate(pdf, report: TrustReport):
    c = report.cost_estimate
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 8, "3-Year Cost Estimate", ln=True)
    rows = [
        ("Annual Maintenance", f"Rs. {c.annual_maintenance_low:,} – {c.annual_maintenance_high:,}"),
        ("Annual Insurance", f"Rs. {c.annual_insurance_estimate:,}"),
        ("3-Year Total (Low)", f"Rs. {c.total_3yr_low:,}"),
        ("3-Year Total (High)", f"Rs. {c.total_3yr_high:,}"),
        ("Fair Market Value", f"Rs. {c.fair_market_value_low:,} – {c.fair_market_value_high:,}"),
        ("Basis", c.basis[:80] if c.basis else ""),
    ]
    _two_col_table(pdf, rows)
    pdf.ln(4)


def _footer(pdf):
    pdf.set_y(-20)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 5, "Generated by CarTrust  |  For educational purposes only. Not financial advice.", align="C")


def _two_col_table(pdf, rows):
    pdf.set_font("Helvetica", "", 10)
    for label, value in rows:
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(70, 6, label + ":", border="B")
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 6, str(value), border="B", ln=True)


def _state_colour(state: str):
    mapping = {
        "verified_clean": (34, 139, 34),
        "verified_flagged": (200, 100, 0),
        "active_resolvable": (30, 80, 160),
        "critical": (200, 30, 30),
        "unverifiable": (120, 120, 120),
    }
    return mapping.get(state, (80, 80, 80))
