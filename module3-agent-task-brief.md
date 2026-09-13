# Task Brief: Build Module 3 — B2A API Gateway & Dynamic Policy Engine

**Project:** ON.E Agent Gateway (UAVS Hackathon 2026 — FPT Australasia challenge)
**Your role:** You are responsible for building Module 3 only. Two other modules (Semantic Catalog Transformation Engine, and AEO Scoring & Merchant Dashboard) are being built in parallel by other agents/teammates. Treat their outputs as external dependencies with the interfaces described below.

## 1. Objective

Build a middleware API layer that lets an autonomous AI shopping agent search a product catalog, retrieve structured product details, check live price/stock, look up policy info, get dynamic bundle offers, and complete a checkout — end to end, with no human step in between.

## 2. Assumed upstream dependency (Module 1 output)

Module 1 produces a standardized product record per SKU, approximately shaped like:

```json
{
  "sku": "SKU001",
  "name": "string",
  "specs": {"field": {"value": "...", "unit": "...", "confidence": "high|low"}},
  "compatible_with": ["SKU002", "SKU003"],
  "warranty": {"duration_months": 24, "coverage": "string", "exclusions": "string"},
  "vector_id": "..."
}
```

Query this data via a vector DB for semantic search, and a standard DB/store for structured lookups. If Module 1's output isn't ready yet, build against this mock schema and swap the data source later — do not block on it.

## 3. Scope

**In scope:**
- 5 REST endpoints (below)
- OpenAPI spec generation
- An MCP server wrapper exposing the same 5 capabilities as tools
- API key based agent identification
- Rate limiting per agent
- Audit logging of every call
- A deterministic (non-LLM) dynamic pricing/bundle rule engine with a hard price floor
- A sample agent script (function-calling) that exercises the full 6-step flow end to end

**Out of scope (do not build):**
- Any consumer-facing chat UI
- Real payment processing (mock the token/auth step)
- Real integration with ON.E/OrderCloud (mock this data source unless credentials are provided)
- LLM-based pricing decisions of any kind

## 4. Endpoints to build

### 4.1 `POST /search`
Semantic search over the catalog.
Request: `{"query": "beginner-friendly podcasting mic under $150"}`
Response: `{"results": [{"sku": "SKU001", "score": 0.87}, ...]}`

### 4.2 `GET /products/{sku}`
Structured product detail, confidence-flagged.
Response: full standardized record from section 2, unmodified except for adding a `retrieved_at` timestamp.

### 4.3 `GET /products/{sku}/availability`
Response: `{"sku": "SKU001", "price": 149.00, "currency": "USD", "stock": 42, "updated_at": "..."}`
Mock this with a static or randomized JSON store if no live backend is available.

### 4.4 `GET /products/{sku}/policy`
Response: `{"sku": "SKU001", "warranty": {...}, "returns": {"window_days": 30, "conditions": "..."}, "shipping": {"eta_days": 3, "cost": 0}}`

### 4.5 `POST /checkout`
Request: `{"agent_id": "agt_123", "items": [{"sku": "SKU001", "qty": 1}], "auth_token": "tok_limited_50usd"}`
Response: `{"session_id": "chk_789", "status": "confirmed", "total": 149.00, "audit_ref": "log_..."}`
Validate the token against a mock spend/time limit; reject if exceeded.

## 5. Dynamic Policy Engine (build as a separate, testable module)

- A rule table (start with a simple JSON/CSV file, not a database) mapping SKU pairs or categories to a discount percentage and a **price floor**.
- Trigger: when `/checkout` or a dedicated `/bundle-offer` call includes 2+ related SKUs, check the rule table.
- Logic: `if discounted_price >= price_floor: offer it; else: return list price, no offer.`
- Hard constraint: this logic must be deterministic code, not an LLM call. Do not let a model set the discount amount.

## 6. Security & governance requirements

- Every request must include an `X-Agent-Key` header, validated against a hardcoded list of demo keys.
- Apply per-agent rate limiting (e.g. 60 requests/minute) — return HTTP 429 when exceeded.
- Log every request/response pair (agent id, endpoint, timestamp, outcome) to a local file or lightweight DB — this becomes the audit trail shown in the demo.
- `auth_token` in checkout must carry an implicit spend limit and expiry; never accept or store real card data.

## 7. Deliverables checklist

- [ ] All 5 endpoints implemented and returning the shapes above
- [ ] OpenAPI spec auto-generated and exported (`openapi.json`)
- [ ] MCP server wrapping the same 5 capabilities as callable tools
- [ ] Rule-table-based bundle/discount logic with enforced price floor
- [ ] API key check + rate limiting + audit logging middleware
- [ ] A working sample agent script that runs the full 6-step scenario (search → detail → availability → policy → bundle offer → checkout) without manual intervention
- [ ] A short README covering: architecture, endpoints, how to run locally, how to swap the mock data source for the real one

## 8. Suggested stack

FastAPI (Python) — pairs well with the MCP Python SDK and auto-generates OpenAPI from route definitions. Use SQLite or a JSON file for the mock catalog/rule table; no need for managed infrastructure at this stage.

## 9. Priority order if time runs short

1. `/search` + `/products/{sku}` — required, this is the integration point with Module 1
2. `/checkout` (mocked token validation is fine) — needed to demonstrate the full scenario
3. `/availability`, `/policy` — hardcoded mock data is acceptable
4. Dynamic Policy Engine (bundle/discount) — cut first if behind schedule

## 10. Definition of done

- All 5 endpoints live and documented in OpenAPI
- The sample agent script completes the 6-step scenario end to end with zero manual steps
- Every transaction produces an audit log entry
- The policy engine never returns an offer below the configured price floor
- README is sufficient for a teammate to run the service with one command
