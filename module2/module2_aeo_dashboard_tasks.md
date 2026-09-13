# Module 2 — AEO Scoring & Merchant Dashboard — Task Breakdown

**Project:** ON.E Agent Gateway (UAVS Hackathon 2026, FPT Australasia challenge)
**Position in system:** Sits between Module 1 (Semantic Catalog Transformation Engine) and Module 3 (B2A API Gateway & Dynamic Policy Engine). Module 2 scores how "agent-ready" each product is across 5 axes and gives merchants a dashboard to see and fix problems.

## Dependency

Requires standardized product records as output from Module 1 (JSON-LD, structured specs, confidence flags per field). Confirm the exact schema/field names with the Module 1 owner before starting. If unavailable yet, build against a mocked version of this schema and swap in the real one later.

## Deliverables

1. Scoring engine (batch job)
2. Dashboard API (REST)
3. Frontend dashboard (3 screens)
4. Agent Query Simulator

## Task list

### A. Scoring engine

- [ ] Define the input schema (fields expected from Module 1)
- [ ] Completeness score: % of required fields that are filled
- [ ] Machine-readability score: valid JSON-LD present (bool) + % of specs that are structured fields vs. free text
- [ ] Retrievability score: run N sample semantic queries against the vector DB, measure % of times this product appears in the top-K results
- [ ] Answerability score: run N sample FAQ-style questions through an LLM using only the standardized data, measure % answered without "unknown"
- [ ] Transactability score: checklist — price, stock, SKU, shipping fee all present
- [ ] Combine the 5 axes into an overall score + color tier (suggested: red <50, yellow 50-80, green >80 — adjust thresholds as needed)
- [ ] Run scoring as a batch job triggered on catalog load/update — not recalculated live on every dashboard view
- [ ] Persist scores (DB table or JSON file) keyed by product ID

### B. Dashboard API

- [ ] `GET /products` — list with overall score and color tier
- [ ] `GET /products/{id}` — 5-axis breakdown + improvement suggestion for the weakest axis
- [ ] `POST /simulate-query` — accepts a natural-language buyer-style question, returns what an agent would retrieve, whether this product was selected, and why/why not
- [ ] Basic auth/rate limiting (can be stubbed for MVP)

### C. Frontend dashboard

- [ ] Product list screen: table or cards, overall score, color tier, sortable/filterable by tier
- [ ] Product detail screen: radar chart or 5 bars for the axes, plus a 1-2 line improvement suggestion for the weakest one
- [ ] Agent Query Simulator screen: input box for a buyer-style question, submit button, shows which products the agent picked, whether this product was included, and the reason if it was excluded
- [ ] Wire all three screens to the Dashboard API

### D. Suggested stack

- Frontend: React + Vite (or Next.js), Tailwind/shadcn for speed
- Backend: any lightweight REST framework (FastAPI, Node/Express)
- Scoring engine: can run as a script/cron job inside the backend — no separate service needed for the MVP

## Time budget (Day 1, ~8h)

- Scoring engine: ~1.5h
- API endpoints: ~1h
- Frontend (3 screens): ~2-3h
- Buffer / integration / polish: remainder

## Priority order if running behind schedule

Keep in this order, drop from the bottom if needed: Product list > Product detail > Agent Query Simulator.

## Open questions to confirm before/during build

- Exact field names/schema coming out of Module 1
- Which LLM/API key to use for the Answerability scoring step
- Final threshold values for the color tiers
