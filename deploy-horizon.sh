#!/bin/bash
# Deploy Peripheral MCP to Prefect Horizon
# Horizon is the official platform for hosting FastMCP servers

set -e

echo "🚀 Deploying Peripheral MCP to Prefect Horizon"
echo "=============================================="
echo ""
echo "Prefect Horizon (https://horizon.prefect.io) is the official"
echo "platform for deploying FastMCP servers publicly."
echo ""

# Load credentials
if [ -f "/home/atlas/GM/.auth/credentials.env" ]; then
    source /home/atlas/GM/.auth/credentials.env
else
    echo "❌ Credentials file not found"
    exit 1
fi

# Check/install dependencies
echo "📦 Syncing dependencies..."
cd "$(dirname "$0")"
uv sync

# Login to Prefect Cloud
echo "🔐 Logging in to Prefect Cloud..."
uvx prefect-cloud whoami 2>/dev/null || uvx prefect-cloud login

echo "✅ Authenticated"
echo ""

# Deploy the Horizon-optimized MCP server
echo "🌐 Deploying MCP server to Horizon..."
echo ""
echo "Server: The Peripheral"
echo "File: src/mcp/horizon_server.py:main"
echo "Tools: 4 (briefing, signals, stories, health)"
echo ""

# Deploy to Horizon
# Note: Horizon deployment syntax may differ from regular Prefect deployments
# This deploys the MCP server itself, not a flow

echo "Deploying..."
uvx prefect-cloud deploy src/mcp/horizon_server.py:main \
    --name peripheral-mcp \
    --secret SUPABASE_URL="$SUPABASE_URL" \
    --secret SUPABASE_KEY="$SUPABASE_SERVICE_KEY" \
    --with-requirements requirements.txt

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Peripheral MCP deployed to Horizon!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "View deployment: https://app.prefect.cloud"
echo "Horizon dashboard: https://horizon.prefect.io"
echo ""
echo "MCP Tools Available:"
echo "  - get_latest_briefing(hours, region)"
echo "  - get_military_signals(region, hours)"
echo "  - get_trending_stories(hours, limit)"
echo "  - health_check()"
echo ""
echo "Users can connect their MCP clients to your Horizon endpoint."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
