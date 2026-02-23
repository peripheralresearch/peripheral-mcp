# 🚨 Peripheral MCP - Deployment Bottleneck

**Date:** February 23, 2026 21:55 AEDT  
**Status:** 95% Complete - ONE BLOCKER REMAINING

---

## The Bottleneck

**ONLY ONE THING blocking public MCP access:**

### ❌ FastAPI Server Not Deployed Publicly

**Current state:**
- Server running on localhost:8080
- Only accessible from local machine
- MCP clients worldwide cannot reach it

**Required state:**
- Server running on public URL (e.g., https://peripheral-mcp.railway.app)
- Accessible from anywhere
- MCP clients can connect and query Peripheral data

---

## What's Already Done ✅

| Component | Status | Details |
|-----------|--------|---------|
| **FastAPI Code** | ✅ Complete | 5 endpoints, tested, working |
| **MCP Server Code** | ✅ Complete | 4 tools (briefing, signals, stories, health) |
| **Supabase Data** | ✅ Live | 338K signals, 116K news, 80K stories |
| **Prefect Cloud** | ✅ Deployed | Daily briefing scheduled 9am Sydney |
| **Testing** | ✅ Complete | All endpoints tested locally |
| **Deployment Configs** | ✅ Ready | Railway, Render, Fly.io, Docker |
| **GitHub** | ✅ Pushed | All code committed |
| **Notion** | ✅ Updated | Task updated with blocker status |

---

## The Fix (10 Minutes)

### Option 1: One-Click Railway Deployment (Recommended)

```bash
cd /home/atlas/GM/sentinel/peripheral-mcp
./deploy-railway.sh
```

**What it does:**
1. Installs Railway CLI (if needed)
2. Logs you in (browser auth)
3. Initializes Railway project
4. Sets environment variables (SUPABASE_URL, SUPABASE_KEY)
5. Deploys to Railway
6. Returns public URL

**Result:** https://peripheral-mcp.railway.app (free tier, auto HTTPS)

---

### Option 2: Manual Railway Deployment

```bash
# Install CLI
npm install -g @railway/cli

# Login (opens browser)
railway login

# Initialize
cd /home/atlas/GM/sentinel/peripheral-mcp
railway init

# Set environment variables in Railway dashboard:
# SUPABASE_URL=https://zghbrwbfdoalgzpcnbcm.supabase.co
# SUPABASE_KEY=<service-key-from-credentials.env>

# Deploy
railway up

# Get public URL
railway domain
```

---

### Option 3: Render (Browser-Based, No CLI)

1. Go to https://render.com
2. Sign in with GitHub
3. New → Web Service
4. Connect repository: `peripheralresearch/peripheral-mcp`
5. Render auto-detects `render.yaml`
6. Add environment variables:
   - `SUPABASE_URL`: https://zghbrwbfdoalgzpcnbcm.supabase.co
   - `SUPABASE_KEY`: (copy from `/home/atlas/GM/.auth/credentials.env`)
7. Click "Create Web Service"
8. Wait 5 minutes for deployment
9. Get public URL: `https://peripheral-mcp.onrender.com`

**No CLI required. All browser-based.**

---

## After Deployment

### Test Public API

```bash
# Replace URL with your deployed URL
export API_URL="https://peripheral-mcp.railway.app"

# Health check
curl $API_URL/health

# Latest briefing
curl "$API_URL/briefing/latest?hours=24" | jq .

# Signals for Ukraine
curl "$API_URL/signals/region/Ukraine?hours=24" | jq .

# Trending stories
curl "$API_URL/stories/trending?hours=24&limit=10" | jq .
```

### Share MCP Access

Once deployed, users worldwide can access The Peripheral MCP:

**MCP Client Config (Claude Desktop, etc.):**
```json
{
  "mcpServers": {
    "peripheral": {
      "command": "npx",
      "args": ["-y", "@peripheral/mcp-client"],
      "env": {
        "PERIPHERAL_API_URL": "https://peripheral-mcp.railway.app"
      }
    }
  }
}
```

**Available Tools:**
- `get_latest_briefing(hours, region)` - Intelligence briefing
- `get_military_signals(region, hours)` - Military signals by region
- `get_trending_stories(hours, limit)` - Trending stories
- `health_check()` - API status

---

## Timeline

| Task | Time | Status |
|------|------|--------|
| Code FastAPI server | 2 hours | ✅ Done |
| Code MCP server | 1 hour | ✅ Done |
| Test locally | 30 min | ✅ Done |
| Create deployment configs | 30 min | ✅ Done |
| Commit to GitHub | 5 min | ✅ Done |
| **Deploy to Railway** | **10 min** | **⏳ WAITING** |
| Test public API | 5 min | ⏳ Pending |
| Update Notion | 2 min | ✅ Done |

**Total remaining: 15 minutes**

---

## Cost

**Railway Free Tier:**
- $0/month
- 500 execution hours/month
- Auto HTTPS
- Sleeps after 30 min inactivity (wakes in 1-2 seconds)

**Render Free Tier:**
- $0/month
- Always-on
- 750 hours/month
- Auto HTTPS

**Both are FREE and more than sufficient for The Peripheral MCP.**

---

## Why This Matters

**Before deployment:**
- MCP only works on your local machine
- No one else can access Peripheral data via MCP
- Tools can't be shared

**After deployment:**
- Public URL accessible worldwide
- Anyone can add Peripheral MCP to their Claude Desktop
- Real-time access to 338K signals, 116K news items, 80K stories
- Automatic daily briefings via Prefect

---

## Decision Required

**Which deployment method do you prefer?**

1. **One-click script** (`./deploy-railway.sh`) - Automated, 10 minutes
2. **Manual Railway CLI** - More control, 10 minutes
3. **Render browser-based** - No CLI, all browser, 15 minutes

**All three result in the same outcome:** Public MCP accessible at `https://your-app.domain.com`

---

## Next Steps After Deployment

1. ✅ Test public API endpoints
2. ✅ Update MCP configuration with public URL
3. ✅ Share access with users (Dan's friends)
4. ✅ Monitor usage and costs
5. ✅ Mark Notion task as "Done"

---

**The ONLY thing between "working locally" and "public MCP" is running ONE deployment command.**

**Ready to deploy?**
