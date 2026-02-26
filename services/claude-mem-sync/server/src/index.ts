import express from "express";
import { readFileSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";
import { config } from "./config.js";
import { pool } from "./db.js";
import healthRoutes from "./routes/health.js";
import authRoutes from "./routes/auth.js";
import syncRoutes from "./routes/sync.js";
import {
  planHashBackfill,
  type ExistingHashRow,
  type PendingObservationRow,
} from "./utils/backfill.js";

const __dirname = dirname(fileURLToPath(import.meta.url));

const app = express();
app.use(express.json({ limit: "50mb" }));
app.use(healthRoutes);
app.use(authRoutes);
app.use(syncRoutes);

async function applyMigrations() {
  const migration001 = readFileSync(
    join(__dirname, "../migrations/001_init.sql"),
    "utf-8"
  );
  await pool.query(migration001);

  const migration002 = readFileSync(
    join(__dirname, "../migrations/002_add_sync_content_hash.sql"),
    "utf-8"
  );
  await pool.query(migration002);

  const migration003 = readFileSync(
    join(__dirname, "../migrations/003_drop_legacy_unique_and_rehash.sql"),
    "utf-8"
  );
  await pool.query(migration003);
}

async function backfillObservationHashes() {
  const pending = await pool.query<PendingObservationRow>(
    `SELECT id, title, narrative, facts, project, type, synced_at
     FROM observations
     WHERE sync_content_hash IS NULL
     ORDER BY synced_at ASC, id ASC`
  );

  if (pending.rows.length === 0) {
    console.log("sync_content_hash backfill skipped (already complete)");
    return;
  }

  console.log(
    `Backfilling ${pending.rows.length} observations with sync_content_hash...`
  );

  const existing = await pool.query<ExistingHashRow>(
    `SELECT id, sync_content_hash, synced_at
     FROM observations
     WHERE sync_content_hash IS NOT NULL`
  );
  const plan = planHashBackfill(pending.rows, existing.rows);

  const client = await pool.connect();
  try {
    await client.query("BEGIN");

    for (const id of plan.deleteIds) {
      await client.query("DELETE FROM observations WHERE id = $1", [id]);
    }

    for (const row of plan.updates) {
      await client.query(
        "UPDATE observations SET sync_content_hash = $1 WHERE id = $2",
        [row.hash, row.id]
      );
    }

    await client.query("COMMIT");
  } catch (err) {
    await client.query("ROLLBACK");
    throw err;
  } finally {
    client.release();
  }

  console.log(
    `sync_content_hash backfill complete: updated=${plan.updates.length} deduped=${plan.deleteIds.length}`
  );
}

async function start() {
  await applyMigrations();
  await backfillObservationHashes();
  console.log("Database migrations applied");

  app.listen(config.port, () => {
    console.log(`claude-mem-sync-server listening on :${config.port}`);
  });
}

start().catch((err) => {
  console.error("Failed to start:", err);
  process.exit(1);
});

export { app };
