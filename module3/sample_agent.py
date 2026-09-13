#!/usr/bin/env python3
"""
Module 3 — Sample Agent Script
Demonstrates the full 6-step autonomous shopping scenario:
  1. Search  → find products matching a query
  2. Detail  → get full product record for top result
  3. Availability → get live price and stock
  4. Policy  → get warranty, returns, and shipping
  5. Bundle Offer → check if buying multiple items gets a discount
  6. Checkout → place the order end-to-end

Run with:
  python sample_agent.py

The script talks directly to the FastAPI server. Start it first:
  uvicorn app.main:app --reload --port 8000
"""

from __future__ import annotations
import json
import sys
import time
import requests

# Ensure UTF-8 output on Windows (avoids cp1252 UnicodeEncodeError)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ── Configuration ─────────────────────────────────────────────────────

BASE_URL = "http://localhost:8000"
AGENT_KEY = "agt-key-demo-001"
AUTH_TOKEN = "tok_limited_500usd"  # $500 limit — enough for any demo item
AGENT_ID = "agt_demo_1"

HEADERS = {
    "X-Agent-Key": AGENT_KEY,
    "Content-Type": "application/json",
}


def _print_step(step: int, title: str):
    print(f"\n{'='*60}")
    print(f"  STEP {step}: {title}")
    print(f"{'='*60}")


def _print_response(label: str, data: dict):
    print(f"\n  [{label}]")
    print(json.dumps(data, indent=4))


def _check_server():
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=3)
        r.raise_for_status()
        return True
    except Exception as exc:
        print(f"\n[ERROR] Cannot reach server at {BASE_URL}: {exc}")
        print("  → Start the server first: uvicorn app.main:app --reload --port 8000")
        return False


# ── Step 1: Search ────────────────────────────────────────────────────

def step1_search() -> str:
    _print_step(1, "Search — 'beginner-friendly podcasting mic under $150'")
    query = "beginner-friendly podcasting mic under $150"

    resp = requests.post(
        f"{BASE_URL}/search",
        headers=HEADERS,
        json={"query": query},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    _print_response("Search Results", data)

    top_sku = data["results"][0]["sku"]
    print(f"\n  → Top result: {top_sku} (score: {data['results'][0]['score']})")
    return top_sku


# ── Step 2: Product Detail ────────────────────────────────────────────

def step2_detail(sku: str) -> dict:
    _print_step(2, f"Product Detail — {sku}")

    resp = requests.get(
        f"{BASE_URL}/products/{sku}",
        headers=HEADERS,
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    _print_response("Product Detail", data)

    print(f"\n  → Name: {data['name']}")
    print(f"  → Brand: {data.get('brand')}")
    print(f"  → Compatible with: {data.get('compatible_with')}")
    return data


# ── Step 3: Availability ──────────────────────────────────────────────

def step3_availability(sku: str) -> dict:
    _print_step(3, f"Availability — {sku}")

    resp = requests.get(
        f"{BASE_URL}/products/{sku}/availability",
        headers=HEADERS,
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    _print_response("Availability", data)

    print(f"\n  → Price: ${data['price']} {data['currency']}")
    print(f"  → Stock: {data['stock']} units")
    return data


# ── Step 4: Policy ────────────────────────────────────────────────────

def step4_policy(sku: str) -> dict:
    _print_step(4, f"Policy — {sku}")

    resp = requests.get(
        f"{BASE_URL}/products/{sku}/policy",
        headers=HEADERS,
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    _print_response("Policy", data)

    print(f"\n  → Warranty: {data['warranty']['duration_months']} months")
    print(f"  → Returns: {data['returns']['window_days']}-day window")
    print(f"  → Shipping: ${data['shipping']['cost']} (ETA {data['shipping']['eta_days']} days)")
    return data


# ── Step 5: Bundle Offer ──────────────────────────────────────────────

def step5_bundle(primary_sku: str, compatible_skus: list) -> tuple[list, float]:
    _print_step(5, f"Bundle Offer — {primary_sku} + accessories")

    # Try the first compatible SKU for a bundle
    bundle_skus = [primary_sku] + compatible_skus[:1]
    print(f"  → Checking bundle: {bundle_skus}")

    resp = requests.post(
        f"{BASE_URL}/bundle-offer",
        headers=HEADERS,
        json={"skus": bundle_skus},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    _print_response("Bundle Offer", data)

    if data["eligible"]:
        print(f"\n  → BUNDLE DISCOUNT AVAILABLE!")
        print(f"     Rule: {data['rule_name']}")
        print(f"     Original: ${data['original_total']}")
        print(f"     Discounted: ${data['discounted_total']} ({data['discount_percent']}% off)")
        print(f"     Price floor enforced: ${data['price_floor']}")
        return bundle_skus, data["discounted_total"]
    else:
        print(f"\n  → No bundle discount available. {data['message']}")
        # Fall back to single item
        return [primary_sku], None


# ── Step 6: Checkout ──────────────────────────────────────────────────

def step6_checkout(skus: list) -> dict:
    _print_step(6, f"Checkout — {skus}")

    items = [{"sku": sku, "qty": 1} for sku in skus]
    payload = {
        "agent_id": AGENT_ID,
        "items": items,
        "auth_token": AUTH_TOKEN,
    }
    print(f"\n  → Submitting order: {items}")

    resp = requests.post(
        f"{BASE_URL}/checkout",
        headers=HEADERS,
        json=payload,
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    _print_response("Checkout Response", data)

    print(f"\n  → Session ID: {data['session_id']}")
    print(f"  → Status: {data['status']}")
    print(f"  → Total: ${data['total']} USD")
    if data.get("bundle_discount_applied"):
        print(f"  → Bundle discount saved: ${data['bundle_discount_applied']}")
    print(f"  → Audit ref: {data['audit_ref']}")
    return data


# ── Main Scenario ─────────────────────────────────────────────────────

def main():
    print("\n" + "="*60)
    print("  ON.E Agent Gateway — Module 3 Sample Agent")
    print("  Full 6-step autonomous shopping scenario")
    print("="*60)

    if not _check_server():
        sys.exit(1)

    print(f"\n  Agent ID : {AGENT_ID}")
    print(f"  API Key  : {AGENT_KEY}")
    print(f"  Token    : {AUTH_TOKEN}")

    # Step 1: Search
    top_sku = step1_search()

    # Step 2: Product Detail
    product = step2_detail(top_sku)
    compatible = product.get("compatible_with", [])

    # Step 3: Availability
    avail = step3_availability(top_sku)

    # Step 4: Policy
    policy = step4_policy(top_sku)

    # Step 5: Bundle offer
    checkout_skus, bundle_price = step5_bundle(top_sku, compatible)

    # Step 6: Checkout
    result = step6_checkout(checkout_skus)

    # ── Summary ────────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print("  SCENARIO COMPLETE ✓")
    print(f"{'='*60}")
    print(f"  Product purchased : {product['name']}")
    print(f"  SKUs in order     : {checkout_skus}")
    print(f"  Final total       : ${result['total']} USD")
    print(f"  Session           : {result['session_id']}")
    print(f"  Audit trail       : {result['audit_ref']}")
    print(f"{'='*60}\n")

    return result


if __name__ == "__main__":
    main()
