import { access } from "node:fs/promises";
import { join } from "node:path";

import { backupDirtyFiles, hasLocalChanges } from "../utils/backup";
import { type CustomRepoConfig, loadCustomRepos } from "../utils/custom-repos";
import { type RunCommandOptions, runCommand } from "../utils/system";

export interface CustomRepoUpdateItem {
  name: string;
  success: boolean;
  status: "updated" | "up-to-date" | "missing" | "failed";
  backupDir?: string;
  message?: string;
}

export interface CustomRepoUpdateResult {
  items: CustomRepoUpdateItem[];
  summary: {
    updated: string[];
    upToDate: string[];
    missing: string[];
  };
  errors: string[];
}

export interface UpdateCustomReposDependencies {
  loadCustomReposFn?: () => Promise<CustomRepoConfig>;
  runCommandFn?: (
    command: string[],
    options?: RunCommandOptions,
  ) => Promise<{ stdout: string; stderr: string; exitCode: number }>;
  accessFn?: typeof access;
  hasLocalChangesFn?: typeof hasLocalChanges;
  backupDirtyFilesFn?: typeof backupDirtyFiles;
}

export interface UpdateCustomReposOptions {
  deps?: UpdateCustomReposDependencies;
}

async function pathExists(
  accessFn: typeof access,
  pathValue: string,
): Promise<boolean> {
  try {
    await accessFn(pathValue);
    return true;
  } catch {
    return false;
  }
}

async function compareRemote(
  repoPath: string,
  branch: string,
  runCommandFn: NonNullable<UpdateCustomReposDependencies["runCommandFn"]>,
): Promise<{ ahead: number; behind: number }> {
  const result = await runCommandFn(
    [
      "git",
      "-C",
      repoPath,
      "rev-list",
      "--left-right",
      "--count",
      `HEAD...origin/${branch}`,
    ],
    {
      check: false,
      timeoutMs: 60_000,
    },
  );

  if (result.exitCode !== 0) {
    return { ahead: 0, behind: 0 };
  }

  const [aheadRaw, behindRaw] = result.stdout.trim().split(/\s+/);
  const ahead = Number.parseInt(aheadRaw ?? "0", 10);
  const behind = Number.parseInt(behindRaw ?? "0", 10);

  return {
    ahead: Number.isFinite(ahead) ? ahead : 0,
    behind: Number.isFinite(behind) ? behind : 0,
  };
}

export async function updateCustomRepos(
  options: UpdateCustomReposOptions = {},
): Promise<CustomRepoUpdateResult> {
  const deps = options.deps ?? {};
  const loadCustomReposFn = deps.loadCustomReposFn ?? loadCustomRepos;
  const runCommandFn = deps.runCommandFn ?? runCommand;
  const accessFn = deps.accessFn ?? access;
  const hasLocalChangesFn = deps.hasLocalChangesFn ?? hasLocalChanges;
  const backupDirtyFilesFn = deps.backupDirtyFilesFn ?? backupDirtyFiles;

  const result: CustomRepoUpdateResult = {
    items: [],
    summary: {
      updated: [],
      upToDate: [],
      missing: [],
    },
    errors: [],
  };

  const config = await loadCustomReposFn();
  for (const [name, repo] of Object.entries(config.repos)) {
    if (!(await pathExists(accessFn, join(repo.localPath, ".git")))) {
      result.items.push({
        name,
        success: false,
        status: "missing",
        message: "repository not found",
      });
      result.summary.missing.push(name);
      continue;
    }

    const fetchResult = await runCommandFn(
      ["git", "-C", repo.localPath, "fetch", "--all"],
      {
        check: false,
        timeoutMs: 60_000,
      },
    );
    if (fetchResult.exitCode !== 0) {
      const message = fetchResult.stderr || "git fetch failed";
      result.items.push({
        name,
        success: false,
        status: "failed",
        message,
      });
      result.errors.push(message);
      continue;
    }

    const diff = await compareRemote(repo.localPath, repo.branch, runCommandFn);

    let backupDir: string | undefined;
    if (await hasLocalChangesFn(repo.localPath)) {
      backupDir = await backupDirtyFilesFn(repo.localPath);
    }

    const resetResult = await runCommandFn(
      ["git", "-C", repo.localPath, "reset", "--hard", `origin/${repo.branch}`],
      {
        check: false,
        timeoutMs: 60_000,
      },
    );
    if (resetResult.exitCode !== 0) {
      const message = resetResult.stderr || "git reset failed";
      result.items.push({
        name,
        success: false,
        status: "failed",
        backupDir,
        message,
      });
      result.errors.push(message);
      continue;
    }

    const updated = diff.behind > 0;
    result.items.push({
      name,
      success: true,
      status: updated ? "updated" : "up-to-date",
      backupDir,
    });
    if (updated) {
      result.summary.updated.push(name);
    } else {
      result.summary.upToDate.push(name);
    }
  }

  result.summary.updated.sort((a, b) => a.localeCompare(b));
  result.summary.upToDate.sort((a, b) => a.localeCompare(b));
  result.summary.missing.sort((a, b) => a.localeCompare(b));

  return result;
}
