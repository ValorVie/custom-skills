import {
  access,
  cp,
  mkdir,
  readdir,
  readlink,
  rm,
  symlink,
} from "node:fs/promises";
import { homedir } from "node:os";
import { dirname, join } from "node:path";
import { backupDirtyFiles, hasLocalChanges } from "../utils/backup";
import { type CustomRepoConfig, loadCustomRepos } from "../utils/custom-repos";
import { paths } from "../utils/paths";
import { BUN_PACKAGES, NPM_PACKAGES, REPOS } from "../utils/shared";
import { commandExists, runCommand } from "../utils/system";
import { updateClaudeCode } from "./claude-code-manager";

type RepoConfig = (typeof REPOS)[number];

const OPENCODE_SUPERPOWERS_URL = "https://github.com/obra/superpowers.git";
const PACKAGE_UPDATE_TIMEOUT_MS = 180_000;

function toErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }
  return String(error);
}

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
  stream?: boolean;
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
  plugins: UpdateItemResult[];
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

async function syncOpencodeSuperpowersRepo(
  runCommandFn: typeof runCommand,
  accessFn: typeof access,
  onProgress: (message: string) => void,
  stream?: boolean,
): Promise<string> {
  const repoPath = paths.superpowersRepo;

  if (await pathExists(accessFn, join(repoPath, ".git"))) {
    onProgress("正在更新 OpenCode superpowers repo...");
    await runCommandFn(["git", "-C", repoPath, "pull"], {
      check: false,
      timeoutMs: 60_000,
      stream,
    });
  } else {
    onProgress("正在 clone OpenCode superpowers repo...");
    await mkdir(dirname(repoPath), { recursive: true });
    await runCommandFn(["git", "clone", OPENCODE_SUPERPOWERS_URL, repoPath], {
      check: false,
      timeoutMs: 120_000,
      stream,
    });
  }

  return repoPath;
}

async function refreshSuperpowersSymlink(
  onProgress: (message: string) => void,
): Promise<void> {
  try {
    await access(paths.superpowersRepo);
  } catch {
    return;
  }

  const isWindows = process.platform === "win32";

  // 1. Plugin symlink: opencodePlugins/superpowers.js
  const pluginDir = paths.opencodePlugins;
  await mkdir(pluginDir, { recursive: true });

  const pluginSource = join(paths.superpowersRepo, "superpowers.js");
  const pluginDest = join(pluginDir, "superpowers.js");

  try {
    const current = await readlink(pluginDest);
    if (current !== pluginSource) {
      await rm(pluginDest, { force: true });
      throw new Error("relink");
    }
  } catch {
    try {
      await rm(pluginDest, { force: true });
      if (isWindows) {
        await cp(pluginSource, pluginDest, { force: true });
      } else {
        await symlink(pluginSource, pluginDest);
      }
    } catch {
      // source may not exist
    }
  }

  // 2. Skills symlink: opencodeConfig/skills/superpowers
  const skillsDir = join(paths.opencodeConfig, "skills");
  await mkdir(skillsDir, { recursive: true });

  const skillsDest = join(skillsDir, "superpowers");

  try {
    const current = await readlink(skillsDest);
    if (current !== paths.superpowersRepo) {
      await rm(skillsDest, { recursive: true, force: true });
      throw new Error("relink");
    }
  } catch {
    await rm(skillsDest, { recursive: true, force: true });
    if (isWindows) {
      await cp(paths.superpowersRepo, skillsDest, {
        recursive: true,
        force: true,
      });
    } else {
      await symlink(paths.superpowersRepo, skillsDest, "dir");
    }
  }

  // 3. Legacy symlink: opencodeSuperpowers
  await mkdir(dirname(paths.opencodeSuperpowers), { recursive: true });

  try {
    const current = await readlink(paths.opencodeSuperpowers);
    if (current === paths.superpowersRepo) {
      onProgress("✓ OpenCode superpowers symlink 已更新");
      return;
    }
  } catch {
    // continue relinking
  }

  await rm(paths.opencodeSuperpowers, { recursive: true, force: true });
  if (isWindows) {
    await cp(paths.superpowersRepo, paths.opencodeSuperpowers, {
      recursive: true,
      force: true,
    });
  } else {
    await symlink(paths.superpowersRepo, paths.opencodeSuperpowers, "dir");
  }

  onProgress("✓ OpenCode superpowers symlink 已更新");
}

