"""
Prefect flow for generating and publishing intelligence briefings.
"""
from prefect import flow, task
from supabase import create_client
from datetime import datetime, timedelta
import os
from typing import Dict, Any, Optional


@task
def fetch_recent_articles(hours: int = 24) -> list[Dict[str, Any]]:
    """Fetch recent articles from Supabase"""
    supabase = create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_KEY")
    )
    
    cutoff = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
    
    result = supabase.table("news_item")\
        .select("*, story(id, title, summary)")\
        .gte("published", cutoff)\
        .order("published", desc=True)\
        .limit(100)\
        .execute()
    
    return result.data


@task
def fetch_recent_signals(hours: int = 24, region: Optional[str] = None) -> list[Dict[str, Any]]:
    """Fetch recent military signals from Supabase"""
    supabase = create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_KEY")
    )
    
    cutoff = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
    
    query = supabase.table("signal")\
        .select("*")\
        .gte("created_at", cutoff)\
        .order("created_at", desc=True)\
        .limit(200)
    
    if region:
        query = query.eq("target_region", region.upper())
    
    result = query.execute()
    return result.data


@task
def format_briefing(articles: list, signals: list) -> str:
    """Format briefing as markdown"""
    briefing_lines = [
        "# **THE PERIPHERAL**",
        f"Intelligence Briefing",
        f"{datetime.utcnow().strftime('%A, %d %B %Y | %H:%M UTC')}",
        "",
        "─" * 60,
        "",
        f"**ARTICLES ANALYZED:** {len(articles)}",
        f"**SIGNALS TRACKED:** {len(signals)}",
        "",
    ]
    
    # Top stories
    if articles:
        briefing_lines.append("## **TOP STORIES (24H)**")
        briefing_lines.append("")
        
        # Group by story
        stories = {}
        for article in articles[:20]:
            story_id = article.get("story", {}).get("id") if article.get("story") else None
            if story_id:
                if story_id not in stories:
                    stories[story_id] = {
                        "title": article.get("story", {}).get("title"),
                        "count": 0
                    }
                stories[story_id]["count"] += 1
        
        # Show top 5 stories
        top_stories = sorted(stories.items(), key=lambda x: x[1]["count"], reverse=True)[:5]
        for story_id, data in top_stories:
            briefing_lines.append(f"• **{data['title']}** ({data['count']} articles)")
        
        briefing_lines.append("")
    
    # Signals breakdown
    if signals:
        briefing_lines.append("## **MILITARY SIGNALS**")
        briefing_lines.append("")
        
        by_type = {}
        by_region = {}
        for signal in signals:
            stype = signal.get("signal_type", "unknown")
            region = signal.get("target_region", "unknown")
            by_type[stype] = by_type.get(stype, 0) + 1
            by_region[region] = by_region.get(region, 0) + 1
        
        briefing_lines.append("**By Type:**")
        for stype, count in sorted(by_type.items(), key=lambda x: x[1], reverse=True):
            briefing_lines.append(f"• {stype}: {count} events")
        
        briefing_lines.append("")
        briefing_lines.append("**Active Regions:**")
        for region, count in sorted(by_region.items(), key=lambda x: x[1], reverse=True)[:10]:
            briefing_lines.append(f"• {region}: {count} signals")
        
        briefing_lines.append("")
    
    briefing_lines.extend([
        "─" * 60,
        "",
        f"Generated: {datetime.utcnow().isoformat()}",
        f"Source: The Peripheral OSINT Platform"
    ])
    
    return "\n".join(briefing_lines)


@flow(name="generate_daily_briefing", log_prints=True)
def generate_daily_briefing(hours: int = 24, region: Optional[str] = None):
    """
    Main flow: Generate intelligence briefing from Peripheral data.
    
    Args:
        hours: Hours to look back (default: 24)
        region: Optional region filter
    """
    print(f"📰 Generating briefing for last {hours}h...")
    
    # Fetch data
    articles = fetch_recent_articles(hours=hours)
    signals = fetch_recent_signals(hours=hours, region=region)
    
    # Format briefing
    briefing = format_briefing(articles, signals)
    
    print(f"✅ Briefing generated: {len(articles)} articles, {len(signals)} signals")
    print("\n" + briefing)
    
    return briefing


if __name__ == "__main__":
    # Test run
    generate_daily_briefing()
