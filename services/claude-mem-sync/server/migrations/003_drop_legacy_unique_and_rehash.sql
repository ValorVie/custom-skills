-- 移除舊的三欄唯一約束（已被 sync_content_hash 取代）
ALTER TABLE observations
  DROP CONSTRAINT IF EXISTS observations_memory_session_id_title_created_at_epoch_key;

-- 清除所有 hash，觸發啟動時 backfill 用新對齊的算法重算
UPDATE observations SET sync_content_hash = NULL;
