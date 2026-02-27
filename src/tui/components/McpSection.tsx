import { Box, Text } from "ink";

import { getMcpConfigPath } from "../utils/openers";
import type { Target } from "../hooks/useResources";

interface McpSectionProps {
  target: Target;
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
      <Text dimColor>f: open config folder</Text>
    </Box>
  );
}
