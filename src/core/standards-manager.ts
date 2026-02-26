import { mkdir, readdir, readFile, rename, writeFile } from "node:fs/promises";
import { join, resolve } from "node:path";

import YAML from "yaml";

import { COPY_TARGETS, type ResourceType, type TargetType } from "../utils/shared";

export interface StandardsStatus {
  initialized: boolean;
  activeProfile: string | null;
  availableProfiles: string[];
}

export interface SwitchProfileResult {
  success: boolean;
  profile: string;
  dryRun: boolean;
  disabledCount?: number;
  movedToDisabled?: number;
  restoredToActive?: number;
  message?: string;
}

export interface DisabledItems {
  standards: string[];
  skills?: string[];
  commands?: string[];
  agents?: string[];
}

export interface SyncStandardsResult {
  success: boolean;
  movedToDisabled: number;
  restoredToActive: number;
  missing: string[];
}

function standardsDir(projectRoot: string): string {
  return join(projectRoot, ".standards");
}

function profilesDir(projectRoot: string): string {
  return join(standardsDir(projectRoot), "profiles");
}

function activeProfilePath(projectRoot: string): string {
  return join(standardsDir(projectRoot), "active-profile.yaml");
}

function disabledYamlPath(projectRoot: string): string {
  return join(standardsDir(projectRoot), "disabled.yaml");
}

function disabledStandardsDir(projectRoot: string): string {
  return join(standardsDir(projectRoot), ".disabled");
}

function overlapsPath(projectRoot: string): string {
  return join(profilesDir(projectRoot), "overlaps.yaml");
}

function isStandardsFile(fileName: string): boolean {
  return fileName.endsWith(".ai.yaml") || fileName.endsWith(".md");
}

function normalizeRelativePath(value: string): string {
  return value.replaceAll("\\", "/").replace(/^\/+/, "");
}

async function listFilesRecursive(
  baseDir: string,
  relativeDir = "",
): Promise<string[]> {
  const currentDir = relativeDir ? join(baseDir, relativeDir) : baseDir;
  const entries = await readdir(currentDir, { withFileTypes: true });
  const files: string[] = [];

  for (const entry of entries) {
    const relativePath = relativeDir
      ? `${normalizeRelativePath(relativeDir)}/${entry.name}`
      : entry.name;

    if (entry.isDirectory()) {
      files.push(...(await listFilesRecursive(baseDir, relativePath)));
      continue;
    }

    files.push(normalizeRelativePath(relativePath));
  }

  return files;
}

async function listStandardFiles(projectRoot: string): Promise<string[]> {
  const root = standardsDir(projectRoot);
  if (!(await pathExists(root))) {
    return [];
  }

  const allFiles = await listFilesRecursive(root);
  return allFiles
    .filter((path) => {
      if (!isStandardsFile(path)) {
        return false;
      }
      if (path.startsWith("profiles/")) {
        return false;
      }
      if (path.startsWith(".disabled/")) {
        return false;
      }
      return true;
    })
    .sort((a, b) => a.localeCompare(b));
}

async function listDisabledStandardFiles(
  projectRoot: string,
): Promise<string[]> {
  const root = disabledStandardsDir(projectRoot);
  if (!(await pathExists(root))) {
    return [];
  }

  const files = await listFilesRecursive(root);
  return files
    .filter((path) => isStandardsFile(path))
    .sort((a, b) => a.localeCompare(b));
}

function toStringArray(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return [];
  }

  return value
    .filter(
      (item): item is string => typeof item === "string" && item.length > 0,
    )
    .map((item) => normalizeRelativePath(item));
}

async function loadProfileConfig(
  profileName: string,
  projectRoot: string,
): Promise<Record<string, unknown>> {
  const path = join(profilesDir(projectRoot), `${profileName}.yaml`);
  const content = await readFile(path, "utf8");
  return (YAML.parse(content) as Record<string, unknown> | null) ?? {};
}

