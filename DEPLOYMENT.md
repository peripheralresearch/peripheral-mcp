# Peripheral MCP - Deployment Guide

## Current Status

- ✅ **Prefect Cloud:** Daily briefing flow deployed (runs 9am Sydney time)
- ⏳ **FastAPI Server:** Running locally, needs public deployment
- ⏳ **MCP Server:** Local only (by design - MCP uses stdio protocol)

## Public API Deployment Options

### Option 1: Railway (Recommended)

**Fastest deployment path with free tier.**

1. Install Railway CLI:
```bash
npm install -g @railway/cli
```

2. Login and initialize:
```bash
railway login
cd /home/atlas/GM/sentinel/peripheral-mcp
railway init
```

3. Set environment variables in Railway dashboard:
```
SUPABASE_URL=https://zghbrwbfdoalgzpcnbcm.supabase.co
SUPABASE_KEY=<service-key-from-credentials.env>
```

4. Deploy:
```bash
railway up
```

5. Get public URL:
```bash
railway domain
```

**Result:** API available at `https://your-app.railway.app`

---

### Option 2: Render

1. Create `render.yaml` (already in repo)

2. Push to GitHub

3. Connect repository to Render:
   - Go to https://render.com
   - New → Web Service
   - Connect GitHub repo: `peripheralresearch/peripheral-mcp`
   - Render auto-detects render.yaml

4. Add environment variables in Render dashboard:
```
SUPABASE_URL=https://zghbrwbfdoalgzpcnbcm.supabase.co
SUPABASE_KEY=<service-key>
```

5. Deploy

**Result:** API available at `https://peripheral-mcp.onrender.com`

---

### Option 3: Fly.io

1. Install flyctl:
```bash
curl -L https://fly.io/install.sh | sh
```

2. Login and launch:
```bash
cd /home/atlas/GM/sentinel/peripheral-mcp
fly launch
```

3. Set secrets:
```bash
source /home/atlas/GM/.auth/credentials.env
fly secrets set SUPABASE_URL=$SUPABASE_URL SUPABASE_KEY=$SUPABASE_SERVICE_KEY
```

4. Deploy:
```bash
fly deploy
```

**Result:** API available at `https://peripheral-mcp.fly.dev`

---

### Option 4: Docker (Self-Hosted)

1. Build image:
```bash
docker build -t peripheral-api .
```

2. Run container:
```bash
docker run -d \
  -p 8080:8080 \
  -e SUPABASE_URL=https://zghbrwbfdoalgzpcnbcm.supabase.co \
  -e SUPABASE_KEY=<service-key> \
  --name peripheral-api \
  peripheral-api
```

3. Expose publicly (nginx reverse proxy, Cloudflare Tunnel, etc.)

---

## After Deployment

### Update MCP Configuration

Once API is public, update `~/.config/mcp/peripheral-mcp.json`:

```json
{
  "mcpServers": {
    "peripheral": {
      "command": "uv",
      "args": [
        "--directory",
        "/home/atlas/GM/sentinel/peripheral-mcp",
        "run",
        "peripheral-mcp"
      ],
      "env": {
        "PERIPHERAL_API_URL": "https://your-deployed-api.railway.app",
        "SUPABASE_URL": "https://zghbrwbfdoalgzpcnbcm.supabase.co",
        "SUPABASE_KEY": "${SUPABASE_SERVICE_KEY}"
      }
    }
  }
}
```

### Test Public API

```bash
# Health check
curl https://your-deployed-api.railway.app/health

# Latest briefing
curl https://your-deployed-api.railway.app/briefing/latest?hours=24

# Signals
curl https://your-deployed-api.railway.app/signals/region/Ukraine

# Trending stories
curl https://your-deployed-api.railway.app/stories/trending?hours=24&limit=10
```

### Share MCP Access

Users can now use The Peripheral MCP by:

1. Installing MCP client (Claude Desktop, etc.)

2. Adding server configuration:
```json
{
  "mcpServers": {
    "peripheral": {
      "command": "npx",
      "args": ["-y", "peripheral-mcp-client"],
      "env": {
        "PERIPHERAL_API_URL": "https://your-deployed-api.railway.app"
      }
    }
  }
}
```

3. MCP tools become available in their client

---

## Architecture After Deployment

```
┌─────────────────────────────────────────────────────────────────┐
│                          Users                                  │
│         (Claude Desktop, MCP Clients Worldwide)                 │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       │ MCP Protocol (stdio)
                       │
          ┌────────────▼────────────┐
          │   MCP Server (local)    │
          │   - get_latest_briefing │
          │   - get_military_signals│
          │   - get_trending_stories│
          │   - health_check        │
          └────────────┬────────────┘
                       │
                       │ HTTP/S
                       │
┌──────────────────────▼──────────────────────────────────────────┐
│           FastAPI Server (PUBLIC - Railway/Render)              │
│                https://peripheral-api.railway.app               │
│                                                                 │
│  Endpoints:                                                     │
│  - GET /health                                                  │
│  - GET /briefing/latest?hours=24&region=ukraine                │
│  - GET /signals/region/{region}?hours=24                       │
│  - GET /stories/trending?hours=24&limit=10                     │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       │ PostgreSQL REST API
                       │
┌──────────────────────▼──────────────────────────────────────────┐
│                  Supabase (Cloud Database)                      │
│           https://zghbrwbfdoalgzpcnbcm.supabase.co             │
│                                                                 │
│  Data:                                                          │
│  - 80,856 stories                                               │
│  - 116,302 news items                                           │
│  - 338,119 signals                                              │
│  - 32,508 persons                                               │
│  - 23,021 locations                                             │
│  - 26,974 organisations                                         │
└─────────────────────────────────────────────────────────────────┘
```

---

## Cost Estimate

### Railway Free Tier
- $0/month
- 500 hours/month execution time
- Sleeps after 30 min inactivity
- Wakes on request (~1-2 seconds)

### Render Free Tier
- $0/month
- Always-on for web services
- 750 hours/month
- Slower cold starts

### Fly.io Free Tier
- $0/month (with credit card)
- 3 shared-cpu VMs
- Always-on
- Global edge deployment

### Recommended: Start with Railway
- Free
- Fast deployment
- Easy to upgrade later
- Auto HTTPS
- Good performance

---

## Security Considerations

### Current Setup (Safe)
- API is read-only (no mutations)
- Supabase Row-Level Security enabled
- Service key only for backend (not exposed to clients)
- CORS enabled for public access
- No authentication required (public data)

### Future Enhancements (Optional)
- Rate limiting per IP
- API key authentication for heavy users
- Webhook notifications for new data
- GraphQL endpoint for complex queries

---

## Next Steps

1. Choose deployment platform (recommend Railway)
2. Deploy FastAPI server
3. Update MCP configuration with public URL
4. Test public API endpoints
5. Share MCP access with users
6. Monitor usage and costs

---

**Status:** Ready to deploy  
**Estimated time:** 10-15 minutes (Railway)  
**Cost:** $0 (free tier)
