import { readdir } from "node:fs/promises";
import { useEffect, useMemo, useReducer } from "react";

import {
  COPY_TARGETS,
  type ResourceType as SourceResourceType,
  type TargetType,
} from "../../utils/shared";
import { collectSourceIndex, resolveResourceSource } from "../utils/source-index";

export type Screen = "main" | "preview" | "confirm" | "settings" | "standards";
export type Target = "claude" | "opencode" | "codex" | "gemini";
export type ResourceType = "skill" | "command" | "agent" | "workflow";
export type ResourceSource =
  | "custom-skills"
  | "superpowers"
  | "universal-dev-standards"
  | "obsidian-skills"
  | "anthropic-skills"
  | "everything-claude-code"
  | "auto-skill"
  | "user-custom"
  | "external"
  | (string & {});

export const SOURCE_LABELS: Record<string, string> = {
  all: "\u5168\u90e8",
  "custom-skills": "Custom Skills",
  superpowers: "Superpowers",
  "universal-dev-standards": "UDS",
  "obsidian-skills": "Obsidian Skills",
  "anthropic-skills": "Anthropic Skills",
  "everything-claude-code": "Everything Claude Code",
  "auto-skill": "Auto Skill",
  "user-custom": "User Custom",
  external: "External",
};
export type TypeFilter = ResourceType | "all";
export type SourceFilter = keyof typeof SOURCE_LABELS;

export interface Resource {
  id: string;
  name: string;
  type: ResourceType;
  source: ResourceSource;
  enabled: boolean;
  selected: boolean;
  content: string;
}

interface ResourcesState {
  target: Target;
  typeFilter: TypeFilter;
  sourceFilter: SourceFilter;
  resources: Resource[];
  selectedIndex: number;
  loading: boolean;
}

type Action =
  | { type: "toggle_selected"; id: string }
  | { type: "toggle_all" }
  | { type: "set_type_filter"; value: TypeFilter }
  | { type: "set_source_filter"; value: SourceFilter }
  | { type: "switch_target" }
  | { type: "move_next" }
  | { type: "move_prev" }
  | { type: "set_enabled_for_selected"; enabled: boolean }
  | { type: "set_resources"; resources: Resource[] };

const TARGETS: Target[] = ["claude", "opencode", "codex", "gemini"];

const RESOURCE_TYPE_MAP: Record<string, ResourceType> = {
  skills: "skill",
  commands: "command",
  agents: "agent",
  workflows: "workflow",
};

const RESOURCE_SOURCE_TYPE_MAP: Record<ResourceType, SourceResourceType> = {
  skill: "skills",
  command: "commands",
  agent: "agents",
  workflow: "workflows",
};

const DISABLED_SUFFIX = ".disabled";

interface ScannedResource {
  name: string;
  enabled: boolean;
}

function parseScannedResource(
  rawName: string,
  resourceType: ResourceType,
): ScannedResource | null {
  if (resourceType === "skill") {
    return {
      name: rawName,
      enabled: true,
    };
  }

  const enabled = !rawName.endsWith(DISABLED_SUFFIX);
  const withoutDisabled = enabled
    ? rawName
    : rawName.slice(0, -DISABLED_SUFFIX.length);

  if (!withoutDisabled.endsWith(".md")) {
    return null;
  }

  return {
    name: withoutDisabled.slice(0, -3),
    enabled,
  };
}

async function scanDirectory(
  dirPath: string,
  resourceType: ResourceType,
): Promise<ScannedResource[]> {
  try {
    const entries = await readdir(dirPath, { withFileTypes: true });
    return entries
      .filter((entry) => {
        if (entry.name.startsWith(".")) {
          return false;
        }
        if (resourceType === "skill") {
          return entry.isDirectory();
        }
        return entry.isFile();
      })
      .map((entry) => parseScannedResource(entry.name, resourceType))
      .filter((entry): entry is ScannedResource => Boolean(entry))
      .sort((a, b) => a.name.localeCompare(b.name));
  } catch {
    return [];
  }
}

