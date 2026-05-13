# CarTrust Architecture

## Design Principles

1. **Determinism first** — Rule engine is pure Python with no randomness. Same inputs always produce the same verdict and score. Tests pass without any API key.
2. **Never fail** — Every module is wrapped in try/except and returns a valid empty result rather than raising. A bad insurance record degrades score; it does not crash the system.
3. **LLM at the edge** — LangChain and LLM SDK imports are confined to `explainer.py` and `cost.py`. The core pipeline has no LLM dependency.
4. **Phase 2 / Phase 3 boundary** — Extraction modules (`extraction/`) extract facts and compute signals. They never make judgments. Rule engine modules (`reasoning/rules/`) interpret signals and assign scores. A line of code belongs in Phase 2 if it asks "what is the data?", and in Phase 3 if it asks "what does it mean?".
5. **Coverage penalty** — Missing data is penalized, not ignored. `composite_score = raw_score × coverage_ratio`. A vehicle with 40% data coverage cannot score above 40%.

---

## Data Flow

```
Raw JSON files (rc.json, listing.json, service_log.json, insurance.json)
           │
           ▼
   orchestration.py: load_vehicle_inputs()
           │
           ▼
   Phase 2: 5 Extraction Modules
   ┌────────────────────────────────────┐
   │ extraction/ownership.py            │
   │ extraction/odometer.py             │  → EvidencePacket (facts + signals)
   │ extraction/accident.py             │
   │ extraction/financial.py            │
   │ extraction/service.py              │
   └────────────────────────────────────┘
           │ VehicleEvidence
           ▼
   Phase 3 Layer 1: Rule Engine
   ┌────────────────────────────────────┐
   │ rules/ownership.py                 │
   │ rules/odometer.py                  │  → DimensionAssessment (state, score, flags)
   │ rules/accident.py                  │
   │ rules/financial.py                 │
   │ rules/service.py                   │
   │ rules/contradictions.py            │  → List[Contradiction]
   └────────────────────────────────────┘
           │ scoring.py → (composite_score, hard_stop, confidence)
           │ verdict.py → verdict string + action checklist
           ▼
   Phase 3 Layer 2: RAG (selective)
   ┌────────────────────────────────────┐
   │ knowledge/rag.py: retrieve()       │  ← ChromaDB (6 knowledge documents)
   └────────────────────────────────────┘
           │ rag_context strings (for odometer, service)
           ▼
   Phase 3 Layer 3: LLM Explanations
   ┌────────────────────────────────────┐
   │ explainer.py: explain_assessment() │  → fills DimensionAssessment.summary/reasoning
   │ explainer.py: explain_contradiction│  → fills Contradiction.description
   │ cost.py: generate_cost_estimate()  │  → CostEstimate (RAG + LLM)
   └────────────────────────────────────┘
           │ TrustReport
           ▼
   Phase 4: Output
   ┌────────────────────────────────────┐
   │ output/pdf_report.py               │  → PDF bytes
   │ app.py (Streamlit)                 │  → Web UI + download
   └────────────────────────────────────┘
```

---

## Key Schema Contracts

### Phase 2 → Phase 3: `EvidencePacket`

```python
@dataclass
class EvidencePacket:
    dimension: str           # "ownership", "odometer", "accident", "financial", "service"
    facts: List[Fact]        # Raw evidence with full provenance
    signals: List[Signal]    # Derived measurements (computed from facts)
    coverage: float          # 0.0–1.0, how much data was available
    observations: List[str]  # Human-readable extraction notes
    data_available: bool
```

`Fact` carries: `value`, `field`, `source_type`, `source_confidence`, `extraction_confidence`, `trust_weight` (property = source × extraction confidence).

`Signal` carries: `name`, `value`, `unit`, `confidence`, `basis`.

### Phase 3 output: `TrustReport`

```python
class TrustReport(BaseModel):
    make, model, year, registration_number, listing_price
    assessments: List[DimensionAssessment]  # 5 items, one per dimension
    contradictions: List[Contradiction]
    composite_score: float       # 0.0–1.0, penalised by coverage
    coverage_ratio: float
    confidence_level: "high" | "moderate" | "low"
    verdict: "BUY" | "NEGOTIATE" | "NEGOTIATE_WITH_SAFEGUARDS" | "WALK_AWAY"
    verdict_explanation: str
    action_checklist: List[str]
    cost_estimate: Optional[CostEstimate]
```

### State machine for `DimensionAssessment.state`

| State | Meaning |
|---|---|
| `verified_clean` | Evidence checked, no issues found |
| `verified_flagged` | Evidence checked, issues flagged |
| `unverifiable` | Insufficient data to make a judgment |
| `active_resolvable` | Financial only: loan exists but seller acknowledged + plan given |
| `critical` | Hard-stop condition (e.g., undisclosed loan) |

---

## Scoring Formula

```
weighted_sum = Σ (assessment.score × dimension_weight)
              for each dimension where state != "unverifiable"

weight_sum = Σ dimension_weight (same filter)

raw_score = weighted_sum / weight_sum

coverage = verifiable_dimensions / 5

composite_score = raw_score × coverage

# Hard stop override
if any dimension.state == "critical":
    composite_score = 0.0
```

**Dimension weights**: Financial=0.30, Odometer=0.25, Accident=0.25, Ownership=0.10, Service=0.10

---

## Contradiction Detection

Four cross-dimensional contradictions are checked deterministically:

1. **CROSS_SELLER_CREDIBILITY_COLLAPSE** (critical): RC shows active hypothecation + seller's `no_loan` claim is True
2. **CROSS_SELLER_VS_INSURANCE** (high): Seller denied accidents + major insurance claim exists
3. **CROSS_CLAIM_NO_SERVICE_ENTRY** (high): Major claim exists but no service entry near the claim date
4. **CROSS_ODO_VS_SERVICE_FREQUENCY** (medium): Service entry count implies far higher mileage than stated

---

## LLM Isolation

The LLM is architecturally isolated:

- `explainer.py` is the only file importing LangChain or LLM SDKs
- `cost.py` imports `langchain.prompts` but no LLM SDK directly — it receives the `llm` object
- All rule engine files (`rules/*.py`, `scoring.py`, `verdict.py`) have zero LLM dependencies
- Tests run 100% without any API key

**What the LLM is allowed to do:**
- Write plain-language flag descriptions
- Write `summary` and `reasoning` fields
- Estimate 3-year costs using RAG knowledge

**What the LLM is NOT allowed to do:**
- Change severity levels
- Add or remove flags
- Change the verdict
- Introduce facts not in the evidence
