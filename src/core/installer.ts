import {
  access,
  mkdir,
  readlink,
  rm,
  symlink,
  writeFile,
} from "node:fs/promises";
import { basename, dirname, join } from "node:path";

import {
  type DistributeResult,
  distributeSkills,
} from "../core/skill-distributor";
import { type CustomRepoConfig, loadCustomRepos } from "../utils/custom-repos";
import { paths } from "../utils/paths";
import {
  BUN_PACKAGES,
  COPY_TARGETS,
  NPM_PACKAGES,
  REPOS,
  type TargetType,
} from "../utils/shared";
import { commandExists, getBunVersion, runCommand } from "../utils/system";
import { showClaudeStatus } from "./claude-code-manager";

type RepoConfig = (typeof REPOS)[number];

export interface InstallDependencies {
  commandExistsFn?: typeof commandExists;
  runCommandFn?: typeof runCommand;
  getBunVersionFn?: typeof getBunVersion;
  loadCustomReposFn?: () => Promise<CustomRepoConfig>;
  distributeSkillsFn?: (
    options?: Parameters<typeof distributeSkills>[0],
  ) => Promise<DistributeResult>;
  npmPackages?: readonly string[];
  bunPackages?: readonly string[];
  repos?: readonly RepoConfig[];
}

export interface InstallOptions {
  skipNpm?: boolean;
  skipBun?: boolean;
  skipRepos?: boolean;
  skipSkills?: boolean;
  syncProject?: boolean;
  stream?: boolean;
  deps?: InstallDependencies;
  onProgress?: (message: string) => void;
}

export interface InstallItemResult {
  name: string;
  success: boolean;
  message?: string;
  version?: string | null;
}

export interface PrerequisiteDetail {
  installed: boolean;
  version: string | null;
  meetsRequirement: boolean;
  hint?: string;
}

export interface InstallResult {
  prerequisites: {
    node: boolean;
    git: boolean;
    gh: boolean;
    bun: boolean;
  };
  prerequisiteDetails: {
    node: PrerequisiteDetail;
    git: PrerequisiteDetail;
    gh: PrerequisiteDetail;
    bun: PrerequisiteDetail;
  };
  claudeCode: {
    installed: boolean;
    version: string | null;
  };
  npmPackages: InstallItemResult[];
  bunPackages: InstallItemResult[];
  repos: InstallItemResult[];
  customRepos: InstallItemResult[];
  skills: {
    installed: string[];
    conflicts: string[];
  };
  shellCompletion: InstallItemResult;
  npmHint: string | null;
  errors: string[];
}

function normalizePackageName(packageName: string): string {
  if (packageName.startsWith("@")) {
    const slashIndex = packageName.indexOf("/");
    const atIndex = packageName.indexOf("@", slashIndex + 1);
    return atIndex === -1 ? packageName : packageName.slice(0, atIndex);
  }
  const atIndex = packageName.indexOf("@");
  return atIndex === -1 ? packageName : packageName.slice(0, atIndex);
}

function parseNodeMajor(version: string | null): number | null {
  if (!version) {
    return null;
  }

  const match = version.match(/v?(\d+)\./);
  if (!match) {
    return null;
  }

  return Number.parseInt(match[1], 10);
}

async function resolveVersion(
  command: string,
  runCommandFn: typeof runCommand,
): Promise<string | null> {
  const result = await runCommandFn([command, "--version"], {
    check: false,
    timeoutMs: 10_000,
  });

  if (result.exitCode !== 0) {
    return null;
  }

  const line = result.stdout.split(/\r?\n/)[0];
  return line?.trim() || null;
}

