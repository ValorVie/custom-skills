import { Request, Response, NextFunction } from "express";
import { createHash } from "crypto";
import { pool } from "../db.js";

export function hashApiKey(key: string): string {
  return createHash("sha256").update(key).digest("hex");
}

export async function requireApiKey(req: Request, res: Response, next: NextFunction) {
  const apiKey = req.headers["x-api-key"] as string;
  if (!apiKey) {
    res.status(401).json({ error: "Missing X-API-Key header" });
    return;
  }

  const hash = hashApiKey(apiKey);
  const result = await pool.query(
    "SELECT id, name FROM devices WHERE api_key_hash = $1",
    [hash]
  );

  if (result.rows.length === 0) {
    res.status(401).json({ error: "Invalid API key" });
    return;
  }

  (req as any).device = result.rows[0];
  next();
}
