import { readdir } from "node:fs/promises";
import { join } from "node:path";

import {
  loadCustomRepos,
  type CustomRepoConfig,
} from "../../utils/custom-repos";
import { REPOS, type ResourceType } from "../../utils/shared";

export type SourceIndex = Record<ResourceType, Map<string, string>>;

export interface SourceRoot {
  source: string;
  root: string;
}

export interface CollectSourceRootsOptions {
  cwd?: string;
  loadCustomReposFn?: () => Promise<CustomRepoConfig>;
}

export interface CollectSourceIndexOptions extends CollectSourceRootsOptions {
  roots?: SourceRoot[];
}

function createSourceIndex(): SourceIndex {
  return {
    skills: new Map<string, string>(),
    commands: new Map<string, string>(),
    agents: new Map<string, string>(),
    workflows: new Map<string, string>(),
  };
}

export function normalizeSourceName(source: string): string {
  if (source === "uds") {
    return "universal-dev-standards";
  }
  return source;
}

async function listFilesRecursive(
  baseDir: string,
  relativeDir = "",
): Promise<string[]> {
  const currentDir = relativeDir ? join(baseDir, relativeDir) : baseDir;
  const entries = await readdir(currentDir, { withFileTypes: true });
  const files: string[] = [];

  for (const entry of entries) {
    if (entry.name.startsWith(".")) {
      continue;
    }

    const relativePath = relativeDir
      ? `${relativeDir}/${entry.name}`
      : entry.name;

    if (entry.isDirectory()) {
      files.push(...(await listFilesRecursive(baseDir, relativePath)));
      continue;
    }

    files.push(relativePath);
  }

  return files;
}

function addToIndex(
  index: SourceIndex,
  resourceType: ResourceType,
  name: string,
  source: string,
): void {
  if (!index[resourceType].has(name)) {
    index[resourceType].set(name, source);
  }
}

async function indexSourceRoot(
  index: SourceIndex,
  sourceRoot: SourceRoot,
): Promise<void> {
  const skillDir = join(sourceRoot.root, "skills");
  try {
    const skillEntries = await readdir(skillDir, { withFileTypes: true });
    for (const entry of skillEntries) {
      if (entry.isDirectory() && !entry.name.startsWith(".")) {
        addToIndex(index, "skills", entry.name, sourceRoot.source);
      }
    }
  } catch {
    // ignore missing skills directory
  }

  for (const type of ["commands", "agents", "workflows"] as const) {
    const typeDir = join(sourceRoot.root, type);
    try {
      const files = await listFilesRecursive(typeDir);
      for (const file of files) {
        if (!file.endsWith(".md")) {
          continue;
        }
        const name = file.split("/").at(-1)?.replace(/\.md$/, "");
        if (!name) {
          continue;
        }
        addToIndex(index, type, name, sourceRoot.source);
      }
    } catch {
      // ignore missing type directory
    }
  }
}

export async function collectSourceRoots(
  options: CollectSourceRootsOptions = {},
): Promise<SourceRoot[]> {
  const cwd = options.cwd ?? process.cwd();
  const roots: SourceRoot[] = [{ source: "custom-skills", root: cwd }];

  for (const repo of REPOS) {
    if (repo.dir === cwd) {
      continue;
    }
    roots.push({
      source: normalizeSourceName(repo.name),
      root: repo.dir,
    });
  }

  const loadFn = options.loadCustomReposFn ?? loadCustomRepos;
  const customRepos = await loadFn();
  for (const [name, repo] of Object.entries(customRepos.repos)) {
    roots.push({ source: name, root: repo.localPath });
  }

  return roots;
}

export async function collectSourceIndex(
  options: CollectSourceIndexOptions = {},
): Promise<SourceIndex> {
  const roots =
    options.roots ??
    (await collectSourceRoots({
      cwd: options.cwd,
      loadCustomReposFn: options.loadCustomReposFn,
    }));
  const index = createSourceIndex();

  for (const root of roots) {
    await indexSourceRoot(index, root);
  }

  return index;
}

export function resolveResourceSource(
  index: SourceIndex,
  resourceType: ResourceType,
  name: string,
  fallback = "user-custom",
): string {
  return index[resourceType].get(name) ?? fallback;
}