async function buildPrerequisiteDetails(
  commandExistsFn: typeof commandExists,
  runCommandFn: typeof runCommand,
  getBunVersionFn: typeof getBunVersion,
): Promise<InstallResult["prerequisiteDetails"]> {
  const nodeInstalled = commandExistsFn("node");
  const gitInstalled = commandExistsFn("git");
  const ghInstalled = commandExistsFn("gh");
  const bunInstalled = commandExistsFn("bun");

  const nodeVersion = nodeInstalled
    ? await resolveVersion("node", runCommandFn)
    : null;
  const gitVersion = gitInstalled
    ? await resolveVersion("git", runCommandFn)
    : null;
  const ghVersion = ghInstalled
    ? await resolveVersion("gh", runCommandFn)
    : null;
  const bunVersion = bunInstalled ? await getBunVersionFn() : null;
  const nodeMajor = parseNodeMajor(nodeVersion);

  return {
    node: {
      installed: nodeInstalled,
      version: nodeVersion,
      meetsRequirement:
        nodeInstalled && (nodeMajor === null || nodeMajor >= 20),
      hint: "Install Node.js >= 20 from https://nodejs.org/",
    },
    git: {
      installed: gitInstalled,
      version: gitVersion,
      meetsRequirement: gitInstalled,
      hint: "Install Git from https://git-scm.com/",
    },
    gh: {
      installed: ghInstalled,
      version: ghVersion,
      meetsRequirement: ghInstalled,
      hint: "Install GitHub CLI from https://cli.github.com/",
    },
    bun: {
      installed: bunInstalled,
      version: bunVersion,
      meetsRequirement: bunInstalled,
      hint: "Install Bun from https://bun.sh/",
    },
  };
}

async function getNpmPackageVersion(
  packageName: string,
  runCommandFn: typeof runCommand,
): Promise<string | null> {
  const normalized = normalizePackageName(packageName);
  const result = await runCommandFn(
    ["npm", "list", "-g", normalized, "--depth=0", "--json"],
    {
      check: false,
      timeoutMs: 60_000,
    },
  );

  if (result.exitCode !== 0) {
    return null;
  }

  try {
    const parsed = JSON.parse(result.stdout) as {
      dependencies?: Record<string, { version?: string }>;
    };
    return parsed.dependencies?.[normalized]?.version ?? null;
  } catch {
    return null;
  }
}

async function installNpmPackage(
  packageName: string,
  runCommandFn: typeof runCommand,
  stream = false,
): Promise<InstallItemResult> {
  const beforeVersion = await getNpmPackageVersion(packageName, runCommandFn);
  const result = await runCommandFn(["npm", "install", "-g", packageName], {
    check: false,
    timeoutMs: 60_000,
    stream,
  });
  const afterVersion = await getNpmPackageVersion(packageName, runCommandFn);

  return {
    name: packageName,
    success: result.exitCode === 0,
    message: result.exitCode === 0 ? undefined : result.stderr,
    version: afterVersion ?? beforeVersion,
  };
}

async function installBunPackage(
  packageName: string,
  runCommandFn: typeof runCommand,
  stream = false,
): Promise<InstallItemResult> {
  const result = await runCommandFn(["bun", "install", "-g", packageName], {
    check: false,
    timeoutMs: 60_000,
    stream,
  });

  return {
    name: packageName,
    success: result.exitCode === 0,
    message: result.exitCode === 0 ? undefined : result.stderr,
  };
}

async function ensureRepo(
  repoName: string,
  repoUrl: string,
  repoDir: string,
  runCommandFn: typeof runCommand,
  stream = false,
): Promise<InstallItemResult> {
  try {
    await access(join(repoDir, ".git"));
    return {
      name: repoName,
      success: true,
      message: "already cloned",
    };
  } catch {
    // continue cloning
  }

  await mkdir(dirname(repoDir), { recursive: true });
  const result = await runCommandFn(["git", "clone", repoUrl, repoDir], {
    check: false,
    timeoutMs: 120_000,
    stream,
  });

  return {
    name: repoName,
    success: result.exitCode === 0,
    message: result.exitCode === 0 ? undefined : result.stderr,
  };
}