async function getEnabledStandards(
  profileName: string,
  projectRoot: string,
): Promise<Set<string>> {
  const enabled = new Set<string>();
  const profile = await loadProfileConfig(profileName, projectRoot);

  for (const item of toStringArray(profile.standards)) {
    enabled.add(item);
  }

  for (const item of toStringArray(profile.enabled_standards)) {
    enabled.add(item);
  }

  try {
    const overlapsContent = await readFile(overlapsPath(projectRoot), "utf8");
    const overlaps =
      (YAML.parse(overlapsContent) as Record<
        string,
        Record<string, unknown>
      > | null) ?? {};

    const shared = overlaps.shared as Record<string, unknown> | undefined;
    for (const item of toStringArray(shared?.standards)) {
      enabled.add(item);
    }

    const preferenceValue = profile.overlap_preference;
    const preference =
      typeof preferenceValue === "string" && preferenceValue.length > 0
        ? preferenceValue
        : profileName;

    const groups =
      (overlaps.groups as
        | Record<string, Record<string, unknown>>
        | undefined) ?? {};
    const explicitEnabledGroups = toStringArray(profile.enabled_groups);
    const enabledGroups =
      explicitEnabledGroups.length > 0
        ? explicitEnabledGroups
        : Object.keys(groups);

    for (const groupName of enabledGroups) {
      const group = groups[groupName];
      if (!group) {
        continue;
      }

      const picked = group[preference] as Record<string, unknown> | undefined;
      for (const item of toStringArray(picked?.standards)) {
        enabled.add(item);
      }
    }

    const enableExclusive =
      (profile.enable_exclusive as Record<string, unknown> | undefined) ?? {};
    const exclusive =
      (overlaps.exclusive as
        | Record<string, Record<string, unknown>>
        | undefined) ?? {};

    for (const [systemName, value] of Object.entries(enableExclusive)) {
      if (value !== true) {
        continue;
      }
      const system = exclusive[systemName];
      if (!system) {
        continue;
      }
      for (const item of toStringArray(system.standards)) {
        enabled.add(item);
      }
    }
  } catch {
    // keep explicit profile standards only
  }

  return enabled;
}

async function readDisabledYaml(projectRoot: string): Promise<DisabledItems> {
  try {
    const content = await readFile(disabledYamlPath(projectRoot), "utf8");
    const parsed =
      (YAML.parse(content) as Record<string, unknown> | null) ?? {};
    return {
      standards: toStringArray(parsed.standards),
      skills: toStringArray(parsed.skills),
      commands: toStringArray(parsed.commands),
      agents: toStringArray(parsed.agents),
    };
  } catch {
    return { standards: [] };
  }
}

async function moveRelativeFile(
  fromBase: string,
  toBase: string,
  relativePath: string,
): Promise<boolean> {
  const normalized = normalizeRelativePath(relativePath);
  const from = join(fromBase, normalized);
  const to = join(toBase, normalized);

  if (!(await pathExists(from))) {
    return false;
  }

  const parent = resolve(to, "..");
  await mkdir(parent, { recursive: true });
  await rename(from, to);
  return true;
}

export async function computeDisabledItems(
  profileName: string,
  projectRoot = process.cwd(),
): Promise<DisabledItems> {
  const root = resolve(projectRoot);
  const allStandards = await listStandardFiles(root);
  const enabled = await getEnabledStandards(profileName, root);

  const effectiveEnabled =
    enabled.size > 0
      ? enabled
      : new Set<string>(
          allStandards.map((path) => normalizeRelativePath(path)),
        );

  const disabledStandards = allStandards
    .map((path) => normalizeRelativePath(path))
    .filter((path) => !effectiveEnabled.has(path))
    .sort((a, b) => a.localeCompare(b));

  // Read profile for resource-level disabled items
  const profile = await loadProfileConfig(profileName, root);
  const disabledSkills = toStringArray(profile.disabled_skills);
  const disabledCommands = toStringArray(profile.disabled_commands);
  const disabledAgents = toStringArray(profile.disabled_agents);

  return {
    standards: disabledStandards,
    ...(disabledSkills.length > 0 ? { skills: disabledSkills } : {}),
    ...(disabledCommands.length > 0 ? { commands: disabledCommands } : {}),
    ...(disabledAgents.length > 0 ? { agents: disabledAgents } : {}),
  };
}

