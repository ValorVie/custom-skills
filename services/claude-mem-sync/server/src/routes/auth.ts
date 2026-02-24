import { Router } from "express";
import { randomBytes } from "crypto";
import { pool } from "../db.js";
import { config } from "../config.js";
import { hashApiKey } from "../middleware/auth.js";

const router = Router();

router.post("/api/auth/register", async (req, res) => {
  const adminSecret = req.headers["x-admin-secret"] as string;
  if (!adminSecret || adminSecret !== config.adminSecret) {
    res.status(403).json({ error: "Invalid admin secret" });
    return;
  }

  const { name } = req.body;
  if (!name || typeof name !== "string") {
    res.status(400).json({ error: "name is required" });
    return;
  }

  const apiKey = `cm_sync_${randomBytes(16).toString("hex")}`;
  const hash = hashApiKey(apiKey);

  const client = await pool.connect();
  try {
    await client.query("BEGIN");

    await client.query(
      "SELECT pg_advisory_xact_lock(hashtext($1))",
      [name]
    );

    const existing = await client.query(
      "SELECT id FROM devices WHERE name = $1 ORDER BY id ASC LIMIT 1",
      [name]
    );

    let deviceId: number;
    let rotated = false;

    if (existing.rows.length > 0) {
      deviceId = existing.rows[0].id;
      rotated = true;
      await client.query(
        "UPDATE devices SET api_key_hash = $1, created_at = now() WHERE id = $2",
        [hash, deviceId]
      );
    } else {
      const inserted = await client.query(
        "INSERT INTO devices (api_key_hash, name) VALUES ($1, $2) RETURNING id",
        [hash, name]
      );
      deviceId = inserted.rows[0].id;
    }

    await client.query("COMMIT");
    res.json({ api_key: apiKey, device_id: deviceId, name, rotated });
  } catch (err: any) {
    await client.query("ROLLBACK");
    console.error("Register failed:", err.message);
    res.status(500).json({ error: "Register failed" });
  } finally {
    client.release();
  }
});

export default router;