async function updateRepository(
  repo: { name: string; dir: string },
  deps: {
    runCommandFn: typeof runCommand;
    accessFn: typeof access;
    hasLocalChangesFn: typeof hasLocalChanges;
    backupDirtyFilesFn: typeof backupDirtyFiles;
    stream?: boolean;
  },
): Promise<{
  item: UpdateItemResult;
  updated: boolean;
  missing: boolean;
  branch: string;
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
      branch: "main",
    };
  }

  // Resolve branch BEFORE fetch so we can show it in progress
  const branch = await resolveCurrentBranch(repo.dir, deps.runCommandFn);

  const fetchResult = await deps.runCommandFn(
    ["git", "-C", repo.dir, "fetch", "--all"],
    {
      check: false,
      timeoutMs: 60_000,
      stream: deps.stream,
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
      branch,
    };
  }

  const diff = await compareRemote(repo.dir, branch, deps.runCommandFn);

  if (await deps.hasLocalChangesFn(repo.dir)) {
    await deps.backupDirtyFilesFn(repo.dir);
  }

  const resetResult = await deps.runCommandFn(
    ["git", "-C", repo.dir, "reset", "--hard", `origin/${branch}`],
    {
      check: false,
      timeoutMs: 60_000,
      stream: deps.stream,
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
    branch,
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
  const stream = options.stream ?? false;
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
    plugins: [],
    summary: {
      updated: [],
      upToDate: [],
      missing: [],
    },
    errors: [],
  };

  // #1 開始更新 header
  onProgress("開始更新...");

  // #2 skipNpm guards Claude Code + tools update
  if (!skipNpm) {
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

    // #6 uds update: check initialization
    const udsInitialized = await pathExists(
      accessFn,
      join(process.cwd(), ".standards"),
    );
    if (udsInitialized) {
      onProgress("正在更新專案 Standards...");
      const udsResult = await runCommandFn(["uds", "update"], {
        check: false,
        timeoutMs: 60_000,
        stream,
      });
      result.tools.push({
        name: "uds",
        success: udsResult.exitCode === 0,
        message: udsResult.exitCode === 0 ? undefined : udsResult.stderr,
      });
    } else {
      onProgress("ℹ️  當前目錄未初始化 Standards（跳過 uds update）");
      onProgress("   如需在此專案使用，請執行: uds init");
      result.tools.push({
        name: "uds",
        success: true,
        message: "not initialized, skipped",
      });
    }

    onProgress("正在更新 Skills...");
    const skillsResult = await runCommandFn(["npx", "skills", "update"], {
      check: false,
      timeoutMs: 60_000,
      stream,
    });
    result.tools.push({
      name: "skills",
      success: skillsResult.exitCode === 0,
      message: skillsResult.exitCode === 0 ? undefined : skillsResult.stderr,
    });
  } else {
    onProgress("跳過 Claude Code 更新");
    onProgress("跳過 NPM 套件更新");
  }

  // #7 NPM progress in Chinese
  if (!skipNpm) {
    if (!commandExistsFn("npm")) {
      result.errors.push("npm is not installed");
    } else {
      onProgress("正在更新全域 NPM 套件...");
      const total = npmPackages.length;
      for (let index = 0; index < total; index += 1) {
        const pkg = npmPackages[index];
        onProgress(`[${index + 1}/${total}] 正在更新 ${pkg}...`);
        try {
          const updateResult = await runCommandFn(["npm", "install", "-g", pkg], {
            check: false,
            timeoutMs: PACKAGE_UPDATE_TIMEOUT_MS,
            stream,
          });
          result.npmPackages.push({
            name: pkg,
            success: updateResult.exitCode === 0,
            message:
              updateResult.exitCode === 0 ? undefined : updateResult.stderr,
          });
        } catch (error) {
          result.npmPackages.push({
            name: pkg,
            success: false,
            message: toErrorMessage(error),
          });
        }
      }
    }
  }

  // #8 Bun not installed = warning not error; #15 skip message
  if (!skipBun) {
    if (!commandExistsFn("bun")) {
      onProgress("⚠️  Bun 未安裝，跳過 Bun 套件更新");
    } else {
      onProgress("正在更新 Bun 套件...");
      const total = bunPackages.length;
      for (let index = 0; index < total; index += 1) {
        const pkg = bunPackages[index];
        onProgress(`[${index + 1}/${total}] 正在更新 ${pkg}...`);
        try {
          const updateResult = await runCommandFn(["bun", "install", "-g", pkg], {
            check: false,
            timeoutMs: PACKAGE_UPDATE_TIMEOUT_MS,
            stream,
          });
          result.bunPackages.push({
            name: pkg,
            success: updateResult.exitCode === 0,
            message:
              updateResult.exitCode === 0 ? undefined : updateResult.stderr,
          });
        } catch (error) {
          result.bunPackages.push({
            name: pkg,
            success: false,
            message: toErrorMessage(error),
          });
        }
      }
    }
  } else {
    onProgress("跳過 Bun 套件更新");
  }

  // #15 skip repos message
  if (!skipRepos) {
    // #13 sync superpowers repo before repo loop
    await syncOpencodeSuperpowersRepo(
      runCommandFn,
      accessFn,
      onProgress,
      stream,
    );

    const missingRepoPaths: string[] = [];

    for (const repo of repos) {
      // #9 resolve branch BEFORE showing progress
      if (await pathExists(accessFn, join(repo.dir, ".git"))) {
        const branch = await resolveCurrentBranch(repo.dir, runCommandFn);
        onProgress(`正在更新 ${repo.name} (${branch})...`);
      } else {
        onProgress(`正在更新 ${repo.name}...`);
      }

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
          stream,
        },
      );

      result.repos.push(updated.item);

      if (updated.missing) {
        result.summary.missing.push(repo.name);
        missingRepoPaths.push(repo.dir);
      } else if (updated.updated) {
        result.summary.updated.push(repo.name);
      } else {
        result.summary.upToDate.push(repo.name);
      }
    }

    const customRepos = (await loadCustomReposFn()).repos;
    for (const [name, repo] of Object.entries(customRepos)) {
      if (await pathExists(accessFn, join(repo.localPath, ".git"))) {
        const branch = await resolveCurrentBranch(repo.localPath, runCommandFn);
        onProgress(`正在更新 ${name} (${branch})...`);
      } else {
        onProgress(`正在更新 ${name}...`);
      }

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
          stream,
        },
      );
      result.customRepos.push(updated.item);
    }

    // #10 grouped missing repos warning
    if (missingRepoPaths.length > 0) {
      onProgress("");
      onProgress("⚠ 以下儲存庫尚未 clone，已跳過更新：");
      for (const p of missingRepoPaths) {
        onProgress(`  • ${p}`);
      }
      onProgress(
        "請執行 `ai-dev install --skip-npm --skip-bun` 來補齊缺失的儲存庫",
      );
    }

    // #11 repo summary message
    if (result.summary.updated.length > 0) {
      onProgress("");
      onProgress("以下儲存庫有新更新：");
      for (const name of result.summary.updated) {
        onProgress(`  • ${name}`);
      }
    } else if (
      result.summary.upToDate.length > 0 &&
      missingRepoPaths.length === 0
    ) {
      onProgress("所有儲存庫皆為最新");
    }

    // #12 refresh superpowers symlinks (plugin + skills + legacy)
    await refreshSuperpowersSymlink(onProgress);
  } else {
    onProgress("跳過 Git 儲存庫更新");
  }

  // #15 skip plugins message; #16 plugin marketplace count messages
  if (!skipPlugins) {
    const marketplacesDir = join(
      homedir(),
      ".claude",
      "plugins",
      "marketplaces",
    );
    let marketplaceNames: string[] = [];
    let dirExists = false;

    try {
      const entries = await readdir(marketplacesDir, { withFileTypes: true });
      dirExists = true;
      marketplaceNames = entries
        .filter((e) => e.isDirectory())
        .map((e) => e.name);
    } catch {
      // directory does not exist
    }

    if (!dirExists) {
      onProgress("未偵測到 Claude Code Plugin 目錄");
    } else if (marketplaceNames.length === 0) {
      onProgress("未偵測到已安裝的 Plugin Marketplace");
    } else {
      onProgress(
        `正在更新 ${marketplaceNames.length} 個 Plugin Marketplace...`,
      );
      for (const name of marketplaceNames) {
        onProgress(`正在更新 marketplace: ${name}...`);
        const pluginResult = await runCommandFn(
          ["claude", "plugin", "marketplace", "update", name],
          {
            check: false,
            timeoutMs: 60_000,
            stream,
          },
        );
        result.plugins.push({
          name,
          success: pluginResult.exitCode === 0,
          message:
            pluginResult.exitCode === 0 ? undefined : pluginResult.stderr,
        });
      }
      onProgress(`已更新 ${marketplaceNames.length} 個 Marketplace`);
    }
  } else {
    onProgress("跳過 Plugin Marketplace 更新");
  }

  for (const toolResult of [
    result.claudeCode,
    ...result.tools,
    ...result.plugins,
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