function targetDirectories(): string[] {
  const dirs = new Set<string>();

  for (const target of Object.keys(COPY_TARGETS) as TargetType[]) {
    const mapping = COPY_TARGETS[target];
    for (const value of Object.values(mapping)) {
      if (value) {
        dirs.add(value);
      }
    }
  }

  dirs.add(paths.opencodeSuperpowers);
  dirs.add(paths.aiDevConfig);

  return [...dirs];
}

async function ensureTargetDirectories(): Promise<void> {
  for (const dir of targetDirectories()) {
    await mkdir(dir, { recursive: true });
  }
}

async function pathExists(pathValue: string): Promise<boolean> {
  try {
    await access(pathValue);
    return true;
  } catch {
    return false;
  }
}

async function detectDistributionSourceRoot(): Promise<string> {
  const cwd = process.cwd();
  if (
    basename(cwd) === "custom-skills" &&
    (await pathExists(join(cwd, "skills")))
  ) {
    return cwd;
  }

  if (await pathExists(join(paths.customSkills, "skills"))) {
    return paths.customSkills;
  }

  return cwd;
}

async function syncSuperpowersSymlink(): Promise<InstallItemResult> {
  if (!(await pathExists(paths.superpowersRepo))) {
    return {
      name: "opencode-superpowers",
      success: false,
      message: "superpowers repository not found",
    };
  }

  await mkdir(dirname(paths.opencodeSuperpowers), { recursive: true });

  try {
    const current = await readlink(paths.opencodeSuperpowers);
    if (current === paths.superpowersRepo) {
      return {
        name: "opencode-superpowers",
        success: true,
        message: "already linked",
      };
    }
  } catch {
    // continue relink
  }

  await rm(paths.opencodeSuperpowers, { recursive: true, force: true });
  await symlink(paths.superpowersRepo, paths.opencodeSuperpowers, "dir");

  return {
    name: "opencode-superpowers",
    success: true,
  };
}

async function installShellCompletion(): Promise<InstallItemResult> {
  const shellName = (process.env.SHELL ?? "sh").split("/").pop() ?? "sh";
  const completionDir = join(paths.aiDevConfig, "completions");
  const completionPath = join(completionDir, `ai-dev.${shellName}`);

  await mkdir(completionDir, { recursive: true });
  await writeFile(
    completionPath,
    "# ai-dev shell completion placeholder\n# TODO: wire generated completion script\n",
    "utf8",
  );

  return {
    name: "shell-completion",
    success: true,
    message: completionPath,
  };
}

