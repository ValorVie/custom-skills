import { execSync } from "node:child_process";
import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";

export interface MetadataChanges {
  modeChanges: string[];
  lineEndingChanges: string[];
}

export function hasChanges(changes: MetadataChanges): boolean {
  return changes.modeChanges.length > 0 || changes.lineEndingChanges.length > 0;
}

export function totalCount(changes: MetadataChanges): number {
  return changes.modeChanges.length + changes.lineEndingChanges.length;
}

function isGitRepo(path: string): boolean {
  return existsSync(join(path, ".git"));
}

interface RawDiffEntry {
  oldMode: string;
  newMode: string;
  filePath: string;
}

function getRawDiff(repoPath: string): RawDiffEntry[] {
  try {
    const output = execSync("git diff --raw", {
      cwd: repoPath,
      encoding: "utf-8",
    });
    return output
      .trim()
      .split("\n")
      .filter(Boolean)
      .map((line) => {
        const parts = line.split("\t");
        if (parts.length < 2) return null;
        const meta = parts[0].split(/\s+/);
        if (meta.length < 5) return null;
        return {
          oldMode: meta[0].replace(/^:/, ""),
          newMode: meta[1],
          filePath: parts[1],
        };
      })
      .filter(Boolean) as RawDiffEntry[];
  } catch {
    return [];
  }
}

function isOnlyLineEndingDiff(filePath: string, repoPath: string): boolean {
  try {
    const gitContent = execSync(`git show HEAD:${filePath}`, {
      cwd: repoPath,
    });
    const fullPath = join(repoPath, filePath);
    if (!existsSync(fullPath)) return false;
    const workContent = readFileSync(fullPath);
    const normalize = (buf: Buffer) =>
      buf.toString("utf-8").replace(/\r\n/g, "\n").replace(/\r/g, "\n");
    return normalize(gitContent) === normalize(workContent);
  } catch {
    return false;
  }
}

export function detectMetadataChanges(repoPath: string): MetadataChanges {
  const result: MetadataChanges = { modeChanges: [], lineEndingChanges: [] };
  if (!isGitRepo(repoPath)) return result;

  const rawDiff = getRawDiff(repoPath);
  const modeChangeFiles = new Set(
    rawDiff.filter((d) => d.oldMode !== d.newMode).map((d) => d.filePath),
  );

  for (const diff of rawDiff) {
    if (modeChangeFiles.has(diff.filePath)) {
      if (isOnlyLineEndingDiff(diff.filePath, repoPath)) {
        result.modeChanges.push(diff.filePath);
      } else {
        // check if content diff exists beyond mode change
        try {
          execSync(`git diff --quiet ${diff.filePath}`, { cwd: repoPath });
          result.modeChanges.push(diff.filePath); // no content diff
        } catch {
          /* has content diff, skip */
        }
      }
    } else {
      if (isOnlyLineEndingDiff(diff.filePath, repoPath)) {
        result.lineEndingChanges.push(diff.filePath);
      }
    }
  }
  return result;
}

export function revertFiles(files: string[], repoPath: string): boolean {
  if (files.length === 0) return true;
  try {
    execSync(`git checkout -- ${files.join(" ")}`, { cwd: repoPath });
    return true;
  } catch {
    return false;
  }
}

export function setFilemodeConfig(repoPath: string, value: boolean): boolean {
  try {
    execSync(`git config core.fileMode ${value}`, { cwd: repoPath });
    return true;
  } catch {
    return false;
  }
}

export function handleMetadataChanges(
  changes: MetadataChanges,
  repoPath: string,
): void {
  if (!hasChanges(changes)) return;

  const count = totalCount(changes);
  console.log(`\n⚠️  偵測到 ${count} 個檔案有非內容異動：`);

  if (changes.modeChanges.length > 0) {
    console.log(`  - 檔案權限變更: ${changes.modeChanges.length} 個`);
  }
  if (changes.lineEndingChanges.length > 0) {
    console.log(`  - 換行符變更: ${changes.lineEndingChanges.length} 個`);
  }

  // Auto-revert (non-interactive, equivalent to v1 option 1)
  const allFiles = [...changes.modeChanges, ...changes.lineEndingChanges];
  const success = revertFiles(allFiles, repoPath);
  if (success) {
    console.log("✓ 已還原所有非內容異動");
  } else {
    console.log("✗ 還原失敗，請手動處理");
  }
}
