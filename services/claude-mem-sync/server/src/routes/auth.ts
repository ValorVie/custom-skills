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

  const result = await pool.query(
    "INSERT INTO devices (api_key_hash, name) VALUES ($1, $2) RETURNING id",
    [hash, name]
  );

  res.json({ api_key: apiKey, device_id: result.rows[0].id, name });
});

export default router;
