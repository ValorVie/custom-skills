## Context
- 現況：ai-dev install/update 僅維護 `~/.config/superpowers` 以追蹤上游，OpenCode 官方安裝需要額外 clone 至 `~/.config/opencode/superpowers` 並建立 plugins/skills symlink，現需人工操作。 [Source: Code] openspec/changes/superpowers-opencode-install/proposal.md:3-10
- 官方 OpenCode 流程：clone 上游至 `~/.config/opencode/superpowers`，建立 `~/.config/opencode/plugins/superpowers.js` 及 `~/.config/opencode/skills/superpowers` 的 symlink。 [Source: Code] ~/.config/superpowers/docs/README.opencode.md:5-41
- 目標是在 ai-dev install/update 中自動化上述流程，同時保留現有 `~/.config/superpowers` 以供上游追蹤。 [Source: Code] openspec/changes/superpowers-opencode-install/proposal.md:7-16

## Goals / Non-Goals
**Goals:**
- 在 ai-dev install/update 增加 OpenCode 模式，自動 clone / 更新 `~/.config/opencode/superpowers` 並建立/更新 symlink。
- 保持冪等：重複執行不產生殘留目錄或壞鏈接，並清理舊鏈接後再建立。
- 保留現有 Claude Code 插件追蹤路徑，不影響 `~/.config/superpowers` 使用。

**Non-Goals:**
- 不處理 OpenCode 應用層的重啟（交由使用者自行重啟）。
- 不改變 superpowers 上游內容或 hooks 實作，只做安裝/更新編排。
- 不在此變更中合併其他上游（如 anthropic-skills）。

## Decisions
- 安裝路徑：遵循官方文件，clone/更新至 `~/.config/opencode/superpowers`。 [Source: Code] ~/.config/superpowers/docs/README.opencode.md:5-41
- Symlink 目標：
  - plugin: `~/.config/opencode/plugins/superpowers.js` → `.opencode/plugins/superpowers.js`
  - skills: `~/.config/opencode/skills/superpowers` → `skills/`
  兩者在安裝前先移除既有鏈接/目錄以避免殘留。 [Source: Code] ~/.config/superpowers/docs/README.opencode.md:30-41
- 作業系統支援：保留 macOS/Linux 路徑與 Windows 指令參考，但 ai-dev 以 POSIX shell 為主；Windows 另以說明文件提示使用者（若未自動支援）。 [Source: Code] ~/.config/superpowers/docs/README.opencode.md:53-110
- 保留上游追蹤：不移除 `~/.config/superpowers`；OpenCode 安裝流程獨立於該路徑，避免破壞現有追蹤機制。 [Source: Code] openspec/changes/superpowers-opencode-install/proposal.md:7-16
- 驗證步驟：執行後列印 `ls -l` 檢查 symlink 以利使用者確認。 [Source: Code] ~/.config/superpowers/docs/README.opencode.md:44-51

## Risks / Trade-offs
- Windows symlink 需 Developer Mode/Administrator；若 ai-dev 以 POSIX shell 執行，Windows 使用者可能失敗 → 在命令中檢測失敗時提示手動依文件操作。 [Source: Code] ~/.config/superpowers/docs/README.opencode.md:53-110
- 若使用者已有自訂 `~/.config/opencode/plugins/superpowers.js`，強制覆寫可能破壞設定 → 先檢查是否為 symlink 指向 superpowers，若非則提示並跳過或備份。 [Inferred]
- 重複 clone 可能造成網路延遲 → 優先 git pull，若目錄不存在才 clone。 [Source: Code] ~/.config/superpowers/docs/README.opencode.md:22-29

## Migration Plan
- install：檢查/建立 `~/.config/opencode` 目錄 → clone/pull superpowers → 清理舊 symlink → 建立新 symlink → 顯示驗證指令。
- update：重用上述流程（git pull + 重新建立 symlink），確保冪等。
- rollback：刪除 symlink 並可移除 `~/.config/opencode/superpowers` 目錄（不影響 `~/.config/superpowers`）。

## Open Questions
- 是否需要在 ai-dev 中加入 Windows 專用分支（cmd/PowerShell）自動化？
- 是否要在 docs/README 增補 OpenCode 段落與已知限制（權限、Developer Mode）？
