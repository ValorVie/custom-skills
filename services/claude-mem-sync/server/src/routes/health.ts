import { Router } from "express";
import { pool } from "../db.js";

const router = Router();

router.get("/api/health", async (_req, res) => {
  try {
    await pool.query("SELECT 1");
    res.json({ status: "ok" });
  } catch {
    res.status(503).json({ status: "error", message: "database unavailable" });
  }
});

export default router;
