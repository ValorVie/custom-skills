import { access, mkdir, readlink, rm, symlink } from "node:fs/promises";
import { dirname, join } from "node:path";
import { backupDirtyFiles, hasLocalChanges } from "../utils/backup";
import { type CustomRepoConfig, loadCustomRepos } from "../utils/custom-repos";
import { paths } from "../utils/paths";
import { BUN_PACKAGES, NPM_PACKAGES, REPOS } from "../utils/shared";
import { commandExists, runCommand } from "../utils/system";
import { updateClaudeCode } from "./claude-code-manager";

type RepoConfig = (typeof REPOS)[number];

export interface UpdateDependencies {
  commandExistsFn?: typeof commandExists;
  runCommandFn?: typeof runCommand;
  accessFn?: typeof access;
  loadCustomReposFn?: () => Promise<CustomRepoConfig>;
  hasLocalChangesFn?: typeof hasLocalChanges;
  backupDirtyFilesFn?: typeof backupDirtyFiles;
  npmPackages?: readonly string[];
  bunPackages?: readonly string[];
  repos?: readonly RepoConfig[];
}

export interface UpdateOptions {
  skipNpm?: boolean;
  skipBun?: boolean;
  skipRepos?: boolean;
  skipPlugins?: boolean;
  deps?: UpdateDependencies;
  onProgress?: (message: string) => void;
}

export interface UpdateItemResult {
  name: string;
  success: boolean;
  message?: string;
}

