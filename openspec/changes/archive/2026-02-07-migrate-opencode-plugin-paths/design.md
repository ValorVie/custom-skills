## Context

目前 `ai-dev clone` 的 OpenCode plugin 分發由 `script/utils/shared.py` 的 `COPY_TARGETS["opencode"]["plugins"]` 控制，目標是 `get_opencode_plugin_dir() / "ecc-hooks"`，而 `get_opencode_plugin_dir()` 回傳 `~/.config/opencode/plugin`（單數）。

OpenCode 官方文件將 `~/.config/opencode/plugins/`（複數）定義為 Global plugins 正式路徑，且啟動時會自動載入 plugin 目錄中的檔案；官方文件也明確表示單數目錄名屬於 backward compatibility。OpenCode 原始碼的 loader 使用 `{plugin,plugins}/*.{ts,js}`，代表會同時掃描單/複數路徑，但僅匹配第一層 `*.ts`/`*.js` entry 檔。

因此現況有兩個主要風險：
- 路徑語意風險：專案規格與程式仍以單數路徑為主要目標，與官方主要慣例不一致。
- 載入模型風險：分發型態偏向子目錄承載，與 loader 單層 entry 掃描模式存在落差。

## Goals / Non-Goals

**Goals:**
- 將 OpenCode plugin 分發主路徑遷移到 `~/.config/opencode/plugins/`。
- 定義「`plugins/` 第一層有明確 entry 檔」的分發格式，確保可直接被 OpenCode 自動載入。
- 提供舊路徑 `~/.config/opencode/plugin/...` 的遷移或 fallback 策略，避免既有使用者中斷。
- 對齊 OpenSpec 主規格與文件敘述，消除路徑與分發模型歧義。

**Non-Goals:**
- 不改動 ecc-hooks plugin 的功能邏輯（事件對映、腳本行為）。
- 不引入新的外部依賴或改變 OpenCode 本身 loader 行為。
- 不在本次變更中重構整個 clone 流程的其他平台分發邏輯。

## Decisions

### Decision 1: 路徑基準改為 `plugins`（複數）

- **Decision**: 將 OpenCode plugin 官方分發目標固定為 `~/.config/opencode/plugins/`。
- **Rationale**: 與官方文件一致，降低未來移除 backward compatibility 時的破壞風險。
- **Alternative considered**:
  - 保持 `plugin`（單數）為主：短期改動最小，但與官方慣例偏離，長期風險較高。

### Decision 2: 分發格式採第一層 entry-file 優先

- **Decision**: 分發完成後，`plugins/` 第一層必須存在可直接載入的明確 entry 檔（`<plugin-name>.ts` 或 `<plugin-name>.js`）。
- **Rationale**: OpenCode loader 的 glob 為單層檔案匹配；以扁平 entry 作為預設能最大化載入可預期性。
- **Alternative considered**:
  - 使用巢狀資料夾作為預設：需要依賴額外顯式設定或間接載入，增加部署與除錯成本。

### Decision 3: 提供漸進式 legacy 相容遷移

- **Decision**: 保留對舊路徑的偵測與一次性搬遷/提示機制，必要時提供 fallback。
- **Rationale**: 既有使用者可能已在 `plugin/` 或 `plugin/ecc-hooks/` 有安裝內容，直接切換會造成載入中斷。
- **Alternative considered**:
  - 一次性硬切：實作簡單，但升級破壞性高。

### Decision 4: 規格先行，實作後對齊

- **Decision**: 先更新 OpenSpec 主規格與 change delta specs，再進入實作。
- **Rationale**: 路徑與分發模型屬跨檔案、跨文件契約，先固化可降低實作歧義。

## Risks / Trade-offs

- [Risk] 舊環境路徑衝突（`plugin` 與 `plugins` 並存） → Mitigation: 在 clone 時執行衝突檢測，提供搬遷提示與可重入策略。
- [Risk] 第一層 entry 命名不一致造成覆蓋 → Mitigation: 定義固定命名規則與碰撞檢查（已存在時提示/備份）。
- [Risk] 文件與實作版本不同步 → Mitigation: 將 spec/docs 更新列為同一 change 的必要任務，apply 前檢查。
- [Trade-off] 增加遷移邏輯複雜度 → Mitigation: 僅保留最小必要 fallback，並規劃後續移除時機。

## Migration Plan

1. 更新路徑常數與分發目標（`plugin` → `plugins`）。
2. 更新分發格式，確保 `plugins/` 第一層產生明確 entry 檔。
3. 加入 legacy 路徑偵測與遷移提示（必要時執行一次性搬遷）。
4. 更新 OpenSpec 主規格與文件路徑描述。
5. 補齊測試：新路徑、第一層 entry、legacy 相容。
6. 發布後觀察，確認無載入回歸問題。

Rollback 策略：
- 保留舊路徑 fallback 能力；若新路徑載入異常，可暫時回退至相容模式並輸出診斷訊息。

## Open Questions

- 第一層 entry 檔命名是否固定為 `ecc-hooks-opencode.ts`（或 `.js`）？
- 對使用者自訂 `plugins/` 既有檔案的衝突策略要採「提示後跳過」或「備份後覆蓋」？
- legacy fallback 的移除時程是否需要在下一個 major 版本宣告？
