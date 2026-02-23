# Secure Peripheral MCP Deployment

**CRITICAL:** Do NOT use service role key in public MCP deployment!

## Security Issue

**Service Role Key (`SUPABASE_SERVICE_KEY`):**
- Bypasses Row-Level Security
- Full database read/write access
- Can INSERT, UPDATE, DELETE anything
- **If compromised = database breach**

**Anon Key (`SUPABASE_ANON_KEY`):**
- Respects Row-Level Security
- Read-only by default
- Safe for public exposure
- **If compromised = limited read access only**

---

## Step-by-Step Secure Deployment

### Step 1: Get Anon Key from Supabase

1. Visit https://supabase.com/dashboard/project/zghbrwbfdoalgzpcnbcm/settings/api
2. Scroll to **"Project API keys"**
3. Copy the **"anon public"** key
   - It starts with `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`
   - This is DIFFERENT from the service_role key
   - This one is safe to expose publicly

**Save it for Step 3.**

---

### Step 2: Apply RLS Policies

1. Visit https://supabase.com/dashboard/project/zghbrwbfdoalgzpcnbcm/sql/new
2. Copy the contents of `supabase_rls_policies.sql` (in this directory)
3. Paste into the SQL editor
4. Click **"Run"**
5. Verify output shows:
   ```
   rls_enabled: true
   ```
   for all tables

**What this does:**
- Enables Row-Level Security on all tables
- Creates policies allowing public SELECT (read) access
- Blocks all INSERT, UPDATE, DELETE from anon key
- Service role key still has full access (for Sentinel workers)

---

### Step 3: Deploy to Horizon with Anon Key

Now deploy to Horizon with these settings:

**Server Name:**
```
peripheral-mcp
```

**Description:**
```
The Peripheral OSINT intelligence MCP server - real-time access to 338K military signals, 116K news articles, and 80K stories
```

**Repository:**
```
peripheralresearch/peripheral-mcp
```

**Entrypoint:**
```
src/mcp/horizon_server.py:mcp
```

**Authentication:**
```
Enabled
```

**Environment Variables:**

**Variable 1:**
- Name: `SUPABASE_URL`
- Value: `https://zghbrwbfdoalgzpcnbcm.supabase.co`

**Variable 2:**
- Name: `SUPABASE_KEY`
- Value: `<paste ANON key from Step 1 here>` ⚠️ NOT the service role key!

---

### Step 4: Test Deployment

Once deployed, Horizon will give you a URL like:
```
https://peripheral-mcp.fastmcp.app/mcp
```

**Test in Horizon ChatMCP:**
```
Get the latest intelligence briefing for the last 24 hours
```

Should return articles from Supabase.

**Test write protection:**
Try to modify data (should fail with permission error).

---

## What Changed

### Before (INSECURE):
```
SUPABASE_KEY = service_role_key
→ Full database access
→ Can delete/modify data
→ Security risk if Horizon or MCP compromised
```

### After (SECURE):
```
SUPABASE_KEY = anon_key
+ RLS policies enabled
→ Read-only access
→ Cannot modify data
→ Safe for public exposure
```

---

## Verification Checklist

Before deploying, confirm:

- [ ] RLS policies applied (Step 2)
- [ ] Using **anon** key (NOT service_role key)
- [ ] Tested queries work with anon key
- [ ] Verified writes are blocked with anon key
- [ ] Authentication enabled in Horizon
- [ ] Service role key stored securely (not in Horizon)

---

## Troubleshooting

**If MCP queries fail after deployment:**

1. Check RLS policies are applied:
   ```sql
   SELECT tablename, rowsecurity FROM pg_tables 
   WHERE schemaname = 'public' AND tablename = 'news_item';
   ```
   Should show `rowsecurity: true`

2. Check policy exists:
   ```sql
   SELECT * FROM pg_policies WHERE tablename = 'news_item';
   ```
   Should show "Allow public read access" policy

3. Test anon key directly:
   ```bash
   curl -H "apikey: <anon-key>" -H "Authorization: Bearer <anon-key>" \
     https://zghbrwbfdoalgzpcnbcm.supabase.co/rest/v1/news_item?limit=1
   ```
   Should return data.

---

## Security Benefits

**With this setup:**

✅ MCP users can query intelligence data  
✅ Read-only access (no modifications)  
✅ RLS enforces permissions at database level  
✅ Service role key never exposed publicly  
✅ Sentinel workers still have full access (service key locally)  
✅ Safe to share MCP URL with friends  

**If someone compromises the anon key:**
- They can only read public data (which is the point)
- They cannot modify, delete, or insert data
- No database breach risk

---

## Next Steps

1. **Get anon key** (Step 1)
2. **Apply RLS policies** (Step 2)
3. **Deploy to Horizon** (Step 3) with anon key
4. **Test MCP tools** (Step 4)
5. **Share URL** with your friends

---

**Files in this directory:**
- `supabase_rls_policies.sql` - SQL to run in Supabase
- `SECURE_DEPLOYMENT.md` - This guide
- `src/mcp/horizon_server.py` - MCP server code (already ready)

---

**Questions?**
- Which key to use: **anon** (public), NOT service_role (secret)
- Where to get anon key: Supabase dashboard → Settings → API
- Where to run SQL: Supabase dashboard → SQL Editor
- Where to deploy: https://horizon.prefect.io

**Status:** Ready to deploy securely ✅
