import { Box } from "ink";

import type { Resource } from "../hooks/useResources";
import { ResourceItem } from "./ResourceItem";

interface ResourceListProps {
  resources: Resource[];
  selectedIndex: number;
}

export function ResourceList({ resources, selectedIndex }: ResourceListProps) {
  if (resources.length === 0) {
    return (
      <Box>
        <ResourceItem
          resource={{
            id: "empty",
            name: "No resources match the current filters",
            type: "skill",
            source: "custom-skills",
            enabled: false,
            selected: false,
            content: "",
          }}
          focused={false}
        />
      </Box>
    );
  }

  return (
    <Box flexDirection="column">
      {resources.map((resource, index) => (
        <ResourceItem
          key={resource.id}
          resource={resource}
          focused={index === selectedIndex}
        />
      ))}
    </Box>
  );
}
