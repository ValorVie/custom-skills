import { homedir } from "node:os";
import { join } from "node:path";

import { Box, Text } from "ink";

interface McpSectionProps {
  target: string;
}

function getMcpConfigPath(target: string): string | null {
  const home = homedir();
  switch (target) {
    case "claude":
      return join(home, ".claude", "claude_desktop_config.json");
    case "opencode":
      return join(home, ".config", "opencode", "config.json");
    default:
      return null;
  }
}

export function McpSection({ target }: McpSectionProps) {
  const configPath = getMcpConfigPath(target);

  return (
    <Box flexDirection="column" marginTop={1}>
      <Text color="cyan">MCP Configuration</Text>
      {configPath ? (
        <Text>
          Config: <Text color="green">{configPath}</Text>
        </Text>
      ) : (
        <Text dimColor>N/A for target: {target}</Text>
      )}
      <Text dimColor>e: open in editor</Text>
    </Box>
  );
}
