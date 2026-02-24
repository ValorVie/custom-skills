## Context

custom-skills 專案整合了 6 個上游來源，其中 ECC (everything-claude-code) 目前標記為 `install_method: manual`，透過 `sources/ecc/` 本地副本手動管理。ECC 上游活躍開發（50K+ stars，日更），手動同步已無法跟上。

現有分發流程：
1. `ai-dev update` — 拉取 ECC 到 `~/.config/everything-claude-code/`
2. `ai-dev clone` — 從 `~/.config/custom-skills/` 分發，ECC 部分來自專案內的 `sources/ecc/` 複製品
3. `integrate_to_dev_project()` — 開發模式下從 `sources/ecc/` 整合到開發目錄

問題：`sources/ecc/` 是 2026-01-24 的快照，已嚴重過時。

## Goals / Non-Goals

**Goals:**
- `ai-dev clone` 直接從 `~/.config/everything-claude-code/` 選擇性分發 ECC 的 skills/agents/commands
- 透過 `upstream/distribution.yaml` 設定檔定義分發規則（來源路徑、平台對應、排除清單）
- 使用現有 ManifestTracker 追蹤分發的 ECC 檔案 hash
- 移除所有 ECC 本地複製品（`sources/ecc/`、`upstream/ecc/`、`plugins/ecc-hooks-old/`、重複的 skills/agents/commands）
- 保留 `plugins/ecc-hooks/`（自訂 Python hooks）和 `plugins/ecc-hooks-opencode/`

**Non-Goals:**
- 不改動 `ai-dev update` 流程（已正確拉取 ECC）
- 不改動 `plugins/ecc-hooks/` 的行為
- 不改動 ECC 以外的上游來源分發方式
- 不自動轉換 ECC commands 為 Gemini TOML 格式

## Decisions

### Decision 1: 新增 distribution.yaml 集中管理 ECC 分發設定

**選擇**: 在 `upstream/distribution.yaml` 定義 ECC 的分發矩陣

**替代方案**:
- A) 擴充 `sources.yaml` 加入分發欄位 → 不採用：sources.yaml 職責是追蹤來源，不應承載分發邏輯
- B) 硬編碼在 `shared.py` 中 → 不採用：難以維護和擴展
- C) 使用 custom_repos 機制 → 不採用：ECC 目錄結構不符（扁平 commands/agents 而非 per-platform 子目錄）

**理由**: distribution.yaml 語意清晰、獨立於來源管理、可擴展到未來其他需要選擇性分發的來源。

### Decision 2: ECC 分發在 custom-skills 分發之後執行

**選擇**: 在 `copy_custom_skills_to_targets()` 的現有分發流程末尾，custom repos 之後新增 ECC 分發階段

**理由**:
- ECC 和 custom-skills 的 skills 會合併到同一目標目錄
- 先分發 custom-skills 再分發 ECC，衝突時 ECC 會覆蓋 custom-skills（但目前無預期衝突）
- 分發順序: custom-skills → custom repos → ECC selective

### Decision 3: 按平台區分 ECC 來源路徑

**選擇**: distribution.yaml 為每個平台定義獨立的來源路徑

```
分發映射:
  claude:    skills/ → skills, commands/ → commands, agents/ → agents
  opencode:  skills/ → skills, .opencode/commands/ → commands, .opencode/prompts/agents/ → agents
  gemini:    skills/ → skills, agents/ → agents（不分發 commands，格式不相容）
  codex:     skills/ → skills（不支援 commands 和 agents）
```

**理由**: ECC 為不同平台維護獨立的 commands/agents 版本（格式和內容不同），必須從正確的來源路徑讀取。

### Decision 4: 移除 integrate_to_dev_project() 的 ECC 段落

**選擇**: 直接移除 `shared.py:1561-1598` 的 ECC 整合邏輯

**理由**: 開發模式不再需要將 ECC 內容複製進 repo。ECC 內容由 clone 分發流程直接處理。

### Decision 5: sources.yaml 保留 ECC 條目但改 install_method

**選擇**: `install_method: manual` → `install_method: selective`

**理由**: ECC 仍在 `ai-dev update` 的拉取清單中，sources.yaml 需要反映其新的分發方式。`selective` 語意表達「選擇性分發，規則見 distribution.yaml」。

## Risks / Trade-offs

- **[Risk] ECC 新增 skill 與 custom-skills 同名** → Mitigation: distribution.yaml 支援 exclude 清單，發現衝突時加入排除。ManifestTracker 的衝突偵測也會提醒。
- **[Risk] ECC 目錄結構變更（重命名 .opencode/ 等）** → Mitigation: distribution.yaml 的路徑設定可快速調整。
- **[Risk] `~/.config/everything-claude-code/` 不存在** → Mitigation: 分發時檢查目錄是否存在，不存在則跳過並警告（與現有 custom repos 行為一致）。
- **[Trade-off] 每次 clone 多一個分發步驟** → 增加少量 I/O 時間，但消除了手動同步的人工成本。
- **[Trade-off] 依賴 ECC 上游目錄結構穩定** → 可接受，ECC 是成熟專案且結構已趨穩定。
