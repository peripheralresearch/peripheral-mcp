"""
Prefect Horizon-optimized MCP server for The Peripheral.
Queries Supabase directly (no intermediate FastAPI server needed).
"""
from fastmcp import FastMCP
from supabase import create_client, Client
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import os

# MCP server instance
mcp = FastMCP("The Peripheral")

# Supabase client
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)


def format_article(article: Dict[str, Any]) -> Dict[str, Any]:
    """Format article for public consumption"""
    return {
        "title": article.get("title"),
        "content": article.get("content", "")[:500],
        "published": article.get("published"),
        "author": article.get("author"),
        "link": article.get("link"),
        "sentiment": article.get("sentiment_category"),
    }


def format_signal(signal: Dict[str, Any]) -> Dict[str, Any]:
    """Format military signal for public consumption"""
    return {
        "type": signal.get("signal_type"),
        "weapon": signal.get("weapon_type"),
        "location": signal.get("target_location"),
        "region": signal.get("target_region"),
        "direction": signal.get("direction"),
        "timestamp": signal.get("created_at"),
    }


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
    try:
        cutoff = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
        
        query = supabase.table("news_item")\
            .select("*, story(id, title, summary)")\
            .gte("published", cutoff)\
            .order("published", desc=True)\
            .limit(50)
        
        result = query.execute()
        articles = [format_article(item) for item in result.data]
        
        # Count unique sources
        sources = set(item.get("author") for item in result.data if item.get("author"))
        
        return {
            "period_hours": hours,
            "article_count": len(articles),
            "source_count": len(sources),
            "articles": articles,
            "generated_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        return {"error": str(e), "status": "failed"}


@mcp.tool()
async def get_military_signals(
    region: str,
    hours: int = 24,
    signal_type: Optional[str] = None
) -> dict:
    """
    Get military signals (air raid warnings, threats) for a specific region.
    
    Args:
        region: Region name (e.g., "Kharkiv", "Kyiv", "Odesa", "Ukraine")
        hours: Hours to look back (1-168). Default: 24
        signal_type: Optional signal type filter
    
    Returns:
        Military signals with breakdown by type
    """
    try:
        cutoff = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
        
        query = supabase.table("signal")\
            .select("*")\
            .ilike("target_region", f"%{region}%")\
            .gte("published", cutoff)\
            .order("published", desc=True)\
            .limit(100)
        
        if signal_type:
            query = query.eq("signal_type", signal_type)
        
        result = query.execute()
        signals = [format_signal(s) for s in result.data]
        
        # Group by type
        by_type = {}
        for signal in signals:
            stype = signal.get("type", "unknown")
            by_type[stype] = by_type.get(stype, 0) + 1
        
        return {
            "region": region,
            "period_hours": hours,
            "count": len(signals),
            "signals": signals,
            "breakdown_by_type": by_type,
            "generated_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        return {"error": str(e), "status": "failed"}


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
    try:
        cutoff = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
        
        # Get recent stories
        result = supabase.table("story")\
            .select("id, title, summary, created")\
            .gte("created", cutoff)\
            .order("created", desc=True)\
            .limit(limit)\
            .execute()
        
        stories = result.data
        
        return {
            "period_hours": hours,
            "count": len(stories),
            "stories": stories,
            "generated_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        return {"error": str(e), "status": "failed"}


@mcp.tool()
async def health_check() -> dict:
    """
    Check if The Peripheral database is healthy.
    
    Returns:
        Health status and database connectivity
    """
    try:
        # Quick DB check
        result = supabase.table("news_item").select("id").limit(1).execute()
        
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


def main():
    """Entry point for Prefect Horizon deployment"""
    mcp.run()


if __name__ == "__main__":
    main()
