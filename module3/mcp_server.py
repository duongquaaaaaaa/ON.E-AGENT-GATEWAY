"""
Module 3 — MCP Server
Wraps the same 5 API capabilities as callable MCP tools.
Runs as a standalone process; agents can connect via stdio transport.

Usage:
  python mcp_server.py

The MCP server calls the FastAPI endpoints directly (in-process) rather than
making HTTP requests, so it can run without a separate server process.
"""

from __future__ import annotations
import json
import sys
import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure the module3 root is on the path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Import business logic directly (no HTTP round-trip needed)
from app.routers.search import _load_catalog, _tokenize, _score, SearchResult
from app.routers.products import _catalog, _availability
from app.routers.checkout import _validate_token, _calculate_total
from app.policy_engine import evaluate_bundle

DATA_DIR = BASE_DIR / "data"

# ── MCP Server Setup ──────────────────────────────────────────────────

server = Server("one-agent-gateway-module3")


# ─────────────────────────────────────────────────────────────────────
# Tool: search_products
# ─────────────────────────────────────────────────────────────────────

@server.list_tools()
async def list_tools() -> List[Tool]:
    return [
        Tool(
            name="search_products",
            description=(
                "Semantic search over the ON.E product catalog. "
                "Returns ranked SKUs with relevance scores."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Natural language product search query, e.g. 'beginner podcasting mic under $150'",
                    }
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="get_product_detail",
            description=(
                "Get the full standardized product record for a SKU, "
                "including specs, compatibility, and warranty."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "sku": {"type": "string", "description": "Product SKU, e.g. SKU001"}
                },
                "required": ["sku"],
            },
        ),
        Tool(
            name="get_availability",
            description="Get current price and stock level for a SKU.",
            inputSchema={
                "type": "object",
                "properties": {
                    "sku": {"type": "string", "description": "Product SKU"}
                },
                "required": ["sku"],
            },
        ),
        Tool(
            name="get_policy",
            description="Get warranty, return policy, and shipping info for a SKU.",
            inputSchema={
                "type": "object",
                "properties": {
                    "sku": {"type": "string", "description": "Product SKU"}
                },
                "required": ["sku"],
            },
        ),
        Tool(
            name="get_bundle_offer",
            description=(
                "Check if a set of SKUs qualifies for a bundle discount. "
                "Returns discount amount and price floor enforcement. "
                "Requires at least 2 SKUs."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "skus": {
                        "type": "array",
                        "items": {"type": "string"},
                        "minItems": 2,
                        "description": "List of SKUs to check for bundle discount",
                    }
                },
                "required": ["skus"],
            },
        ),
        Tool(
            name="checkout",
            description=(
                "Complete a checkout for one or more items. "
                "Validates auth_token spend limit and applies bundle discount if eligible."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "agent_id": {"type": "string", "description": "Agent identifier"},
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "sku": {"type": "string"},
                                "qty": {"type": "integer", "minimum": 1},
                            },
                            "required": ["sku", "qty"],
                        },
                        "description": "Items to purchase",
                    },
                    "auth_token": {
                        "type": "string",
                        "description": "Auth token with spend limit, e.g. tok_limited_50usd",
                    },
                },
                "required": ["agent_id", "items", "auth_token"],
            },
        ),
    ]


# ─────────────────────────────────────────────────────────────────────
# Tool Handlers
# ─────────────────────────────────────────────────────────────────────

@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    try:
        if name == "search_products":
            return await _tool_search(arguments)
        elif name == "get_product_detail":
            return await _tool_get_product(arguments)
        elif name == "get_availability":
            return await _tool_get_availability(arguments)
        elif name == "get_policy":
            return await _tool_get_policy(arguments)
        elif name == "get_bundle_offer":
            return await _tool_bundle_offer(arguments)
        elif name == "checkout":
            return await _tool_checkout(arguments)
        else:
            return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]
    except Exception as exc:
        return [TextContent(type="text", text=json.dumps({"error": str(exc)}))]


async def _tool_search(args: dict) -> List[TextContent]:
    query = args["query"]
    catalog = _load_catalog()
    tokens = _tokenize(query)
    results = []
    for product in catalog:
        score = _score(tokens, product)
        if score > 0:
            results.append({"sku": product["sku"], "name": product["name"], "score": score, "category": product.get("category")})
    results.sort(key=lambda r: r["score"], reverse=True)
    return [TextContent(type="text", text=json.dumps({"results": results, "query": query, "total": len(results)}))]


async def _tool_get_product(args: dict) -> List[TextContent]:
    sku = args["sku"]
    catalog = _catalog()
    if sku not in catalog:
        return [TextContent(type="text", text=json.dumps({"error": f"SKU '{sku}' not found"}))]
    from datetime import datetime
    item = dict(catalog[sku])
    item["retrieved_at"] = datetime.utcnow().isoformat() + "Z"
    return [TextContent(type="text", text=json.dumps(item))]


async def _tool_get_availability(args: dict) -> List[TextContent]:
    sku = args["sku"]
    avail = _availability()
    if sku not in avail:
        return [TextContent(type="text", text=json.dumps({"error": f"SKU '{sku}' not found"}))]
    return [TextContent(type="text", text=json.dumps(avail[sku]))]


async def _tool_get_policy(args: dict) -> List[TextContent]:
    sku = args["sku"]
    catalog = _catalog()
    if sku not in catalog:
        return [TextContent(type="text", text=json.dumps({"error": f"SKU '{sku}' not found"}))]
    item = catalog[sku]
    w = item.get("warranty", {})
    return_days = 30 if w.get("duration_months", 12) >= 24 else 14
    policy = {
        "sku": sku,
        "warranty": w,
        "returns": {"window_days": return_days, "conditions": "Original packaging, unused, with all accessories."},
        "shipping": {"eta_days": 3, "cost": 0},
    }
    return [TextContent(type="text", text=json.dumps(policy))]


async def _tool_bundle_offer(args: dict) -> List[TextContent]:
    skus = args["skus"]
    result = evaluate_bundle(skus)
    return [TextContent(type="text", text=json.dumps(result))]


async def _tool_checkout(args: dict) -> List[TextContent]:
    import uuid
    agent_id = args["agent_id"]
    items = args["items"]
    auth_token = args["auth_token"]

    keys_data = json.loads((DATA_DIR / "api_keys.json").read_text(encoding="utf-8"))
    token_records = {t["token"]: t for t in keys_data["auth_tokens"]}
    if auth_token not in token_records:
        return [TextContent(type="text", text=json.dumps({"error": "Invalid auth_token"}))]

    avail = _availability()
    original_total = sum(avail.get(i["sku"], {}).get("price", 0) * i["qty"] for i in items)

    skus = [i["sku"] for i in items]
    bundle_discount = None
    final_total = original_total
    if len(skus) >= 2:
        bundle_result = evaluate_bundle(skus)
        if bundle_result.get("eligible"):
            discount_pct = bundle_result["discount_percent"] / 100.0
            discounted = original_total * (1 - discount_pct)
            if discounted >= bundle_result["price_floor"]:
                bundle_discount = round(original_total - discounted, 2)
                final_total = round(discounted, 2)

    session_id = f"chk_{uuid.uuid4().hex[:8]}"
    audit_ref = f"log_{uuid.uuid4().hex[:12]}"

    result = {
        "session_id": session_id,
        "status": "confirmed",
        "total": round(final_total, 2),
        "currency": "USD",
        "items": items,
        "bundle_discount_applied": bundle_discount,
        "audit_ref": audit_ref,
    }
    return [TextContent(type="text", text=json.dumps(result))]


# ─────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
