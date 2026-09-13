"""
AEO Scoring Engine — Module 2
==============================
Scores each product across 5 axes of agent-readiness using data adapted
from Module 1 (catalog_standardized.json via module1_loader.py).

Axes:
  1. Completeness        — % of required fields that are filled
  2. Machine-Readability — structured spec ratio + JSON-LD signal
  3. Retrievability      — keyword/semantic match against sample buyer queries
  4. Answerability       — % of buyer FAQs answerable from product data
  5. Transactability     — checklist: price, stock, SKU, warranty present
"""

import json
import os
from typing import Any

from module1_loader import load_module1_products, get_data_source_info

# ─────────────────────────────────────────────────────────────────────────────
# Paths
# ─────────────────────────────────────────────────────────────────────────────

DATA_DIR   = os.path.join(os.path.dirname(__file__), "data")
SCORES_FILE = os.path.join(DATA_DIR, "scores.json")

# ─────────────────────────────────────────────────────────────────────────────
# Domain constants  (updated for monitor / display product domain from Module 1)
# ─────────────────────────────────────────────────────────────────────────────

# Fields that a well-prepared product record should have
REQUIRED_FIELDS = [
    "name",        # product title
    "brand",       # manufacturer
    "category",    # product category
    "sku",         # unique identifier
    "price",       # sale price
    "currency",    # price currency
    "stock",       # inventory count
    "description", # rich text (agent_text from Module 1)
    "specs",       # structured specification dict
    "tags",        # retrieval tags (derived by adapter)
    "policy",      # warranty / return policy
    "agent_text",  # Module 1 rich-text representation
]

# Fields required for a product to be transactable by an agent
TRANSACTABILITY_FIELDS = [
    "price",           # must have a price
    "stock",           # must know stock level
    "sku",             # must have a machine-readable ID
    "warranty_months", # policy completeness signal (Module 1 provides this)
]

# Sample buyer-style queries used to simulate semantic retrieval
# Updated for the monitor / display domain matching Module 1 catalog
SAMPLE_QUERIES = [
    "4K monitor for graphic design",
    "gaming monitor with high refresh rate 144Hz or 165Hz",
    "office monitor full HD budget",
    "large 32 inch 4K display",
    "professional monitor with USB-C and wide color gamut",
    "IPS panel monitor for color accuracy",
    "curved ultrawide monitor",
    "monitor with multiple ports HDMI DisplayPort",
    "QHD monitor for video editing",
    "monitor long warranty professional use",
]

# FAQ-style buyer questions mapped to relevant spec keys
# Updated for monitor domain
SAMPLE_FAQS = [
    ("What is the screen size?",       ["screen_size", "size", "diagonal"]),
    ("What is the panel type?",        ["panel_type", "panel", "display_type"]),
    ("What is the resolution?",        ["resolution", "display_resolution"]),
    ("What is the refresh rate?",      ["refresh_rate", "response_time", "hz"]),
    ("What ports are available?",      ["ports", "connectivity", "inputs"]),
    ("What is the warranty?",          ["warranty_months", "warranty"]),
    ("What is the price?",             ["price"]),
]

# Color tier thresholds
TIER_THRESHOLDS = {"green": 80, "yellow": 50}

# Axis weights (must sum to 1.0)
AXIS_WEIGHTS = {
    "completeness":        0.25,
    "machine_readability": 0.20,
    "retrievability":      0.20,
    "answerability":       0.20,
    "transactability":     0.15,
}

# Improvement suggestions per axis
AXIS_SUGGESTIONS = {
    "completeness": (
        "Fill in missing required fields: ensure brand, SKU, policy (warranty/return), "
        "and a rich agent_text description are all present."
    ),
    "machine_readability": (
        "Add more structured spec entries (panel type, resolution, refresh rate, ports) "
        "with high-confidence extraction. Avoid free-text-only specs."
    ),
    "retrievability": (
        "Enrich tags with use-case keywords (e.g. 'gaming', 'graphic_design', '4K'), "
        "improve category naming, and ensure agent_text covers key buyer search terms."
    ),
    "answerability": (
        "Add structured spec fields for: screen size, panel type, resolution, refresh rate, "
        "available ports, and warranty duration so agents can answer buyer FAQs directly."
    ),
    "transactability": (
        "Ensure price, stock quantity, SKU, and warranty information are all present "
        "and machine-readable so agents can complete purchase transactions."
    ),
}


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _has_value(val: Any) -> bool:
    """Return True if the value is meaningfully present (not None/empty)."""
    if val is None:
        return False
    if isinstance(val, str) and val.strip() == "":
        return False
    if isinstance(val, (list, dict)) and len(val) == 0:
        return False
    return True


def _color_tier(score: float) -> str:
    if score >= TIER_THRESHOLDS["green"]:
        return "green"
    elif score >= TIER_THRESHOLDS["yellow"]:
        return "yellow"
    return "red"


