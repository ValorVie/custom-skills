import { Router, Request, Response } from "express";
import { pool } from "../db.js";
import { requireApiKey } from "../middleware/auth.js";
import { computeContentHash } from "../utils/hash.js";

const router = Router();
router.use(requireApiKey);

// ─── POST /api/sync/push ───
router.post("/api/sync/push", async (req: Request, res: Response) => {
  const device = (req as any).device;
  const { sessions = [], observations = [], summaries = [], prompts = [] } = req.body;

  const client = await pool.connect();
  try {
    await client.query("BEGIN");

    const stats = {
      sessionsImported: 0, sessionsSkipped: 0,
      observationsImported: 0, observationsSkipped: 0,
      summariesImported: 0, summariesSkipped: 0,
      promptsImported: 0, promptsSkipped: 0,
    };

    // sessions first (FK parent)
    for (const s of sessions) {
      const r = await client.query(
        `INSERT INTO sdk_sessions
          (content_session_id, memory_session_id, project, user_prompt, custom_title,
           started_at, started_at_epoch, completed_at, completed_at_epoch,
           status, worker_port, prompt_counter, origin_device_id)
         VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13)
         ON CONFLICT (content_session_id) DO UPDATE SET
           memory_session_id = COALESCE(sdk_sessions.memory_session_id, EXCLUDED.memory_session_id),
           completed_at = COALESCE(EXCLUDED.completed_at, sdk_sessions.completed_at),
           completed_at_epoch = COALESCE(EXCLUDED.completed_at_epoch, sdk_sessions.completed_at_epoch),
           status = COALESCE(EXCLUDED.status, sdk_sessions.status),
           custom_title = COALESCE(EXCLUDED.custom_title, sdk_sessions.custom_title)`,
        [s.content_session_id, s.memory_session_id, s.project, s.user_prompt,
         s.custom_title, s.started_at, s.started_at_epoch, s.completed_at,
         s.completed_at_epoch, s.status || "active", s.worker_port,
         s.prompt_counter, device.id]
      );
      if (r.rowCount && r.rowCount > 0) stats.sessionsImported++;
      else stats.sessionsSkipped++;
    }

    // observations (per-row try/catch — 單筆失敗不影響整批)
    for (const o of observations) {
      try {
        const syncContentHash =
          typeof o.sync_content_hash === "string" && o.sync_content_hash.length > 0
            ? o.sync_content_hash
            : computeContentHash(o);

        const r = await client.query(
          `INSERT INTO observations
            (memory_session_id, project, type, title, subtitle, narrative, text,
              facts, concepts, files_read, files_modified, prompt_number,
              content_hash, created_at, created_at_epoch, origin_device_id, sync_content_hash)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17)
            ON CONFLICT (sync_content_hash) DO NOTHING`,
          [o.memory_session_id, o.project, o.type, o.title, o.subtitle,
            o.narrative, o.text, o.facts, o.concepts, o.files_read,
            o.files_modified, o.prompt_number, o.content_hash,
            o.created_at, o.created_at_epoch, device.id, syncContentHash]
        );
        if (r.rowCount && r.rowCount > 0) stats.observationsImported++;
        else stats.observationsSkipped++;
      } catch {
        stats.observationsSkipped++;
      }
    }

    // summaries
    for (const s of summaries) {
      const r = await client.query(
        `INSERT INTO session_summaries
          (session_id, request, investigated, learned, completed, next_steps,
           project, files_read, files_edited, notes, prompt_number,
           discovery_tokens, created_at, created_at_epoch, origin_device_id)
         VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15)
         ON CONFLICT (session_id) DO NOTHING`,
        [s.session_id, s.request, s.investigated, s.learned, s.completed,
         s.next_steps, s.project, s.files_read, s.files_edited, s.notes,
         s.prompt_number, s.discovery_tokens, s.created_at,
         s.created_at_epoch, device.id]
      );
      if (r.rowCount && r.rowCount > 0) stats.summariesImported++;
      else stats.summariesSkipped++;
    }

    // prompts
    for (const p of prompts) {
      const r = await client.query(
        `INSERT INTO user_prompts
          (content_session_id, project, prompt_number, prompt_text,
           created_at, created_at_epoch, origin_device_id)
         VALUES ($1,$2,$3,$4,$5,$6,$7)
         ON CONFLICT (content_session_id, prompt_number) DO NOTHING`,
        [p.content_session_id, p.project, p.prompt_number, p.prompt_text,
         p.created_at, p.created_at_epoch, device.id]
      );
      if (r.rowCount && r.rowCount > 0) stats.promptsImported++;
      else stats.promptsSkipped++;
    }

    await client.query("COMMIT");
    res.json({ success: true, stats, server_epoch: Date.now() });
  } catch (err: any) {
    await client.query("ROLLBACK");
    console.error("Push failed:", err.message);
    res.status(500).json({ error: "Push failed" });
  } finally {
    client.release();
  }
});

