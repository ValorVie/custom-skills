import { access, cp, mkdir } from "node:fs/promises";
import { dirname, join } from "node:path";

import { runCommand } from "./system";

async function gitStatus(repoDir: string): Promise<string> {
  const result = await runCommand(
    ["git", "-C", repoDir, "status", "--porcelain"],
    {
      check: false,
      timeoutMs: 10_000,
    },
  );

  if (result.exitCode !== 0) {
    return "";
  }

  return result.stdout;
}

function normalizePath(pathValue: string): string {
  if (pathValue.startsWith('"') && pathValue.endsWith('"')) {
    return pathValue.slice(1, -1).replaceAll('\\"', '"');
  }
  return pathValue;
}

function parseDirtyPaths(statusOutput: string): string[] {
  const files = new Set<string>();

  for (const line of statusOutput.split(/\r?\n/)) {
    if (line.length < 4) {
      continue;
    }

    const value = line.slice(3).trim();
    const pathValue = value.includes(" -> ")
      ? (value.split(" -> ").at(-1) ?? "")
      : value;

    if (!pathValue) {
      continue;
    }

    files.add(normalizePath(pathValue));
  }

  return [...files].sort((a, b) => a.localeCompare(b));
}

async function exists(pathValue: string): Promise<boolean> {
  try {
    await access(pathValue);
    return true;
  } catch {
    return false;
  }
}

export async function hasLocalChanges(repoDir: string): Promise<boolean> {
  const statusOutput = await gitStatus(repoDir);
  return statusOutput.trim().length > 0;
}

export async function backupDirtyFiles(repoDir: string): Promise<string> {
  const statusOutput = await gitStatus(repoDir);
  const backupDir = join(
    repoDir,
    ".ai-dev-backups",
    new Date().toISOString().replace(/[:.]/g, "-"),
  );

  await mkdir(backupDir, { recursive: true });

  for (const filePath of parseDirtyPaths(statusOutput)) {
    const sourcePath = join(repoDir, filePath);
    if (!(await exists(sourcePath))) {
      continue;
    }

    const targetPath = join(backupDir, filePath);
    await mkdir(dirname(targetPath), { recursive: true });
    await cp(sourcePath, targetPath, { recursive: true, force: true });
  }

  return backupDir;
}

export async function restoreBackup(
  backupDir: string,
  targetDir: string,
): Promise<void> {
  await cp(backupDir, targetDir, { recursive: true, force: true });
}
