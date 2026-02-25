import { Box, Text } from "ink";

import type { Resource } from "../hooks/useResources";

interface ResourceItemProps {
  resource: Resource;
  focused: boolean;
}

export function ResourceItem({ resource, focused }: ResourceItemProps) {
  const marker = resource.selected ? "[x]" : "[ ]";
  const status = resource.enabled ? "on" : "off";

  return (
    <Box>
      <Text color={focused ? "green" : "white"}>
        {focused ? ">" : " "} {marker} {resource.name} ({resource.type},{" "}
        {resource.source}, {status})
      </Text>
    </Box>
  );
}
