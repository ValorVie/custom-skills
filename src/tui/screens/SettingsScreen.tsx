import { Box, Text } from "ink";

import { McpSection } from "../components/McpSection";
import type { Target } from "../hooks/useResources";

interface SettingsScreenProps {
  target: Target;
}

export function SettingsScreen({ target }: SettingsScreenProps) {
  return (
    <Box flexDirection="column">
      <Text color="cyan">Settings</Text>
      <Text>Current target: {target}</Text>
      <Text>Use "t" to switch target from main screen.</Text>
      <McpSection target={target} />
      <Text dimColor>Press ESC to return.</Text>
    </Box>
  );
}
