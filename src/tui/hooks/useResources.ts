import { useMemo, useReducer } from "react";

export type Screen = "main" | "preview" | "confirm" | "settings";
export type Target = "claude" | "opencode" | "codex" | "gemini";
export type ResourceType = "skill" | "command" | "agent" | "workflow";
export type ResourceSource = "custom-skills" | "external";
export type TypeFilter = ResourceType | "all";
export type SourceFilter = ResourceSource | "all";

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
}

type Action =
  | { type: "toggle_selected"; id: string }
  | { type: "toggle_all" }
  | { type: "set_type_filter"; value: TypeFilter }
  | { type: "set_source_filter"; value: SourceFilter }
  | { type: "switch_target" }
  | { type: "move_next" }
  | { type: "move_prev" }
  | { type: "set_enabled_for_selected"; enabled: boolean };

const TARGETS: Target[] = ["claude", "opencode", "codex", "gemini"];

const DEFAULT_RESOURCES: Resource[] = [
  {
    id: "skill-ops",
    name: "openspec-apply-change",
    type: "skill",
    source: "custom-skills",
    enabled: true,
    selected: false,
    content: "Implements tasks from an OpenSpec change.",
  },
  {
    id: "skill-auto",
    name: "auto-skill",
    type: "skill",
    source: "custom-skills",
    enabled: true,
    selected: false,
    content: "Bootstraps skill workflows with memory support.",
  },
  {
    id: "cmd-sync",
    name: "sync",
    type: "command",
    source: "external",
    enabled: true,
    selected: false,
    content: "Sync command group for cross-device workflows.",
  },
  {
    id: "agent-reviewer",
    name: "reviewer",
    type: "agent",
    source: "external",
    enabled: false,
    selected: false,
    content: "Code review specialist.",
  },
  {
    id: "wf-checkin",
    name: "checkin-assistant",
    type: "workflow",
    source: "custom-skills",
    enabled: true,
    selected: false,
    content: "Guides pre-commit quality gates.",
  },
];

const INITIAL_STATE: ResourcesState = {
  target: "claude",
  typeFilter: "all",
  sourceFilter: "all",
  resources: DEFAULT_RESOURCES,
  selectedIndex: 0,
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
