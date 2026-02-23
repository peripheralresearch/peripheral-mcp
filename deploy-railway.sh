#!/bin/bash
# Quick Railway Deployment Script for Peripheral MCP
# This makes the API publicly accessible

set -e

echo "🚀 Deploying Peripheral MCP to Railway"
echo "========================================"
echo ""

# Check Railway CLI
if ! command -v railway &> /dev/null; then
    echo "📦 Installing Railway CLI..."
    npm install -g @railway/cli
fi

# Load credentials
if [ -f "/home/atlas/GM/.auth/credentials.env" ]; then
    source /home/atlas/GM/.auth/credentials.env
else
    echo "❌ Credentials file not found: /home/atlas/GM/.auth/credentials.env"
    exit 1
fi

# Login to Railway
echo "🔐 Logging in to Railway..."
echo "(This will open a browser window for authentication)"
railway login

# Initialize project (if not already)
if [ ! -f "railway.toml" ]; then
    echo "🎬 Initializing Railway project..."
    railway init
fi

# Set environment variables
echo "🔧 Setting environment variables..."
railway variables set SUPABASE_URL="$SUPABASE_URL"
railway variables set SUPABASE_KEY="$SUPABASE_SERVICE_KEY"

# Deploy
echo "🚢 Deploying to Railway..."
railway up

# Get the public URL
echo ""
echo "✅ Deployment complete!"
echo ""
echo "Getting public URL..."
PUBLIC_URL=$(railway domain 2>/dev/null || echo "Run 'railway domain' to get your public URL")

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Peripheral MCP is now PUBLIC!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "API URL: $PUBLIC_URL"
echo ""
echo "Test it:"
echo "  curl $PUBLIC_URL/health"
echo "  curl $PUBLIC_URL/briefing/latest?hours=24"
echo ""
echo "Share MCP access:"
echo "  Users can add this to their MCP client config:"
echo "  PERIPHERAL_API_URL=$PUBLIC_URL"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
