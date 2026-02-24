import express from "express";
import { readFileSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";
import { config } from "./config.js";
import { pool } from "./db.js";
import healthRoutes from "./routes/health.js";
import authRoutes from "./routes/auth.js";

const __dirname = dirname(fileURLToPath(import.meta.url));

const app = express();
app.use(express.json({ limit: "50mb" }));
app.use(healthRoutes);
app.use(authRoutes);

async function start() {
  const migrationSql = readFileSync(
    join(__dirname, "../migrations/001_init.sql"),
    "utf-8"
  );
  await pool.query(migrationSql);
  console.log("Database migration applied");

  app.listen(config.port, () => {
    console.log(`claude-mem-sync-server listening on :${config.port}`);
  });
}

start().catch((err) => {
  console.error("Failed to start:", err);
  process.exit(1);
});

export { app };
