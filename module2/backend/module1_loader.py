"""
Module 1 Loader — Module 2
===========================
Loads catalog_standardized.json output from Module 1 and adapts it into
Module 2's internal product schema.

Module 1 schema:
  sku, name, brand, category, price, currency, stock
  specs:    list[{name, value, unit, confidence, source_span}]
  policy:   {warranty_months:{value,confidence}, return_days:{value}, exclusions:[]}
  outcomes: {use_cases:{value:[...]}, skill_level:{value}, environment:{value}}
  values:   [{claim, confidence, source_span}]
  agent_text: str

Module 2 internal schema (after adaptation):
  id, sku, name, brand, category, price, currency, stock,
  description (= agent_text), specs (dict), specs_list (original list),
  jsonld_valid, structured_spec_count, total_spec_count,
  tags, policy, warranty_months, return_days, exclusions,
  outcomes, use_cases, skill_level, environment,
  value_claims, agent_text, images, confidence_flags
"""

import json
import logging
import os

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Path resolution
# ─────────────────────────────────────────────────────────────────────────────

_HERE = os.path.dirname(os.path.abspath(__file__))

# Candidates for Module 1 output path (first found wins)
_MODULE1_CANDIDATES = [
    # 1) Explicit env var override
    os.environ.get("MODULE1_OUTPUT_PATH", ""),
    # 2) Standard relative location (module1 sits next to module2 inside ON.E-AGENT-GATEWAY)
    os.path.normpath(
        os.path.join(_HERE, "..", "..", "module1", "output", "catalog_standardized.json")
    ),
]

_MOCK_FALLBACK = os.path.join(_HERE, "data", "products_mock.json")


def _find_module1_path() -> tuple[str, bool]:
    """
    Locate the Module 1 output file.
    Returns (absolute_path, is_real_module1) where is_real_module1 is True
    when using the actual Module 1 catalog, False when falling back to mock.
    """
    for candidate in _MODULE1_CANDIDATES:
        if candidate and os.path.isfile(candidate):
            return os.path.normpath(candidate), True

    logger.warning(
        "[Module1Loader] Module 1 output not found at any candidate path. "
        "Falling back to products_mock.json. "
        "Set MODULE1_OUTPUT_PATH env var to override."
    )
    return _MOCK_FALLBACK, False


# ─────────────────────────────────────────────────────────────────────────────
# Adapter
# ─────────────────────────────────────────────────────────────────────────────

def _extract(obj: dict | None, key: str, default=None):
    """Extract .value from a Module 1 confidence-wrapped field."""
    if not isinstance(obj, dict):
        return default
    field = obj.get(key)
    if isinstance(field, dict):
        return field.get("value", default)
    return field if field is not None else default


