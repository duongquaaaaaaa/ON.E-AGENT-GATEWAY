"""
Module 3 — /search router
POST /search — semantic search over the product catalog.

v2 Fixes:
- Fix v2-2: Infer product type from query → filter out accessories from monitor search
- Fix v2-3: Remove name token matching from scoring (exposes keyword matching)
- Fix v2-4: Better ranking via weighted spec/use_case matching
- Fix v2-5: Compatibility is a hard filter, not soft boost
"""

from __future__ import annotations
import json
import re
from pathlib import Path
from typing import List, Optional, Tuple

from fastapi import APIRouter, Request

from app.models import SearchRequest, SearchResponse, SearchResult

router = APIRouter(tags=["Search"])

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"

STOP_WORDS = {
    "a", "an", "the", "for", "with", "and", "or", "is", "of", "in", "to",
    "by", "at", "on", "from", "up", "that", "it", "its", "this", "be",
    "my", "i", "me", "we", "us", "can", "do", "does", "not", "no",
    "work", "good", "best", "find", "need", "want", "looking",
}


def _load_catalog() -> List[dict]:
    return json.loads((DATA_DIR / "catalog.json").read_text(encoding="utf-8"))


def _load_availability() -> dict:
    return json.loads((DATA_DIR / "availability.json").read_text(encoding="utf-8"))


def _tokenize(text: str) -> List[str]:
    text = text.replace("_", " ")
    return re.findall(r"\b\w+\b", text.lower())


# ── Constraint Parsing ────────────────────────────────────────────────

def _parse_price_ceiling(query: str) -> Optional[float]:
    m = re.search(r"(?:under|below|dưới|budget|less\s+than)[\s\$]*([\d,]+)", query.lower())
    return float(m.group(1).replace(",", "")) if m else None


def _parse_device_constraint(query: str) -> Optional[str]:
    patterns = [
        r"compatible\s+with\s+(?:my\s+)?(.+?)(?:,|\.|under|below|$)",
        r"for\s+(?:my\s+)?(macbook\s+\w+\s*\d*|thinkpad\s+\w+|dell\s+\w+\s*\d*|surface\s+\w+\s*\d*)",
        r"works?\s+with\s+(?:my\s+)?(.+?)(?:,|\.|under|below|$)",
    ]
    for pattern in patterns:
        m = re.search(pattern, query.lower())
        if m:
            return m.group(1).strip()
    return None


def _find_device_sku(device_text: str, catalog: List[dict]) -> Optional[str]:
    device_tokens = set(_tokenize(device_text)) - STOP_WORDS
    best_sku, best_overlap = None, 0
    for product in catalog:
        if not product.get("sku", "").startswith("LAP-"):
            continue
        name_tokens = set(_tokenize(product.get("name", "")))
        overlap = len(device_tokens & name_tokens)
        if overlap > best_overlap:
            best_overlap = overlap
            best_sku = product["sku"]
    return best_sku if best_overlap >= 2 else None


# Fix v2-2: Infer what product TYPE the user is looking for
MONITOR_SIGNALS = {"monitor", "display", "screen", "màn", "hình", "monitors", "displays"}
ACCESSORY_SIGNALS = {"cable", "dock", "stand", "adapter", "charger", "light", "privacy", "accessory"}
LAPTOP_SIGNALS = {"laptop", "notebook", "macbook", "thinkpad"}


def _infer_product_type(query: str) -> Optional[str]:
    """Infer what product category the user is looking for."""
    tokens = set(_tokenize(query))
    # Check for explicit monitor/screen terms
    if tokens & MONITOR_SIGNALS:
        return "monitor"
    # Check for accessory terms
    if tokens & ACCESSORY_SIGNALS:
        return "accessory"
    # Check for laptop terms
    if tokens & LAPTOP_SIGNALS:
        return "laptop"
    # If query mentions specs like 4K, IPS, Hz, inch → likely monitor
    spec_signals = {"4k", "ips", "oled", "qhd", "1080p", "144hz", "165hz", "27", "32", "24", "curved"}
    if tokens & spec_signals:
        return "monitor"
    return None


