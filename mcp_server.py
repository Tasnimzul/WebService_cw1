"""
mcp_server.py
─────────────
MCP (Model Context Protocol) server for the Skincare & Ingredient Analysis API.
Exposes API endpoints as tools that AI assistants (e.g. Claude) can call directly.
 
Run from project root: python mcp_server.py
Requires the FastAPI server to be running at http://127.0.0.1:8000
 
What is MCP?
MCP is an open standard by Anthropic that allows AI models to interact with
external services and APIs through a standardised tool interface. This server
makes the Skincare API callable by any MCP-compatible AI assistant.
"""
 
import asyncio
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
 
# ── CONFIG ────────────────────────────────────────────────────────────────────
API_BASE = "http://127.0.0.1:8000"
 
# ── SERVER SETUP ─────────────────────────────────────────────────────────────
server = Server("skincare-api")
 
 
# ── TOOL DEFINITIONS ─────────────────────────────────────────────────────────
 
@server.list_tools()
async def list_tools() -> list[Tool]:
    """Declare all tools the AI can use."""
    return [
        Tool(
            name="search_products",
            description=(
                "Search and filter skincare products from the Lookfantastic dataset. "
                "Returns a list of products with name, type, and price. "
                "Use this to find products by type (e.g. Serum, Moisturiser) or price range."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "product_type": {
                        "type": "string",
                        "description": "Type of product to filter by. Options: Moisturiser, Serum, Oil, Mist, Balm, Mask, Peel, Eye Care, Cleanser, Toner, Exfoliator, Bath Salts, Body Wash, Bath Oil",
                    },
                    "min_price": {
                        "type": "number",
                        "description": "Minimum price in GBP"
                    },
                    "max_price": {
                        "type": "number",
                        "description": "Maximum price in GBP"
                    }
                },
                "required": []
            }
        ),
 
        Tool(
            name="get_product_details",
            description=(
                "Get full details of a specific skincare product by its ID, "
                "including its complete ingredient list ordered by concentration "
                "(position 1 = highest concentration)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "product_id": {
                        "type": "integer",
                        "description": "The product ID"
                    }
                },
                "required": ["product_id"]
            }
        ),
 
        Tool(
            name="check_safety_score",
            description=(
                "Analyse the safety of a skincare product based on its ingredients. "
                "Returns a safety score from 0-10 (10 = safest) and a breakdown of "
                "high, medium, and low irritation ingredients. "
                "Use this to assess whether a product is suitable for sensitive skin."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "product_id": {
                        "type": "integer",
                        "description": "The product ID to analyse"
                    }
                },
                "required": ["product_id"]
            }
        ),
 
        Tool(
            name="check_product_conflicts",
            description=(
                "Check whether multiple skincare products have conflicting ingredients. "
                "Detects known ingredient conflicts (e.g. Retinol + AHA, Vitamin C + BHA) "
                "and returns severity (high/medium/low). "
                "Use this to check if a skincare routine is safe to use together."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "product_ids": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "List of 2-5 product IDs to check for conflicts",
                        "minItems": 2
                    }
                },
                "required": ["product_ids"]
            }
        ),
 
        Tool(
            name="get_recommendations",
            description=(
                "Get personalised skincare product recommendations based on skin type and concerns. "
                "Matches products containing ingredients recommended for the given skin type. "
                "Uses fuzzy ingredient matching to handle variant ingredient names."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "skin_type": {
                        "type": "string",
                        "description": "Skin type. Options: Normal, Dry, Oily, Combination"
                    },
                    "concern": {
                        "type": "string",
                        "description": "Skin concern e.g. Acne, Dullness, Dark Spots, Wrinkles, Redness, Open Pores"
                    }
                },
                "required": ["skin_type"]
            }
        ),
 
        Tool(
            name="get_known_conflicts",
            description=(
                "List all known ingredient conflict pairs in the database. "
                "Each conflict has a severity level: high, medium, or low. "
                "Use this to educate users about which ingredients should not be combined."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
 
        Tool(
            name="profile_match",
            description=(
                "Check how well a specific product matches a given skin type. "
                "Returns a match score (0-100%) and lists which ingredients in the product "
                "are recommended for that skin type."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "product_id": {
                        "type": "integer",
                        "description": "The product ID to check"
                    },
                    "skin_type": {
                        "type": "string",
                        "description": "Skin type to match against. Options: Normal, Dry, Oily, Combination"
                    }
                },
                "required": ["product_id", "skin_type"]
            }
        ),
 
        Tool(
            name="get_ingredient_frequency",
            description=(
                "Get the most common ingredients across all skincare products in the database. "
                "Returns the top 20 ingredients by frequency with percentage of products they appear in."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
    ]
 
 
# ── TOOL HANDLERS ─────────────────────────────────────────────────────────────
 
@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls from the AI assistant."""
 
    async with httpx.AsyncClient(timeout=30.0) as client:
 
        try:
            if name == "search_products":
                params = {}
                if arguments.get("product_type"):
                    params["product_type"] = arguments["product_type"]
                if arguments.get("min_price") is not None:
                    params["min_price"] = arguments["min_price"]
                if arguments.get("max_price") is not None:
                    params["max_price"] = arguments["max_price"]
 
                res = await client.get(f"{API_BASE}/products/", params=params)
                products = res.json()
 
                if not products:
                    return [TextContent(type="text", text="No products found matching those criteria.")]
 
                # Format nicely for AI consumption
                lines = [f"Found {len(products)} products:\n"]
                for p in products[:20]:  # limit to 20 for readability
                    price = f"£{p['price']:.2f}" if p.get('price') else "Price N/A"
                    lines.append(f"- ID {p['id']}: {p['name']} ({p.get('product_type', 'Unknown')}) — {price}")
 
                if len(products) > 20:
                    lines.append(f"\n...and {len(products) - 20} more products.")
 
                return [TextContent(type="text", text="\n".join(lines))]
 
            elif name == "get_product_details":
                product_id = arguments["product_id"]
                res = await client.get(f"{API_BASE}/products/{product_id}")
 
                if res.status_code == 404:
                    return [TextContent(type="text", text=f"Product ID {product_id} not found.")]
 
                p = res.json()
                ings = sorted(p.get("product_ingredients", []), key=lambda x: x["position"])
 
                lines = [
                    f"Product: {p['name']}",
                    f"Type: {p.get('product_type', 'N/A')}",
                    f"Price: £{p['price']:.2f}" if p.get('price') else "Price: N/A",
                    f"\nIngredients ({len(ings)}, listed highest to lowest concentration):"
                ]
                for ing in ings:
                    lines.append(f"  {ing['position']}. {ing['ingredient']['name']} [{ing['ingredient']['irritation_level']} irritation]")
 
                return [TextContent(type="text", text="\n".join(lines))]
 
            elif name == "check_safety_score":
                product_id = arguments["product_id"]
                res = await client.get(f"{API_BASE}/products/{product_id}/safety-score")
 
                if res.status_code == 404:
                    return [TextContent(type="text", text=f"Product ID {product_id} not found or has no ingredients.")]
 
                d = res.json()
                rating = "Safe" if d['safety_score'] >= 7 else "Moderate" if d['safety_score'] >= 4 else "High Risk"
 
                text = (
                    f"Safety Analysis: {d['product_name']}\n"
                    f"Safety Score: {d['safety_score']}/10 ({rating})\n"
                    f"Total Ingredients: {d['total_ingredients']}\n"
                    f"High Irritation: {d['high_irritation_count']} ingredients\n"
                    f"Medium Irritation: {d['medium_irritation_count']} ingredients\n"
                    f"Low Irritation: {d['low_irritation_count']} ingredients"
                )
                return [TextContent(type="text", text=text)]
 
            elif name == "check_product_conflicts":
                product_ids = arguments["product_ids"]
                res = await client.post(
                    f"{API_BASE}/products/conflict-check",
                    json={"product_ids": product_ids}
                )
 
                if res.status_code == 400:
                    return [TextContent(type="text", text="Please provide at least 2 product IDs.")]
 
                d = res.json()
                if not d["has_conflicts"]:
                    products_checked = ", ".join(p["name"] for p in d["products_checked"])
                    return [TextContent(type="text", text=f"✓ No conflicts found. These products are safe to use together:\n{products_checked}")]
 
                lines = [f"⚠ {d['conflict_count']} conflict(s) found:\n"]
                for c in d["conflicts"]:
                    lines.append(f"- {c['product_1']} × {c['product_2']}")
                    lines.append(f"  Conflicting ingredients: {c['conflicting_ingredients']}")
                    lines.append(f"  Severity: {c['severity'].upper()}\n")
 
                return [TextContent(type="text", text="\n".join(lines))]
 
            elif name == "get_recommendations":
                skin_type = arguments["skin_type"]
                concern = arguments.get("concern", "")
 
                # get concerns for this skin type
                res = await client.get(
                    f"{API_BASE}/profile/common-concerns",
                    params={"skin_type": skin_type}
                )
 
                if res.status_code != 200:
                    return [TextContent(type="text", text=f"No data found for skin type: {skin_type}")]
 
                concerns = res.json()
 
                # filter by concern if provided
                if concern:
                    matched = [c for c in concerns if concern.lower() in c["name"].lower()]
                    concerns = matched if matched else concerns
 
                # get recommended ingredients
                all_ingredients = []
                seen = set()
                for c in concerns:
                    for ing in c.get("recommended_ingredients", []):
                        if ing["name"] not in seen:
                            all_ingredients.append(ing)
                            seen.add(ing["name"])
 
                lines = [
                    f"Recommendations for {skin_type} skin{' (' + concern + ')' if concern else ''}:\n",
                    f"Key recommended ingredients ({len(all_ingredients)}):"
                ]
                for ing in all_ingredients[:10]:
                    lines.append(f"  - {ing['name']} [{ing['irritation_level']} irritation]")
 
                lines.append(f"\nSearch for products containing these ingredients using search_products.")
                return [TextContent(type="text", text="\n".join(lines))]
 
            elif name == "get_known_conflicts":
                res = await client.get(f"{API_BASE}/conflicts/")
                conflicts = res.json()
 
                lines = [f"Known ingredient conflicts ({len(conflicts)} pairs):\n"]
                for c in conflicts:
                    lines.append(
                        f"- {c['ingredient_1']['name']} + {c['ingredient_2']['name']} "
                        f"[{c['severity'].upper()}]"
                    )
 
                return [TextContent(type="text", text="\n".join(lines))]
 
            elif name == "profile_match":
                product_id = arguments["product_id"]
                skin_type = arguments["skin_type"]
 
                res = await client.get(
                    f"{API_BASE}/products/{product_id}/profile-match",
                    params={"skin_type": skin_type}
                )
 
                if res.status_code == 404:
                    return [TextContent(type="text", text=f"Product ID {product_id} not found.")]
 
                d = res.json()
                rating = "Excellent" if d['match_score'] >= 70 else "Good" if d['match_score'] >= 40 else "Poor"
 
                lines = [
                    f"Profile Match: {d['product_name']}",
                    f"Skin Type: {skin_type}",
                    f"Match Score: {d['match_score']}% ({rating})",
                    f"Matched {d['matched']} of {d['total_recommended']} recommended ingredients",
                ]
                if d["matching_ingredients"]:
                    lines.append(f"\nMatching ingredients:")
                    for ing in d["matching_ingredients"]:
                        lines.append(f"  - {ing}")
 
                return [TextContent(type="text", text="\n".join(lines))]
 
            elif name == "get_ingredient_frequency":
                res = await client.get(f"{API_BASE}/analytics/ingredient-frequency")
                d = res.json()
 
                lines = [f"Top ingredients across {d['total_products']} products:\n"]
                for item in d["top_ingredients"]:
                    lines.append(f"- {item['name']}: appears in {item['appears_in']} products ({item['percentage']})")
 
                return [TextContent(type="text", text="\n".join(lines))]
 
            else:
                return [TextContent(type="text", text=f"Unknown tool: {name}")]
 
        except httpx.ConnectError:
            return [TextContent(type="text", text="Cannot connect to Skincare API. Make sure the server is running at http://127.0.0.1:8000")]
        except Exception as e:
            return [TextContent(type="text", text=f"Error calling API: {str(e)}")]
 
 
# ── ENTRY POINT ───────────────────────────────────────────────────────────────
 
async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )
 
if __name__ == "__main__":
    asyncio.run(main())