// ─── POST /api/sync/push-preflight ───
router.post("/api/sync/push-preflight", async (req: Request, res: Response) => {
  const rawHashes = req.body?.hashes;
  if (!Array.isArray(rawHashes) || rawHashes.length === 0) {
    res.json({ missing: [] });
    return;
  }

  const hashes = [
    ...new Set(rawHashes.filter((value): value is string => typeof value === "string" && value.length > 0)),
  ];
  if (hashes.length === 0) {
    res.json({ missing: [] });
    return;
  }

  try {
    const result = await pool.query(
      "SELECT sync_content_hash FROM observations WHERE sync_content_hash = ANY($1::text[])",
      [hashes],
    );
    const found = new Set(
      result.rows
        .map((row: { sync_content_hash: string | null }) => row.sync_content_hash)
        .filter((hash): hash is string => typeof hash === "string"),
    );

    const missing = hashes.filter((hash) => !found.has(hash));
    res.json({ missing });
  } catch (err: any) {
    console.error("Preflight failed:", err.message);
    res.status(500).json({ error: "Preflight failed" });
  }
});

// ─── GET /api/sync/pull ───
router.get("/api/sync/pull", async (req: Request, res: Response) => {
  const device = (req as any).device;
  const since = req.query.since
    ? new Date(Number(req.query.since)).toISOString()
    : new Date(0).toISOString();
  const limit = Math.min(Number(req.query.limit) || 500, 1000);

  const deviceFilter = "AND origin_device_id IS DISTINCT FROM $2";

  try {
    const [sessions, observations, summaries, prompts] = await Promise.all([
      pool.query(
        `SELECT * FROM sdk_sessions WHERE synced_at > $1 ${deviceFilter}
         ORDER BY synced_at LIMIT $3`,
        [since, device.id, limit]
      ),
      pool.query(
        `SELECT * FROM observations WHERE synced_at > $1 ${deviceFilter}
         ORDER BY synced_at LIMIT $3`,
        [since, device.id, limit]
      ),
      pool.query(
        `SELECT * FROM session_summaries WHERE synced_at > $1 ${deviceFilter}
         ORDER BY synced_at LIMIT $3`,
        [since, device.id, limit]
      ),
      pool.query(
        `SELECT * FROM user_prompts WHERE synced_at > $1 ${deviceFilter}
         ORDER BY synced_at LIMIT $3`,
        [since, device.id, limit]
      ),
    ]);

    const hasMore = [sessions, observations, summaries, prompts]
      .some((r) => r.rows.length === limit);

    let maxSyncedAt = since;
    for (const result of [sessions, observations, summaries, prompts]) {
      for (const row of result.rows) {
        const rowTime = new Date(row.synced_at).toISOString();
        if (rowTime > maxSyncedAt) maxSyncedAt = rowTime;
      }
    }

    res.json({
      sessions: sessions.rows,
      observations: observations.rows,
      summaries: summaries.rows,
      prompts: prompts.rows,
      has_more: hasMore,
      next_since: new Date(maxSyncedAt).getTime(),
      server_epoch: Date.now(),
    });
  } catch (err: any) {
    console.error("Pull failed:", err.message);
    res.status(500).json({ error: "Pull failed" });
  }
});

// ─── GET /api/sync/status ───
router.get("/api/sync/status", async (_req: Request, res: Response) => {
  const counts = await pool.query(`
    SELECT
      (SELECT COUNT(*) FROM sdk_sessions)::int AS sessions,
      (SELECT COUNT(*) FROM observations)::int AS observations,
      (SELECT COUNT(*) FROM session_summaries)::int AS summaries,
      (SELECT COUNT(*) FROM user_prompts)::int AS prompts,
      (SELECT COUNT(*) FROM devices)::int AS devices
  `);
  res.json(counts.rows[0]);
});

export default router;