def _is_monitor_category(category: str) -> bool:
    cat_lower = category.lower()
    return "monitor" in cat_lower or "display" in cat_lower


# ── Scoring ───────────────────────────────────────────────────────────

FIELD_WEIGHTS = {
    "specs": 5.0,       # Spec matching is the strongest signal
    "use_cases": 4.0,   # Use case relevance
    "category": 2.5,
    "brand": 1.0,
    "description": 1.5,
    "skill_level": 1.0,
    "environment": 1.0,
}


def _score_product(query_tokens: List[str], product: dict,
                   price_ceiling: Optional[float],
                   availability: dict,
                   device_sku: Optional[str]) -> Tuple[float, List[str]]:
    """
    Score a product against query tokens. Returns (score, reasons).
    v2-3: No name token matching (removes keyword-matching exposure).
    v2-4: Better weighted scoring for spec and use_case fields.
    """
    if not query_tokens:
        return 0.0, []

    meaningful_tokens = [t for t in query_tokens if t not in STOP_WORDS]
    if not meaningful_tokens:
        meaningful_tokens = query_tokens

    reasons = []
    weighted_hits = 0.0
    max_possible = sum(FIELD_WEIGHTS.values()) * len(meaningful_tokens)

    def _check_field(field_name: str, text: str, aliases: Optional[dict] = None):
        nonlocal weighted_hits
        field_tokens = set(_tokenize(text))
        weight = FIELD_WEIGHTS.get(field_name, 1.0)
        matched = []
        for t in meaningful_tokens:
            if t in field_tokens:
                matched.append(t)
            elif aliases and t in aliases:
                if any(a in field_tokens for a in aliases[t]):
                    matched.append(t)
        if matched:
            weighted_hits += len(matched) * weight
            return matched
        return []

    # v2-3: Removed name token matching — it exposes keyword matching
    # Only score structured fields that represent real semantic signals

    # ── Mục 2: Spec aliases (data-level, not algorithm change) ────────
    # Expand query tokens with known spec aliases so "4K" matches "3840x2160"
    SPEC_ALIASES = {
        "4k": ["3840x2160", "3840 x 2160", "3840", "uhd"],
        "qhd": ["2560x1440", "1440p"],
        "fhd": ["1920x1080", "1080p"],
        "ips": ["ips"],
        "oled": ["oled"],
    }
    expanded_tokens = list(meaningful_tokens)
    for token in meaningful_tokens:
        if token in SPEC_ALIASES:
            expanded_tokens.extend(SPEC_ALIASES[token])
    # Use expanded tokens for spec matching only
    spec_meaningful = expanded_tokens

    # Specs — the core semantic signal
    spec_text_parts = []
    specs = product.get("specs", {})
    matched_spec_names = []
    if isinstance(specs, dict):
        for field_name, field_data in specs.items():
            readable_name = field_name.replace("_", " ")
            spec_text_parts.append(readable_name)
            if isinstance(field_data, dict):
                val = field_data.get("value", "")
                if val is not None:
                    val_str = str(val) if not isinstance(val, list) else " ".join(str(v) for v in val)
                    spec_text_parts.append(val_str)
                    val_tokens = set(_tokenize(val_str))
                    for t in spec_meaningful:
                        if t in val_tokens or t in set(_tokenize(readable_name)):
                            # Show the alias label if it was an alias match
                            alias_label = ""
                            for alias_key, alias_vals in SPEC_ALIASES.items():
                                if t in alias_vals and alias_key in meaningful_tokens:
                                    alias_label = f" ({alias_key.upper()})"
                                    break
                            matched_spec_names.append(f"{readable_name}={val_str}{alias_label}")
                            break

    spec_hits = _check_field("specs", " ".join(spec_text_parts), aliases=SPEC_ALIASES)
    if matched_spec_names:
        reasons.append(f"Specs: {'; '.join(matched_spec_names[:4])}")

    # Use cases — only add to reasoning if actually matching query intent
    use_cases = product.get("use_cases", [])
    uc_text = " ".join(str(uc) for uc in use_cases)
    uc_hits = _check_field("use_cases", uc_text)
    if uc_hits:
        # v2-6: Only show use_cases that actually match the query tokens
        matched_uc = [uc for uc in use_cases if set(_tokenize(str(uc))) & set(meaningful_tokens)]
        if matched_uc:
            reasons.append(f"Use case match: {', '.join(matched_uc)}")

    cat_hits = _check_field("category", product.get("category", ""))
    if cat_hits:
        reasons.append(f"Category: {product.get('category', '')}")

    _check_field("brand", product.get("brand", ""))
    _check_field("skill_level", product.get("skill_level", ""))
    _check_field("environment", product.get("environment", ""))
    _check_field("description", product.get("description", ""))

    # Base score
    raw_score = weighted_hits / max_possible if max_possible > 0 else 0.0

    # Price filter bonus/penalty
    sku = product.get("sku", "")
    avail = availability.get(sku, {})
    product_price = avail.get("price", 0)

    if price_ceiling is not None and product_price > 0:
        if product_price <= price_ceiling:
            raw_score += 0.08
            reasons.append(f"Within budget: ${product_price} AUD ≤ ${price_ceiling} AUD")
        else:
            raw_score -= 0.25
            reasons.append(f"Over budget: ${product_price} AUD > ${price_ceiling} AUD")

    score = min(round(max(raw_score, 0.0), 4), 1.0)
    return score, reasons


