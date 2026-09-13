"""
Module 3 — /checkout and /bundle-offer routers
POST /checkout        — validate token, apply bundle discount, confirm order
POST /bundle-offer    — check bundle eligibility without committing
"""

from __future__ import annotations
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import List

from fastapi import APIRouter, HTTPException, Request

from app.models import (
    CheckoutRequest,
    CheckoutResponse,
    BundleOfferRequest,
    BundleOfferResponse,
    CheckoutItem,
)
from app.policy_engine import evaluate_bundle
from app.middleware import log_audit

router = APIRouter(tags=["Checkout"])

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"


def _load_keys() -> dict:
    return json.loads((DATA_DIR / "api_keys.json").read_text(encoding="utf-8"))


def _load_availability() -> dict:
    return json.loads((DATA_DIR / "availability.json").read_text(encoding="utf-8"))


def _load_catalog() -> dict:
    items = json.loads((DATA_DIR / "catalog.json").read_text(encoding="utf-8"))
    return {item["sku"]: item for item in items}


def _validate_token(token: str) -> dict:
    """
    Validate auth_token: must exist, must not be expired, must have spend headroom.
    Returns the token record or raises HTTPException.
    """
    keys_data = _load_keys()
    token_records = {t["token"]: t for t in keys_data["auth_tokens"]}

    if token not in token_records:
        raise HTTPException(status_code=401, detail="Invalid auth_token")

    rec = token_records[token]
    expires = datetime.fromisoformat(rec["expires_at"].replace("Z", "+00:00"))
    now = datetime.now(tz=expires.tzinfo)

    if now > expires:
        raise HTTPException(status_code=401, detail="auth_token has expired")

    remaining = rec["spend_limit_usd"] - rec.get("used_usd", 0.0)
    if remaining <= 0:
        raise HTTPException(status_code=402, detail="auth_token spend limit exceeded")

    return rec


def _calculate_total(items: List[CheckoutItem], availability: dict) -> float:
    total = 0.0
    for item in items:
        if item.sku not in availability:
            raise HTTPException(status_code=404, detail=f"SKU '{item.sku}' not found in availability")
        total += availability[item.sku]["price"] * item.qty
    return round(total, 2)


# ── POST /checkout ────────────────────────────────────────────────────

@router.post(
    "/checkout",
    response_model=CheckoutResponse,
    summary="Complete a checkout session",
)
async def checkout(body: CheckoutRequest, request: Request):
    """
    Validates the auth_token against spend limit and expiry.
    Applies bundle discount if eligible.
    Returns a session_id and audit reference. Does NOT process real payments.
    """
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    agent_id = getattr(request.state, "agent_id", body.agent_id)

    # Token validation
    token_rec = _validate_token(body.auth_token)

    availability = _load_availability()
    original_total = _calculate_total(body.items, availability)

    # Check spend limit
    remaining = token_rec["spend_limit_usd"] - token_rec.get("used_usd", 0.0)
    if original_total > remaining:
        raise HTTPException(
            status_code=402,
            detail=f"Order total ${original_total:.2f} AUD exceeds remaining spend limit ${remaining:.2f} AUD",
        )

    # Bundle discount check
    skus = [item.sku for item in body.items]
    bundle_result = evaluate_bundle(skus) if len(skus) >= 2 else {"eligible": False}
    bundle_discount = None
    final_total = original_total

    if bundle_result.get("eligible"):
        # Recalculate with quantities (engine gives single-unit total; scale accordingly)
        qty_map = {item.sku: item.qty for item in body.items}
        total_qty = sum(qty_map.values())
        # Apply discount proportionally
        discount_pct = bundle_result["discount_percent"] / 100.0
        discounted = original_total * (1 - discount_pct)
        floor = bundle_result["price_floor"]
        if discounted >= floor:
            bundle_discount = round(original_total - discounted, 2)
            final_total = round(discounted, 2)

    session_id = f"chk_{uuid.uuid4().hex[:8]}"
    audit_ref = f"log_{request_id}"

    log_audit(
        agent_id=agent_id,
        endpoint="/checkout",
        method="POST",
        status_code=200,
        request_id=request_id,
        request_body={"items": [i.model_dump() for i in body.items], "agent_id": body.agent_id},
        response_summary=f"session={session_id} total=${final_total:.2f}",
    )

    return CheckoutResponse(
        session_id=session_id,
        status="confirmed",
        total=final_total,
        currency="AUD",
        items=body.items,
        bundle_discount_applied=bundle_discount,
        audit_ref=audit_ref,
        token_remaining=round(remaining - final_total, 2),  # Fix 8
        token_expires_at=token_rec.get("expires_at"),        # Fix 8
    )


# ── POST /bundle-offer ────────────────────────────────────────────────

@router.post(
    "/bundle-offer",
    response_model=BundleOfferResponse,
    summary="Check bundle discount eligibility",
)
async def bundle_offer(body: BundleOfferRequest, request: Request):
    """
    Non-destructive: checks whether a set of SKUs qualifies for a bundle discount
    without creating an order. The policy engine is purely deterministic.
    Includes anti-abuse price probing detection (DP-04).
    """
    if len(body.skus) < 2:
        raise HTTPException(status_code=422, detail="At least 2 SKUs required for bundle evaluation")

    # Pass agent_id for anti-abuse tracking (DP-04)
    agent_id = getattr(request.state, "agent_id", None)
    result = evaluate_bundle(body.skus, agent_id=agent_id)

    # If blocked by anti-abuse detection, return 429
    if result.get("blocked"):
        raise HTTPException(status_code=429, detail=result["message"])

    return BundleOfferResponse(
        eligible=result["eligible"],
        rule_id=result.get("rule_id"),
        rule_name=result.get("rule_name"),
        original_total=result["original_total"],
        discounted_total=result.get("discounted_total"),
        final_total=result.get("final_total"),
        discount_percent=result.get("discount_percent"),
        price_floor=result.get("price_floor"),
        message=result["message"],
    )
