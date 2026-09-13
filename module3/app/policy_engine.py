"""
Module 3 — Dynamic Policy Engine
Deterministic (non-LLM) bundle/discount rule engine with enforced price floor.

Rules are loaded from data/rules.json. No LLM calls are made here.
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


def _load_rules() -> List[dict]:
    rules_path = DATA_DIR / "rules.json"
    data = json.loads(rules_path.read_text(encoding="utf-8"))
    return [r for r in data["rules"] if r.get("active", True)]


def _load_catalog() -> Dict[str, dict]:
    catalog_path = DATA_DIR / "catalog.json"
    items = json.loads(catalog_path.read_text(encoding="utf-8"))
    return {item["sku"]: item for item in items}


def _load_availability() -> Dict[str, dict]:
    avail_path = DATA_DIR / "availability.json"
    return json.loads(avail_path.read_text(encoding="utf-8"))


def evaluate_bundle(skus: List[str]) -> Dict[str, Any]:
    """
    Check if a list of SKUs qualifies for a bundle discount.

    Returns a result dict with:
      - eligible: bool
      - rule matched (if any)
      - original_total, discounted_total (if eligible)
      - price_floor enforcement

    This is purely deterministic — no LLM involved.
    """
    rules = _load_rules()
    catalog = _load_catalog()
    availability = _load_availability()

    # Get categories for each sku
    sku_categories = {sku: catalog[sku]["category"] for sku in skus if sku in catalog}

    # Calculate original total
    original_total = 0.0
    for sku in skus:
        if sku in availability:
            original_total += availability[sku]["price"]

    best_rule = None
    best_discount = 0.0

    for rule in rules:
        matched = False

        # ── SKU-based matching ─────────────────────────────────────────
        if rule.get("trigger_skus"):
            trigger_set = set(rule["trigger_skus"])
            request_set = set(skus)
            if trigger_set.issubset(request_set):
                matched = True

        # ── Category-based matching ────────────────────────────────────
        elif rule.get("trigger_categories"):
            trigger_cats = set(rule["trigger_categories"])
            request_cats = set(sku_categories.values())
            if trigger_cats.issubset(request_cats):
                matched = True

        if matched and rule["discount_percent"] > best_discount:
            best_discount = rule["discount_percent"]
            best_rule = rule

    if best_rule is None:
        return {
            "eligible": False,
            "rule_id": None,
            "rule_name": None,
            "original_total": round(original_total, 2),
            "discounted_total": None,
            "discount_percent": None,
            "price_floor": None,
            "message": "No bundle discount available for this combination.",
        }

    # ── Apply discount ─────────────────────────────────────────────────
    discount_amount = original_total * (best_rule["discount_percent"] / 100.0)
    discounted_total = original_total - discount_amount
    price_floor = best_rule["price_floor"]

    # HARD CONSTRAINT: never offer below price floor
    if discounted_total < price_floor:
        return {
            "eligible": False,
            "rule_id": best_rule["id"],
            "rule_name": best_rule["name"],
            "original_total": round(original_total, 2),
            "discounted_total": None,
            "discount_percent": best_rule["discount_percent"],
            "price_floor": price_floor,
            "message": (
                f"Bundle rule '{best_rule['name']}' matched but discounted price "
                f"${discounted_total:.2f} would fall below price floor ${price_floor:.2f}. "
                f"Returning list price."
            ),
        }

    return {
        "eligible": True,
        "rule_id": best_rule["id"],
        "rule_name": best_rule["name"],
        "original_total": round(original_total, 2),
        "discounted_total": round(discounted_total, 2),
        "discount_percent": best_rule["discount_percent"],
        "price_floor": price_floor,
        "message": (
            f"Bundle discount applied: {best_rule['discount_percent']}% off "
            f"via rule '{best_rule['name']}'."
        ),
    }
