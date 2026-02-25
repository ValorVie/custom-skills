import { Box, Text } from "ink";

import type { Target } from "../hooks/useResources";

interface TabBarProps {
  current: Target;
  targets: Target[];
}

export function TabBar({ current, targets }: TabBarProps) {
  return (
    <Box marginBottom={1}>
      {targets.map((target) => (
        <Box key={target} marginRight={2}>
          <Text color={target === current ? "green" : "gray"}>
            [{target === current ? "*" : " "}] {target}
          </Text>
        </Box>
      ))}
    </Box>
  );
}
