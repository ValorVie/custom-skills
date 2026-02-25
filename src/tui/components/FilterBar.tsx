import { Box, Text } from "ink";

import type { SourceFilter, TypeFilter } from "../hooks/useResources";

interface FilterBarProps {
  typeFilter: TypeFilter;
  sourceFilter: SourceFilter;
}

export function FilterBar({ typeFilter, sourceFilter }: FilterBarProps) {
  return (
    <Box marginBottom={1}>
      <Text>
        type: <Text color="magenta">{typeFilter}</Text> | source:{" "}
        <Text color="magenta">{sourceFilter}</Text>
      </Text>
    </Box>
  );
}
