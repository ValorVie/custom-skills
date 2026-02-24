-- 裝置註冊表
CREATE TABLE IF NOT EXISTS devices (
  id          SERIAL PRIMARY KEY,
  api_key_hash TEXT UNIQUE NOT NULL,
  name        TEXT NOT NULL,
  created_at  TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS sdk_sessions (
  id                  SERIAL PRIMARY KEY,
  content_session_id  TEXT UNIQUE NOT NULL,
  memory_session_id   TEXT UNIQUE,
  project             TEXT NOT NULL,
  user_prompt         TEXT,
  custom_title        TEXT,
  started_at          TEXT NOT NULL,
  started_at_epoch    BIGINT NOT NULL,
  completed_at        TEXT,
  completed_at_epoch  BIGINT,
  status              TEXT NOT NULL DEFAULT 'active',
  worker_port         INTEGER,
  prompt_counter      INTEGER DEFAULT 0,
  origin_device_id    INTEGER REFERENCES devices(id),
  synced_at           TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS observations (
  id                  SERIAL PRIMARY KEY,
  memory_session_id   TEXT NOT NULL,
  project             TEXT NOT NULL,
  type                TEXT NOT NULL,
  title               TEXT,
  subtitle            TEXT,
  narrative           TEXT,
  text                TEXT,
  facts               TEXT,
  concepts            TEXT,
  files_read          TEXT,
  files_modified      TEXT,
  prompt_number       INTEGER,
  content_hash        TEXT,
  created_at          TEXT NOT NULL,
  created_at_epoch    BIGINT NOT NULL,
  origin_device_id    INTEGER REFERENCES devices(id),
  synced_at           TIMESTAMPTZ DEFAULT now(),
  UNIQUE(memory_session_id, title, created_at_epoch)
);

CREATE TABLE IF NOT EXISTS session_summaries (
  id                  SERIAL PRIMARY KEY,
  session_id          TEXT UNIQUE NOT NULL,
  request             TEXT,
  investigated        TEXT,
  learned             TEXT,
  completed           TEXT,
  next_steps          TEXT,
  project             TEXT,
  files_read          TEXT,
  files_edited        TEXT,
  notes               TEXT,
  prompt_number       INTEGER,
  discovery_tokens    INTEGER DEFAULT 0,
  created_at          TEXT NOT NULL,
  created_at_epoch    BIGINT NOT NULL,
  origin_device_id    INTEGER REFERENCES devices(id),
  synced_at           TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS user_prompts (
  id                  SERIAL PRIMARY KEY,
  content_session_id  TEXT NOT NULL,
  project             TEXT,
  prompt_number       INTEGER NOT NULL,
  prompt_text         TEXT,
  created_at          TEXT NOT NULL,
  created_at_epoch    BIGINT NOT NULL,
  origin_device_id    INTEGER REFERENCES devices(id),
  synced_at           TIMESTAMPTZ DEFAULT now(),
  UNIQUE(content_session_id, prompt_number)
);

CREATE INDEX IF NOT EXISTS idx_sessions_synced    ON sdk_sessions(synced_at);
CREATE INDEX IF NOT EXISTS idx_observations_synced ON observations(synced_at);
CREATE INDEX IF NOT EXISTS idx_summaries_synced   ON session_summaries(synced_at);
CREATE INDEX IF NOT EXISTS idx_prompts_synced     ON user_prompts(synced_at);
