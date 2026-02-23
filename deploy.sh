#!/bin/bash
# Deployment script for Peripheral MCP Server

set -e

echo "🚀 Deploying Peripheral MCP Server to Prefect Cloud"

# Check prerequisites
command -v uvx >/dev/null 2>&1 || { echo "❌ uvx not found. Install with: curl -LsSf https://astral.sh/uv/install.sh | sh"; exit 1; }

# Login to Prefect Cloud
echo "📝 Logging in to Prefect Cloud..."
uvx prefect-cloud login

# Connect to GitHub
echo "🔗 Connecting to GitHub..."
uvx prefect-cloud github setup

# Deploy the briefing flow
echo "📦 Deploying briefing generation flow..."
uvx prefect-cloud deploy src/flows/briefing.py:generate_daily_briefing \
    --from peripheralresearch/peripheral-mcp \
    --name daily-briefing \
    --with-requirements requirements.txt \
    --secret SUPABASE_URL="$SUPABASE_URL" \
    --secret SUPABASE_KEY="$SUPABASE_KEY" \
    --parameter hours=24

# Schedule daily briefing at 9am Sydney time (midnight UTC in summer, 11pm UTC in winter)
echo "⏰ Scheduling daily briefing..."
uvx prefect-cloud schedule generate_daily_briefing/daily-briefing "0 23 * * *"

echo "✅ Deployment complete!"
echo ""
echo "View your deployment: https://app.prefect.cloud"
echo ""
echo "To run manually:"
echo "  uvx prefect-cloud run generate_daily_briefing/daily-briefing"
