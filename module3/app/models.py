"""
Module 3 — Pydantic Models
Request/response schemas for all endpoints.
"""

from __future__ import annotations
from typing import Optional, List, Any, Dict
from datetime import datetime
from pydantic import BaseModel, Field


# ── Search ────────────────────────────────────────────────────────────

class SearchRequest(BaseModel):
    query: str = Field(..., description="Natural language product search query", example="27 inch 4K monitor compatible with MacBook Pro 14, under 1000 AUD")


class SearchResult(BaseModel):
    sku: str
    name: str
    score: float = Field(..., ge=0.0, le=1.0)
    category: Optional[str] = None
    price: Optional[float] = Field(None, description="Current price in AUD")          # Fix 1
    currency: Optional[str] = Field(None, description="Currency code (AUD)")           # Fix 1
    reasoning: Optional[str] = Field(None, description="Why this product matched")     # Fix 10


class SearchResponse(BaseModel):
    results: List[SearchResult]
    query: str
    total: int
    constraints_applied: Optional[List[str]] = Field(None, description="Parsed constraints from query")  # Fix 1


# ── Product Detail ────────────────────────────────────────────────────

class SpecField(BaseModel):
    value: Optional[Any] = None
    unit: Optional[str] = None
    confidence: Optional[str] = Field(None, description="high|medium|low")
    source_span: Optional[str] = Field(None, description="Source text the value was extracted from")
    inferred_from: Optional[str] = Field(None, description="If confidence=low, why it was inferred")


class WarrantyInfo(BaseModel):
    duration_months: int
    coverage: str
    exclusions: str


class ProductDetail(BaseModel):
    sku: str
    name: str
    brand: Optional[str] = None
    category: Optional[str] = None
    specs: Optional[Dict[str, SpecField]] = None
    use_cases: Optional[List[str]] = None
    skill_level: Optional[str] = None
    environment: Optional[str] = None
    compatible_with: Optional[List[str]] = None
    warranty: Optional[WarrantyInfo] = None
    vector_id: Optional[str] = None
    description: Optional[str] = None
    retrieved_at: datetime = Field(default_factory=datetime.utcnow)


# ── Availability ──────────────────────────────────────────────────────

class AvailabilityResponse(BaseModel):
    sku: str
    price: float
    currency: str
    stock: int
    updated_at: str


# ── Policy ───────────────────────────────────────────────────────────

class ReturnsPolicy(BaseModel):
    window_days: int
    conditions: str


class ShippingPolicy(BaseModel):
    eta_days: int
    cost: float


class PolicyResponse(BaseModel):
    sku: str
    warranty: WarrantyInfo
    returns: ReturnsPolicy
    shipping: ShippingPolicy


# ── Checkout ─────────────────────────────────────────────────────────

class CheckoutItem(BaseModel):
    sku: str
    qty: int = Field(..., ge=1)


class CheckoutRequest(BaseModel):
    agent_id: str
    items: List[CheckoutItem]
    auth_token: str


class CheckoutResponse(BaseModel):
    session_id: str
    status: str
    total: float
    currency: str = "AUD"
    items: List[CheckoutItem]
    bundle_discount_applied: Optional[float] = None
    audit_ref: str
    token_remaining: Optional[float] = Field(None, description="Remaining spend limit after this order")  # Fix 8
    token_expires_at: Optional[str] = Field(None, description="Token expiry datetime")                    # Fix 8


# ── Bundle Offer ──────────────────────────────────────────────────────

class BundleOfferRequest(BaseModel):
    skus: List[str] = Field(..., min_items=2)


class BundleOfferResponse(BaseModel):
    eligible: bool
    rule_id: Optional[str] = None
    rule_name: Optional[str] = None
    original_total: Optional[float] = None
    discounted_total: Optional[float] = None
    final_total: Optional[float] = None
    discount_percent: Optional[float] = None
    price_floor: Optional[float] = None
    message: str


# ── Error ─────────────────────────────────────────────────────────────

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    audit_ref: Optional[str] = None
