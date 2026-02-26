import { Box, Text } from "ink";

export function ActionBar() {
  return (
    <Box marginTop={1} flexDirection="column">
      <Text dimColor>
        q quit | space toggle | a toggle-all | p preview | c settings | t
        switch-target
      </Text>
      <Text dimColor>
        n add | s save | e editor | f files | S standards | esc back
      </Text>
    </Box>
  );
}
