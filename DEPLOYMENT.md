# Peripheral MCP - Deployment Guide

## ✅ Current Status (Feb 23, 2026 - 17:12 AEDT)

**Repository:** https://github.com/peripheralresearch/peripheral-mcp  
**Org:** peripheralresearch  
**API Testing:** ✓ All endpoints working locally

### Test Results

```
Health Check: ✓ Connected to Supabase
Briefing (6h): 50 articles, 14 sources active
Database: 95K+ articles, 336K+ signals accessible
```

---

## Quick Deploy Options

### Option 1: Railway (Recommended - Free Tier)

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Deploy from repo root
cd /home/atlas/GM/peripheral-mcp
railway init
railway up

# Set environment variables in Railway dashboard:
# SUPABASE_URL=https://zghbrwbfdoalgzpcnbcm.supabase.co
# SUPABASE_KEY=eyJhbGci... (from .env)
```

**URL will be:** `https://peripheral-mcp.railway.app` (or similar)

### Option 2: Render (Auto-deploy from GitHub)

1. Visit https://render.com
2. New → Web Service
3. Connect `peripheralresearch/peripheral-mcp` repo
4. Build Command: `uv sync`
5. Start Command: `uv run uvicorn src.api.main:app --host 0.0.0.0 --port $PORT`
6. Add environment variables (SUPABASE_URL, SUPABASE_KEY)

**Auto-deploys** on every push to master.

### Option 3: Fly.io (Edge Deployment)

```bash
# Install flyctl
curl -L https://fly.io/install.sh | sh

# Login and launch
cd /home/atlas/GM/peripheral-mcp
fly launch
fly secrets set SUPABASE_URL=... SUPABASE_KEY=...
fly deploy
```

---

## Prefect Cloud Setup

**Account:** daniel@theperipheral.org

### Manual Setup (if CLI fails)

1. Visit https://app.prefect.cloud
2. Sign up with daniel@theperipheral.org
3. Create new workspace
4. Connect GitHub: peripheralresearch/peripheral-mcp
5. Deploy flow:
   ```bash
   cd /home/atlas/GM/peripheral-mcp
   uvx prefect-cloud deploy src/flows/briefing.py:generate_daily_briefing \
       --from peripheralresearch/peripheral-mcp \
       --name daily-briefing \
       --secret SUPABASE_URL="$SUPABASE_URL" \
       --secret SUPABASE_KEY="$SUPABASE_KEY"
   ```

6. Schedule: Daily at 9am Sydney time (`0 23 * * *` UTC)

---

## MCP Integration (For Your Friends)

Once API is deployed (e.g., https://peripheral-mcp.railway.app):

### Claude Desktop Config

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "peripheral": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/peripheralresearch/peripheral-mcp",
        "peripheral-mcp"
      ],
      "env": {
        "PERIPHERAL_API_URL": "https://peripheral-mcp.railway.app"
      }
    }
  }
}
```

### Test Prompts

Once configured, users can ask Claude:

- "What's happening in Ukraine today?" (uses `get_latest_briefing`)
- "Show me Kyiv military signals in the last 12 hours" (uses `get_military_signals`)
- "Get the top 5 trending stories" (uses `get_trending_stories`)
- "Is The Peripheral API healthy?" (uses `health_check`)

---

## Monitoring

### API Endpoints (Public)

- `GET https://peripheral-mcp.railway.app/health`
- `GET https://peripheral-mcp.railway.app/briefing/latest?hours=24`
- `GET https://peripheral-mcp.railway.app/signals/region/Kyiv?hours=12`
- `GET https://peripheral-mcp.railway.app/stories/trending?limit=10`

### Prefect Dashboard

- https://app.prefect.cloud
- View flow runs, logs, and schedules
- Monitor daily briefing generation

---

## Current Configuration

**Database:** Supabase (zghbrwbfdoalgzpcnbcm.supabase.co)  
**Tables:** news_item (95K+), signal (336K+), story (74K+)  
**Authentication:** Service role key (full read access)  
**Rate Limiting:** None (currently public, add later if needed)  
**Caching:** None (can add Cloudflare Workers layer)

---

## Security Notes

- API is read-only (no POST/PUT/DELETE endpoints)
- Content truncated to 500 chars per article
- Internal fields hidden (no raw IDs exposed)
- Service role key stored as secret in Prefect/Railway
- Consider adding rate limiting if traffic spikes

---

## Next Actions

**For Dan:**
1. Choose deployment platform (Railway recommended)
2. Deploy API server (10 min)
3. Note the public URL
4. Update MCP config with API URL
5. Share config with friends

**For Atlas:**
1. Fix FastMCP dependency issue (add `mcp` package)
2. Test MCP tools with deployed API
3. Create example queries documentation
4. Set up monitoring/alerts

---

**Last Updated:** 2026-02-23 17:12 AEDT  
**Status:** Ready for deployment  
**Repository:** https://github.com/peripheralresearch/peripheral-mcp
