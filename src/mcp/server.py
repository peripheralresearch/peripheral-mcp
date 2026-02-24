"""
FastMCP server wrapping The Peripheral API.
This provides MCP tools for Claude and other MCP clients.
"""
from fastmcp import FastMCP
import httpx
import os
from typing import Optional

# MCP server instance
mcp = FastMCP("The Peripheral")

# API base URL (will be configurable)
API_BASE = os.getenv("PERIPHERAL_API_URL", "http://localhost:8000")

# Shared timeout for API calls
TIMEOUT = 30.0


@mcp.tool()
async def get_latest_briefing(
    hours: int = 24,
    region: Optional[str] = None,
) -> dict:
    """
    Get the latest intelligence briefing from The Peripheral.

    Args:
        hours: Hours to look back (1-168). Default: 24
        region: Optional region filter (ukraine, middle-east, global)

    Returns:
        Intelligence briefing with articles, sources, and summary
    """
    params = {"hours": hours}
    if region:
        params["region"] = region

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        response = await client.get(f"{API_BASE}/briefing/latest", params=params)
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_military_signals(
    region: str,
    hours: int = 24,
    signal_type: Optional[str] = None,
) -> dict:
    """
    Get military signals (air raid warnings, threats) for a specific region.

    Args:
        region: Region name (e.g., "Kharkiv", "Kyiv", "Odesa")
        hours: Hours to look back (1-168). Default: 24
        signal_type: Optional signal type filter

    Returns:
        Military signals with breakdown by type
    """
    params = {"hours": hours}
    if signal_type:
        params["signal_type"] = signal_type

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        response = await client.get(
            f"{API_BASE}/signals/region/{region}",
            params=params,
        )
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_trending_stories(
    hours: int = 24,
    limit: int = 10,
) -> dict:
    """
    Get trending stories from The Peripheral (ranked by article count).

    Args:
        hours: Hours to look back (1-168). Default: 24
        limit: Maximum number of stories (1-50). Default: 10

    Returns:
        List of trending stories with summaries
    """
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        response = await client.get(
            f"{API_BASE}/stories/trending",
            params={"hours": hours, "limit": limit},
        )
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def health_check() -> dict:
    """
    Check if The Peripheral API and database are healthy.

    Returns:
        Health status and database connectivity
    """
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        response = await client.get(f"{API_BASE}/health")
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def search_stories(
    query: str,
    hours: int = 168,
    limit: int = 20,
) -> dict:
    """
    Search stories by keyword or topic. Searches across story titles, summaries,
    and topic keywords.

    Args:
        query: Search term (e.g., "Ukraine offensive", "NATO", "drone strike")
        hours: Hours to look back (1-720). Default: 168 (7 days)
        limit: Maximum number of results (1-50). Default: 20

    Returns:
        Matching stories with titles, summaries, and metadata
    """
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        response = await client.get(
            f"{API_BASE}/stories/search",
            params={"q": query, "hours": hours, "limit": limit},
        )
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_story_details(
    story_id: str,
) -> dict:
    """
    Get full details for a specific story, including all linked articles
    and entities (people, organizations, locations).

    Args:
        story_id: The story UUID (from search_stories or get_trending_stories)

    Returns:
        Complete story with articles, persons, organisations, and locations
    """
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        response = await client.get(f"{API_BASE}/stories/{story_id}")
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def search_entities(
    name: str,
    entity_type: str = "all",
    limit: int = 20,
) -> dict:
    """
    Search for entities (people, organizations, locations, countries) by name.
    Uses fuzzy matching to find partial name matches.

    Args:
        name: Entity name to search (e.g., "Putin", "NATO", "Kyiv")
        entity_type: Filter by type: "person", "organisation", "location", "country", or "all"
        limit: Maximum number of results (1-50). Default: 20

    Returns:
        Matching entities with their type, role, and metadata
    """
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        response = await client.get(
            f"{API_BASE}/entities/search",
            params={"name": name, "type": entity_type, "limit": limit},
        )
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_entity_context(
    entity_id: str,
    entity_type: str,
    hours: int = 168,
) -> dict:
    """
    Get recent articles and stories mentioning a specific entity.
    Use search_entities first to find the entity ID.

    Args:
        entity_id: The entity ID (from search_entities)
        entity_type: Entity type: "person", "organisation", "location", or "country"
        hours: Hours to look back (1-720). Default: 168 (7 days)

    Returns:
        Recent articles and stories mentioning the entity
    """
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        response = await client.get(
            f"{API_BASE}/entities/{entity_type}/{entity_id}/context",
            params={"hours": hours},
        )
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def search_articles(
    query: str,
    hours: int = 168,
    limit: int = 50,
) -> dict:
    """
    Search individual news articles by keyword. Searches across article titles
    and content. More granular than search_stories.

    Args:
        query: Search term (e.g., "missile strike", "ceasefire", "sanctions")
        hours: Hours to look back (1-720). Default: 168 (7 days)
        limit: Maximum number of results (1-100). Default: 50

    Returns:
        Matching articles with titles, content snippets, and metadata
    """
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        response = await client.get(
            f"{API_BASE}/articles/search",
            params={"q": query, "hours": hours, "limit": limit},
        )
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_signal_timeline(
    region: str,
    hours: int = 168,
) -> dict:
    """
    Get military signals grouped by hour for timeline visualization.
    Useful for tracking escalation patterns and activity trends.

    Args:
        region: Region name (e.g., "KYIV", "KHARKIV", "ODESA")
        hours: Hours to look back (1-720). Default: 168 (7 days)

    Returns:
        Hourly signal counts with breakdowns by type and weapon
    """
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        response = await client.get(
            f"{API_BASE}/signals/timeline/{region}",
            params={"hours": hours},
        )
        response.raise_for_status()
        return response.json()


def main():
    """Entry point for uvx/mcp client"""
    mcp.run()


# Entry point for uvx
if __name__ == "__main__":
    main()
