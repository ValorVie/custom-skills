import { describe, expect, test } from "bun:test";
import {
  mkdir,
  mkdtemp,
  readFile,
  rm,
  unlink,
  writeFile,
} from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

import {
  backupDirtyFiles,
  hasLocalChanges,
  restoreBackup,
} from "../../src/utils/backup";
import { runCommand } from "../../src/utils/system";

async function initRepo(dir: string): Promise<void> {
  await runCommand(["git", "init", dir], { check: true, timeoutMs: 10_000 });
}

describe("utils/backup", () => {
  test("hasLocalChanges is false for clean repository", async () => {
    const root = await mkdtemp(join(tmpdir(), "ai-dev-backup-"));

    try {
      await initRepo(root);
      expect(await hasLocalChanges(root)).toBe(false);
    } finally {
      await rm(root, { recursive: true, force: true });
    }
  });

  test("hasLocalChanges is true when untracked file exists", async () => {
    const root = await mkdtemp(join(tmpdir(), "ai-dev-backup-"));

    try {
      await initRepo(root);
      await writeFile(join(root, "new.txt"), "new\n", "utf8");
      expect(await hasLocalChanges(root)).toBe(true);
    } finally {
      await rm(root, { recursive: true, force: true });
    }
  });

  test("backupDirtyFiles and restoreBackup preserve dirty files", async () => {
    const root = await mkdtemp(join(tmpdir(), "ai-dev-backup-"));
    const nestedDir = join(root, "nested");
    const targetFile = join(nestedDir, "item.txt");

    try {
      await initRepo(root);
      await mkdir(nestedDir, { recursive: true });
      await writeFile(targetFile, "draft\n", "utf8");

      const backupDir = await backupDirtyFiles(root);
      const backupFile = join(backupDir, "nested", "item.txt");
      expect((await readFile(backupFile, "utf8")).trim()).toBe("draft");

      await unlink(targetFile);
      await restoreBackup(backupDir, root);
      expect((await readFile(targetFile, "utf8")).trim()).toBe("draft");
    } finally {
      await rm(root, { recursive: true, force: true });
    }
  });
});
