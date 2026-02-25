import { mkdir, readFile, writeFile } from "node:fs/promises";
import { homedir } from "node:os";
import { join } from "node:path";

import YAML from "yaml";

export interface CustomRepoEntry {
  url: string;
  branch: string;
  localPath: string;
  addedAt: string;
}

export interface CustomRepoConfig {
  repos: Record<string, CustomRepoEntry>;
}

export interface ParsedRepo {
  name: string;
  repoPath: string;
  url: string;
  defaultBranch: string;
}

export function getCustomReposConfigPath(): string {
  return join(homedir(), ".config", "ai-dev", "repos.yaml");
}

export async function loadCustomRepos(): Promise<CustomRepoConfig> {
  const filePath = getCustomReposConfigPath();

  try {
    const content = await readFile(filePath, "utf8");
    const parsed = YAML.parse(content) as CustomRepoConfig | null;
    if (!parsed || typeof parsed !== "object") {
      return { repos: {} };
    }
    if (!parsed.repos || typeof parsed.repos !== "object") {
      parsed.repos = {};
    }
    return parsed;
  } catch (error) {
    const err = error as NodeJS.ErrnoException;
    if (err.code === "ENOENT") {
      return { repos: {} };
    }
    throw error;
  }
}

export async function saveCustomRepos(config: CustomRepoConfig): Promise<void> {
  const filePath = getCustomReposConfigPath();
  await mkdir(join(homedir(), ".config", "ai-dev"), { recursive: true });
  await writeFile(filePath, YAML.stringify(config), "utf8");
}

export function parseRepoUrl(input: string): ParsedRepo {
  const value = input.trim().replace(/\/$/, "");
  const withoutGit = value.endsWith(".git") ? value.slice(0, -4) : value;

  if (withoutGit.startsWith("https://github.com/")) {
    const rest = withoutGit.replace("https://github.com/", "");
    const [owner, repo] = rest.split("/");
    if (!owner || !repo) {
      throw new Error(`Invalid GitHub URL: ${input}`);
    }
    return {
      name: repo,
      repoPath: `${owner}/${repo}`,
      url: `https://github.com/${owner}/${repo}.git`,
      defaultBranch: "main",
    };
  }

  if (withoutGit.startsWith("git@github.com:")) {
    const rest = withoutGit.replace("git@github.com:", "");
    const [owner, repo] = rest.split("/");
    if (!owner || !repo) {
      throw new Error(`Invalid GitHub SSH URL: ${input}`);
    }
    return {
      name: repo,
      repoPath: `${owner}/${repo}`,
      url: `git@github.com:${owner}/${repo}.git`,
      defaultBranch: "main",
    };
  }

  const parts = withoutGit.split("/");
  if (parts.length === 2 && parts[0] && parts[1]) {
    const [owner, repo] = parts;
    return {
      name: repo,
      repoPath: `${owner}/${repo}`,
      url: `https://github.com/${owner}/${repo}.git`,
      defaultBranch: "main",
    };
  }

  throw new Error(`Unsupported repository format: ${input}`);
}

export async function addCustomRepo(
  name: string,
  url: string,
  branch: string,
  localPath: string,
): Promise<void> {
  const config = await loadCustomRepos();
  config.repos[name] = {
    url,
    branch,
    localPath,
    addedAt: new Date().toISOString(),
  };
  await saveCustomRepos(config);
}
