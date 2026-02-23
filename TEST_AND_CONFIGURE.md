# Peripheral MCP - Test & Configuration Guide

## Setup Complete ✅

### 1. Supabase Query Tool

**Location:** `/home/atlas/GM/sentinel/scripts/supabase-query.sh`

**Usage:**
```bash
# Database statistics
./supabase-query.sh stats

# Recent stories
./supabase-query.sh stories:recent 10

# Search stories
./supabase-query.sh stories:search "Ukraine"

# Signals by region
./supabase-query.sh signals:region Ukraine 20

# Raw query
./supabase-query.sh raw 'story?select=id,title&limit=5'

# Help
./supabase-query.sh help
```

**Current Database Stats:**
```
Stories: 80,856
News Items: 116,302
Signals: 338,119
Persons: 32,508
Locations: 23,021
Organisations: 26,974
```

---

## Phase 2: Test FastAPI Server

### Start API Server

```bash
cd /home/atlas/GM/sentinel/peripheral-mcp
source /home/atlas/GM/.auth/credentials.env

# Option 1: uvicorn directly
uvicorn src.api.main:app --host 0.0.0.0 --port 8080 --reload

# Option 2: uv run
uv run uvicorn src.api.main:app --host 0.0.0.0 --port 8080
```

### Test Endpoints

```bash
# Health check
curl http://localhost:8080/health

# Root endpoint
curl http://localhost:8080/

# Latest briefing (last 24 hours)
curl http://localhost:8080/briefing/latest?hours=24

# Signals for Ukraine
curl http://localhost:8080/signals/region/Ukraine?hours=24

# Trending stories
curl http://localhost:8080/stories/trending?hours=24&limit=10
```

---

## Phase 3: Test MCP Server

### MCP Server Configuration

**File:** `~/.config/mcp/peripheral-mcp.json`

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
        "SUPABASE_URL": "https://zghbrwbfdoalgzpcnbcm.supabase.co",
        "SUPABASE_KEY": "${SUPABASE_SERVICE_KEY}",
        "PERIPHERAL_API_URL": "http://localhost:8080"
      }
    }
  }
}
```

### Fix MCP Entry Point

The `pyproject.toml` references `mcp.server:main`, but the code uses `mcp.run()`. Let's add a main() function:

```bash
cat >> src/mcp/server.py << 'EOF'


def main():
    """Entry point for uvx/mcp client"""
    mcp.run()
EOF
```

### Test MCP Server Standalone

```bash
cd /home/atlas/GM/sentinel/peripheral-mcp
source /home/atlas/GM/.auth/credentials.env

# Run MCP server
uv run peripheral-mcp
```

### Test MCP Tools

Once MCP server is running, test the tools:

**Available Tools:**
1. `get_latest_briefing(hours=24, region=None)` - Get intelligence briefing
2. `get_military_signals(region, hours=24, signal_type=None)` - Get military signals
3. `get_trending_stories(hours=24, limit=10)` - Get trending stories
4. `health_check()` - Check API health

---

## Phase 4: Integrate with OpenClaw (Atlas)

### Option A: MCP Client in OpenClaw

If OpenClaw has MCP client support, add to configuration:

```json
{
  "mcpServers": {
    "peripheral": {
      "command": "uv",
      "args": ["--directory", "/home/atlas/GM/sentinel/peripheral-mcp", "run", "peripheral-mcp"],
      "env": {
        "SUPABASE_URL": "https://zghbrwbfdoalgzpcnbcm.supabase.co",
        "SUPABASE_KEY": "[service-key-here]",
        "PERIPHERAL_API_URL": "http://localhost:8080"
      }
    }
  }
}
```

### Option B: Direct API Access

Use Supabase query tool or curl commands directly:

```bash
# In OpenClaw context
/home/atlas/GM/sentinel/scripts/supabase-query.sh stories:recent 5

# Or raw queries
source /home/atlas/GM/.auth/credentials.env
curl -s "$SUPABASE_URL/rest/v1/story?select=id,title&limit=5" \
  -H "apikey: $SUPABASE_SERVICE_KEY" \
  -H "Authorization: Bearer $SUPABASE_SERVICE_KEY" | jq .
```

---

## Testing Checklist

### ✅ Phase 1: Supabase Query Tool
- [x] Created `/home/atlas/GM/sentinel/scripts/supabase-query.sh`
- [x] Tested stats command (80K+ stories, 116K+ news items)
- [x] Tested stories:recent (works)
- [x] Tested signals:recent (works)
- [ ] Test stories:search
- [ ] Test signals:region
- [ ] Test entities commands

### ⏳ Phase 2: FastAPI Server
- [ ] Start API server on port 8080
- [ ] Test /health endpoint
- [ ] Test /briefing/latest
- [ ] Test /signals/region/Ukraine
- [ ] Test /stories/trending

### ⏳ Phase 3: MCP Server
- [ ] Fix mcp.server:main entry point
- [ ] Test MCP server startup
- [ ] Test get_latest_briefing tool
- [ ] Test get_military_signals tool
- [ ] Test get_trending_stories tool
- [ ] Test health_check tool

### ⏳ Phase 4: OpenClaw Integration
- [ ] Determine MCP support in OpenClaw
- [ ] If yes: Add MCP server config
- [ ] If no: Use direct API/query tool access
- [ ] Test querying from Atlas context

---

## Next Steps

1. **Start FastAPI Server** (terminal 1):
   ```bash
   cd /home/atlas/GM/sentinel/peripheral-mcp
   source /home/atlas/GM/.auth/credentials.env
   uv run uvicorn src.api.main:app --host 0.0.0.0 --port 8080 --reload
   ```

2. **Test API Endpoints** (terminal 2):
   ```bash
   curl http://localhost:8080/health
   curl http://localhost:8080/briefing/latest?hours=24 | jq .
   ```

3. **Fix MCP Entry Point**:
   ```bash
   # Add main() function to src/mcp/server.py
   ```

4. **Test MCP Server**:
   ```bash
   cd /home/atlas/GM/sentinel/peripheral-mcp
   source /home/atlas/GM/.auth/credentials.env
   export PERIPHERAL_API_URL=http://localhost:8080
   uv run peripheral-mcp
   ```

5. **Configure OpenClaw**:
   - Determine if OpenClaw supports MCP clients
   - If yes: Add peripheral-mcp to MCP servers config
   - If no: Use Supabase query tool for direct access

---

## Troubleshooting

**Issue: API server fails to start**
- Check credentials: `source /home/atlas/GM/.auth/credentials.env`
- Verify Supabase URL/key are set: `echo $SUPABASE_URL`
- Check port 8080 is free: `lsof -i :8080`

**Issue: MCP server fails to start**
- Fix entry point: Add `main()` function to `src/mcp/server.py`
- Check API server is running first
- Set PERIPHERAL_API_URL: `export PERIPHERAL_API_URL=http://localhost:8080`

**Issue: Queries timeout**
- Large tables (news_item: 116K rows) may timeout on COUNT queries
- Use Content-Range header method (already implemented in supabase-query.sh)
- Consider pagination for large result sets

---

## Current Status

✅ **Complete:**
- Supabase query tool created and tested
- Database stats confirmed (80K+ stories, 338K+ signals)
- MCP client config created
- Prefect Cloud deployment successful

⏳ **Next:**
- Start and test FastAPI server
- Fix MCP entry point
- Test MCP tools
- Integrate with OpenClaw/Atlas

---

**Ready to proceed with FastAPI server startup and testing?**
