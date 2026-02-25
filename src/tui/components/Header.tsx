import { Box, Text } from "ink";

import type { Target } from "../hooks/useResources";

interface HeaderProps {
  target: Target;
  total: number;
  selected: number;
}

export function Header({ target, total, selected }: HeaderProps) {
  return (
    <Box justifyContent="space-between" marginBottom={1}>
      <Text color="cyanBright">ai-dev TUI</Text>
      <Text>
        target: <Text color="yellow">{target}</Text> | selected: {selected}/
        {total}
      </Text>
    </Box>
  );
}
