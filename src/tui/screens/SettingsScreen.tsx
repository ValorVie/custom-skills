import { Box, Text } from "ink";

import { McpSection } from "../components/McpSection";
import type { Target } from "../hooks/useResources";

interface SettingsScreenProps {
  target: Target;
  message?: string | null;
}

export function SettingsScreen({ target, message = null }: SettingsScreenProps) {
  return (
    <Box flexDirection="column">
      <Text color="cyan">Settings</Text>
      <Text>Current target: {target}</Text>
      <Text>Use "t" to switch target from main screen.</Text>
      <McpSection target={target} />
      {message && <Text color="green">{message}</Text>}
      <Text dimColor>Press ESC to return.</Text>
    </Box>
  );
}
