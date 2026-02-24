"""
FastAPI server providing curated endpoints for Peripheral OSINT data.
This layer sits between the MCP server and Supabase, providing controlled access.
"""
from fastapi import FastAPI, HTTPException, Query, Path
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from collections import defaultdict
import os
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

app = FastAPI(
    title="The Peripheral API",
    description="Curated OSINT intelligence data from The Peripheral",
    version="0.2.0",
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
    os.getenv("SUPABASE_KEY"),
)


# --- Formatters ---


def format_article(article: Dict[str, Any]) -> Dict[str, Any]:
    """Format article for public consumption (hide internal fields)"""
    return {
        "id": article.get("id"),
        "title": article.get("title"),
        "content": (article.get("content") or "")[:500],
        "published": article.get("published"),
        "author": article.get("author"),
        "link": article.get("link"),
        "sentiment": article.get("sentiment_category"),
        "story_id": article.get("story_id"),
    }


def format_signal(signal: Dict[str, Any]) -> Dict[str, Any]:
    """Format military signal for public consumption"""
    return {
        "type": signal.get("signal_type"),
        "weapon": signal.get("weapon_type"),
        "location": signal.get("target_location"),
        "region": signal.get("target_region"),
        "direction": signal.get("direction"),
        "alert_type": signal.get("alert_type"),
        "alert_status": signal.get("alert_status"),
        "timestamp": signal.get("created_at"),
    }


def format_story(story: Dict[str, Any]) -> Dict[str, Any]:
    """Format story for public consumption"""
    return {
        "id": story.get("id"),
        "title": story.get("title"),
        "summary": story.get("summary"),
        "description": story.get("description"),
        "topic_keywords": story.get("topic_keywords"),
        "created": story.get("created"),
        "updated": story.get("updated"),
        "source_count": story.get("source_count"),
    }