def _specs_to_text(specs: dict | list) -> str:
    """Convert specs (dict or list) to a flat text string for corpus building."""
    if isinstance(specs, dict):
        parts = []
        for v in specs.values():
            if isinstance(v, list):
                parts.append(" ".join(str(i) for i in v))
            else:
                parts.append(str(v))
        return " ".join(parts)
    if isinstance(specs, list):
        parts = []
        for s in specs:
            if isinstance(s, dict):
                v = s.get("value", "")
                parts.append(" ".join(str(i) for i in v) if isinstance(v, list) else str(v))
        return " ".join(parts)
    return ""


# ─────────────────────────────────────────────────────────────────────────────
# Axis 1 — Completeness Score
# ─────────────────────────────────────────────────────────────────────────────

def completeness_score(product: dict) -> float:
    """% of REQUIRED_FIELDS that are meaningfully filled."""
    filled = sum(1 for f in REQUIRED_FIELDS if _has_value(product.get(f)))
    return round((filled / len(REQUIRED_FIELDS)) * 100, 1)


# ─────────────────────────────────────────────────────────────────────────────
# Axis 2 — Machine-Readability Score
# ─────────────────────────────────────────────────────────────────────────────

def machine_readability_score(product: dict) -> float:
    """
    50 pts: JSON-LD / structured-specs signal (jsonld_valid flag from adapter).
    50 pts: ratio of high/medium-confidence specs to total specs.
    """
    # jsonld_valid is True when ≥1 high-confidence structured spec exists (set by adapter)
    jsonld_score = 50.0 if product.get("jsonld_valid") else 0.0

    total     = product.get("total_spec_count", 0)
    structured = product.get("structured_spec_count", 0)

    if total > 0:
        spec_score = (structured / total) * 50.0
    else:
        spec_score = 0.0  # No specs at all → zero

    return round(jsonld_score + spec_score, 1)


# ─────────────────────────────────────────────────────────────────────────────
# Axis 3 — Retrievability Score
# ─────────────────────────────────────────────────────────────────────────────

def _normalize_text(text: str) -> str:
    """
    Normalize text for keyword matching:
    - Lowercase
    - Replace underscores with spaces (graphic_design → graphic design)
    - Strip punctuation characters that cluster tokens (periods, colons, quotes)
    """
    import re
    text = text.lower()
    text = text.replace("_", " ")
    text = re.sub(r'[.,:;\"\'\(\)\[\]\/\\]', " ", text)
    return text


def _query_matches_product(query: str, product: dict) -> bool:
    """
    Simulate vector search via keyword overlap.
    Uses agent_text (Module 1's rich representation) as the primary corpus,
    supplemented by name, category, tags, and spec values.

    Normalization: underscores split to spaces, punctuation stripped — so
    English technical terms embedded in Vietnamese text (e.g. 'graphic_design',
    '4K', 'IPS', 'studio') are tokenized correctly against English queries.

    In production: replace with cosine similarity on real embeddings.
    """
    query_tokens = set(_normalize_text(query).split())

    corpus_parts = [
        product.get("agent_text", ""),      # Module 1 rich text — primary signal
        product.get("name", ""),
        product.get("description", ""),     # Same as agent_text after adapter
        product.get("category", ""),
        " ".join(str(t) for t in product.get("tags", [])),
        _specs_to_text(product.get("specs", {})),
    ]

    raw_corpus = " ".join(corpus_parts)
    corpus = _normalize_text(raw_corpus)
    corpus_tokens = set(corpus.split())

    overlap = query_tokens & corpus_tokens
    stop_words = {"a", "an", "the", "for", "with", "and", "or", "is", "of", "in", "to",
                  "by", "at", "on", "from", "up", "that", "it", "its", "this", "be"}
    meaningful_overlap = overlap - stop_words
    return len(meaningful_overlap) >= 2


def retrievability_score(product: dict) -> float:
    """
    Run SAMPLE_QUERIES against the product; % that match.
    Simulated via keyword overlap (production: vector DB top-K).
    """
    hits = sum(1 for q in SAMPLE_QUERIES if _query_matches_product(q, product))
    return round((hits / len(SAMPLE_QUERIES)) * 100, 1)


# ─────────────────────────────────────────────────────────────────────────────
# Axis 4 — Answerability Score
# ─────────────────────────────────────────────────────────────────────────────

def answerability_score(product: dict) -> float:
    """
    Run SAMPLE_FAQS against product data; % of questions answerable.
    Checks specs dict, top-level fields, and policy sub-fields.
    """
    answered = 0
    specs: dict = product.get("specs", {})

    for _question, relevant_keys in SAMPLE_FAQS:
        found = False

        # 1) Check in structured specs dict
        if any(k in specs for k in relevant_keys):
            found = True

        # 2) Price is at top level
        elif "price" in relevant_keys and _has_value(product.get("price")):
            found = True

        # 3) Warranty is at top level (set by adapter) or in policy
        elif any(k in ("warranty_months", "warranty") for k in relevant_keys):
            if _has_value(product.get("warranty_months")) or (
                isinstance(product.get("policy"), dict)
                and product["policy"].get("warranty_months")
            ):
                found = True

        if found:
            answered += 1

    return round((answered / len(SAMPLE_FAQS)) * 100, 1)