export async function runInstall(
  options: InstallOptions = {},
): Promise<InstallResult> {
  const deps = options.deps ?? {};
  const skipNpm = options.skipNpm ?? false;
  const skipBun = options.skipBun ?? false;
  const skipRepos = options.skipRepos ?? false;
  const skipSkills = options.skipSkills ?? false;
  const syncProject = options.syncProject ?? false;
  const stream = options.stream ?? false;
  const commandExistsFn = deps.commandExistsFn ?? commandExists;
  const runCommandFn = deps.runCommandFn ?? runCommand;
  const getBunVersionFn = deps.getBunVersionFn ?? getBunVersion;
  const loadCustomReposFn = deps.loadCustomReposFn ?? loadCustomRepos;
  const distributeSkillsFn = deps.distributeSkillsFn ?? distributeSkills;
  const npmPackages = deps.npmPackages ?? NPM_PACKAGES;
  const bunPackages = deps.bunPackages ?? BUN_PACKAGES;
  const repos = deps.repos ?? REPOS;
  const onProgress = options.onProgress ?? (() => {});

  const prerequisiteDetails = await buildPrerequisiteDetails(
    commandExistsFn,
    runCommandFn,
    getBunVersionFn,
  );

  const prerequisites = {
    node:
      prerequisiteDetails.node.installed &&
      prerequisiteDetails.node.meetsRequirement,
    git: prerequisiteDetails.git.installed,
    gh: prerequisiteDetails.gh.installed,
    bun: prerequisiteDetails.bun.installed,
  };

  const result: InstallResult = {
    prerequisites,
    prerequisiteDetails,
    claudeCode: {
      installed: commandExistsFn("claude"),
      version: null,
    },
    npmPackages: [],
    bunPackages: [],
    repos: [],
    customRepos: [],
    skills: {
      installed: [],
      conflicts: [],
    },
    shellCompletion: {
      name: "shell-completion",
      success: false,
      message: "skipped",
    },
    npmHint: null,
    errors: [],
  };

  onProgress("檢查 Claude Code 安裝狀態...");
  const claudeStatus = await showClaudeStatus(onProgress, {
    commandExistsFn,
    runCommandFn,
  });
  result.claudeCode = {
    installed: claudeStatus.type !== null,
    version: claudeStatus.version,
  };

  if (!prerequisiteDetails.node.installed) {
    result.errors.push("Node.js is required");
  } else if (!prerequisiteDetails.node.meetsRequirement) {
    result.errors.push("Node.js >= 20 is required");
  }

  if (!prerequisiteDetails.git.installed) {
    result.errors.push("Git is required");
  }

  if (!prerequisiteDetails.gh.installed) {
    result.errors.push("GitHub CLI (gh) is required");
  }

  await ensureTargetDirectories();

  if (!skipNpm && prerequisites.node) {
    const total = npmPackages.length;
    for (let index = 0; index < total; index += 1) {
      const pkg = npmPackages[index];
      onProgress(`[${index + 1}/${total}] Installing npm package: ${pkg}...`);
      result.npmPackages.push(
        await installNpmPackage(pkg, runCommandFn, stream),
      );
    }
  }

  if (!skipBun) {
    if (!prerequisiteDetails.bun.installed) {
      result.errors.push(
        "Bun is not installed; skipped Bun package installation",
      );
    } else {
      const total = bunPackages.length;
      for (let index = 0; index < total; index += 1) {
        const pkg = bunPackages[index];
        onProgress(`[${index + 1}/${total}] Installing bun package: ${pkg}...`);
        result.bunPackages.push(
          await installBunPackage(pkg, runCommandFn, stream),
        );
      }
    }
  }

  if (!skipRepos && prerequisites.git) {
    for (const repo of repos) {
      onProgress(`Cloning repository: ${repo.name}...`);
      result.repos.push(
        await ensureRepo(repo.name, repo.url, repo.dir, runCommandFn, stream),
      );
    }

    const customRepos = (await loadCustomReposFn()).repos;
    for (const [name, repo] of Object.entries(customRepos)) {
      onProgress(`Cloning custom repository: ${name}...`);
      result.customRepos.push(
        await ensureRepo(name, repo.url, repo.localPath, runCommandFn, stream),
      );
    }

    await syncSuperpowersSymlink();
  }

  if (!skipSkills) {
    const sourceRoot = await detectDistributionSourceRoot();
    const distribution = await distributeSkillsFn({
      sourceRoot,
      force: true,
      skipConflicts: false,
      backup: false,
      devMode: false,
      onProgress,
    });

    result.skills.installed = distribution.distributed
      .filter((item) => item.type === "skills")
      .map((item) => item.name)
      .sort((a, b) => a.localeCompare(b));

    result.skills.conflicts = distribution.conflicts
      .filter((item) => item.type === "skills")
      .map((item) => item.name)
      .sort((a, b) => a.localeCompare(b));

    for (const error of distribution.errors) {
      result.errors.push(`distribution: ${error}`);
    }
  }

  if (syncProject) {
    onProgress("sync-project requested");
  }

  result.shellCompletion = await installShellCompletion();
  result.npmHint = "Tip: run `npx skills --help` to explore community skills.";

  return result;
}
