import { access, mkdir, readFile, writeFile } from "node:fs/promises";
import { homedir } from "node:os";
import { join } from "node:path";

import YAML from "yaml";

import { parseRepoUrl } from "../utils/custom-repos";
import { type CommandResult, runCommand } from "../utils/system";

export type RepoFormat =
  | "uds"
  | "claude-code-native"
  | "skills-repo"
  | "unknown";

export interface RepoAnalysis {
  format: RepoFormat;
  hasStandards: boolean;
  hasSkills: boolean;
  hasCommands: boolean;
  hasAgents: boolean;
  hasWorkflows: boolean;
  recommendation: string;
}

interface UpstreamSourceEntry {
  repo: string;
  branch: string;
  local_path: string;
  format: RepoFormat;
  install_method: "standards" | "ai-dev" | "manual";
}

interface UpstreamSourcesConfig {
  sources: Record<string, UpstreamSourceEntry>;
}

export interface AddUpstreamRepoOptions {
  repoInput: string;
  name?: string;
  branch?: string;
  skipClone?: boolean;
  analyze?: boolean;
  projectRoot?: string;
  configDir?: string;
  runCommandFn?: (
    command: string[],
    options?: { cwd?: string; check?: boolean },
  ) => Promise<CommandResult>;
}

export interface AddUpstreamRepoResult {
  success: boolean;
  duplicate: boolean;
  name: string;
  repo: string;
  branch: string;
  localPath: string;
  format: RepoFormat;
  analysis?: RepoAnalysis;
  message?: string;
}

function upstreamSourcesPath(projectRoot: string): string {
  return join(projectRoot, "upstream", "sources.yaml");
}

async function pathExists(path: string): Promise<boolean> {
  try {
    await access(path);
    return true;
  } catch {
    return false;
  }
}

async function loadSourcesConfig(
  projectRoot: string,
): Promise<UpstreamSourcesConfig> {
  const path = upstreamSourcesPath(projectRoot);
  try {
    const content = await readFile(path, "utf8");
    const parsed = (YAML.parse(content) as UpstreamSourcesConfig | null) ?? {
      sources: {},
    };
    if (!parsed.sources || typeof parsed.sources !== "object") {
      parsed.sources = {};
    }
    return parsed;
  } catch {
    return { sources: {} };
  }
}

async function saveSourcesConfig(
  projectRoot: string,
  config: UpstreamSourcesConfig,
): Promise<void> {
  const path = upstreamSourcesPath(projectRoot);
  await mkdir(join(projectRoot, "upstream"), { recursive: true });
  await writeFile(path, YAML.stringify(config), "utf8");
}

export async function detectRepoFormat(repoDir: string): Promise<RepoFormat> {
  if (await pathExists(join(repoDir, ".standards"))) {
    return "uds";
  }

  const hasSkills = await pathExists(join(repoDir, "skills"));
  const hasCommands = await pathExists(join(repoDir, "commands"));
  const hasAgents = await pathExists(join(repoDir, "agents"));
  const hasWorkflows = await pathExists(join(repoDir, "workflows"));

  if (hasSkills && (hasCommands || hasAgents || hasWorkflows)) {
    return "claude-code-native";
  }

  if (hasSkills) {
    return "skills-repo";
  }

  return "unknown";
}

export async function analyzeRepositoryStructure(
  repoDir: string,
): Promise<RepoAnalysis> {
  const hasStandards = await pathExists(join(repoDir, ".standards"));
  const hasSkills = await pathExists(join(repoDir, "skills"));
  const hasCommands = await pathExists(join(repoDir, "commands"));
  const hasAgents = await pathExists(join(repoDir, "agents"));
  const hasWorkflows = await pathExists(join(repoDir, "workflows"));
  const format = await detectRepoFormat(repoDir);

  const recommendation =
    format === "uds"
      ? "Use standards sync workflow"
      : format === "claude-code-native"
        ? "Use ai-dev clone distribution"
        : format === "skills-repo"
          ? "Use ai-dev clone with skills-only integration"
          : "Review repository manually before integration";

  return {
    format,
    hasStandards,
    hasSkills,
    hasCommands,
    hasAgents,
    hasWorkflows,
    recommendation,
  };
}

function getInstallMethod(
  format: RepoFormat,
): "standards" | "ai-dev" | "manual" {
  if (format === "uds") {
    return "standards";
  }
  if (format === "claude-code-native" || format === "skills-repo") {
    return "ai-dev";
  }
  return "manual";
}

export async function addUpstreamRepo(
  options: AddUpstreamRepoOptions,
): Promise<AddUpstreamRepoResult> {
  const projectRoot = options.projectRoot ?? process.cwd();
  const branch = options.branch ?? "main";
  const configDir = options.configDir ?? join(homedir(), ".config");
  const runner = options.runCommandFn ?? runCommand;

  const parsed = parseRepoUrl(options.repoInput);
  const name = options.name ?? parsed.name;
  const localPath = join(configDir, name);

  const config = await loadSourcesConfig(projectRoot);
  const duplicate = Object.entries(config.sources).some(([key, entry]) => {
    return key === name || entry.repo === parsed.repoPath;
  });

  if (duplicate) {
    return {
      success: false,
      duplicate: true,
      name,
      repo: parsed.repoPath,
      branch,
      localPath,
      format: "unknown",
      message: `Repository already exists in upstream sources: ${parsed.repoPath}`,
    };
  }

  if (!options.skipClone) {
    if (!(await pathExists(localPath))) {
      const clone = await runner(["git", "clone", parsed.url, localPath], {
        check: false,
      });
      if (clone.exitCode !== 0) {
        return {
          success: false,
          duplicate: false,
          name,
          repo: parsed.repoPath,
          branch,
          localPath,
          format: "unknown",
          message: `Clone failed: ${clone.stderr || clone.stdout}`,
        };
      }
    }
  }

  const analysis = await analyzeRepositoryStructure(localPath);

  config.sources[name] = {
    repo: parsed.repoPath,
    branch,
    local_path: localPath,
    format: analysis.format,
    install_method: getInstallMethod(analysis.format),
  };
  await saveSourcesConfig(projectRoot, config);

  return {
    success: true,
    duplicate: false,
    name,
    repo: parsed.repoPath,
    branch,
    localPath,
    format: analysis.format,
    analysis: options.analyze ? analysis : undefined,
  };
}