def _cutoff_iso(hours: int) -> str:
    """Return ISO timestamp for N hours ago."""
    return (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()


# --- Existing endpoints ---


@app.get("/")
async def root():
    return {
        "service": "The Peripheral API",
        "version": "0.2.0",
        "endpoints": [
            "/health",
            "/briefing/latest",
            "/signals/region/{region}",
            "/signals/timeline/{region}",
            "/stories/trending",
            "/stories/search",
            "/stories/{story_id}",
            "/articles/search",
            "/entities/search",
            "/entities/{entity_type}/{entity_id}/context",
        ],
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    try:
        result = supabase.table("news_item").select("id").limit(1).execute()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database unhealthy: {str(e)}")


@app.get("/briefing/latest")
async def get_latest_briefing(
    hours: int = Query(24, ge=1, le=168, description="Hours to look back (1-168)"),
    region: Optional[str] = Query(None, description="Filter by region"),
):
    """Get latest intelligence briefing for specified timeframe"""
    try:
        cutoff = _cutoff_iso(hours)

        query = (
            supabase.table("news_item")
            .select("*, story(id, title, summary)")
            .gte("published", cutoff)
            .order("published", desc=True)
            .limit(50)
        )

        result = query.execute()

        articles = [format_article(item) for item in result.data]

        sources = {}
        for item in result.data:
            source_id = item.get("osint_source_id")
            sources[source_id] = sources.get(source_id, 0) + 1

        return {
            "timeframe": f"{hours}h",
            "count": len(articles),
            "articles": articles[:20],
            "sources_active": len(sources),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        logger.exception("briefing/latest failed")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/signals/region/{region}")
async def get_signals_by_region(
    region: str,
    hours: int = Query(24, ge=1, le=168),
    signal_type: Optional[str] = Query(None, description="Filter by signal type"),
):
    """Get military signals for a specific region"""
    try:
        cutoff = _cutoff_iso(hours)

        query = (
            supabase.table("signal")
            .select("*")
            .ilike("target_region", region)
            .gte("created_at", cutoff)
            .order("created_at", desc=True)
            .limit(100)
        )

        if signal_type:
            query = query.eq("signal_type", signal_type)

        result = query.execute()

        signals = [format_signal(s) for s in result.data]

        # Resolve actual region name from data
        actual_region = region
        if result.data:
            actual_region = result.data[0].get("target_region", region)

        by_type = {}
        for s in result.data:
            stype = s.get("signal_type", "unknown")
            by_type[stype] = by_type.get(stype, 0) + 1

        return {
            "region": actual_region,
            "timeframe": f"{hours}h",
            "count": len(signals),
            "signals": signals[:50],
            "breakdown": by_type,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        logger.exception("signals/region failed")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stories/trending")
async def get_trending_stories(
    hours: int = Query(24, ge=1, le=168),
    limit: int = Query(10, ge=1, le=50),
):
    """Get trending stories (by article count)"""
    try:
        cutoff = _cutoff_iso(hours)

        result = supabase.rpc(
            "get_trending_stories",
            {"hours_ago": hours, "max_results": limit},
        ).execute()

        # Fallback if RPC doesn't exist
        if not result.data:
            result = (
                supabase.table("story")
                .select("id, title, summary, created")
                .gte("created", cutoff)
                .order("created", desc=True)
                .limit(limit)
                .execute()
            )

        return {
            "timeframe": f"{hours}h",
            "count": len(result.data),
            "stories": result.data,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        logger.exception("stories/trending failed")
        raise HTTPException(status_code=500, detail=str(e))


# --- New endpoints ---


@app.get("/stories/search")
async def search_stories(
    q: str = Query(..., min_length=2, max_length=200, description="Search query"),
    hours: int = Query(168, ge=1, le=720, description="Hours to look back"),
    limit: int = Query(20, ge=1, le=50, description="Max results"),
):
    """Search stories by keyword/topic across title, summary, and topic_keywords."""
    try:
        cutoff = _cutoff_iso(hours)

        # Use ilike for case-insensitive partial matching on title and summary
        # Supabase PostgREST supports `or` filter syntax
        result = (
            supabase.table("story")
            .select("id, title, summary, description, topic_keywords, created, updated, source_count")
            .or_(f"title.ilike.%{q}%,summary.ilike.%{q}%")
            .gte("created", cutoff)
            .order("created", desc=True)
            .limit(limit)
            .execute()
        )

        stories = [format_story(s) for s in result.data]

        return {
            "query": q,
            "timeframe": f"{hours}h",
            "count": len(stories),
            "stories": stories,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        logger.exception("stories/search failed")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stories/{story_id}")
async def get_story_details(
    story_id: str = Path(..., description="Story UUID"),
):
    """Get full story details with linked articles and entities."""
    try:
        # Get story
        story_result = (
            supabase.table("story")
            .select("*")
            .eq("id", story_id)
            .execute()
        )

        if not story_result.data:
            raise HTTPException(status_code=404, detail=f"Story {story_id} not found")

        story = story_result.data[0]

        # Get linked articles
        articles_result = (
            supabase.table("news_item")
            .select("id, title, content, published, author, link, sentiment_category")
            .eq("story_id", story_id)
            .order("published", desc=True)
            .limit(50)
            .execute()
        )

        # Get linked entities (persons, orgs, locations) via join tables
        persons_result = (
            supabase.table("story_entity_person")
            .select("person_id, rank, confidence, entity_person(id, name, role)")
            .eq("story_id", story_id)
            .order("rank")
            .limit(20)
            .execute()
        )

        orgs_result = (
            supabase.table("story_entity_organisation")
            .select("organisation_id, rank, confidence, entity_organisation(id, name, org_type)")
            .eq("story_id", story_id)
            .order("rank")
            .limit(20)
            .execute()
        )

        locations_result = (
            supabase.table("story_entity_location")
            .select("location_id, rank, confidence, entity_location(id, name, lat, lon, country_code)")
            .eq("story_id", story_id)
            .order("rank")
            .limit(20)
            .execute()
        )

        # Extract entity details from nested joins
        persons = [
            {
                "id": r["entity_person"]["id"],
                "name": r["entity_person"]["name"],
                "role": r["entity_person"].get("role"),
                "rank": r.get("rank"),
                "confidence": r.get("confidence"),
            }
            for r in persons_result.data
            if r.get("entity_person")
        ]

        orgs = [
            {
                "id": r["entity_organisation"]["id"],
                "name": r["entity_organisation"]["name"],
                "type": r["entity_organisation"].get("org_type"),
                "rank": r.get("rank"),
                "confidence": r.get("confidence"),
            }
            for r in orgs_result.data
            if r.get("entity_organisation")
        ]

        locations = [
            {
                "id": r["entity_location"]["id"],
                "name": r["entity_location"]["name"],
                "lat": r["entity_location"].get("lat"),
                "lon": r["entity_location"].get("lon"),
                "country_code": r["entity_location"].get("country_code"),
                "rank": r.get("rank"),
                "confidence": r.get("confidence"),
            }
            for r in locations_result.data
            if r.get("entity_location")
        ]

        articles = [format_article(a) for a in articles_result.data]

        return {
            "story": format_story(story),
            "article_count": len(articles),
            "articles": articles,
            "entities": {
                "persons": persons,
                "organisations": orgs,
                "locations": locations,
            },
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("stories/{story_id} failed")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/entities/search")
async def search_entities(
    name: str = Query(..., min_length=2, max_length=200, description="Entity name to search"),
    type: str = Query("all", description="Entity type: person, organisation, location, country, all"),
    limit: int = Query(20, ge=1, le=50, description="Max results"),
):
    """Search entities across person, organisation, location, and country tables."""
    try:
        valid_types = {"person", "organisation", "location", "country", "all"}
        if type not in valid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid entity type '{type}'. Must be one of: {', '.join(sorted(valid_types))}",
            )

        results = []
        search_types = [type] if type != "all" else ["person", "organisation", "location", "country"]

        for entity_type in search_types:
            table = f"entity_{entity_type}"

            if entity_type == "person":
                select = "id, name, role, created"
            elif entity_type == "organisation":
                select = "id, name, org_type, created"
            elif entity_type == "location":
                select = "id, name, lat, lon, country_code, location_type"
            else:  # country
                select = "id, name, official_name, iso_alpha2, region, flag_emoji, mention_count"

            query_result = (
                supabase.table(table)
                .select(select)
                .ilike("name", f"%{name}%")
                .limit(limit)
                .execute()
            )

            for entity in query_result.data:
                entity["entity_type"] = entity_type
                results.append(entity)

        # Sort by name relevance (exact match first, then starts-with, then contains)
        name_lower = name.lower()
        def sort_key(e):
            n = (e.get("name") or "").lower()
            if n == name_lower:
                return (0, n)
            if n.startswith(name_lower):
                return (1, n)
            return (2, n)

        results.sort(key=sort_key)

        return {
            "query": name,
            "type_filter": type,
            "count": len(results[:limit]),
            "entities": results[:limit],
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("entities/search failed")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/entities/{entity_type}/{entity_id}/context")
async def get_entity_context(
    entity_type: str = Path(..., description="Entity type: person, organisation, location, country"),
    entity_id: str = Path(..., description="Entity ID"),
    hours: int = Query(168, ge=1, le=720, description="Hours to look back"),
):
    """Get articles and stories mentioning a specific entity."""
    try:
        valid_types = {"person", "organisation", "location", "country"}
        if entity_type not in valid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid entity type '{entity_type}'. Must be one of: {', '.join(sorted(valid_types))}",
            )

        cutoff = _cutoff_iso(hours)

        # Map entity types to their join table and FK column names
        join_config = {
            "person": ("news_item_entity_person", "person_id", "story_entity_person"),
            "organisation": ("news_item_entity_organisation", "organisation_id", "story_entity_organisation"),
            "location": ("news_item_entity_location", "location_id", "story_entity_location"),
            "country": ("news_item_entity_country", "country_id", "story_entity_country"),
        }

        ni_join_table, fk_col, story_join_table = join_config[entity_type]

        # Get entity info
        entity_table = f"entity_{entity_type}"
        entity_result = (
            supabase.table(entity_table)
            .select("*")
            .eq("id", entity_id)
            .execute()
        )

        if not entity_result.data:
            raise HTTPException(
                status_code=404,
                detail=f"{entity_type} with id {entity_id} not found",
            )

        entity = entity_result.data[0]

        # Get news items mentioning this entity
        ni_join_result = (
            supabase.table(ni_join_table)
            .select(f"{fk_col}, news_item_id, news_item(id, title, published, link, sentiment_category)")
            .eq(fk_col, entity_id)
            .limit(100)
            .execute()
        )

        # Filter by date and format
        articles = []
        for row in ni_join_result.data:
            ni = row.get("news_item")
            if ni and ni.get("published") and ni["published"] >= cutoff:
                articles.append({
                    "id": ni["id"],
                    "title": ni["title"],
                    "published": ni["published"],
                    "link": ni.get("link"),
                    "sentiment": ni.get("sentiment_category"),
                })

        # Sort by published date descending
        articles.sort(key=lambda a: a.get("published", ""), reverse=True)

        # Get stories mentioning this entity
        story_join_result = (
            supabase.table(story_join_table)
            .select(f"story_id, rank, confidence, story(id, title, summary, created)")
            .eq(fk_col if entity_type != "location" else "location_id", entity_id)
            .limit(50)
            .execute()
        )

        stories = []
        for row in story_join_result.data:
            s = row.get("story")
            if s and s.get("created") and s["created"] >= cutoff:
                stories.append({
                    "id": s["id"],
                    "title": s["title"],
                    "summary": s.get("summary"),
                    "created": s["created"],
                    "rank": row.get("rank"),
                })

        stories.sort(key=lambda s: s.get("created", ""), reverse=True)

        return {
            "entity": {
                "id": entity.get("id"),
                "name": entity.get("name"),
                "type": entity_type,
            },
            "timeframe": f"{hours}h",
            "article_count": len(articles),
            "articles": articles[:30],
            "story_count": len(stories),
            "stories": stories[:20],
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("entities/{entity_type}/{entity_id}/context failed")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/articles/search")
async def search_articles(
    q: str = Query(..., min_length=2, max_length=200, description="Search query"),
    hours: int = Query(168, ge=1, le=720, description="Hours to look back"),
    limit: int = Query(50, ge=1, le=100, description="Max results"),
):
    """Search news articles by title and content."""
    try:
        cutoff = _cutoff_iso(hours)

        result = (
            supabase.table("news_item")
            .select("id, title, content, published, author, link, sentiment_category, story_id")
            .or_(f"title.ilike.%{q}%,content.ilike.%{q}%")
            .gte("published", cutoff)
            .order("published", desc=True)
            .limit(limit)
            .execute()
        )

        articles = [format_article(a) for a in result.data]

        return {
            "query": q,
            "timeframe": f"{hours}h",
            "count": len(articles),
            "articles": articles,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        logger.exception("articles/search failed")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/signals/timeline/{region}")
async def get_signal_timeline(
    region: str = Path(..., description="Region name (e.g. Харківська, Київська, or partial match)"),
    hours: int = Query(168, ge=1, le=720, description="Hours to look back"),
):
    """Get signals grouped by hour for timeline visualization and escalation tracking."""
    try:
        cutoff = _cutoff_iso(hours)

        result = (
            supabase.table("signal")
            .select("signal_type, weapon_type, alert_type, target_region, created_at")
            .ilike("target_region", region)
            .gte("created_at", cutoff)
            .order("created_at", desc=True)
            .limit(1000)
            .execute()
        )

        # Group signals by hour
        hourly = defaultdict(lambda: {"count": 0, "by_type": defaultdict(int), "by_weapon": defaultdict(int)})

        for signal in result.data:
            ts = signal.get("created_at", "")
            # Truncate to hour: "2026-02-24T14:35:00" -> "2026-02-24T14:00"
            hour_key = ts[:13] + ":00" if len(ts) >= 13 else ts
            bucket = hourly[hour_key]
            bucket["count"] += 1

            stype = signal.get("signal_type") or signal.get("alert_type") or "unknown"
            bucket["by_type"][stype] += 1

            weapon = signal.get("weapon_type")
            if weapon:
                bucket["by_weapon"][weapon] += 1

        # Convert to sorted list
        timeline = []
        for hour_key in sorted(hourly.keys()):
            bucket = hourly[hour_key]
            timeline.append({
                "hour": hour_key,
                "count": bucket["count"],
                "by_type": dict(bucket["by_type"]),
                "by_weapon": dict(bucket["by_weapon"]),
            })

        # Overall aggregates
        total = len(result.data)
        type_totals = defaultdict(int)
        weapon_totals = defaultdict(int)
        for signal in result.data:
            stype = signal.get("signal_type") or signal.get("alert_type") or "unknown"
            type_totals[stype] += 1
            weapon = signal.get("weapon_type")
            if weapon:
                weapon_totals[weapon] += 1

        # Resolve actual region name from data
        actual_region = region
        if result.data:
            actual_region = result.data[0].get("target_region", region)

        return {
            "region": actual_region,
            "timeframe": f"{hours}h",
            "total_signals": total,
            "hours_with_activity": len(timeline),
            "type_totals": dict(type_totals),
            "weapon_totals": dict(weapon_totals),
            "timeline": timeline,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        logger.exception("signals/timeline failed")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
