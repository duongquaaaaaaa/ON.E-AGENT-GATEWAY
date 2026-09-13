# ON.E Agent Gateway

> **UAVS Hackathon 2026 — FPT Australasia Challenge**
>
> A B2A (Business-to-Agent) Readiness Layer for the ON.E e-commerce platform.
> Helps retailers get found, correctly understood, and automatically transacted with by AI Shopping Agents.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        ON.E Agent Gateway                                   │
│                                                                             │
│  ┌─────────────────────┐   ┌─────────────────────┐  ┌───────────────────┐  │
│  │   MODULE 1          │   │   MODULE 2          │  │   MODULE 3        │  │
│  │   Semantic Catalog  │──▶│   AEO Scoring &     │  │   B2A API Gateway │  │
│  │   Transformation    │   │   Merchant Dashboard │  │   & Policy Engine │  │
│  │   Engine            │──▶│                     │  │                   │  │
│  │                     │   │                     │  │                   │  │
│  │  • Ingest raw SKUs  │   │  • 5-axis scoring   │  │  • REST API (5+)  │  │
│  │  • LLM extraction   │   │  • Product list     │  │  • MCP server     │  │
│  │  • Anti-hallucinate  │   │  • Detail view      │  │  • Auth + rate    │  │
│  │  • Vector indexing   │   │  • Query simulator  │  │  • Bundle pricing │  │
│  │                     │   │                     │  │  • Checkout + log  │  │
│  └─────────┬───────────┘   └─────────────────────┘  └─────────┬─────────┘  │
│            │                                                   │            │
│            │  catalog_standardized.json (63 SKU)               │            │
│            └──────────────────────────────────────────────────▶┘            │
│                                                                             │
│                    ┌─────────────────────────────┐                          │
│                    │  Test Harness (mock buyer)   │                         │
│                    │  6-step end-to-end scenario  │─── validates Gateway    │
│                    └─────────────────────────────┘                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
catalog_raw.json (63 SKU thô, "bẩn")
    │
    ▼
Module 1: Ingest → Extract (Gemini) → Verify → Compose → Index (BGE-M3)
    │
    ├──▶ catalog_standardized.json ──▶ Module 2 (scoring + dashboard)
    │                                      │
    ├──▶ catalog_standardized.json ──▶ Module 3 (API gateway)
    │                                      │
    └──▶ index.npy + index.meta.json      ▼
                                     AI Shopping Agent (test harness)
```

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| LLM | Google Gemini 2.5 Flash | Spec extraction from marketing text |
| Embeddings | BAAI/bge-m3 | Multilingual semantic vector index |
| Backend (M1) | Python 3.10+ | Transformation pipeline |
| Backend (M2) | FastAPI | AEO scoring API |
| Backend (M3) | FastAPI | B2A API Gateway |
| Frontend (M2) | React + Vite | Merchant dashboard |
| Agent Protocol | MCP (stdio) | Tool-based agent integration |
| Data | JSON files | Mock catalog, rules, availability |

### External Dependencies

| Dependency | Usage | License |
|-----------|-------|---------|
| `google-generativeai` | Gemini API for spec extraction | Apache 2.0 |
| `sentence-transformers` | BGE-M3 embedding model | Apache 2.0 |
| `fastapi` | REST API framework | MIT |
| `uvicorn` | ASGI server | BSD |
| `mcp` | MCP Python SDK | MIT |
| `numpy` | Vector operations | BSD |
| `pydantic` | Data validation | MIT |
| `requests` | HTTP client (test harness) | Apache 2.0 |

---

## Quick Start (One-Command Setup)

### Prerequisites
- Python 3.10+
- Node.js 18+ (for Module 2 frontend)

### Option A: Run Module 3 (API Gateway) — fastest path to demo

```bash
# 1. Install dependencies
cd module3
python -m pip install -r requirements.txt

# 2. Generate data from Module 1 output
cd ..
python generate_module3_data.py

# 3. Start the API server
cd module3
python -m uvicorn app.main:app --port 8000

# 4. In another terminal, run the 6-step demo
cd module3
python sample_agent.py
```

### Option B: Run full pipeline (Module 1 → Module 2 → Module 3)

```bash
# Module 1: Run transformation pipeline (uses cache, no API key needed)
cd module1
python -m pip install -r requirements.txt
python run_pipeline.py --skip-extract

