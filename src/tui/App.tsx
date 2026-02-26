import { useApp } from "ink";
import { useMemo, useState } from "react";

import { useKeyBindings } from "./hooks/useKeyBindings";
import { type Screen, useResources } from "./hooks/useResources";
import { ConfirmScreen } from "./screens/ConfirmScreen";
import { MainScreen } from "./screens/MainScreen";
import { PreviewScreen } from "./screens/PreviewScreen";
import { SettingsScreen } from "./screens/SettingsScreen";
import {
  StandardsScreen,
  performSwitchProfile,
} from "./screens/StandardsScreen";

export function App() {
  const { exit } = useApp();
  const resources = useResources();
  const [screen, setScreen] = useState<Screen>("main");
  const [confirmMessage, setConfirmMessage] =
    useState<string>("No pending action.");
  const [standardsIndex, setStandardsIndex] = useState(0);

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
      setConfirmMessage("Open editor action requested.");
      setScreen("confirm");
    },
    onOpenFileManager: () => {
      setConfirmMessage("Open file manager action requested.");
      setScreen("confirm");
    },
    onSettings: () => setScreen("settings"),
    onStandards: () => {
      setStandardsIndex(0);
      setScreen("standards");
    },
    onSwitchTarget: () => resources.switchTarget(),
    onNext: () => {
      if (screen === "standards") {
        setStandardsIndex((prev) => prev + 1);
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
        // handled via performSwitchProfile - need profile name
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
    return <StandardsScreen selectedIndex={standardsIndex} />;
  }

  if (screen === "settings") {
    return <SettingsScreen target={resources.target} />;
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