export async function syncStandards(
  projectRoot = process.cwd(),
): Promise<SyncStandardsResult> {
  const root = resolve(projectRoot);
  const standardsRoot = standardsDir(root);
  const disabledRoot = disabledStandardsDir(root);
  await mkdir(disabledRoot, { recursive: true });

  const disabled = await readDisabledYaml(root);
  const disabledSet = new Set(
    disabled.standards.map((item) => normalizeRelativePath(item)),
  );

  let movedToDisabled = 0;
  let restoredToActive = 0;
  const missing: string[] = [];

  for (const item of disabledSet) {
    const moved = await moveRelativeFile(standardsRoot, disabledRoot, item);
    const existsInDisabled = await pathExists(join(disabledRoot, item));
    if (moved) {
      movedToDisabled += 1;
      continue;
    }
    if (!existsInDisabled) {
      missing.push(item);
    }
  }

  const currentlyDisabled = await listDisabledStandardFiles(root);
  for (const item of currentlyDisabled) {
    if (disabledSet.has(item)) {
      continue;
    }
    const restored = await moveRelativeFile(disabledRoot, standardsRoot, item);
    if (restored) {
      restoredToActive += 1;
    }
  }

  // Sync resources (skills/commands/agents) across all targets
  const resourceTypes: ResourceType[] = ["skills", "commands", "agents"];
  for (const type of resourceTypes) {
    const disabledNames = new Set(
      (disabled[type as keyof DisabledItems] as string[] | undefined) ?? [],
    );
    if (disabledNames.size === 0) continue;

    for (const target of Object.keys(COPY_TARGETS) as TargetType[]) {
      const basePath = COPY_TARGETS[target][type];
      if (!basePath) continue;

      try {
        const entries = await readdir(basePath, { withFileTypes: true });
        for (const entry of entries) {
          if (entry.name.startsWith(".")) continue;
          const rawName = entry.name
            .replace(/\.disabled$/, "")
            .replace(/\.md$/, "");
          const isDisabled = entry.name.endsWith(".disabled");

          if (disabledNames.has(rawName) && !isDisabled) {
            // Should be disabled but is active -> disable it
            const activePath = join(basePath, entry.name);
            await rename(activePath, `${activePath}.disabled`);
            movedToDisabled += 1;
          } else if (!disabledNames.has(rawName) && isDisabled) {
            // Should be active but is disabled -> enable it
            const disabledPath = join(basePath, entry.name);
            const activeName = entry.name.slice(0, -".disabled".length);
            await rename(disabledPath, join(basePath, activeName));
            restoredToActive += 1;
          }
        }
      } catch {
        // target directory may not exist
      }
    }
  }

  return {
    success: true,
    movedToDisabled,
    restoredToActive,
    missing: missing.sort((a, b) => a.localeCompare(b)),
  };
}

async function pathExists(path: string): Promise<boolean> {
  try {
    await Bun.file(path).stat();
    return true;
  } catch {
    return false;
  }
}

export async function listProfiles(
  projectRoot = process.cwd(),
): Promise<string[]> {
  const dir = profilesDir(resolve(projectRoot));
  try {
    const entries = await readdir(dir, { withFileTypes: true });
    return entries
      .filter((entry) => entry.isFile() && entry.name.endsWith(".yaml"))
      .map((entry) => entry.name.replace(/\.yaml$/, ""))
      .sort((a, b) => a.localeCompare(b));
  } catch {
    return [];
  }
}

