import { useApp } from "ink";
import { useCallback, useMemo, useState } from "react";

import { useKeyBindings } from "./hooks/useKeyBindings";
import { type Screen, useResources } from "./hooks/useResources";
import { ConfirmScreen } from "./screens/ConfirmScreen";
import { MainScreen } from "./screens/MainScreen";
import { PreviewScreen } from "./screens/PreviewScreen";
import { SettingsScreen } from "./screens/SettingsScreen";
import {
  type ProfileEntry,
  StandardsScreen,
  performSwitchProfile,
} from "./screens/StandardsScreen";
import { openMcpConfigFolder, openMcpConfigInEditor } from "./utils/openers";

export async function switchStandardsProfileByIndex(
  profiles: string[],
  selectedIndex: number,
  switchProfileFn: (profileName: string) => Promise<string> =
    performSwitchProfile,
): Promise<string | null> {
  const profileName = profiles[selectedIndex];
  if (!profileName) {
    return null;
  }

  return await switchProfileFn(profileName);
}

export function App() {
  const { exit } = useApp();
  const resources = useResources();
  const [screen, setScreen] = useState<Screen>("main");
  const [confirmMessage, setConfirmMessage] =
    useState<string>("No pending action.");
  const [standardsIndex, setStandardsIndex] = useState(0);
  const [standardsProfiles, setStandardsProfiles] = useState<string[]>([]);
  const [standardsMessage, setStandardsMessage] = useState<string | null>(null);
  const [standardsReloadToken, setStandardsReloadToken] = useState(0);
  const [settingsMessage, setSettingsMessage] = useState<string | null>(null);

  const focusedIndex = useMemo(() => {
    if (resources.visibleResources.length === 0) {
      return 0;
    }
    return Math.min(
      resources.selectedIndex,
      resources.visibleResources.length - 1,
    );
  }, [resources.selectedIndex, resources.visibleResources.length]);

  const focusedResource = resources.visibleResources[focusedIndex] ?? null;

  const handleStandardsProfilesLoaded = useCallback((profiles: ProfileEntry[]) => {
    const names = profiles.map((profile) => profile.name);
    setStandardsProfiles(names);
    setStandardsIndex((prev) => {
      if (names.length === 0) {
        return 0;
      }
      return Math.min(prev, names.length - 1);
    });
  }, []);

  useKeyBindings({
    onQuit: () => exit(),
    onToggleSelection: () => {
      if (!focusedResource) {
        return;
      }
      resources.toggleSelected(focusedResource.id);
    },
    onToggleAll: () => resources.toggleAll(),
    onAdd: () => {
      setConfirmMessage("Add action requested.");
      setScreen("confirm");
    },
    onSave: () => {
      resources.setEnabledForSelected(true);
      setConfirmMessage("Changes saved.");
      setScreen("confirm");
    },
    onPreview: () => setScreen("preview"),
    onOpenEditor: () => {
      if (screen === "settings") {
        const target = resources.target;
        void (async () => {
          const result = await openMcpConfigInEditor(target);
          setSettingsMessage(result.message);
        })();
        return;
      }
      setConfirmMessage("Open editor action requested.");
      setScreen("confirm");
    },
    onOpenFileManager: () => {
      if (screen === "settings") {
        const target = resources.target;
        void (async () => {
          const result = await openMcpConfigFolder(target);
          setSettingsMessage(result.message);
        })();
        return;
      }
      setConfirmMessage("Open file manager action requested.");
      setScreen("confirm");
    },
    onSettings: () => {
      setSettingsMessage(null);
      setScreen("settings");
    },
    onStandards: () => {
      setStandardsIndex(0);
      setStandardsMessage(null);
      setScreen("standards");
    },
    onSwitchTarget: () => resources.switchTarget(),
    onNext: () => {
      if (screen === "standards") {
        setStandardsIndex((prev) => {
          if (standardsProfiles.length === 0) {
            return 0;
          }
          return Math.min(prev + 1, standardsProfiles.length - 1);
        });
      } else {
        resources.moveNext();
      }
    },
    onPrevious: () => {
      if (screen === "standards") {
        setStandardsIndex((prev) => Math.max(0, prev - 1));
      } else {
        resources.movePrev();
      }
    },
    onConfirmEnter: () => {
      if (screen === "standards") {
        const profileNames = [...standardsProfiles];
        const selected = standardsIndex;
        void (async () => {
          const message = await switchStandardsProfileByIndex(
            profileNames,
            selected,
          );
          if (!message) {
            return;
          }
          setStandardsMessage(message);
          setStandardsReloadToken((prev) => prev + 1);
        })();
      }
    },
    onBack: () => {
      if (screen !== "main") {
        setScreen("main");
      }
    },
  });

  if (screen === "preview") {
    return <PreviewScreen resource={focusedResource} />;
  }

  if (screen === "confirm") {
    return <ConfirmScreen message={confirmMessage} />;
  }

  if (screen === "standards") {
    return (
      <StandardsScreen
        selectedIndex={standardsIndex}
        message={standardsMessage}
        reloadToken={standardsReloadToken}
        onProfilesLoaded={handleStandardsProfilesLoaded}
      />
    );
  }

  if (screen === "settings") {
    return <SettingsScreen target={resources.target} message={settingsMessage} />;
  }

  return (
    <MainScreen
      target={resources.target}
      targets={resources.targets}
      typeFilter={resources.typeFilter}
      sourceFilter={resources.sourceFilter}
      selectedCount={
        resources.resources.filter((resource) => resource.selected).length
      }
      resources={resources.visibleResources}
      selectedIndex={focusedIndex}
    />
  );
}
