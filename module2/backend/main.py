"""
Module 2 — AEO Dashboard API
FastAPI backend serving the AEO scoring dashboard.
Products are loaded from Module 1 (catalog_standardized.json) via module1_loader.
"""

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import json
import os
import time
from collections import defaultdict

from module1_loader import get_data_source_info
from scoring_engine import (
    load_scores, run_batch_scoring, simulate_agent_query, load_all_products,
)

# ─────────────────────────────────────────────────────────────────────────────
# App Setup
# ─────────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="AEO Scoring Dashboard API",
    description=(
        "Module 2 — Agent-Experience Optimization scoring and merchant dashboard. "
        "Consumes standardized product catalog from Module 1."
    ),
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # In production: restrict to frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────────────────────────────────────
# Rate Limiting (MVP stub — in-memory, per IP)
# ─────────────────────────────────────────────────────────────────────────────

RATE_LIMIT = 60   # requests per minute
_request_counts: dict = defaultdict(list)


def rate_limit_check(request: Request):
    client_ip = request.client.host
    now = time.time()
    window = 60  # seconds
    _request_counts[client_ip] = [
        t for t in _request_counts[client_ip] if now - t < window
    ]
    if len(_request_counts[client_ip]) >= RATE_LIMIT:
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Max 60 req/min.")
    _request_counts[client_ip].append(now)


# ─────────────────────────────────────────────────────────────────────────────
# Auth (MVP stub — static API key)
# ─────────────────────────────────────────────────────────────────────────────

VALID_API_KEYS = {"demo", "hackathon2026"}  # In prod: read from env/DB


def auth_check(request: Request):
    api_key = request.headers.get("X-API-Key", "")
    if api_key and api_key not in VALID_API_KEYS:
        raise HTTPException(status_code=401, detail="Invalid API key.")


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def get_products_index() -> dict:
    """Dict of product_id → product (adapted from Module 1)."""
    return {p["id"]: p for p in load_all_products()}


def get_scores_index() -> dict:
    """Dict of product_id → score_record."""
    return {s["product_id"]: s for s in load_scores()}


# ─────────────────────────────────────────────────────────────────────────────
# Models
# ─────────────────────────────────────────────────────────────────────────────

class SimulateQueryRequest(BaseModel):
    question: str


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/", tags=["Health"])
def root():
    """Basic health check + data source info."""
    info = get_data_source_info()
    return {
        "status":  "ok",
        "module":  "AEO Dashboard API",
        "version": "2.0.0",
        "data_source": info,
    }


@app.get("/health", tags=["Health"])
def health():
    """Detailed health check with data source and product count."""
    info = get_data_source_info()
    try:
        products = load_all_products()
        scores   = load_scores()
        return {
            "status":         "ok",
            "data_source":    info,
            "products_loaded": len(products),
            "scores_computed": len(scores),
        }
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Health check failed: {exc}")


@app.get("/products", tags=["Products"])
def list_products(
    tier:    str | None = None,
    sort:    str = "score_desc",
    request: Request = None,
):
    """
    List all products with their overall AEO score and color tier.

    Query params:
    - **tier**: filter by 'red', 'yellow', or 'green'
    - **sort**: 'score_desc' (default), 'score_asc', 'name_asc'
    """
    rate_limit_check(request)
    auth_check(request)

    scores_index  = get_scores_index()
    products      = load_all_products()

    result = []
    for p in products:
        score_data = scores_index.get(p["id"], {})
        result.append({
            "id":            p["id"],
            "sku":           p.get("sku", ""),
            "name":          p["name"],
            "category":      p.get("category", ""),
            "brand":         p.get("brand"),
            "price":         p.get("price"),
            "currency":      p.get("currency", "AUD"),
            "stock":         p.get("stock"),
            "overall_score": score_data.get("overall_score", 0),
            "tier":          score_data.get("tier", "red"),
            "weakest_axis":  score_data.get("weakest_axis", ""),
        })

    # Filter by tier
    if tier and tier in ("red", "yellow", "green"):
        result = [r for r in result if r["tier"] == tier]

    # Sort
    if sort == "score_asc":
        result.sort(key=lambda x: x["overall_score"])
    elif sort == "name_asc":
        result.sort(key=lambda x: x["name"])
    else:   # score_desc (default)
        result.sort(key=lambda x: -x["overall_score"])

    return {"products": result, "total": len(result)}


