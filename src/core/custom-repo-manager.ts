import { access, mkdir } from "node:fs/promises";
import { join } from "node:path";

const EXPECTED_DIRS = [
  "skills",
  "commands",
  "agents",
  "workflows",
  "hooks",
  "plugins",
] as const;

const VALID_MARKERS = ["skills", "commands", "agents", "workflows"] as const;

export interface RepoStructureValidation {
  valid: boolean;
  existing: string[];
  missing: string[];
}

export interface RepoStructureFixResult {
  created: string[];
}

async function pathExists(pathValue: string): Promise<boolean> {
  try {
    await access(pathValue);
    return true;
  } catch {
    return false;
  }
}

export async function validateRepoStructure(
  repoDir: string,
): Promise<RepoStructureValidation> {
  const existing: string[] = [];
  const missing: string[] = [];

  for (const dirName of EXPECTED_DIRS) {
    const fullPath = join(repoDir, dirName);
    if (await pathExists(fullPath)) {
      existing.push(dirName);
    } else {
      missing.push(dirName);
    }
  }

  const hasValidMarker = VALID_MARKERS.some((name) => existing.includes(name));

  return {
    valid: hasValidMarker,
    existing: existing.sort((a, b) => a.localeCompare(b)),
    missing: missing.sort((a, b) => a.localeCompare(b)),
  };
}

export async function fixRepoStructure(
  repoDir: string,
): Promise<RepoStructureFixResult> {
  const created: string[] = [];

  for (const dirName of EXPECTED_DIRS) {
    const fullPath = join(repoDir, dirName);
    if (await pathExists(fullPath)) {
      continue;
    }
    await mkdir(fullPath, { recursive: true });
    created.push(dirName);
  }

  return { created: created.sort((a, b) => a.localeCompare(b)) };
}
