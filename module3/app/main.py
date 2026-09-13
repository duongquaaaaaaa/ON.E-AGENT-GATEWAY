"""
Module 3 — FastAPI Application Entrypoint
B2A API Gateway & Dynamic Policy Engine
"""

from __future__ import annotations
import json
import subprocess
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.middleware import AgentAuthMiddleware
from app.routers import search, products, checkout

# ── App Metadata ──────────────────────────────────────────────────────

app = FastAPI(
    title="ON.E Agent Gateway — Module 3",
    description=(
        "B2A API Gateway & Dynamic Policy Engine for autonomous AI shopping agents. "
        "Provides semantic search, product details, availability, policy lookup, "
        "and checkout with deterministic bundle/discount rules."
    ),
    version="1.0.0",
    contact={
        "name": "ON.E Agent Gateway Team",
        "url": "https://github.com/duongquaaaaaaa/ON.E-AGENT-GATEWAY",
    },
    license_info={"name": "MIT"},
    openapi_tags=[
        {"name": "Search", "description": "Semantic product search"},
        {"name": "Products", "description": "Product detail, availability, and policy"},
        {"name": "Checkout", "description": "Checkout and bundle offer evaluation"},
        {"name": "Health", "description": "Service health and metadata"},
    ],
)

# ── Middleware ────────────────────────────────────────────────────────

app.add_middleware(AgentAuthMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────

app.include_router(search.router)
app.include_router(products.router)
app.include_router(checkout.router)


# ── Health / Root ─────────────────────────────────────────────────────

@app.get("/", tags=["Health"], summary="Root")
async def root():
    return {
        "service": "ON.E Agent Gateway — Module 3",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "openapi": "/openapi.json",
    }


@app.get("/health", tags=["Health"], summary="Health check")
async def health():
    return {"status": "ok"}


# ── OpenAPI export on startup ─────────────────────────────────────────

@app.on_event("startup")
async def export_openapi():
    """Auto-export openapi.json on startup."""
    try:
        spec = app.openapi()
        out_path = Path(__file__).resolve().parent.parent / "openapi.json"
        out_path.write_text(json.dumps(spec, indent=2), encoding="utf-8")
    except Exception as exc:
        print(f"[WARN] Could not export openapi.json: {exc}")
