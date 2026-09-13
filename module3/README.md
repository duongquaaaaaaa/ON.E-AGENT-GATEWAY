# Module 3 — B2A API Gateway & Dynamic Policy Engine

> **ON.E Agent Gateway | UAVS Hackathon 2026 — FPT Australasia Challenge**

An autonomous AI shopping agent middleware: 5 REST endpoints, an MCP server, and a deterministic bundle pricing engine — all runnable with one command.

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
│   ├── catalog.json        # Mock product catalog (Module 1 schema)
│   ├── availability.json   # Mock price/stock
│   ├── rules.json          # Bundle discount rule table
│   └── api_keys.json       # Demo agent keys & auth tokens
├── logs/
│   └── audit.log           # Append-only audit trail (created at runtime)
├── mcp_server.py           # MCP server — 6 tools over stdio
├── sample_agent.py         # 6-step autonomous agent demo
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
| Data source | JSON files (swap to real DB — see *Swapping the data source*) |
| MCP transport | stdio (compatible with Claude, Gemini, OpenAI function calling) |

---

## Quick start

### 1. Install dependencies

```bash
cd module3
pip install -r requirements.txt
```

### 2. Start the API server

```bash
uvicorn app.main:app --reload --port 8000
```

The server will:
- Start at `http://localhost:8000`
- Auto-export `openapi.json` on startup
- Begin writing `logs/audit.log`

### 3. Explore the API

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

### 4. Run the sample agent (full 6-step scenario)

In a second terminal, with the server running:

```bash
python sample_agent.py
```

Expected output — no manual steps, completes all 6 phases:
```
STEP 1: Search
STEP 2: Product Detail
STEP 3: Availability
STEP 4: Policy
STEP 5: Bundle Offer
STEP 6: Checkout
SCENARIO COMPLETE ✓
```

### 5. Run the MCP server

```bash
python mcp_server.py
```

Point any MCP-compatible client (Claude Desktop, a custom agent) at this process via stdio.

---

## Endpoints

All endpoints require:
- `X-Agent-Key: <your-key>` header (see `data/api_keys.json` for demo keys)
- Rate limit: 60 req/min per agent (HTTP 429 if exceeded)

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/search` | Semantic product search |
| `GET` | `/products/{sku}` | Full product detail |
| `GET` | `/products/{sku}/availability` | Price & stock |
| `GET` | `/products/{sku}/policy` | Warranty, returns, shipping |
| `POST` | `/bundle-offer` | Check bundle discount eligibility |
| `POST` | `/checkout` | Complete purchase with token validation |

### Demo API keys

| Key | Agent ID | Rate limit |
|-----|----------|------------|
| `agt-key-demo-001` | `agt_demo_1` | 60/min |
| `agt-key-demo-002` | `agt_demo_2` | 60/min |
| `agt-key-hackathon-judge` | `agt_judge` | 120/min |

### Demo auth tokens (checkout)

| Token | Spend limit |
|-------|-------------|
| `tok_limited_50usd` | $50 USD |
| `tok_limited_500usd` | $500 USD |
| `tok_judge_1000usd` | $1,000 USD |

---

## Dynamic Policy Engine

The bundle/discount engine (`app/policy_engine.py`) is **100% deterministic**:
- Rules are loaded from `data/rules.json`
- Matching: SKU-set match OR category-set match
- Discount: `original_total × (1 - discount_percent/100)`
- **Hard price floor**: if `discounted_price < price_floor`, the offer is rejected and list price is returned
- No LLM calls anywhere in this path

### Example rule entry

```json
{
  "id": "rule_001",
  "name": "Mic + Boom Arm Bundle",
  "trigger_skus": ["SKU001", "SKU002"],
  "discount_percent": 15,
  "price_floor": 180.00,
  "active": true
}
```

---

## MCP Tools

The MCP server exposes 6 tools matching the REST surface:

| Tool | Equivalent endpoint |
|------|---------------------|
| `search_products` | `POST /search` |
| `get_product_detail` | `GET /products/{sku}` |
| `get_availability` | `GET /products/{sku}/availability` |
| `get_policy` | `GET /products/{sku}/policy` |
| `get_bundle_offer` | `POST /bundle-offer` |
| `checkout` | `POST /checkout` |

---

## Audit Logging

Every request is logged to `logs/audit.log` as JSON:

```json
{
  "timestamp": "2026-09-13T02:20:00Z",
  "request_id": "a1b2c3d4-...",
  "agent_id": "agt_demo_1",
  "endpoint": "/checkout",
  "method": "POST",
  "status_code": 200,
  "response_summary": "session=chk_abc12345 total=$207.65"
}
```

---

## Swapping the mock data source for the real one

When Module 1's output is ready:

1. **Catalog** (`GET /products/{sku}` and `POST /search`):
   - Replace `data/catalog.json` reads in `app/routers/products.py` and `app/routers/search.py`
   - Hook into Module 1's vector DB via `retrieve.py` for the `/search` endpoint
   - The `SpecField` / `ProductDetail` Pydantic models already match Module 1's schema

2. **Availability** (`GET /products/{sku}/availability`):
   - Replace `data/availability.json` with a live inventory/pricing API call in `_availability()` inside `app/routers/products.py`

3. **Rules** (`data/rules.json`):
   - Promote to a SQLite DB or managed store — `policy_engine.py` only calls `_load_rules()`; swap that function

No changes to middleware, models, or MCP server are needed.

---

## Security notes

- No real card data is ever accepted or stored
- `auth_token` carries a spend limit and expiry; mock validation only
- Rate limiting is in-memory (restart resets counts); use Redis in production
- Audit log is append-only; back it up externally in production
