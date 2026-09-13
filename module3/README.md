# Module 3 — B2A API Gateway & Dynamic Policy Engine

> **ON.E Agent Gateway | UAVS Hackathon 2026 — FPT Australasia Challenge**

An autonomous AI shopping agent middleware: 5+ REST endpoints, an MCP server, and a deterministic bundle pricing engine — all runnable with one command. Integrated with Module 1's 63-product monitor/display catalog.

---

## Architecture

```
module3/
├── app/
│   ├── main.py             # FastAPI entrypoint, registers middleware & routers
│   ├── middleware.py        # X-Agent-Key auth, sliding-window rate limiting, audit log
│   ├── models.py           # Pydantic request/response schemas
│   ├── policy_engine.py    # Deterministic bundle/discount rule engine (NO LLM)
│   └── routers/
│       ├── search.py       # POST /search
│       ├── products.py     # GET /products/{sku}, /availability, /policy
│       └── checkout.py     # POST /checkout, POST /bundle-offer
├── data/
│   ├── catalog.json        # 63 products from Module 1 (monitors, displays, accessories)
│   ├── availability.json   # Price (AUD) & stock for all 63 SKUs
│   ├── rules.json          # 20 bundle discount rules (monitor + accessory combos)
│   └── api_keys.json       # Demo agent keys & auth tokens (AUD spend limits)
├── logs/
│   └── audit.log           # Append-only audit trail (created at runtime)
├── mcp_server.py           # MCP server — 6 tools over stdio
├── sample_agent.py         # Test harness — 6-step autonomous demo
├── openapi.json            # Auto-exported on server startup
└── requirements.txt
```

### Key design decisions

| Concern | Choice |
|---|---|
| Framework | FastAPI — auto-generates OpenAPI from type hints |
| Auth | `X-Agent-Key` header validated against `data/api_keys.json` |
| Rate limiting | In-memory sliding window, 60 req/min default |
| Audit logging | Structured JSON written to `logs/audit.log` |
| Pricing | 100% deterministic rule table — no LLM touch |
| Price floor | Hard-coded per rule; offer rejected if floor not met |
| Data source | Module 1 `catalog_standardized.json` → transformed via `generate_module3_data.py` |
| Currency | AUD (Australian Dollars) — matching ON.E platform |
| MCP transport | stdio (compatible with Claude, Gemini, OpenAI function calling) |

---

## Quick start

### 1. Generate data from Module 1 (if not already done)

```bash
cd ..  # project root
python generate_module3_data.py
```

### 2. Install dependencies

```bash
cd module3
python -m pip install -r requirements.txt
```

### 3. Start the API server

```bash
python -m uvicorn app.main:app --reload --port 8000
```

### 4. Run the test harness (full 6-step scenario)

```bash
python sample_agent.py
```

Expected output:
```
STEP 1: Search — '27 inch 4K IPS monitor for design work under 1000 AUD'
STEP 2: Product Detail — MON-27-4K-01 (with confidence flags)
STEP 3: Availability — $899 AUD, 45 units
STEP 4: Policy — 12-month warranty, 14-day returns
STEP 5: Bundle Offer — 10% off with ACC-DOCK-01, price floor enforced
STEP 6: Checkout — $859.28 AUD, order confirmed
SCENARIO COMPLETE ✓
```

> **Note:** `sample_agent.py` is a **test harness** used to validate the Gateway.
> It is NOT a consumer-facing product (per §2.4 scope rules).

---

## Endpoints

All endpoints require `X-Agent-Key` header. Rate limit: 60 req/min per agent (HTTP 429 if exceeded).

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/search` | Semantic product search (63 monitor/display SKUs) |
| `GET` | `/products/{sku}` | Full product detail with confidence flags |
| `GET` | `/products/{sku}/availability` | Price (AUD) & stock |
| `GET` | `/products/{sku}/policy` | Warranty, returns, shipping |
| `POST` | `/bundle-offer` | Check bundle discount eligibility |
| `POST` | `/checkout` | Complete purchase with token validation |

### Demo API keys

| Key | Agent ID | Rate limit |
|-----|----------|------------|
| `agt-key-demo-001` | `agt_demo_1` | 60/min |
| `agt-key-demo-002` | `agt_demo_2` | 60/min |
| `agt-key-hackathon-judge` | `agt_judge` | 120/min |

### Demo auth tokens

| Token | Spend limit |
|-------|-------------|
| `tok_limited_50usd` | $50 |
| `tok_limited_500usd` | $500 |
| `tok_limited_2000aud` | $2,000 AUD |
| `tok_judge_5000aud` | $5,000 AUD |

---

## Dynamic Policy Engine

The bundle/discount engine (`app/policy_engine.py`) is **100% deterministic**:
- Rules are loaded from `data/rules.json` (20 rules generated from Module 1 relations)
- Matching: SKU-set match OR category-set match
- Discount: `original_total × (1 - discount_percent/100)`
- **Hard price floor**: if `discounted_price < price_floor`, the offer is rejected
- No LLM calls anywhere in this path

---

## Security notes

- No real card data is ever accepted or stored
- `auth_token` carries a spend limit and expiry; mock validation only
- Agent identification via `X-Agent-Key` — transparent, auditable
- Audit log is append-only; every transaction recorded
- Compliant with Australian Privacy Act principles

---

## Swapping the data source

When Module 1's output changes:

```bash
# Re-generate from latest Module 1 output
cd ..  # project root
python generate_module3_data.py
```

This regenerates `catalog.json`, `availability.json`, and `rules.json` from `module1/output/catalog_standardized.json`.
