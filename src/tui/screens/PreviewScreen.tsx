import { Box, Text } from "ink";

import type { Resource } from "../hooks/useResources";

interface PreviewScreenProps {
  resource: Resource | null;
}

export function PreviewScreen({ resource }: PreviewScreenProps) {
  return (
    <Box flexDirection="column">
      <Text color="cyan">Preview</Text>
      {resource ? (
        <>
          <Text color="green">{resource.name}</Text>
          <Text>{resource.content}</Text>
        </>
      ) : (
        <Text>No resource selected.</Text>
      )}
      <Text dimColor>Press ESC to return.</Text>
    </Box>
  );
}