# Module 2: Start scoring backend
cd ../module2/backend
python -m pip install -r requirements.txt
python -m uvicorn main:app --port 8001

# Module 2: Start frontend
cd ../frontend
npm install
npm run dev

# Module 3: Generate data + start API
cd ../../
python generate_module3_data.py
cd module3
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --port 8000

# Run full demo
python sample_agent.py
```

---

## Module Overview

### Module 1 — Semantic Catalog Transformation Engine
**Input:** 63 raw SKUs (monitors, displays, accessories) with specs buried in marketing text
**Output:** `catalog_standardized.json` — structured, confidence-flagged, machine-readable product records

Key features:
- Anti-hallucination: every extracted field has `source_span` + `confidence` flag
- Anti-greenwashing: closed taxonomy for sustainability claims
- Outcome-based bundling via `relations.csv`
- 100% retrieval hit rate (top-3) on golden query set

### Module 2 — AEO Scoring & Merchant Dashboard
**Input:** Module 1 standardized catalog
**Output:** 5-axis AEO scores + interactive dashboard

Scoring axes (per product):
1. **Completeness** — % of required fields filled
2. **Machine-Readability** — structured specs ratio + JSON-LD signal
3. **Retrievability** — semantic query match rate
4. **Answerability** — % of buyer FAQs answerable from data
5. **Transactability** — price, stock, SKU, warranty present

Dashboard screens:
- Product list (sortable by score, filterable by tier)
- Product detail (5-axis breakdown + improvement suggestions)
- Agent Query Simulator (what would an agent find?)

### Module 3 — B2A API Gateway & Dynamic Policy Engine
**Input:** Module 1 standardized catalog (via `generate_module3_data.py`)
**Output:** REST API + MCP server for autonomous AI agents

Endpoints:
| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/search` | Semantic product search |
| `GET` | `/products/{sku}` | Full product detail with confidence flags |
| `GET` | `/products/{sku}/availability` | Price (AUD) & stock |
| `GET` | `/products/{sku}/policy` | Warranty, returns, shipping |
| `POST` | `/bundle-offer` | Bundle discount check |
| `POST` | `/checkout` | Complete purchase with token validation |

Security: X-Agent-Key auth, per-agent rate limiting (60 req/min), audit logging.
Pricing: 100% deterministic rule engine, hard price floor enforced, zero LLM involvement.

---

## Demo Scenario (6 Steps + 3 Negative Cases)

The test harness (`module3/sample_agent.py`) runs the complete end-to-end autonomous buyer agent flow:

1. **Search** — `"27 inch 4K monitor compatible with my MacBook Pro 14, under 1000 AUD for design work"` (5 constraints parsed: price ≤ $1000 AUD, device compatibility with `LAP-MBP-14`, product type `monitor`, 4K spec alias `3840x2160`, `design_work` use case)
2. **Detail** — Traced specs with confidence levels & anti-hallucination provenance (`source_span`, `inferred_from`)
3. **Availability** — Real-time price ($899 AUD) and inventory stock (45 units)
4. **Policy** — Warranty duration (12 months), return window (14 days), free shipping
5. **Bundle Offer** — Deterministic policy engine applies 10% bundle discount with USB-C adapter ($840.60 AUD, price floor enforced)
6. **Checkout** — Token-validated order (`chk_...`), spend limit deduction, tamper-evident audit trail log generated

### Negative Cases (Gateway Governance & Safeguards)
- **N1 (Auth Failure — 401 Unauthorized):** Rejects requests missing or having invalid `X-Agent-Key`.
- **N2 (Token Over-Limit — 402 Payment Required):** Blocks orders exceeding agent's delegated spend limit ($899 order with $50 token).
- **N3 (Price Floor Protection — 200 OK Blocked):** High-margin bundle (`MON-27-4K-01` + `ACC-PRIVACY-01`) triggers rule but discount falls below 95% price floor ($919.60). Gateway strictly protects merchant margin and returns list price (`$968.00 AUD`).

---

## Dataset

- **63 SKUs** across monitors, displays, laptops, and accessories (electronics domain)
- **Intentionally noisy** — specs buried in marketing prose, inconsistent field names
- **Synthetic** — generated to demonstrate the transformation pipeline
- **58 relationships** — compatibility, alternatives, upgrades (from `relations.csv`)
- **16 golden queries** — with ground-truth answers for evaluation