export async function getStandardsStatus(
  projectRoot = process.cwd(),
): Promise<StandardsStatus> {
  const root = resolve(projectRoot);
  const initialized = await pathExists(standardsDir(root));
  const availableProfiles = await listProfiles(root);

  let activeProfile: string | null = null;
  try {
    const content = await readFile(activeProfilePath(root), "utf8");
    const parsed = YAML.parse(content) as { active?: string } | null;
    activeProfile = parsed?.active ?? null;
  } catch {
    activeProfile = null;
  }

  return { initialized, activeProfile, availableProfiles };
}

export async function showProfile(
  profileName: string,
  projectRoot = process.cwd(),
): Promise<Record<string, unknown> | null> {
  const root = resolve(projectRoot);
  const path = join(profilesDir(root), `${profileName}.yaml`);
  try {
    const content = await readFile(path, "utf8");
    return (YAML.parse(content) as Record<string, unknown> | null) ?? {};
  } catch {
    return null;
  }
}

export async function switchProfile(
  profileName: string,
  options: { projectRoot?: string; dryRun?: boolean } = {},
): Promise<SwitchProfileResult> {
  const projectRoot = resolve(options.projectRoot ?? process.cwd());
  const dryRun = options.dryRun ?? false;

  const profiles = await listProfiles(projectRoot);
  if (!profiles.includes(profileName)) {
    return {
      success: false,
      profile: profileName,
      dryRun,
      message: `profile not found: ${profileName}`,
    };
  }

  if (dryRun) {
    const disabled = await computeDisabledItems(profileName, projectRoot);
    return {
      success: true,
      profile: profileName,
      dryRun,
      disabledCount: disabled.standards.length,
      message: "dry-run only",
    };
  }

  await mkdir(standardsDir(projectRoot), { recursive: true });
  await writeFile(
    activeProfilePath(projectRoot),
    YAML.stringify({
      active: profileName,
      lastUpdated: new Date().toISOString().slice(0, 10),
    }),
    "utf8",
  );

  const disabled = await computeDisabledItems(profileName, projectRoot);
  const disabledYamlData: Record<string, string[]> = {
    standards: disabled.standards,
  };
  if (disabled.skills?.length) disabledYamlData.skills = disabled.skills;
  if (disabled.commands?.length) disabledYamlData.commands = disabled.commands;
  if (disabled.agents?.length) disabledYamlData.agents = disabled.agents;

  await writeFile(
    disabledYamlPath(projectRoot),
    YAML.stringify(disabledYamlData),
    "utf8",
  );

  const syncResult = await syncStandards(projectRoot);

  return {
    success: true,
    profile: profileName,
    dryRun,
    disabledCount: disabled.standards.length,
    movedToDisabled: syncResult.movedToDisabled,
    restoredToActive: syncResult.restoredToActive,
  };
}

export async function detectOverlaps(
  projectRoot = process.cwd(),
): Promise<Record<string, string[]>> {
  const overlaps: Record<string, string[]> = {};
  const profileNames = await listProfiles(projectRoot);
  const itemOwners = new Map<string, string[]>();

  for (const profile of profileNames) {
    const content = await showProfile(profile, projectRoot);
    if (!content) {
      continue;
    }

    for (const [key, value] of Object.entries(content)) {
      if (!Array.isArray(value)) {
        continue;
      }
      for (const item of value) {
        if (typeof item !== "string") {
          continue;
        }
        const itemKey = `${key}:${item}`;
        const owners = itemOwners.get(itemKey) ?? [];
        owners.push(profile);
        itemOwners.set(itemKey, owners);
      }
    }
  }

  for (const [item, owners] of itemOwners.entries()) {
    if (owners.length > 1) {
      overlaps[item] = owners.sort((a, b) => a.localeCompare(b));
    }
  }

  return overlaps;
}
