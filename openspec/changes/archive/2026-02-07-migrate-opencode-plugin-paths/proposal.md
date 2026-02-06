## Why

`ai-dev clone` 目前將 OpenCode plugin 分發到 `~/.config/opencode/plugin/ecc-hooks/`，且路徑常數也使用單數 `plugin`。

但 OpenCode 官方文件以 `plugins`（複數）作為本機 plugin 主路徑，並說明本機 plugin 會自動載入；同時目前專案的 OpenCode plugin 分發採「複製整個目錄到 `ecc-hooks` 子目錄」模式，與官方文件慣例存在落差，增加載入不一致與升級維護風險。

## What Changes

### Path Migration

- 將 OpenCode plugin 目標路徑由 `~/.config/opencode/plugin/...` 遷移為 `~/.config/opencode/plugins/...`。
- 調整 `get_opencode_plugin_dir()` 與 `COPY_TARGETS["opencode"]["plugins"]` 的路徑定義，對齊官方主路徑。

### Distribution Behavior Clarification

- 明確定義 OpenCode plugin 在 `ai-dev clone` 的分發型態（目標目錄層級、entry 檔案放置策略、是否保留子目錄）。
- 調整 plugin 分發格式為「`plugins/` 第一層有明確 entry 檔」模式（例如 `<plugin-name>.ts` 或 `<plugin-name>.js`），確保可被 OpenCode 直接載入。
- 確保分發結果可被 OpenCode 穩定載入，避免依賴非官方或模糊行為。

### Backward Compatibility

- 提供 legacy 路徑相容策略：
  - 偵測舊路徑（`~/.config/opencode/plugin/...`）
  - 提供一次性搬遷或相容 fallback（含提示訊息與可回復策略）

### Spec/Docs Alignment

- 更新 OpenSpec 主規格中與 OpenCode plugin 路徑相關條目。
- 更新使用文件中仍指向 `~/.config/opencode/plugin` 的內容，統一為官方 `plugins` 路徑。

## Impact

- **修改範圍**：`script/utils/paths.py`、`script/utils/shared.py`、OpenSpec 相關規格與文件。
- **使用者影響**：已使用舊路徑的使用者需要搬遷或透過相容策略無痛過渡。
- **風險**：若未處理相容，可能導致既有環境 plugin 未被載入。
- **收益**：對齊官方路徑慣例，降低後續維護成本與路徑歧義。

## Evidence

- 現行實作使用單數 `plugin`：
  - `script/utils/paths.py`
  - `script/utils/shared.py`
- 現行 OpenSpec 主規格使用 `~/.config/opencode/plugin/ecc-hooks/`：
  - `openspec/specs/opencode-plugin/spec.md`
  - `openspec/specs/clone-command/spec.md`
- 官方 OpenCode 文件使用 `plugins`（複數）路徑：
  - https://opencode.ai/docs/plugins/
  - https://opencode.ai/docs/config/
