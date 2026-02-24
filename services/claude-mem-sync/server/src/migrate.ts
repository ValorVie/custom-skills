import { Pool } from "pg";
import { readFileSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));

async function migrate() {
  const pool = new Pool({ connectionString: process.env.DATABASE_URL });
  const sql001 = readFileSync(join(__dirname, "../migrations/001_init.sql"), "utf-8");
  await pool.query(sql001);

  const sql002 = readFileSync(
    join(__dirname, "../migrations/002_add_sync_content_hash.sql"),
    "utf-8"
  );
  await pool.query(sql002);
  console.log("Migration complete");
  await pool.end();
}

migrate().catch((err) => {
  console.error("Migration failed:", err);
  process.exit(1);
});
