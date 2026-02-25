import { useInput } from "ink";

export interface KeyBindingHandlers {
  onQuit: () => void;
  onToggleSelection: () => void;
  onToggleAll: () => void;
  onAdd: () => void;
  onSave: () => void;
  onPreview: () => void;
  onOpenEditor: () => void;
  onOpenFileManager: () => void;
  onSettings: () => void;
  onSwitchTarget: () => void;
  onNext: () => void;
  onPrevious: () => void;
  onBack: () => void;
}

export function useKeyBindings(handlers: KeyBindingHandlers): void {
  useInput((input, key) => {
    if (key.escape || key.backspace) {
      handlers.onBack();
      return;
    }

    if (key.upArrow) {
      handlers.onPrevious();
      return;
    }

    if (key.downArrow) {
      handlers.onNext();
      return;
    }

    switch (input) {
      case "q":
        handlers.onQuit();
        break;
      case " ":
        handlers.onToggleSelection();
        break;
      case "a":
        handlers.onToggleAll();
        break;
      case "n":
        handlers.onAdd();
        break;
      case "s":
        handlers.onSave();
        break;
      case "p":
        handlers.onPreview();
        break;
      case "e":
        handlers.onOpenEditor();
        break;
      case "f":
        handlers.onOpenFileManager();
        break;
      case "c":
        handlers.onSettings();
        break;
      case "t":
        handlers.onSwitchTarget();
        break;
      default:
        break;
    }
  });
}
