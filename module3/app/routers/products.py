"""
Module 3 — /products router
GET /products/{sku}          — full product detail
GET /products/{sku}/availability — live price/stock
GET /products/{sku}/policy   — warranty, returns, shipping
"""

from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request

from app.models import (
    ProductDetail,
    AvailabilityResponse,
    PolicyResponse,
    WarrantyInfo,
    ReturnsPolicy,
    ShippingPolicy,
    SpecField,
)

router = APIRouter(tags=["Products"])

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"


def _catalog() -> dict:
    items = json.loads((DATA_DIR / "catalog.json").read_text(encoding="utf-8"))
    return {item["sku"]: item for item in items}


def _availability() -> dict:
    return json.loads((DATA_DIR / "availability.json").read_text(encoding="utf-8"))


# ── GET /products/{sku} ───────────────────────────────────────────────

@router.get(
    "/products/{sku}",
    response_model=ProductDetail,
    summary="Get full product detail",
)
async def get_product(sku: str, request: Request):
    """
    Returns the full standardized product record for a given SKU.
    Mirrors Module 1 output schema; adds a `retrieved_at` timestamp.
    """
    catalog = _catalog()
    if sku not in catalog:
        raise HTTPException(status_code=404, detail=f"SKU '{sku}' not found")

    item = catalog[sku]

    # Coerce specs into SpecField objects
    raw_specs = item.get("specs", {})
    coerced_specs = {}
    for field_name, field_val in raw_specs.items():
        if isinstance(field_val, dict):
            coerced_specs[field_name] = SpecField(**field_val)
        else:
            coerced_specs[field_name] = SpecField(value=field_val)

    warranty_raw = item.get("warranty", {})
    warranty = WarrantyInfo(
        duration_months=warranty_raw.get("duration_months", 12),
        coverage=warranty_raw.get("coverage", ""),
        exclusions=warranty_raw.get("exclusions", ""),
    ) if warranty_raw else None

    return ProductDetail(
        sku=item["sku"],
        name=item["name"],
        brand=item.get("brand"),
        category=item.get("category"),
        specs=coerced_specs,
        use_cases=item.get("use_cases"),
        skill_level=item.get("skill_level"),
        environment=item.get("environment"),
        compatible_with=item.get("compatible_with"),
        warranty=warranty,
        vector_id=item.get("vector_id"),
        description=item.get("description"),
        retrieved_at=datetime.utcnow(),
    )


# ── GET /products/{sku}/availability ─────────────────────────────────

@router.get(
    "/products/{sku}/availability",
    response_model=AvailabilityResponse,
    summary="Get live price and stock",
)
async def get_availability(sku: str, request: Request):
    """
    Returns current price, currency, and stock level for a SKU.
    Data is served from availability.json (mock); swap for a live backend when ready.
    """
    availability = _availability()
    if sku not in availability:
        raise HTTPException(status_code=404, detail=f"Availability data for SKU '{sku}' not found")

    return AvailabilityResponse(**availability[sku])


# ── GET /products/{sku}/policy ────────────────────────────────────────

@router.get(
    "/products/{sku}/policy",
    response_model=PolicyResponse,
    summary="Get warranty, return, and shipping policy",
)
async def get_policy(sku: str, request: Request):
    """
    Returns warranty terms, return policy window, and shipping details for a SKU.
    """
    catalog = _catalog()
    if sku not in catalog:
        raise HTTPException(status_code=404, detail=f"SKU '{sku}' not found")

    item = catalog[sku]
    warranty_raw = item.get("warranty", {})

    warranty = WarrantyInfo(
        duration_months=warranty_raw.get("duration_months", 12),
        coverage=warranty_raw.get("coverage", "Standard coverage"),
        exclusions=warranty_raw.get("exclusions", "Physical damage"),
    )

    # Return policy: derive from warranty duration (mock logic)
    return_days = 30 if warranty.duration_months >= 24 else 14

    returns = ReturnsPolicy(
        window_days=return_days,
        conditions="Item must be in original packaging, unused, with all accessories included.",
    )

    shipping = ShippingPolicy(
        eta_days=3,
        cost=0.0,  # Free shipping on all demo items
    )

    return PolicyResponse(
        sku=sku,
        warranty=warranty,
        returns=returns,
        shipping=shipping,
    )
