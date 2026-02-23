-- Supabase RLS Policies for Peripheral MCP Public Access
-- Run this in Supabase SQL Editor before deploying MCP with anon key
-- This allows public READ-ONLY access while protecting against writes

-- ============================================================================
-- NEWS ITEMS
-- ============================================================================
ALTER TABLE news_item ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist
DROP POLICY IF EXISTS "Allow public read access" ON news_item;

-- Allow public SELECT
CREATE POLICY "Allow public read access" ON news_item
FOR SELECT
USING (true);

-- ============================================================================
-- STORIES
-- ============================================================================
ALTER TABLE story ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Allow public read access" ON story;

CREATE POLICY "Allow public read access" ON story
FOR SELECT
USING (true);

-- ============================================================================
-- SIGNALS
-- ============================================================================
ALTER TABLE signal ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Allow public read access" ON signal;

CREATE POLICY "Allow public read access" ON signal
FOR SELECT
USING (true);

-- ============================================================================
-- ENTITIES
-- ============================================================================
ALTER TABLE entity_person ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Allow public read access" ON entity_person;

CREATE POLICY "Allow public read access" ON entity_person
FOR SELECT
USING (true);

ALTER TABLE entity_organisation ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Allow public read access" ON entity_organisation;

CREATE POLICY "Allow public read access" ON entity_organisation
FOR SELECT
USING (true);

ALTER TABLE entity_location ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Allow public read access" ON entity_location;

CREATE POLICY "Allow public read access" ON entity_location
FOR SELECT
USING (true);

ALTER TABLE entity_country ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Allow public read access" ON entity_country;

CREATE POLICY "Allow public read access" ON entity_country
FOR SELECT
USING (true);

ALTER TABLE entity_product ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Allow public read access" ON entity_product;

CREATE POLICY "Allow public read access" ON entity_product
FOR SELECT
USING (true);

-- ============================================================================
-- EMBEDDINGS (if queried)
-- ============================================================================
ALTER TABLE news_item_embedding ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Allow public read access" ON news_item_embedding;

CREATE POLICY "Allow public read access" ON news_item_embedding
FOR SELECT
USING (true);

-- ============================================================================
-- OSINT SOURCES (if queried)
-- ============================================================================
ALTER TABLE osint_source ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Allow public read access" ON osint_source;

CREATE POLICY "Allow public read access" ON osint_source
FOR SELECT
USING (true);

-- ============================================================================
-- VERIFICATION
-- ============================================================================

-- Verify RLS is enabled on all tables
SELECT 
    schemaname,
    tablename,
    rowsecurity AS rls_enabled
FROM pg_tables
WHERE schemaname = 'public'
    AND tablename IN (
        'news_item',
        'story', 
        'signal',
        'entity_person',
        'entity_organisation',
        'entity_location',
        'entity_country',
        'entity_product',
        'news_item_embedding',
        'osint_source'
    )
ORDER BY tablename;

-- List all RLS policies
SELECT 
    schemaname,
    tablename,
    policyname,
    permissive,
    roles,
    cmd,
    qual
FROM pg_policies
WHERE schemaname = 'public'
ORDER BY tablename, policyname;

-- ============================================================================
-- NOTES
-- ============================================================================

-- These policies allow:
-- ✅ Public SELECT (read) access via anon key
-- ❌ No INSERT, UPDATE, DELETE without service role key
-- ✅ Service role key still has full access for Sentinel workers

-- To test policies:
-- 1. Get anon key from Supabase dashboard
-- 2. Try querying with anon key (should work)
-- 3. Try inserting with anon key (should fail)

-- If you need to disable RLS (NOT RECOMMENDED):
-- ALTER TABLE <table_name> DISABLE ROW LEVEL SECURITY;