export interface UpdateResult {
  claudeCode: UpdateItemResult;
  tools: UpdateItemResult[];
  npmPackages: UpdateItemResult[];
  bunPackages: UpdateItemResult[];
  repos: UpdateItemResult[];
  customRepos: UpdateItemResult[];
  plugins: UpdateItemResult;
  summary: {
    updated: string[];
    upToDate: string[];
    missing: string[];
  };
  errors: string[];
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

async function resolveCurrentBranch(
  repoDir: string,
  runCommandFn: typeof runCommand,
): Promise<string> {
  const result = await runCommandFn(
    ["git", "-C", repoDir, "rev-parse", "--abbrev-ref", "HEAD"],
    {
      check: false,
      timeoutMs: 60_000,
    },
  );

  if (result.exitCode !== 0) {
    return "main";
  }

  return result.stdout.trim() || "main";
}

async function compareRemote(
  repoDir: string,
  branch: string,
  runCommandFn: typeof runCommand,
): Promise<{ ahead: number; behind: number }> {
  const result = await runCommandFn(
    [
      "git",
      "-C",
      repoDir,
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

async function refreshSuperpowersSymlink(): Promise<void> {
  try {
    await access(paths.superpowersRepo);
  } catch {
    return;
  }

  await mkdir(dirname(paths.opencodeSuperpowers), { recursive: true });

  try {
    const current = await readlink(paths.opencodeSuperpowers);
    if (current === paths.superpowersRepo) {
      return;
    }
  } catch {
    // continue relinking
  }

  await rm(paths.opencodeSuperpowers, { recursive: true, force: true });
  await symlink(paths.superpowersRepo, paths.opencodeSuperpowers, "dir");
}

async function updateRepository(
  repo: { name: string; dir: string },
  deps: {
    runCommandFn: typeof runCommand;
    accessFn: typeof access;
    hasLocalChangesFn: typeof hasLocalChanges;
    backupDirtyFilesFn: typeof backupDirtyFiles;
  },
): Promise<{
  item: UpdateItemResult;
  updated: boolean;
  missing: boolean;
}> {
  if (!(await pathExists(deps.accessFn, join(repo.dir, ".git")))) {
    return {
      item: {
        name: repo.name,
        success: false,
        message: "repository not found",
      },
      updated: false,
      missing: true,
    };
  }

  const fetchResult = await deps.runCommandFn(
    ["git", "-C", repo.dir, "fetch", "--all"],
    {
      check: false,
      timeoutMs: 60_000,
    },
  );

  if (fetchResult.exitCode !== 0) {
    return {
      item: {
        name: repo.name,
        success: false,
        message: fetchResult.stderr,
      },
      updated: false,
      missing: false,
    };
  }

  const branch = await resolveCurrentBranch(repo.dir, deps.runCommandFn);
  const diff = await compareRemote(repo.dir, branch, deps.runCommandFn);

  if (await deps.hasLocalChangesFn(repo.dir)) {
    await deps.backupDirtyFilesFn(repo.dir);
  }

  const resetResult = await deps.runCommandFn(
    ["git", "-C", repo.dir, "reset", "--hard", `origin/${branch}`],
    {
      check: false,
      timeoutMs: 60_000,
    },
  );

  return {
    item: {
      name: repo.name,
      success: resetResult.exitCode === 0,
      message: resetResult.exitCode === 0 ? undefined : resetResult.stderr,
    },
    updated: diff.behind > 0,
    missing: false,
  };
}

export async function runUpdate(
  options: UpdateOptions = {},
): Promise<UpdateResult> {
  const deps = options.deps ?? {};
  const skipNpm = options.skipNpm ?? false;
  const skipBun = options.skipBun ?? false;
  const skipRepos = options.skipRepos ?? false;
  const skipPlugins = options.skipPlugins ?? false;
  const commandExistsFn = deps.commandExistsFn ?? commandExists;
  const runCommandFn = deps.runCommandFn ?? runCommand;
  const accessFn = deps.accessFn ?? access;
  const loadCustomReposFn = deps.loadCustomReposFn ?? loadCustomRepos;
  const hasLocalChangesFn = deps.hasLocalChangesFn ?? hasLocalChanges;
  const backupDirtyFilesFn = deps.backupDirtyFilesFn ?? backupDirtyFiles;
  const npmPackages = deps.npmPackages ?? NPM_PACKAGES;
  const bunPackages = deps.bunPackages ?? BUN_PACKAGES;
  const repos = deps.repos ?? REPOS;
  const onProgress = options.onProgress ?? (() => {});

  const result: UpdateResult = {
    claudeCode: {
      name: "claude-code",
      success: true,
      message: "skipped",
    },
    tools: [],
    npmPackages: [],
    bunPackages: [],
    repos: [],
    customRepos: [],
    plugins: {
      name: "plugin-marketplace",
      success: true,
      message: "skipped",
    },
    summary: {
      updated: [],
      upToDate: [],
      missing: [],
    },
    errors: [],
  };

  onProgress("更新 Claude Code...");
  const claudeResult = await updateClaudeCode(onProgress, {
    commandExistsFn,
    runCommandFn,
  });
  result.claudeCode = {
    name: "claude-code",
    success: claudeResult.success,
    message: claudeResult.message,
  };

  onProgress("Running tools update: uds");
  const udsResult = await runCommandFn(["uds", "update"], {
    check: false,
    timeoutMs: 60_000,
  });
  result.tools.push({
    name: "uds",
    success: udsResult.exitCode === 0,
    message: udsResult.exitCode === 0 ? undefined : udsResult.stderr,
  });

  onProgress("Running tools update: npx skills update");
  const skillsResult = await runCommandFn(["npx", "skills", "update"], {
    check: false,
    timeoutMs: 60_000,
  });
  result.tools.push({
    name: "skills",
    success: skillsResult.exitCode === 0,
    message: skillsResult.exitCode === 0 ? undefined : skillsResult.stderr,
  });

  if (!skipNpm) {
    if (!commandExistsFn("npm")) {
      result.errors.push("npm is not installed");
    } else {
      const total = npmPackages.length;
      for (let index = 0; index < total; index += 1) {
        const pkg = npmPackages[index];
        onProgress(`[${index + 1}/${total}] Updating npm package: ${pkg}...`);
        const updateResult = await runCommandFn(["npm", "install", "-g", pkg], {
          check: false,
          timeoutMs: 60_000,
        });
        result.npmPackages.push({
          name: pkg,
          success: updateResult.exitCode === 0,
          message:
            updateResult.exitCode === 0 ? undefined : updateResult.stderr,
        });
      }
    }
  }

  if (!skipBun) {
    if (!commandExistsFn("bun")) {
      result.errors.push("bun is not installed");
    } else {
      const total = bunPackages.length;
      for (let index = 0; index < total; index += 1) {
        const pkg = bunPackages[index];
        onProgress(`[${index + 1}/${total}] Updating bun package: ${pkg}...`);
        const updateResult = await runCommandFn(["bun", "install", "-g", pkg], {
          check: false,
          timeoutMs: 60_000,
        });
        result.bunPackages.push({
          name: pkg,
          success: updateResult.exitCode === 0,
          message:
            updateResult.exitCode === 0 ? undefined : updateResult.stderr,
        });
      }
    }
  }

  if (!skipRepos) {
    for (const repo of repos) {
      onProgress(`Updating repository: ${repo.name}...`);
      const updated = await updateRepository(
        {
          name: repo.name,
          dir: repo.dir,
        },
        {
          runCommandFn,
          accessFn,
          hasLocalChangesFn,
          backupDirtyFilesFn,
        },
      );

      result.repos.push(updated.item);

      if (updated.missing) {
        result.summary.missing.push(repo.name);
      } else if (updated.updated) {
        result.summary.updated.push(repo.name);
      } else {
        result.summary.upToDate.push(repo.name);
      }
    }

    const customRepos = (await loadCustomReposFn()).repos;
    for (const [name, repo] of Object.entries(customRepos)) {
      onProgress(`Updating custom repository: ${name}...`);
      const updated = await updateRepository(
        {
          name,
          dir: repo.localPath,
        },
        {
          runCommandFn,
          accessFn,
          hasLocalChangesFn,
          backupDirtyFilesFn,
        },
      );
      result.customRepos.push(updated.item);
    }

    await refreshSuperpowersSymlink();
  }

  if (!skipPlugins) {
    onProgress("Updating plugin marketplace...");
    const pluginResult = await runCommandFn(
      ["npx", "@anthropic-ai/plugin-marketplace@latest", "update"],
      {
        check: false,
        timeoutMs: 60_000,
      },
    );
    result.plugins = {
      name: "plugin-marketplace",
      success: pluginResult.exitCode === 0,
      message: pluginResult.exitCode === 0 ? undefined : pluginResult.stderr,
    };
  }

  for (const toolResult of [
    result.claudeCode,
    ...result.tools,
    result.plugins,
  ]) {
    if (!toolResult.success && toolResult.message) {
      result.errors.push(toolResult.message);
    }
  }

  for (const item of [
    ...result.npmPackages,
    ...result.bunPackages,
    ...result.repos,
    ...result.customRepos,
  ]) {
    if (!item.success && item.message) {
      result.errors.push(item.message);
    }
  }

  return result;
}
