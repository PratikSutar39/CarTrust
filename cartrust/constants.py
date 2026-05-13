"""
CarTrust — Centralized Configuration

All thresholds, confidence values, and tunable parameters.
Modules import from here. Nothing is hardcoded in extraction logic.

To recalibrate: change values here. All modules update automatically.
"""

# ──────────────────────────────────────────────
# Source Confidence Values
# ──────────────────────────────────────────────

SOURCE_CONFIDENCE = {
    "government_portal":        0.90,   # VAHAN, mParivahan
    "insurance_record":         0.80,   # Regulated, audit-trailed
    "service_log":              0.75,   # Authorized service centers
    "independent_inspection":   0.70,   # Professional but single viewpoint
    "rc_document":              0.90,   # Registration certificate
    "seller_document_original": 0.55,   # Real but selectively provided
    "seller_document_copy":     0.40,   # Easier to alter
    "seller_claim":             0.30,   # Self-interested, unverified
    "listing":                  0.25,   # Optimized for sale
}


# ──────────────────────────────────────────────
# Extraction Confidence Defaults
# ──────────────────────────────────────────────

EXTRACTION_CONFIDENCE = {
    "digital_json":         0.99,   # Structured data, no parsing ambiguity
    "digital_pdf_text":     0.95,   # Clear text layer in PDF
    "scanned_clear":        0.80,   # OCR on clear scan
    "scanned_blurry":       0.50,   # OCR on blurry or low-res image
    "handwritten":          0.35,   # Handwritten notes
    "voice_transcription":  0.60,   # Speech-to-text output
}


# ──────────────────────────────────────────────
# Odometer Module — Signal Computation
# ──────────────────────────────────────────────

OIL_CHANGE_INTERVAL_KM = 5500
TYRE_REPLACEMENT_INTERVAL_KM = 40000
BRAKE_REPLACEMENT_INTERVAL_KM = 30000
AVERAGE_ANNUAL_KM_INDIA = 11000
MIN_ODOMETER_SIGNALS = 2

ODOMETER_SIGNAL_CONFIDENCE = {
    "oil_change":           0.80,
    "tyre_replacement":     0.70,
    "brake_replacement":    0.70,
    "vehicle_age":          0.50,
    "insurance_declaration": 0.75,
}


# ──────────────────────────────────────────────
# Accident Module
# ──────────────────────────────────────────────

MAJOR_CLAIM_THRESHOLD_INR = 50000
CLAIM_SERVICE_MATCH_WINDOW_DAYS = 60


# ──────────────────────────────────────────────
# Service Module
# ──────────────────────────────────────────────

SERVICE_GAP_THRESHOLD_MONTHS = 12
SERVICE_STALE_THRESHOLD_MONTHS = 18


# ──────────────────────────────────────────────
# Ownership Module
# ──────────────────────────────────────────────

RAPID_FLIP_OWNER_THRESHOLD = 3
RAPID_FLIP_YEARS_THRESHOLD = 3


# ──────────────────────────────────────────────
# Dimension Severity Weights (used by Phase 3)
# ──────────────────────────────────────────────

DIMENSION_WEIGHTS = {
    "financial":  0.30,
    "odometer":   0.25,
    "accident":   0.25,
    "ownership":  0.10,
    "service":    0.10,
}