---

## Security & Privacy

- No real payment data is ever accepted or stored
- `auth_token` carries a mock spend limit and expiry; authorization only
- Agent identification via `X-Agent-Key` header — transparent to merchants
- Audit log records every API interaction for traceability
- Minimal PII: only agent identifiers, no end-consumer data
- Compliant with Australian Privacy Act principles: data minimization, purpose limitation, transparency of agent identity

---

## Infrastructure Cost Estimate (from demo run)

| Component | One-time | Monthly | Per 1,000 queries |
|-----------|----------|---------|-------------------|
| Gemini Flash (63 SKU extraction) | ~$0.04 | — | — |
| BGE-M3 embedding (63 SKU) | ~$0.00 (local) | — | — |
| Vector search (NumPy, local) | — | $0 | ~$0.00 |
| FastAPI hosting (1 vCPU) | — | ~$10 | — |
| Storage (JSON files, <1 MB) | — | ~$0.01 | — |
| **Total (demo scale)** | **~$0.04** | **~$10** | **~$0.00** |

At 100K SKU scale: embedding cost ~$6.35, vector DB (managed) ~$50/mo, API compute ~$100/mo.

---

## Repository Structure

```
ON.E-AGENT-GATEWAY/
├── module1/                    # Semantic Catalog Transformation Engine
│   ├── src/                    # Pipeline modules (ingest, extract, verify, compose, index)
│   ├── data/                   # Raw catalog + golden queries + relations
│   ├── output/                 # Standardized catalog + evaluation report
│   ├── run_pipeline.py         # Pipeline entrypoint
│   └── demo.py                # Interactive demo script
│
├── module2/                    # AEO Scoring & Merchant Dashboard
│   ├── backend/                # FastAPI scoring API
│   │   ├── main.py             # API endpoints
│   │   ├── scoring_engine.py   # 5-axis scoring logic
│   │   └── module1_loader.py   # Adapter for Module 1 data
│   └── frontend/               # React + Vite dashboard
│       └── src/pages/          # ProductList, ProductDetail, QuerySimulator
│
├── module3/                    # B2A API Gateway & Policy Engine
│   ├── app/                    # FastAPI application
│   │   ├── main.py             # App entrypoint
│   │   ├── middleware.py       # Auth, rate limiting, audit
│   │   ├── models.py           # Pydantic schemas
│   │   ├── policy_engine.py    # Deterministic bundle/discount engine
│   │   └── routers/            # search, products, checkout
│   ├── data/                   # Catalog, availability, rules, API keys
│   ├── mcp_server.py           # MCP tool server (stdio)
│   └── sample_agent.py         # Test harness — 6-step demo
│
├── generate_module3_data.py    # Bridges Module 1 → Module 3 data
├── TESTING_GUIDE_BGK.md        # Quick test guide for Hackathon judges (2-min test)
├── ROUND2_SUBMISSION.md        # Round 2 deliverables & 100-point rubric mapping
└── README.md                   # System architecture & documentation
```

---

## Known Limitations

1. **Similarity score not normalized.** Score is a raw weighted ratio
   (range ~0.1–0.4), not scaled to a human-friendly 0–1 range. Planned
   fix: min-max normalize per result set before returning to agent.

2. **Provenance partial for high-confidence specs.** The anti-hallucination
   traceability layer is fully implemented for low-confidence fields
   (source_span points to character range in marketing copy). High-confidence
   fields currently echo the spec value as source reference; next iteration
   will reference datasheet row IDs from Module 1.

3. **Price floor rejects instead of capping.** When a bundle discount would
   fall below the price floor, the current implementation returns list price
   (no discount). The intended behaviour is to cap the discount at the floor
   amount (e.g., offer $919.60 instead of rejecting entirely). This was a
   deliberate design choice to avoid complexity risk before the demo.

---

## Team

- **Project:** UAVS Hackathon 2026 — FPT Australasia Challenge
- **Product:** ON.E Agent Gateway
- **GitHub:** [ON.E-AGENT-GATEWAY](https://github.com/duongquaaaaaaa/ON.E-AGENT-GATEWAY)