# ─────────────────────────────────────────────────────────────────────────────
# Axis 5 — Transactability Score
# ─────────────────────────────────────────────────────────────────────────────

def transactability_score(product: dict) -> float:
    """
    Checklist: price, stock, SKU, warranty_months all present.
    Module 1 provides warranty info which replaces shipping_fee
    (not available from Module 1) as the 4th transactability signal.
    """
    present = sum(1 for f in TRANSACTABILITY_FIELDS if _has_value(product.get(f)))
    return round((present / len(TRANSACTABILITY_FIELDS)) * 100, 1)


# ─────────────────────────────────────────────────────────────────────────────
# Overall Score + Weakest Axis
# ─────────────────────────────────────────────────────────────────────────────

def compute_overall(scores: dict) -> tuple[float, str]:
    overall = sum(scores[axis] * weight for axis, weight in AXIS_WEIGHTS.items())
    overall = round(overall, 1)
    return overall, _color_tier(overall)


def weakest_axis(scores: dict) -> tuple[str, str]:
    """Return (axis_name, improvement_suggestion) for the lowest-scoring axis."""
    worst = min(scores, key=lambda k: scores[k])
    return worst, AXIS_SUGGESTIONS[worst]


# ─────────────────────────────────────────────────────────────────────────────
# Per-product scoring
# ─────────────────────────────────────────────────────────────────────────────

def score_product(product: dict) -> dict:
    """Score a single product across all 5 axes and compute overall."""
    axes = {
        "completeness":        completeness_score(product),
        "machine_readability": machine_readability_score(product),
        "retrievability":      retrievability_score(product),
        "answerability":       answerability_score(product),
        "transactability":     transactability_score(product),
    }
    overall, tier = compute_overall(axes)
    weak_axis, suggestion = weakest_axis(axes)

    return {
        "product_id":            product["id"],   # = sku from Module 1
        "product_name":          product["name"],
        "axes":                  axes,
        "overall_score":         overall,
        "tier":                  tier,
        "weakest_axis":          weak_axis,
        "improvement_suggestion": suggestion,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Batch scoring
# ─────────────────────────────────────────────────────────────────────────────

def run_batch_scoring() -> list[dict]:
    """Load all products from Module 1, score them, persist to scores.json."""
    products, is_real = load_module1_products()

    results = [score_product(p) for p in products]

    os.makedirs(DATA_DIR, exist_ok=True)
    with open(SCORES_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    source_label = "Module 1 (real)" if is_real else "mock fallback"
    print(f"[Scoring Engine] Scored {len(results)} products from {source_label} -> {SCORES_FILE}")
    return results


def load_scores() -> list[dict]:
    """Load persisted scores; run batch scoring if not yet computed."""
    if not os.path.exists(SCORES_FILE):
        return run_batch_scoring()
    with open(SCORES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def load_all_products() -> list[dict]:
    """Load all adapted products from Module 1 (or mock fallback)."""
    products, _ = load_module1_products()
    return products


# ─────────────────────────────────────────────────────────────────────────────
# Agent Query Simulator
# ─────────────────────────────────────────────────────────────────────────────

def simulate_agent_query(question: str) -> list[dict]:
    """
    Simulate an agent answering a buyer-style question.
    Returns all products ranked by: selected first, then overall_score desc.
    Selection criteria: matches query AND overall_score >= 50 (yellow or green).
    """
    products = load_all_products()
    scores   = load_scores()
    scores_by_id = {s["product_id"]: s for s in scores}

    results = []
    for product in products:
        pid        = product["id"]
        score_data = scores_by_id.get(pid, {})
        matched    = _query_matches_product(question, product)
        overall    = score_data.get("overall_score", 0)
        tier       = score_data.get("tier", "red")

        # Agent selects: must match query AND score >= 50
        selected = matched and overall >= 50

        if matched:
            if selected:
                reason = (
                    f"Matched query with {overall:.0f}/100 AEO score (tier: {tier}). "
                    "Strong agent-readability."
                )
            else:
                reason = (
                    f"Matched query but AEO score is {overall:.0f}/100 (tier: {tier}). "
                    f"Excluded: {score_data.get('improvement_suggestion', 'Improve data completeness.')}"
                )
        else:
            reason = "Did not match query keywords."

        results.append({
            "product_id":    pid,
            "product_name":  product["name"],
            "matched_query": matched,
            "selected":      selected,
            "overall_score": overall,
            "tier":          tier,
            "reason":        reason,
        })

    # Sort: selected first, then by score descending
    results.sort(key=lambda x: (-int(x["selected"]), -x["overall_score"]))
    return results


if __name__ == "__main__":
    info = get_data_source_info()
    print(f"[Scoring Engine] Data source: {info['source']} -> {info['path']}")
    run_batch_scoring()
    print("Batch scoring complete.")
