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


@mcp.tool()
async def get_latest_briefing(
    hours: int = 24,
    region: Optional[str] = None
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
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE}/briefing/latest", params=params)
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_military_signals(
    region: str,
    hours: int = 24,
    signal_type: Optional[str] = None
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
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_BASE}/signals/region/{region}",
            params=params
        )
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_trending_stories(
    hours: int = 24,
    limit: int = 10
) -> dict:
    """
    Get trending stories from The Peripheral (ranked by article count).
    
    Args:
        hours: Hours to look back (1-168). Default: 24
        limit: Maximum number of stories (1-50). Default: 10
    
    Returns:
        List of trending stories with summaries
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_BASE}/stories/trending",
            params={"hours": hours, "limit": limit}
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
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE}/health")
        response.raise_for_status()
        return response.json()


# Entry point for uvx
if __name__ == "__main__":
    mcp.run()