@app.get("/products/{product_id}", tags=["Products"])
def get_product(product_id: str, request: Request = None):
    """
    Get full 5-axis AEO score breakdown for a single product,
    plus improvement suggestion for the weakest axis.
    Also returns Module 1 enriched fields: policy, outcomes, specs_list, agent_text.
    """
    rate_limit_check(request)
    auth_check(request)

    products_index = get_products_index()
    scores_index   = get_scores_index()

    product = products_index.get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail=f"Product '{product_id}' not found.")

    score_data = scores_index.get(product_id, {})

    # Build specs_list summary for frontend display
    specs_list = product.get("specs_list", [])

    return {
        # Identity
        "id":          product["id"],
        "sku":         product.get("sku", ""),
        "name":        product["name"],
        "category":    product.get("category", ""),
        "brand":       product.get("brand"),

        # Commerce
        "price":        product.get("price"),
        "currency":     product.get("currency", "AUD"),
        "stock":        product.get("stock"),
        "shipping_fee": product.get("shipping_fee"),   # None if not available

        # Rich text
        "description": product.get("description", ""),   # = agent_text
        "agent_text":  product.get("agent_text", ""),

        # Specs
        "specs":      product.get("specs", {}),          # dict for machine use
        "specs_list": specs_list,                         # original list for display

        # Machine-readability signals
        "jsonld_valid":          product.get("jsonld_valid", False),
        "structured_spec_count": product.get("structured_spec_count", 0),
        "total_spec_count":      product.get("total_spec_count", 0),

        # Retrieval
        "tags":   product.get("tags", []),
        "images": product.get("images", []),

        # Policy (from Module 1)
        "policy":          product.get("policy", {}),
        "warranty_months": product.get("warranty_months"),
        "warranty_scope":  product.get("warranty_scope"),
        "return_days":     product.get("return_days"),
        "exclusions":      product.get("exclusions", []),

        # Outcomes (from Module 1)
        "outcomes":    product.get("outcomes", {}),
        "use_cases":   product.get("use_cases", []),
        "skill_level": product.get("skill_level", ""),
        "environment": product.get("environment", ""),

        # Value claims
        "value_claims": product.get("value_claims", []),

        # AEO scores
        "axes":                   score_data.get("axes", {}),
        "overall_score":          score_data.get("overall_score", 0),
        "tier":                   score_data.get("tier", "red"),
        "weakest_axis":           score_data.get("weakest_axis", ""),
        "improvement_suggestion": score_data.get("improvement_suggestion", ""),
    }


@app.post("/simulate-query", tags=["Simulator"])
def simulate_query(body: SimulateQueryRequest, request: Request = None):
    """
    Accepts a natural-language buyer-style question.
    Returns what an agent would retrieve, whether each product was selected, and why/why not.
    """
    rate_limit_check(request)
    auth_check(request)

    if not body.question or len(body.question.strip()) < 3:
        raise HTTPException(status_code=400, detail="Question must be at least 3 characters.")

    results      = simulate_agent_query(body.question.strip())
    selected     = [r for r in results if r["selected"]]
    not_selected = [r for r in results if not r["selected"]]

    return {
        "question":                body.question,
        "total_products_evaluated": len(results),
        "selected_count":          len(selected),
        "selected":                selected,
        "not_selected":            not_selected,
    }


@app.post("/run-scoring", tags=["Admin"])
def trigger_scoring(request: Request = None):
    """
    Trigger a batch re-scoring of all products loaded from Module 1.
    In production, this would be triggered by catalog load/update events.
    """
    rate_limit_check(request)
    auth_check(request)

    results = run_batch_scoring()
    info    = get_data_source_info()

    return {
        "status":           "success",
        "data_source":      info,
        "products_scored":  len(results),
        "summary": {
            "green":  sum(1 for r in results if r["tier"] == "green"),
            "yellow": sum(1 for r in results if r["tier"] == "yellow"),
            "red":    sum(1 for r in results if r["tier"] == "red"),
        },
    }
