"""
FastMCP cloud server querying Supabase directly.

Provides MCP tools for curated OSINT intelligence data without FastAPI intermediary.
Includes free tier gating (720 hours = 30 days), token-based authentication, and usage logging.
"""

import os
import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Optional, Any
from collections import defaultdict

from fastmcp import FastMCP
from fastmcp.server.auth import StaticTokenVerifier
from starlette.requests import Request
from starlette.responses import JSONResponse
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("peripheral.cloud")


# --- Constants ---

FREE_TIER_MAX_HOURS = 720  # 30 days


# --- Supabase Client ---

supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY"),
)


# --- Auth Setup ---


def _build_auth():
    """Build auth from MCP_AUTH_TOKENS env var. Empty = no auth (open access)."""
    raw = os.getenv("MCP_AUTH_TOKENS", "")
    if not raw.strip():
        return None
    tokens = {}
    for i, token in enumerate(raw.split(",")):
        token = token.strip()
        if token:
            tokens[token] = {
                "client_id": f"friend_{i}",
                "scopes": ["read"],
            }
    return StaticTokenVerifier(tokens=tokens)


# --- Formatters ---


def format_article(article: dict[str, Any]) -> dict[str, Any]:
    """Format article for public consumption (hide internal fields)."""
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


def format_signal(signal: dict[str, Any]) -> dict[str, Any]:
    """Format military signal for public consumption."""
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


def format_story(story: dict[str, Any]) -> dict[str, Any]:
    """Format story for public consumption."""
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


# --- Helpers ---


