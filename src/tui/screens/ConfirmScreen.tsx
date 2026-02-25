import { Box, Text } from "ink";

interface ConfirmScreenProps {
  message: string;
}

export function ConfirmScreen({ message }: ConfirmScreenProps) {
  return (
    <Box flexDirection="column">
      <Text color="yellow">Confirmation</Text>
      <Text>{message}</Text>
      <Text dimColor>Press ESC to return.</Text>
    </Box>
  );
}