def adapt_product(raw: dict) -> dict:
    """
    Convert a single Module 1 product record into Module 2's internal schema.
    Safe for all optional fields — falls back gracefully.
    """
    # ── Specs ──────────────────────────────────────────────────────────────
    specs_list: list[dict] = raw.get("specs", [])

    # Flatten specs list → dict for fast key lookup in scoring
    specs_dict: dict = {}
    for s in specs_list:
        key = s.get("name", "")
        val = s.get("value")
        if key:
            # For list values (e.g. ports), join to string for text search
            specs_dict[key] = val

    total_spec_count = len(specs_list)
    structured_spec_count = sum(
        1 for s in specs_list
        if s.get("confidence") in ("high", "medium") and s.get("value") is not None
    )

    # jsonld_valid proxy: True when there is at least 1 high-confidence structured spec
    jsonld_valid = structured_spec_count > 0

    # ── Policy ─────────────────────────────────────────────────────────────
    policy: dict = raw.get("policy", {})
    warranty_months = _extract(policy, "warranty_months")
    return_days = _extract(policy, "return_days")
    warranty_scope = _extract(policy, "warranty_scope")
    exclusions: list = policy.get("exclusions", [])

    # ── Outcomes ───────────────────────────────────────────────────────────
    outcomes: dict = raw.get("outcomes", {})

    use_cases_raw = _extract(outcomes, "use_cases", [])
    if isinstance(use_cases_raw, str):
        use_cases = [use_cases_raw]
    elif isinstance(use_cases_raw, list):
        use_cases = use_cases_raw
    else:
        use_cases = []

    skill_level = _extract(outcomes, "skill_level", "")
    environment = _extract(outcomes, "environment", "")

    # ── Value claims ───────────────────────────────────────────────────────
    value_claims: list[str] = [
        v.get("claim", "") for v in raw.get("values", []) if isinstance(v, dict)
    ]

    # ── Tags (derived) ─────────────────────────────────────────────────────
    tags = list(filter(None, [
        raw.get("category", ""),
        raw.get("brand", ""),
    ] + use_cases
      + ([environment] if environment else [])
      + ([skill_level] if skill_level else [])
      + value_claims
    ))

    # ── Agent text ─────────────────────────────────────────────────────────
    agent_text: str = raw.get("agent_text", "")

    # ── Confidence flags ───────────────────────────────────────────────────
    spec_conf = structured_spec_count / max(total_spec_count, 1)
    confidence_flags = {
        "name":        1.0,
        "specs":       round(spec_conf, 2),
        "price":       1.0 if raw.get("price") is not None else 0.0,
        "sku":         1.0 if raw.get("sku") else 0.0,
        "policy":      1.0 if policy else 0.0,
        "agent_text":  1.0 if agent_text else 0.0,
    }

    return {
        # ── Core identity
        "id":          raw.get("sku", ""),      # Module 1 uses sku as primary key
        "sku":         raw.get("sku", ""),
        "name":        raw.get("name", ""),
        "brand":       raw.get("brand", ""),
        "category":    raw.get("category", ""),

        # ── Commerce
        "price":       raw.get("price"),
        "currency":    raw.get("currency", "AUD"),
        "stock":       raw.get("stock"),
        "shipping_fee": None,                   # Module 1 does not export this

        # ── Rich text (agent_text used as description for scoring + display)
        "description": agent_text,
        "agent_text":  agent_text,

        # ── Specs — two forms for different consumers
        "specs":       specs_dict,              # dict — for scoring key lookups
        "specs_list":  specs_list,              # list — original for display

        # ── Machine-readability signals
        "jsonld_valid":          jsonld_valid,
        "structured_spec_count": structured_spec_count,
        "total_spec_count":      total_spec_count,

        # ── Retrieval signals
        "tags": tags,

        # ── Policy
        "policy":          policy,
        "warranty_months": warranty_months,
        "warranty_scope":  warranty_scope,
        "return_days":     return_days,
        "exclusions":      exclusions,

        # ── Outcomes / use-cases
        "outcomes":     outcomes,
        "use_cases":    use_cases,
        "skill_level":  skill_level,
        "environment":  environment,

        # ── Value claims
        "value_claims": value_claims,

        # ── Assets (Module 1 does not provide images)
        "images": [],

        # ── Confidence summary
        "confidence_flags": confidence_flags,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def load_module1_products() -> tuple[list[dict], bool]:
    """
    Load products from Module 1 catalog (or mock fallback).

    Returns:
        (products, is_real)  where is_real=True when using live Module 1 data.
    """
    path, is_real = _find_module1_path()

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if is_real:
        # Module 1 wraps products: {"products": [...], "count": N, ...}
        raw_list = data.get("products", []) if isinstance(data, dict) else data
        adapted = [adapt_product(p) for p in raw_list]
        logger.info(
            "[Module1Loader] Loaded %d products from Module 1: %s",
            len(adapted), path,
        )
        return adapted, True
    else:
        # Mock fallback: already in Module 2 format (list)
        products = data if isinstance(data, list) else data.get("products", [])
        logger.info("[Module1Loader] Loaded %d products from mock fallback.", len(products))
        return products, False


def get_data_source_info() -> dict:
    """Return metadata about which data source is being used."""
    path, is_real = _find_module1_path()
    return {
        "source":              "module1_real" if is_real else "mock_fallback",
        "path":                path,
        "is_live_module1_data": is_real,
    }