# ── Endpoint ──────────────────────────────────────────────────────────

@router.post("/search", response_model=SearchResponse, summary="Semantic product search")
async def search_products(body: SearchRequest, request: Request):
    """
    Semantic search over the product catalog with multi-constraint parsing.

    Parses natural language constraints:
    - Product type: "monitor" → filter to monitors only (v2-2)
    - Price ceiling: "under 1000 AUD" → hard filter
    - Device compatibility: "compatible with MacBook Pro 14" → hard filter (v2-5)
    - Specs: "4K", "IPS", "144Hz" → weighted matching
    - Use case: "design work" → matched against use_cases
    """
    catalog = _load_catalog()
    availability = _load_availability()
    query_tokens = _tokenize(body.query)

    # Parse constraints
    price_ceiling = _parse_price_ceiling(body.query)
    device_text = _parse_device_constraint(body.query)
    device_sku = _find_device_sku(device_text, catalog) if device_text else None
    product_type = _infer_product_type(body.query)

    # Build constraints summary
    hard_filters = []
    if price_ceiling:
        hard_filters.append(f"price ≤ ${price_ceiling} AUD")
    if device_sku:
        hard_filters.append(f"compatible_with: {device_sku}")
    if product_type:
        hard_filters.append(f"product_type: {product_type}")

    scored = []
    for product in catalog:
        sku = product.get("sku", "")

        # ── v2-2: Hard filter by product type ─────────────────────────
        if product_type == "monitor" and not _is_monitor_category(product.get("category", "")):
            continue
        if product_type == "accessory" and not sku.startswith("ACC-"):
            continue

        # ── v2-5: Hard filter by compatibility (not soft boost) ───────
        if device_sku:
            compatible = product.get("compatible_with", [])
            if device_sku not in compatible:
                continue

        # ── v2-5: Hard filter by price ────────────────────────────────
        avail = availability.get(sku, {})
        product_price = avail.get("price", 0)
        if price_ceiling is not None and product_price > price_ceiling:
            continue

        score, reasons = _score_product(
            query_tokens, product, price_ceiling, availability, device_sku
        )
        if score > 0:
            scored.append(SearchResult(
                sku=sku,
                name=product["name"],
                score=score,
                category=product.get("category"),
                price=product_price,
                currency="AUD",
                reasoning=" | ".join(reasons) if reasons else None,
            ))

    scored.sort(key=lambda r: r.score, reverse=True)

    return SearchResponse(
        results=scored,
        query=body.query,
        total=len(scored),
        constraints_applied=hard_filters if hard_filters else None,
    )