def _cutoff_iso(hours: int) -> str:
    """Return ISO timestamp for N hours ago."""
    return (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()


def _enforce_free_tier(hours: int) -> tuple[int, str | None]:
    """Clamp hours to FREE_TIER_MAX_HOURS. Returns (clamped_hours, message_or_None)."""
    if hours <= FREE_TIER_MAX_HOURS:
        return hours, None
    return FREE_TIER_MAX_HOURS, f"Free tier limited to {FREE_TIER_MAX_HOURS}h (30 days). Requested {hours}h was clamped."


def _log_usage(
    tool_name: str,
    params: dict | None,
    client_id: str | None,
    status: str,
    duration_ms: int,
) -> None:
    """Fire-and-forget usage log to Supabase."""
    try:
        supabase.table("mcp_usage_log").insert(
            {
                "tool_name": tool_name,
                "params": params,
                "client_id": client_id,
                "response_status": status,
                "duration_ms": duration_ms,
            }
        ).execute()
    except Exception as e:
        logger.warning(f"Usage log failed: {e}")


def _get_client_id(request: Request) -> str | None:
    """Extract client_id from request context if authenticated."""
    try:
        if hasattr(request, "auth"):
            return request.auth.get("client_id")
    except Exception:
        pass
    return None


# --- Initialize FastMCP ---

auth = _build_auth()
mcp = FastMCP("The Peripheral", auth=auth)


# --- Health Endpoint ---


@mcp.custom_route("/health", methods=["GET"])
async def health_endpoint(request: Request) -> JSONResponse:
    """Health check endpoint."""
    start = time.time()
    try:
        supabase.table("news_item").select("id").limit(1).execute()
        duration_ms = int((time.time() - start) * 1000)
        client_id = _get_client_id(request)
        _log_usage("health_check", None, client_id, "ok", duration_ms)
        return JSONResponse(
            {
                "status": "healthy",
                "service": "peripheral-mcp-cloud",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
    except Exception as e:
        duration_ms = int((time.time() - start) * 1000)
        client_id = _get_client_id(request)
        _log_usage("health_check", None, client_id, "error", duration_ms)
        return JSONResponse(
            {
                "status": "unhealthy",
                "error": str(e),
                "service": "peripheral-mcp-cloud",
            },
            status_code=503,
        )


# --- Tools ---


@mcp.tool()
def health_check() -> dict[str, Any]:
    """Check database connectivity and service health."""
    start = time.time()
    try:
        result = supabase.table("news_item").select("id").limit(1).execute()
        duration_ms = int((time.time() - start) * 1000)
        _log_usage("health_check", None, None, "ok", duration_ms)
        return {
            "status": "healthy",
            "service": "peripheral-mcp-cloud",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        duration_ms = int((time.time() - start) * 1000)
        _log_usage("health_check", None, None, "error", duration_ms)
        return {
            "status": "error",
            "error": str(e),
        }


@mcp.tool()
def get_latest_briefing(
    hours: int = 24,
    region: Optional[str] = None,
) -> dict[str, Any]:
    """Get latest intelligence briefing for specified timeframe.

    Args:
        hours: Hours to look back (1-720). Free tier limited to 720h (30 days).
        region: Optional region filter.

    Returns:
        Dictionary with articles, source count, and metadata.
    """
    start = time.time()
    params = {"hours": hours, "region": region}

    try:
        hours, gating_msg = _enforce_free_tier(hours)
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

        response = {
            "timeframe": f"{hours}h",
            "count": len(articles),
            "articles": articles[:20],
            "sources_active": len(sources),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

        if gating_msg:
            response["gating_message"] = gating_msg

        duration_ms = int((time.time() - start) * 1000)
        _log_usage("get_latest_briefing", params, None, "ok", duration_ms)

        return response
    except Exception as e:
        duration_ms = int((time.time() - start) * 1000)
        _log_usage("get_latest_briefing", params, None, "error", duration_ms)
        logger.exception("get_latest_briefing failed")
        return {"status": "error", "error": str(e)}


@mcp.tool()
def get_military_signals(
    region: str,
    hours: int = 24,
    signal_type: Optional[str] = None,
) -> dict[str, Any]:
    """Get military signals for a specific region.

    Args:
        region: Target region name.
        hours: Hours to look back (1-720). Free tier limited to 720h (30 days).
        signal_type: Optional filter by signal type.

    Returns:
        Dictionary with signals, breakdown by type, and metadata.
    """
    start = time.time()
    params = {"region": region, "hours": hours, "signal_type": signal_type}

    try:
        hours, gating_msg = _enforce_free_tier(hours)
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

        response = {
            "region": actual_region,
            "timeframe": f"{hours}h",
            "count": len(signals),
            "signals": signals[:50],
            "breakdown": by_type,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

        if gating_msg:
            response["gating_message"] = gating_msg

        duration_ms = int((time.time() - start) * 1000)
        _log_usage("get_military_signals", params, None, "ok", duration_ms)

        return response
    except Exception as e:
        duration_ms = int((time.time() - start) * 1000)
        _log_usage("get_military_signals", params, None, "error", duration_ms)
        logger.exception("get_military_signals failed")
        return {"status": "error", "error": str(e)}


@mcp.tool()
def get_trending_stories(
    hours: int = 24,
    limit: int = 10,
) -> dict[str, Any]:
    """Get trending stories by article count.

    Args:
        hours: Hours to look back (1-720). Free tier limited to 720h (30 days).
        limit: Max results (1-50).

    Returns:
        Dictionary with trending stories and metadata.
    """
    start = time.time()
    params = {"hours": hours, "limit": limit}

    try:
        hours, gating_msg = _enforce_free_tier(hours)

        # Try RPC first, fallback to simple query
        try:
            result = supabase.rpc(
                "get_trending_stories",
                {"hours_ago": hours, "max_results": limit},
            ).execute()
        except Exception:
            # Fallback: simple query ordered by created
            cutoff = _cutoff_iso(hours)
            result = (
                supabase.table("story")
                .select("id, title, summary, created")
                .gte("created", cutoff)
                .order("created", desc=True)
                .limit(limit)
                .execute()
            )

        response = {
            "timeframe": f"{hours}h",
            "count": len(result.data),
            "stories": result.data,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

        if gating_msg:
            response["gating_message"] = gating_msg

        duration_ms = int((time.time() - start) * 1000)
        _log_usage("get_trending_stories", params, None, "ok", duration_ms)

        return response
    except Exception as e:
        duration_ms = int((time.time() - start) * 1000)
        _log_usage("get_trending_stories", params, None, "error", duration_ms)
        logger.exception("get_trending_stories failed")
        return {"status": "error", "error": str(e)}


@mcp.tool()
def search_stories(
    query: str,
    hours: int = 168,
    limit: int = 20,
) -> dict[str, Any]:
    """Search stories by keyword/topic.

    Args:
        query: Search term (2-200 chars).
        hours: Hours to look back (1-720). Free tier limited to 720h (30 days).
        limit: Max results (1-50).

    Returns:
        Dictionary with matching stories and metadata.
    """
    start = time.time()
    params = {"query": query, "hours": hours, "limit": limit}

    try:
        hours, gating_msg = _enforce_free_tier(hours)
        cutoff = _cutoff_iso(hours)

        result = (
            supabase.table("story")
            .select("id, title, summary, description, topic_keywords, created, updated, source_count")
            .or_(f"title.ilike.%{query}%,summary.ilike.%{query}%")
            .gte("created", cutoff)
            .order("created", desc=True)
            .limit(limit)
            .execute()
        )

        stories = [format_story(s) for s in result.data]

        response = {
            "query": query,
            "timeframe": f"{hours}h",
            "count": len(stories),
            "stories": stories,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

        if gating_msg:
            response["gating_message"] = gating_msg

        duration_ms = int((time.time() - start) * 1000)
        _log_usage("search_stories", params, None, "ok", duration_ms)

        return response
    except Exception as e:
        duration_ms = int((time.time() - start) * 1000)
        _log_usage("search_stories", params, None, "error", duration_ms)
        logger.exception("search_stories failed")
        return {"status": "error", "error": str(e)}


@mcp.tool()
def get_story_details(story_id: str) -> dict[str, Any]:
    """Get full story details with linked articles and entities.

    Args:
        story_id: Story UUID.

    Returns:
        Dictionary with story, articles, and entities (persons, orgs, locations).
    """
    start = time.time()
    params = {"story_id": story_id}

    try:
        # Get story
        story_result = (
            supabase.table("story")
            .select("*")
            .eq("id", story_id)
            .execute()
        )

        if not story_result.data:
            duration_ms = int((time.time() - start) * 1000)
            _log_usage("get_story_details", params, None, "not_found", duration_ms)
            return {"status": "error", "error": f"Story {story_id} not found"}

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

        response = {
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

        duration_ms = int((time.time() - start) * 1000)
        _log_usage("get_story_details", params, None, "ok", duration_ms)

        return response
    except Exception as e:
        duration_ms = int((time.time() - start) * 1000)
        _log_usage("get_story_details", params, None, "error", duration_ms)
        logger.exception("get_story_details failed")
        return {"status": "error", "error": str(e)}


@mcp.tool()
def search_entities(
    name: str,
    entity_type: str = "all",
    limit: int = 20,
) -> dict[str, Any]:
    """Search entities across person, organisation, location, and country tables.

    Args:
        name: Entity name to search (2-200 chars).
        entity_type: One of: person, organisation, location, country, all.
        limit: Max results (1-50).

    Returns:
        Dictionary with matching entities sorted by relevance.
    """
    start = time.time()
    params = {"name": name, "entity_type": entity_type, "limit": limit}

    try:
        valid_types = {"person", "organisation", "location", "country", "all"}
        if entity_type not in valid_types:
            duration_ms = int((time.time() - start) * 1000)
            _log_usage("search_entities", params, None, "invalid_type", duration_ms)
            return {
                "status": "error",
                "error": f"Invalid entity type '{entity_type}'. Must be one of: {', '.join(sorted(valid_types))}",
            }

        results = []
        search_types = [entity_type] if entity_type != "all" else ["person", "organisation", "location", "country"]

        for etype in search_types:
            table = f"entity_{etype}"

            if etype == "person":
                select = "id, name, role, created"
            elif etype == "organisation":
                select = "id, name, org_type, created"
            elif etype == "location":
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
                entity["entity_type"] = etype
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

        response = {
            "query": name,
            "type_filter": entity_type,
            "count": len(results[:limit]),
            "entities": results[:limit],
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

        duration_ms = int((time.time() - start) * 1000)
        _log_usage("search_entities", params, None, "ok", duration_ms)

        return response
    except Exception as e:
        duration_ms = int((time.time() - start) * 1000)
        _log_usage("search_entities", params, None, "error", duration_ms)
        logger.exception("search_entities failed")
        return {"status": "error", "error": str(e)}


@mcp.tool()
def get_entity_context(
    entity_id: str,
    entity_type: str,
    hours: int = 168,
) -> dict[str, Any]:
    """Get articles and stories mentioning a specific entity.

    Args:
        entity_id: Entity UUID.
        entity_type: One of: person, organisation, location, country.
        hours: Hours to look back (1-720). Free tier limited to 720h (30 days).

    Returns:
        Dictionary with articles, stories, and entity metadata.
    """
    start = time.time()
    params = {"entity_id": entity_id, "entity_type": entity_type, "hours": hours}

    try:
        valid_types = {"person", "organisation", "location", "country"}
        if entity_type not in valid_types:
            duration_ms = int((time.time() - start) * 1000)
            _log_usage("get_entity_context", params, None, "invalid_type", duration_ms)
            return {
                "status": "error",
                "error": f"Invalid entity type '{entity_type}'. Must be one of: {', '.join(sorted(valid_types))}",
            }

        hours, gating_msg = _enforce_free_tier(hours)
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
            duration_ms = int((time.time() - start) * 1000)
            _log_usage("get_entity_context", params, None, "not_found", duration_ms)
            return {
                "status": "error",
                "error": f"{entity_type} with id {entity_id} not found",
            }

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
                articles.append(
                    {
                        "id": ni["id"],
                        "title": ni["title"],
                        "published": ni["published"],
                        "link": ni.get("link"),
                        "sentiment": ni.get("sentiment_category"),
                    }
                )

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
                stories.append(
                    {
                        "id": s["id"],
                        "title": s["title"],
                        "summary": s.get("summary"),
                        "created": s["created"],
                        "rank": row.get("rank"),
                    }
                )

        stories.sort(key=lambda s: s.get("created", ""), reverse=True)

        response = {
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

        if gating_msg:
            response["gating_message"] = gating_msg

        duration_ms = int((time.time() - start) * 1000)
        _log_usage("get_entity_context", params, None, "ok", duration_ms)

        return response
    except Exception as e:
        duration_ms = int((time.time() - start) * 1000)
        _log_usage("get_entity_context", params, None, "error", duration_ms)
        logger.exception("get_entity_context failed")
        return {"status": "error", "error": str(e)}


@mcp.tool()
def search_articles(
    query: str,
    hours: int = 168,
    limit: int = 50,
) -> dict[str, Any]:
    """Search news articles by title and content.

    Args:
        query: Search term (2-200 chars).
        hours: Hours to look back (1-720). Free tier limited to 720h (30 days).
        limit: Max results (1-100).

    Returns:
        Dictionary with matching articles and metadata.
    """
    start = time.time()
    params = {"query": query, "hours": hours, "limit": limit}

    try:
        hours, gating_msg = _enforce_free_tier(hours)
        cutoff = _cutoff_iso(hours)

        result = (
            supabase.table("news_item")
            .select("id, title, content, published, author, link, sentiment_category, story_id")
            .or_(f"title.ilike.%{query}%,content.ilike.%{query}%")
            .gte("published", cutoff)
            .order("published", desc=True)
            .limit(limit)
            .execute()
        )

        articles = [format_article(a) for a in result.data]

        response = {
            "query": query,
            "timeframe": f"{hours}h",
            "count": len(articles),
            "articles": articles,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

        if gating_msg:
            response["gating_message"] = gating_msg

        duration_ms = int((time.time() - start) * 1000)
        _log_usage("search_articles", params, None, "ok", duration_ms)

        return response
    except Exception as e:
        duration_ms = int((time.time() - start) * 1000)
        _log_usage("search_articles", params, None, "error", duration_ms)
        logger.exception("search_articles failed")
        return {"status": "error", "error": str(e)}


@mcp.tool()
def get_signal_timeline(
    region: str,
    hours: int = 168,
) -> dict[str, Any]:
    """Get signals grouped by hour for timeline visualization and escalation tracking.

    Args:
        region: Region name (e.g. Харківська, Київська, or partial match).
        hours: Hours to look back (1-720). Free tier limited to 720h (30 days).

    Returns:
        Dictionary with hourly signal counts, breakdowns by type/weapon, and timeline.
    """
    start = time.time()
    params = {"region": region, "hours": hours}

    try:
        hours, gating_msg = _enforce_free_tier(hours)
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
            timeline.append(
                {
                    "hour": hour_key,
                    "count": bucket["count"],
                    "by_type": dict(bucket["by_type"]),
                    "by_weapon": dict(bucket["by_weapon"]),
                }
            )

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

        response = {
            "region": actual_region,
            "timeframe": f"{hours}h",
            "total_signals": total,
            "hours_with_activity": len(timeline),
            "type_totals": dict(type_totals),
            "weapon_totals": dict(weapon_totals),
            "timeline": timeline,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

        if gating_msg:
            response["gating_message"] = gating_msg

        duration_ms = int((time.time() - start) * 1000)
        _log_usage("get_signal_timeline", params, None, "ok", duration_ms)

        return response
    except Exception as e:
        duration_ms = int((time.time() - start) * 1000)
        _log_usage("get_signal_timeline", params, None, "error", duration_ms)
        logger.exception("get_signal_timeline failed")
        return {"status": "error", "error": str(e)}


# --- ASGI Export ---

app = mcp.http_app(path="/mcp", transport="streamable-http")


# --- Main ---


def main():
    """Run the MCP server over HTTP transport."""
    mcp.run(transport="http")


if __name__ == "__main__":
    main()
