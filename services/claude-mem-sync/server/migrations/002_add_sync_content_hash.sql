ALTER TABLE observations ADD COLUMN IF NOT EXISTS sync_content_hash TEXT;

CREATE UNIQUE INDEX IF NOT EXISTS idx_observations_sync_content_hash
  ON observations (sync_content_hash);
