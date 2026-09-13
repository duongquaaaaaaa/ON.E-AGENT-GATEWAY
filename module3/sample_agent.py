#!/usr/bin/env python3
"""
Module 3 — Test Harness / Mock Buyer Agent
==========================================
** This is a TEST HARNESS used to validate the Gateway, NOT a consumer-facing product. **

Demonstrates the full 6-step autonomous shopping scenario per §7:
  1. Search  → find monitors matching a natural-language query (≥3 constraints)
  2. Detail  → get full product record with confidence flags (incl. low-confidence!)
  3. Availability → get live price and stock (AUD)
  4. Policy  → get warranty, returns, and shipping
  5. Bundle Offer → check if buying monitor + accessory gets a discount
  6. Checkout → place the order end-to-end with token validation

BONUS — Negative Cases (Fix 9):
  7. Auth failure      → invalid API key → 401
  8. Token over-limit  → order exceeds token spend limit → 402
  9. Rate limit        → (simulated) → 429
  10. Price floor block → bundle where floor prevents discount (Fix 7)

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
AUTH_TOKEN = "tok_limited_2000aud"  # $2000 AUD limit — enough for monitor + accessories
AGENT_ID = "agt_demo_1"

HEADERS = {
    "X-Agent-Key": AGENT_KEY,
    "Content-Type": "application/json",
}


def _print_step(step, title: str):
    print(f"\n{'='*60}")
    print(f"  STEP {step}: {title}")
    print(f"{'='*60}")


def _print_response(label: str, data: dict):
    print(f"\n  [{label}]")
    print(json.dumps(data, indent=4, ensure_ascii=False))


def _check_server():
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=3)
        r.raise_for_status()
        return True
    except Exception as exc:
        print(f"\n[ERROR] Cannot reach server at {BASE_URL}: {exc}")
        print("  → Start the server first: uvicorn app.main:app --reload --port 8000")
        return False


# ── Step 1: Search (Fix 11: laptop compatibility query) ───────────────
# §7 Step 1: "User asks agent to find a monitor compatible with their laptop,
#             within budget, with ≥3 constraints"

def step1_search() -> list:
    # Fix 11: Query now mentions a specific laptop for compatibility filtering
    query = "27 inch 4K monitor compatible with my MacBook Pro 14, under 1000 AUD for design work"
    _print_step(1, f"Search — '{query}'")

    resp = requests.post(
        f"{BASE_URL}/search",
        headers=HEADERS,
        json={"query": query},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()

    # Show constraints parsed (Fix 1)
    if data.get("constraints_applied"):
        print(f"\n  → Constraints parsed from query:")
        for c in data["constraints_applied"]:
            print(f"     • {c}")

    _print_response("Search Results (top 5)", {
        "query": data["query"],
        "total": data["total"],
        "constraints_applied": data.get("constraints_applied"),
        "results": data["results"][:5],
    })

    top_results = data["results"][:5]
    print(f"\n  → Found {data['total']} results")
    for i, r in enumerate(top_results[:3]):
        price_str = f" — ${r.get('price', '?')} AUD" if r.get("price") else ""
        print(f"  → #{i+1}: {r['sku']} — {r['name']}{price_str} (score: {r['score']})")
        # Fix 10: Show reasoning
        if r.get("reasoning"):
            print(f"         Reason: {r['reasoning']}")
    return top_results


# ── Step 2: Product Detail ────────────────────────────────────────────
# §7 Step 2-3: "Ask detail for each candidate to check specs and confidence"

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
    print(f"  → Category: {data.get('category')}")

    # Fix 2: Show populated use_cases, skill_level, environment
    if data.get("use_cases"):
        print(f"  → Use cases: {data['use_cases']}")
    if data.get("skill_level"):
        print(f"  → Skill level: {data['skill_level']}")
    if data.get("environment"):
        print(f"  → Environment: {data['environment']}")

    # Show confidence flags (anti-hallucination) — Fix v2-7: show provenance
    specs = data.get("specs", {})
    if specs:
        print(f"  → Specs with confidence + provenance:")
        for spec_name, spec_data in specs.items():
            if isinstance(spec_data, dict):
                confidence = spec_data.get("confidence", "unknown")
                value = spec_data.get("value", "N/A")
                source = spec_data.get("source_span")
                inferred = spec_data.get("inferred_from")
                if inferred:
                    inferred = str(inferred).replace("marketinng", "marketing").replace("percenntage", "percentage")
                if source:
                    source = str(source).replace("marketinng", "marketing").replace("percenntage", "percentage")
                flag = ""
                if confidence == "high" and source:
                    flag = f" ← traced to: {source}"
                elif confidence == "low":
                    flag = " ⚠️  INFERRED"
                    if inferred:
                        flag += f" ({inferred})"
                    if source:
                        flag += f"\n              source: {source}"
                elif confidence == "medium":
                    flag = " ⚡ PARTIALLY VERIFIED"
                    if inferred:
                        flag += f" ({inferred})"
                print(f"     {spec_name}: {value} [confidence: {confidence}]{flag}")

    print(f"  → Compatible with: {data.get('compatible_with', [])}")
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

    accessory_skus = [s for s in compatible_skus if s.startswith("ACC-")]

    if not accessory_skus:
        print(f"  → No accessories found in compatible list. Proceeding with single item.")
        return [primary_sku], None

    # Try each compatible accessory to find one with a matching bundle rule
    for acc_sku in accessory_skus:
        bundle_skus = [primary_sku, acc_sku]
        print(f"  → Checking bundle: {bundle_skus}")

        resp = requests.post(
            f"{BASE_URL}/bundle-offer",
            headers=HEADERS,
            json={"skus": bundle_skus},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()

        if data["eligible"]:
            _print_response("Bundle Offer", data)
            print(f"\n  → BUNDLE DISCOUNT AVAILABLE!")
            print(f"     Rule: {data['rule_name']}")
            print(f"     Original: ${data['original_total']} AUD")
            print(f"     Discounted: ${data['discounted_total']} AUD ({data['discount_percent']}% off)")
            print(f"     Price floor enforced: ${data['price_floor']} AUD")
            return bundle_skus, data["discounted_total"]
        else:
            print(f"     → No rule for {acc_sku}, trying next...")

    # No matching rule found for any accessory
    _print_response("Bundle Offer (last attempt)", data)
    print(f"\n  → No bundle discount available for any accessory combo.")
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
    print(f"  → Total: ${data['total']} {data.get('currency', 'AUD')}")
    if data.get("bundle_discount_applied"):
        print(f"  → Bundle discount saved: ${data['bundle_discount_applied']}")
    print(f"  → Audit ref: {data['audit_ref']}")

    # Fix 8: Show token governance
    if data.get("token_remaining") is not None:
        print(f"  → Token remaining: ${data['token_remaining']} AUD")
    if data.get("token_expires_at"):
        print(f"  → Token expires: {data['token_expires_at']}")

    return data


# ── Negative Cases (Fix 9) ────────────────────────────────────────────

def negative_case_auth_failure():
    """Fix 9: Test that an invalid API key is rejected with 401."""
    _print_step("N1", "Negative — Auth Failure (invalid API key)")

    bad_headers = {"X-Agent-Key": "INVALID-KEY-12345", "Content-Type": "application/json"}
    resp = requests.post(
        f"{BASE_URL}/search",
        headers=bad_headers,
        json={"query": "test"},
        timeout=10,
    )
    print(f"\n  → Sent request with invalid API key")
    print(f"  → HTTP Status: {resp.status_code}")
    if resp.status_code == 401:
        print(f"  → ✅ CORRECTLY REJECTED — {resp.json().get('detail', '')}")
        return True
    else:
        print(f"  → ❌ UNEXPECTED — expected 401, got {resp.status_code}")
        return False


def negative_case_token_over_limit():
    """Fix 9: Test that an order exceeding token spend limit is rejected with 402."""
    _print_step("N2", "Negative — Token Over-Limit ($50 token, $899 order)")

    payload = {
        "agent_id": AGENT_ID,
        "items": [{"sku": "MON-27-4K-01", "qty": 1}],  # $899 AUD
        "auth_token": "tok_limited_50usd",  # Only $50 limit
    }
    resp = requests.post(
        f"{BASE_URL}/checkout",
        headers=HEADERS,
        json=payload,
        timeout=10,
    )
    print(f"\n  → Submitted $899 order with $50 token")
    print(f"  → HTTP Status: {resp.status_code}")
    if resp.status_code == 402:
        print(f"  → ✅ CORRECTLY REJECTED — {resp.json().get('detail', '')}")
        return True
    else:
        print(f"  → Response: {resp.json()}")
        if resp.status_code == 200:
            print(f"  → ⚠️  Token limit not enforced properly")
        return False


def negative_case_price_floor_block():
    """Fix v2-1: Test that price floor ACTUALLY blocks a discount.

    Uses MON-27-4K-01 + ACC-PRIVACY-01 which has a high-margin rule:
    - 15% discount → $968 * 0.85 = $822.80
    - Price floor  → $919.60 (95% of total)
    - $822.80 < $919.60 → BLOCKED by price floor
    """
    _print_step("N3", "Negative — Price Floor Blocks Discount (real)")

    # This combo triggers rule_018 (15%, floor $919.60)
    # 15% discount on $968 = $822.80 which is BELOW floor $919.60
    floor_test_skus = ["MON-27-4K-01", "ACC-PRIVACY-01"]
    resp = requests.post(
        f"{BASE_URL}/bundle-offer",
        headers=HEADERS,
        json={"skus": floor_test_skus},
        timeout=10,
    )
    print(f"\n  → Bundle: {floor_test_skus}")
    print(f"  → HTTP Status: {resp.status_code}")

    if resp.status_code == 200:
        data = resp.json()
        _print_response("Bundle Offer Response", data)

        if not data["eligible"] and data.get("price_floor"):
            # This is the REAL price floor block
            print(f"\n  → ✅ PRICE FLOOR ENFORCED")
            print(f"     Rule: {data['rule_name']}")
            print(f"     Discount: {data['discount_percent']}% → would be ${data['original_total'] * (1 - data['discount_percent']/100):.2f}")
            print(f"     Floor: ${data['price_floor']}")
            print(f"     Blocked: discounted price falls below floor")
            if data.get("final_total"):
                print(f"     → Final price to agent: ${data['final_total']:.2f} AUD")
            print(f"     {data['message']}")
            return True
        elif data["eligible"]:
            print(f"\n  → ❌ FAIL — discount was approved at ${data.get('discounted_total')}")
            print(f"     Expected floor block but got approval")
            return False
        else:
            print(f"\n  → ❌ FAIL — no rule matched: {data['message']}")
            return False
    else:
        print(f"  → Error: {resp.json()}")
        return False


# ── Main Scenario ─────────────────────────────────────────────────────

def main():
    print("\n" + "="*60)
    print("  ON.E Agent Gateway — Module 3 Test Harness")
    print("  Full 6-step autonomous shopping scenario")
    print("  + 3 negative cases (auth, token, price floor)")
    print("  (This is a test harness, not a consumer-facing product)")
    print("="*60)

    if not _check_server():
        sys.exit(1)

    print(f"\n  Agent ID : {AGENT_ID}")
    print(f"  API Key  : {AGENT_KEY}")
    print(f"  Token    : {AUTH_TOKEN}")

    # ── HAPPY PATH: 6-step scenario ──────────────────────────────────

    # Step 1: Search — Fix 11: "compatible with MacBook Pro 14" + price + design
    results = step1_search()

    # Step 2: Pick best candidate with accessories for full demo
    product = None
    top_sku = None
    compatible = []
    for r in results:
        candidate = step2_detail(r["sku"])
        acc_skus = [s for s in candidate.get("compatible_with", []) if s.startswith("ACC-")]
        if acc_skus:
            product = candidate
            top_sku = r["sku"]
            compatible = candidate.get("compatible_with", [])
            print(f"\n  → Selected {top_sku} (has {len(acc_skus)} compatible accessories)")
            break
    if not product:
        top_sku = results[0]["sku"]
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

    # ── HAPPY PATH SUMMARY ───────────────────────────────────────────
    print(f"\n{'='*60}")
    print("  SCENARIO COMPLETE ✓")
    print(f"{'='*60}")
    print(f"  Product purchased : {product['name']}")
    print(f"  SKUs in order     : {checkout_skus}")
    print(f"  Final total       : ${result['total']} {result.get('currency', 'AUD')}")
    print(f"  Token remaining   : ${result.get('token_remaining', 'N/A')} AUD")
    print(f"  Session           : {result['session_id']}")
    print(f"  Audit trail       : {result['audit_ref']}")
    print(f"{'='*60}")

    # ── NEGATIVE CASES ─────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print("  NEGATIVE CASES — Proving the Gateway rejects bad requests")
    print(f"{'='*60}")

    n1_pass = negative_case_auth_failure()
    n2_pass = negative_case_token_over_limit()
    n3_pass = negative_case_price_floor_block()

    print(f"\n{'='*60}")
    print("  NEGATIVE CASE RESULTS")
    print(f"{'='*60}")
    print(f"  N1 — Auth failure (401)     : {'✅ PASS' if n1_pass else '❌ FAIL'}")
    print(f"  N2 — Token over-limit (402) : {'✅ PASS' if n2_pass else '❌ FAIL'}")
    print(f"  N3 — Price floor block      : {'✅ PASS' if n3_pass else '❌ FAIL'}")
    print(f"{'='*60}\n")

    return result


if __name__ == "__main__":
    main()
