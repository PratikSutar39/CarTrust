# CarTrust — AI-Powered Used Car Trust Assessment

CarTrust is a capstone AI project that helps first-time used car buyers in India make safer, more informed decisions. It ingests documents for a single vehicle listing (RC, service log, insurance record) and produces a structured **Trust Report** with a verdict, dimension scores, flags, contradictions, and a 3-year cost estimate.

---

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API key (optional — LLM explanations)

```bash
cp .env.example .env
# Edit .env and add OPENAI_API_KEY or ANTHROPIC_API_KEY
```

### 3. Run the Streamlit demo

```bash
streamlit run app.py
```

Open http://localhost:8501 in a browser. Select one of the three sample vehicles and click **Run Assessment**.

### 4. Run tests

```bash
pytest tests/ -v
```

---

## Project Structure

```
CarTrust/
├── app.py                          # Streamlit demo application
├── requirements.txt
├── .env.example
│
├── cartrust/
│   ├── schemas.py                  # Phase 2 data contracts (dataclasses)
│   ├── constants.py                # All thresholds and weights
│   ├── utils.py                    # Date parsing, normalization helpers
│   ├── orchestration.py            # Loads vehicle inputs, runs extractors
│   │
│   ├── extraction/                 # Phase 2: Evidence extraction
│   │   ├── ownership.py
│   │   ├── odometer.py             # Multi-signal odometer estimation
│   │   ├── accident.py
│   │   ├── financial.py
│   │   └── service.py
│   │
│   ├── knowledge/                  # RAG knowledge base
│   │   ├── rag.py                  # ChromaDB build + retrieval
│   │   └── documents/              # 6 .txt files (maintenance, pricing, insurance)
│   │
│   ├── reasoning/                  # Phase 3: Rule engine + LLM
│   │   ├── schemas.py              # Pydantic models (Flag, DimensionAssessment, TrustReport)
│   │   ├── pipeline.py             # Main orchestrator: rules → RAG → LLM → TrustReport
│   │   ├── scoring.py              # Deterministic weighted scoring
│   │   ├── verdict.py              # Verdict + action checklist
│   │   ├── explainer.py            # LLM explanation layer (LangChain)
│   │   ├── cost.py                 # 3-year cost estimate (RAG + LLM)
│   │   └── rules/
│   │       ├── ownership.py
│   │       ├── odometer.py
│   │       ├── accident.py
│   │       ├── financial.py
│   │       ├── service.py
│   │       └── contradictions.py   # Cross-dimension contradiction detection
│   │
│   └── output/
│       └── pdf_report.py           # FPDF2 PDF report generator
│
├── samples/
│   ├── vehicle_01_clean/           # Honda City 2018 — expected BUY
│   ├── vehicle_02_contradictions/  # Maruti Swift 2019 — expected NEGOTIATE
│   └── vehicle_03_hard_stop/       # Hyundai Creta 2020 — expected WALK_AWAY
│
└── tests/
    ├── conftest.py                 # Shared fixtures
    ├── test_edge_cases.py          # Scoring bounds, verdict, never-fail
    ├── test_integration.py         # End-to-end pipeline on sample vehicles
    ├── test_rules/                 # Rule engine unit tests (5 dimensions + contradictions)
    └── test_extraction/            # Extraction module unit tests
```

---

## The Four Verdicts

| Verdict | Meaning |
|---|---|
| **BUY** | Score ≥ 80%, no critical issues. Proceed with standard due diligence. |
| **NEGOTIATE** | Score 50–79%. Use flagged issues to negotiate a price reduction. |
| **NEGOTIATE WITH SAFEGUARDS** | Active loan that seller acknowledged. Escrow payment to lender first. |
| **WALK AWAY** | Score < 50% or any critical issue. Do not proceed. |

---

## Five Trust Dimensions

| Dimension | Weight | What It Checks |
|---|---|---|
| Financial | 30% | Hypothecation (loan on RC), seller disclosure |
| Odometer | 25% | Multi-signal mileage estimation vs. stated odometer |
| Accident | 25% | Insurance claims vs. seller disclosure |
| Ownership | 10% | Name match, owner count, rapid flipping |
| Service | 10% | Service regularity, gaps, center switches |

---

## LLM Usage

The system works **without** any API key — all verdicts, scores, and flags are produced by the deterministic rule engine. The LLM is used only to write plain-language explanations of pre-computed results.

Supported providers (auto-detected from `.env`):
- OpenAI: `OPENAI_API_KEY=sk-...`
- Anthropic: `ANTHROPIC_API_KEY=sk-ant-...`

---

## Sample Vehicles

Three sample vehicles are included under `samples/`:

| Vehicle | Expected Verdict | Key Issue |
|---|---|---|
| `vehicle_01_clean` — Honda City 2018 | BUY | No issues |
| `vehicle_02_contradictions` — Maruti Swift 2019 | NEGOTIATE | Major accident claim + service gap |
| `vehicle_03_hard_stop` — Hyundai Creta 2020 | WALK_AWAY | Active hypothecation; seller denied |
