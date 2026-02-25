import { mkdir, readdir, readFile, writeFile } from "node:fs/promises";
import { join, resolve } from "node:path";

import YAML from "yaml";

export interface StandardsStatus {
  initialized: boolean;
  activeProfile: string | null;
  availableProfiles: string[];
}

export interface SwitchProfileResult {
  success: boolean;
  profile: string;
  dryRun: boolean;
  message?: string;
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
    return {
      success: true,
      profile: profileName,
      dryRun,
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

  return {
    success: true,
    profile: profileName,
    dryRun,
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
