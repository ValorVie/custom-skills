import { Box, Text } from "ink";
import { useEffect, useState } from "react";

import {
  getStandardsStatus,
  listProfiles,
  switchProfile,
} from "../../core/standards-manager";

interface StandardsScreenProps {
  selectedIndex: number;
  message?: string | null;
  reloadToken?: number;
  onProfilesLoaded?: (profiles: ProfileEntry[]) => void;
}

export interface ProfileEntry {
  name: string;
  active: boolean;
}

export function StandardsScreen({
  selectedIndex,
  message = null,
  reloadToken = 0,
  onProfilesLoaded,
}: StandardsScreenProps) {
  const [profiles, setProfiles] = useState<ProfileEntry[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      const [allProfiles, status] = await Promise.all([
        listProfiles(),
        getStandardsStatus(),
      ]);

      if (cancelled) return;

      const nextProfiles = allProfiles.map((name) => ({
        name,
        active: name === status.activeProfile,
      }));

      setProfiles(nextProfiles);
      onProfilesLoaded?.(nextProfiles);
      setLoading(false);
    }

    void load();
    return () => {
      cancelled = true;
    };
  }, [reloadToken, onProfilesLoaded]);

  if (loading) {
    return (
      <Box flexDirection="column">
        <Text color="cyan">Standards Profiles</Text>
        <Text>Loading...</Text>
      </Box>
    );
  }

  if (profiles.length === 0) {
    return (
      <Box flexDirection="column">
        <Text color="cyan">Standards Profiles</Text>
        <Text>No profiles found.</Text>
        <Text dimColor>Press ESC to return.</Text>
      </Box>
    );
  }

  return (
    <Box flexDirection="column">
      <Text color="cyan">Standards Profiles</Text>
      {message && <Text color="green">{message}</Text>}
      <Box flexDirection="column" marginTop={1}>
        {profiles.map((profile, index) => {
          const isFocused = index === selectedIndex;
          const prefix = isFocused ? ">" : " ";
          const activeTag = profile.active ? " [active]" : "";

          return (
            <Text key={profile.name}>
              <Text color={isFocused ? "yellow" : undefined}>
                {prefix} {profile.name}
              </Text>
              <Text color="green">{activeTag}</Text>
            </Text>
          );
        })}
      </Box>
      <Box marginTop={1}>
        <Text dimColor>
          Up/Down select | Enter switch profile | ESC back
        </Text>
      </Box>
    </Box>
  );
}

export async function performSwitchProfile(
  profileName: string,
): Promise<string> {
  const result = await switchProfile(profileName);
  if (result.success) {
    return `Switched to profile: ${profileName}`;
  }
  return result.message ?? `Failed to switch to profile: ${profileName}`;
}
