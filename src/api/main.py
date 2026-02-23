"""
FastAPI server providing curated endpoints for Peripheral OSINT data.
This layer sits between the MCP server and Supabase, providing controlled access.
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="The Peripheral API",
    description="Curated OSINT intelligence data from The Peripheral",
    version="0.1.0"
)

# CORS for public access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)

# Supabase client
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)


def format_article(article: Dict[str, Any]) -> Dict[str, Any]:
    """Format article for public consumption (hide internal fields)"""
    return {
        "title": article.get("title"),
        "content": article.get("content", "")[:500],  # Truncate content
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


@app.get("/")
async def root():
    return {
        "service": "The Peripheral API",
        "version": "0.1.0",
        "endpoints": [
            "/briefing/latest",
            "/briefing/{date}",
            "/signals/region/{region}",
            "/stories/trending",
            "/health"
        ]
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    try:
        # Quick DB check
        result = supabase.table("news_item").select("id").limit(1).execute()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database unhealthy: {str(e)}")


@app.get("/briefing/latest")
async def get_latest_briefing(
    hours: int = Query(24, ge=1, le=168, description="Hours to look back (1-168)"),
    region: Optional[str] = Query(None, description="Filter by region (ukraine, middle-east, global)")
):
    """Get latest intelligence briefing for specified timeframe"""
    try:
        cutoff = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
        
        query = supabase.table("news_item")\
            .select("*, story(id, title, summary)")\
            .gte("published", cutoff)\
            .order("published", desc=True)\
            .limit(50)
        
        result = query.execute()
        
        articles = [format_article(item) for item in result.data]
        
        # Count by source
        sources = {}
        for item in result.data:
            source_id = item.get("osint_source_id")
            sources[source_id] = sources.get(source_id, 0) + 1
        
        return {
            "timeframe": f"{hours}h",
            "count": len(articles),
            "articles": articles[:20],  # Return top 20
            "sources_active": len(sources),
            "generated_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/signals/region/{region}")
async def get_signals_by_region(
    region: str,
    hours: int = Query(24, ge=1, le=168),
    signal_type: Optional[str] = Query(None, description="Filter by signal type")
):
    """Get military signals for a specific region"""
    try:
        cutoff = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
        
        query = supabase.table("signal")\
            .select("*")\
            .eq("target_region", region.upper())\
            .gte("created_at", cutoff)\
            .order("created_at", desc=True)\
            .limit(100)
        
        if signal_type:
            query = query.eq("signal_type", signal_type)
        
        result = query.execute()
        
        signals = [format_signal(s) for s in result.data]
        
        # Count by type
        by_type = {}
        for s in result.data:
            stype = s.get("signal_type", "unknown")
            by_type[stype] = by_type.get(stype, 0) + 1
        
        return {
            "region": region,
            "timeframe": f"{hours}h",
            "count": len(signals),
            "signals": signals[:50],  # Return top 50
            "breakdown": by_type,
            "generated_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stories/trending")
async def get_trending_stories(
    hours: int = Query(24, ge=1, le=168),
    limit: int = Query(10, ge=1, le=50)
):
    """Get trending stories (by article count)"""
    try:
        cutoff = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
        
        # Get stories with article counts
        result = supabase.rpc(
            "get_trending_stories",
            {"hours_ago": hours, "max_results": limit}
        ).execute()
        
        # Fallback if RPC doesn't exist
        if not result.data:
            result = supabase.table("story")\
                .select("id, title, summary, created_at")\
                .gte("created_at", cutoff)\
                .order("created_at", desc=True)\
                .limit(limit)\
                .execute()
        
        return {
            "timeframe": f"{hours}h",
            "count": len(result.data),
            "stories": result.data,
            "generated_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