export async function loadResources(target: Target): Promise<Resource[]> {
  const targetConfig = COPY_TARGETS[target as TargetType];
  if (!targetConfig) {
    return [];
  }

  const sourceIndex = await collectSourceIndex();
  const resources: Resource[] = [];

  for (const [dirKey, dirPath] of Object.entries(targetConfig)) {
    const resourceType = RESOURCE_TYPE_MAP[dirKey];
    if (!resourceType || !dirPath) {
      continue;
    }

    const sourceType = RESOURCE_SOURCE_TYPE_MAP[resourceType];
    const entries = await scanDirectory(dirPath, resourceType);
    for (const entry of entries) {
      resources.push({
        id: `${dirKey}-${entry.name}`,
        name: entry.name,
        type: resourceType,
        source: resolveResourceSource(sourceIndex, sourceType, entry.name),
        enabled: entry.enabled,
        selected: false,
        content: "",
      });
    }
  }

  return resources;
}

const INITIAL_STATE: ResourcesState = {
  target: "claude",
  typeFilter: "all",
  sourceFilter: "all",
  resources: [],
  selectedIndex: 0,
  loading: true,
};

function clampSelectedIndex(index: number, maxExclusive: number): number {
  if (maxExclusive <= 0) {
    return 0;
  }
  if (index < 0) {
    return maxExclusive - 1;
  }
  if (index >= maxExclusive) {
    return 0;
  }
  return index;
}

function resourcesReducer(
  state: ResourcesState,
  action: Action,
): ResourcesState {
  switch (action.type) {
    case "set_resources":
      return {
        ...state,
        resources: action.resources,
        selectedIndex: 0,
        loading: false,
      };

    case "toggle_selected":
      return {
        ...state,
        resources: state.resources.map((resource) =>
          resource.id === action.id
            ? { ...resource, selected: !resource.selected }
            : resource,
        ),
      };

    case "toggle_all": {
      const shouldSelectAll = state.resources.some(
        (resource) => !resource.selected,
      );
      return {
        ...state,
        resources: state.resources.map((resource) => ({
          ...resource,
          selected: shouldSelectAll,
        })),
      };
    }

    case "set_type_filter":
      return {
        ...state,
        typeFilter: action.value,
        selectedIndex: 0,
      };

    case "set_source_filter":
      return {
        ...state,
        sourceFilter: action.value,
        selectedIndex: 0,
      };

    case "switch_target": {
      const currentIndex = TARGETS.indexOf(state.target);
      const nextTarget =
        TARGETS[(currentIndex + 1) % TARGETS.length] ?? "claude";
      return {
        ...state,
        target: nextTarget,
        loading: true,
      };
    }

    case "move_next":
      return {
        ...state,
        selectedIndex: clampSelectedIndex(
          state.selectedIndex + 1,
          state.resources.length,
        ),
      };

    case "move_prev":
      return {
        ...state,
        selectedIndex: clampSelectedIndex(
          state.selectedIndex - 1,
          state.resources.length,
        ),
      };

    case "set_enabled_for_selected": {
      const targetResource = state.resources[state.selectedIndex];
      if (!targetResource) {
        return state;
      }

      return {
        ...state,
        resources: state.resources.map((resource) =>
          resource.id === targetResource.id
            ? { ...resource, enabled: action.enabled }
            : resource,
        ),
      };
    }

    default:
      return state;
  }
}

export function useResources() {
  const [state, dispatch] = useReducer(resourcesReducer, INITIAL_STATE);

  useEffect(() => {
    let cancelled = false;
    loadResources(state.target).then((resources) => {
      if (!cancelled) {
        dispatch({ type: "set_resources", resources });
      }
    });
    return () => {
      cancelled = true;
    };
  }, [state.target]);

  const visibleResources = useMemo(
    () =>
      state.resources.filter((resource) => {
        const typeMatch =
          state.typeFilter === "all" || resource.type === state.typeFilter;
        const sourceMatch =
          state.sourceFilter === "all" ||
          resource.source === state.sourceFilter;
        return typeMatch && sourceMatch;
      }),
    [state.resources, state.sourceFilter, state.typeFilter],
  );

  return {
    ...state,
    targets: TARGETS,
    visibleResources,
    toggleSelected: (id: string) => dispatch({ type: "toggle_selected", id }),
    toggleAll: () => dispatch({ type: "toggle_all" }),
    setTypeFilter: (value: TypeFilter) =>
      dispatch({ type: "set_type_filter", value }),
    setSourceFilter: (value: SourceFilter) =>
      dispatch({ type: "set_source_filter", value }),
    switchTarget: () => dispatch({ type: "switch_target" }),
    moveNext: () => dispatch({ type: "move_next" }),
    movePrev: () => dispatch({ type: "move_prev" }),
    setEnabledForSelected: (enabled: boolean) =>
      dispatch({ type: "set_enabled_for_selected", enabled }),
  };
}
