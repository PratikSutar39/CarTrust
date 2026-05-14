# CarTrust Evaluation

## Test Coverage Summary

```
102 tests, 0 failures
```

### Test categories

| Category | Count | Description |
|---|---|---|
| Financial rule engine | 13 | clean, critical undisclosed, active resolvable, missing data |
| Odometer rule engine | 12 | clean, major discrepancy, minor discrepancy, unverifiable |
| Accident rule engine | 8 | clean, undisclosed major, disclosed major |
| Ownership rule engine | 9 | clean, name mismatch, rapid flipping |
| Service rule engine | 9 | clean, no records, gap |
| Contradiction detection | 7 | no contradictions, seller credibility collapse, seller vs insurance |
| Scoring & verdict | 10 | score bounds, never-negative, hard-stop, verdict thresholds, coverage |
| Action checklist | 3 | deduplication, severity ordering, empty |
| Extraction: financial | 5 | hypothecation extraction, lender, seller denial |
| Extraction: odometer | 7 | oil change counting, median computation, never-raise |
| Integration: 3 vehicles | 12 | end-to-end verdict verification, report structure |

---

## Manual Evaluation: Sample Vehicles

### Vehicle 01 — Honda City 2018 (expected: BUY)

**Input signals:**
- RC owner matches seller (Rakesh Sharma)
- 0 insurance claims
- No hypothecation in RC
- 5 service entries over 48 months at authorized centers
- Stated odometer 38,000 km; oil change count implies ~35,000 km (within 8%)

**Expected output:**
- Financial: `verified_clean` (0.95)
- Accident: `verified_clean` (0.95)
- Ownership: `verified_clean` (0.90+)
- Service: `verified_clean` (0.90+)
- Composite: ≥ 0.80
- Verdict: **BUY**

---

### Vehicle 02 — Maruti Swift 2019 (expected: NEGOTIATE)

**Input signals:**
- Stated odometer 45,000 km
- 1 major insurance claim Rs. 1,20,000 on 2022-03-15; seller denied any accident
- Service: 18-month gap from 2021-11 to 2023-09; switched from authorized to local garage
- No hypothecation

**Expected output:**
- Accident: `verified_flagged` — `ACC_UNDISCLOSED_MAJOR_CLAIM` (high)
- Service: `verified_flagged` — `SVC_GAP_OVER_12_MONTHS` (medium) + `SVC_CENTER_CHANGE` (low)
- Contradiction: `CROSS_SELLER_VS_INSURANCE` (high)
- Composite: 0.50–0.79
- Verdict: **NEGOTIATE**

---

### Vehicle 03 — Hyundai Creta 2020 (expected: WALK_AWAY)

**Input signals:**
- RC shows active hypothecation: Bajaj Finance Limited
- Listing claim: "No loan, free of dues"
- Stated odometer 32,000 km

**Expected output:**
- Financial: `critical` — `FIN_UNDISCLOSED_LOAN` (critical, score 0.0)
- Contradiction: `CROSS_SELLER_CREDIBILITY_COLLAPSE` (critical)
- Composite: **0.0** (hard-stop override)
- Verdict: **WALK_AWAY**

---

## Failure Modes & Graceful Degradation

| Scenario | System Behaviour |
|---|---|
| No API key | LLM fields filled with evidence summaries; rule engine output unchanged |
| Missing RC document | Financial → `critical` with `FIN_UNVERIFIABLE_CRITICAL_GAP` flag |
| No service log | Service → `unverifiable`; coverage penalty applied |
| Only 1 odometer signal | Odometer → `unverifiable`; no discrepancy judgment made |
| LLM returns malformed JSON | Fallback to evidence_summary; no exception propagates |
| ChromaDB not installed | RAG unavailable; LLM prompted without context |
| Any extraction crash | Returns empty EvidencePacket; pipeline continues |
| Any rule crash | Returns `unverifiable` assessment; pipeline continues |

---

## Design Decisions

### Why is financial encumbrance weighted at 30%?

An undisclosed loan is an existential legal risk. Purchasing a vehicle with active hypothecation means the lender can repossess it even from a legitimate buyer. The 30% weight reflects that this risk alone can override all other dimensions.

### Why does missing financial data trigger `critical` rather than `unverifiable`?

Unlike odometer or service data, the absence of an RC is itself suspicious. In a legitimate sale, the seller can always produce the RC. Financial status cannot be assumed clean when verification is impossible — the default assumption must be pessimistic.

### Why is the LLM not allowed to change severity or scores?

Separating judgment (rule engine) from communication (LLM) ensures the system is auditable and testable without an API key. It also prevents LLM hallucinations from changing the verdict — a concern when the output influences a major financial decision.

### Why is the coverage penalty multiplicative, not additive?

An additive penalty (e.g., subtracting 0.10 per missing dimension) would allow a vehicle with 3 out of 5 clean dimensions to score 0.80 even with 40% coverage. The multiplicative model ensures that `composite_score = raw_score × coverage` — a vehicle with 40% coverage cannot score above 0.40 regardless of how clean the available data is.
