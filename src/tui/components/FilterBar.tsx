import { Box, Text } from "ink";

import {
  SOURCE_LABELS,
  type SourceFilter,
  type TypeFilter,
} from "../hooks/useResources";

interface FilterBarProps {
  typeFilter: TypeFilter;
  sourceFilter: SourceFilter;
}

export function FilterBar({ typeFilter, sourceFilter }: FilterBarProps) {
  const sourceLabel = SOURCE_LABELS[sourceFilter] ?? sourceFilter;

  return (
    <Box marginBottom={1} flexDirection="column">
      <Text>
        type: <Text color="magenta">{typeFilter}</Text> | source:{" "}
        <Text color="magenta">{sourceLabel}</Text>
      </Text>
      <Text dimColor>
        sources:{" "}
        {Object.entries(SOURCE_LABELS)
          .map(([key, label]) => {
            const isActive = key === sourceFilter;
            return isActive ? `[${label}]` : label;
          })
          .join(" | ")}
      </Text>
    </Box>
  );
}
