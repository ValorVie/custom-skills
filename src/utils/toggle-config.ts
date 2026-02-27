import { join } from "node:path";

import { readYaml, writeYaml } from "./config";
import { paths } from "./paths";
import type { ResourceType, TargetType } from "./shared";

export interface ToggleConfigSection {
  enabled: boolean;
  disabled: string[];
}

export type ToggleConfig = Partial<
  Record<TargetType, Partial<Record<ResourceType, ToggleConfigSection>>>
>;

const RESOURCE_TYPES: ResourceType[] = [
  "skills",
  "commands",
  "agents",
  "workflows",
];

function isResourceType(value: string): value is ResourceType {
  return RESOURCE_TYPES.includes(value as ResourceType);
}

function normalizeDisabledList(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return [];
  }

  return [...new Set(value.filter((item): item is string => typeof item === "string"))].sort(
    (a, b) => a.localeCompare(b),
  );
}

function normalizeSection(value: unknown): ToggleConfigSection {
  const section =
    value && typeof value === "object" && !Array.isArray(value)
      ? (value as Record<string, unknown>)
      : {};

  return {
    enabled: section.enabled === false ? false : true,
    disabled: normalizeDisabledList(section.disabled),
  };
}

export function defaultToggleConfigPath(): string {
  return join(paths.customSkills, "toggle-config.yaml");
}

export async function loadToggleConfig(
  configPath = defaultToggleConfigPath(),
): Promise<ToggleConfig> {
  const raw = await readYaml<Record<string, unknown>>(configPath);
  if (!raw || typeof raw !== "object" || Array.isArray(raw)) {
    return {};
  }

  const config: ToggleConfig = {};

  for (const [target, targetValue] of Object.entries(raw)) {
    if (
      !targetValue ||
      typeof targetValue !== "object" ||
      Array.isArray(targetValue)
    ) {
      continue;
    }

    const sections: Partial<Record<ResourceType, ToggleConfigSection>> = {};

    for (const [type, sectionValue] of Object.entries(targetValue)) {
      if (!isResourceType(type)) {
        continue;
      }
      sections[type] = normalizeSection(sectionValue);
    }

    if (Object.keys(sections).length > 0) {
      config[target as TargetType] = sections;
    }
  }

  return config;
}

export async function saveToggleConfig(
  config: ToggleConfig,
  configPath = defaultToggleConfigPath(),
): Promise<void> {
  await writeYaml(configPath, config);
}

export function getToggleConfigSection(
  config: ToggleConfig,
  target: TargetType,
  type: ResourceType,
): ToggleConfigSection {
  const targetConfig = config[target] ?? {};
  const section = normalizeSection(targetConfig[type]);

  config[target] = {
    ...targetConfig,
    [type]: section,
  };

  return section;
}

export function applySingleToggleConfig(
  config: ToggleConfig,
  target: TargetType,
  type: ResourceType,
  name: string,
  enabled: boolean,
): ToggleConfigSection {
  const section = getToggleConfigSection(config, target, type);

  if (enabled) {
    section.disabled = section.disabled.filter((item) => item !== name);
  } else {
    section.disabled = normalizeDisabledList([...section.disabled, name]);
  }

  return section;
}

export function applyAllToggleConfig(
  config: ToggleConfig,
  target: TargetType,
  type: ResourceType,
  enabled: boolean,
): ToggleConfigSection {
  const section = getToggleConfigSection(config, target, type);
  section.enabled = enabled;
  return section;
}
