"""
Module 3 — /search router
POST /search — semantic search over the product catalog.
Uses TF-IDF-style keyword matching as a lightweight semantic proxy
(no vector DB required at this stage; swap retrieve.py when Module 1 is live).
"""

from __future__ import annotations
import json
import re
from pathlib import Path
from typing import List

from fastapi import APIRouter, Request

from app.models import SearchRequest, SearchResponse, SearchResult

router = APIRouter(tags=["Search"])

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"


def _load_catalog() -> List[dict]:
    return json.loads((DATA_DIR / "catalog.json").read_text(encoding="utf-8"))


def _tokenize(text: str) -> List[str]:
    return re.findall(r"\b\w+\b", text.lower())


def _score(query_tokens: List[str], product: dict) -> float:
    """
    Lightweight similarity: count token overlap across searchable fields.
    Returns a normalized score in [0, 1].
    """
    searchable = " ".join([
        product.get("name", ""),
        product.get("brand", ""),
        product.get("category", ""),
        product.get("description", ""),
        " ".join(product.get("use_cases", [])),
        product.get("skill_level", ""),
        product.get("environment", ""),
    ]).lower()

    product_tokens = set(_tokenize(searchable))
    hits = sum(1 for t in query_tokens if t in product_tokens)

    if not query_tokens:
        return 0.0

    # Bonus: price filter hint ("under $X")
    price_bonus = 0.0
    catalog_path = DATA_DIR / "availability.json"
    availability = json.loads(catalog_path.read_text(encoding="utf-8"))
    avail = availability.get(product["sku"], {})
    product_price = avail.get("price", float("inf"))

    query_str = " ".join(query_tokens)
    price_match = re.search(r"under[\s\$]*(\d+)", query_str)
    if price_match:
        ceiling = float(price_match.group(1))
        if product_price <= ceiling:
            price_bonus = 0.15

    raw_score = hits / len(query_tokens)
    return min(round(raw_score + price_bonus, 4), 1.0)


@router.post("/search", response_model=SearchResponse, summary="Semantic product search")
async def search_products(body: SearchRequest, request: Request):
    """
    Semantic search over the product catalog.

    Accepts a natural-language query and returns ranked product results.
    Swap the scoring function with a real vector DB lookup when Module 1 is connected.
    """
    catalog = _load_catalog()
    query_tokens = _tokenize(body.query)

    scored = []
    for product in catalog:
        score = _score(query_tokens, product)
        if score > 0:
            scored.append(SearchResult(
                sku=product["sku"],
                name=product["name"],
                score=score,
                category=product.get("category"),
            ))

    scored.sort(key=lambda r: r.score, reverse=True)

    return SearchResponse(
        results=scored,
        query=body.query,
        total=len(scored),
    )
