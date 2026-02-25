## Context

ai-dev CLI (v1.2.5) 以 Python 3.13 + uv 開發，使用 Typer (CLI)、Rich (輸出)、Textual (TUI)。服務端 claude-mem-sync 已是 Bun/TypeScript + Express + PostgreSQL。團隊僅一人維護，雙語言棧增加認知成本。

現有程式碼約 9,200 行 Python，分佈在 18 個指令、6 個工具模組、1 個 TUI。

完整技術設計參見 [設計文件](../../docs/plans/2026-02-24-v2-bun-migration-design.md)。

## Goals / Non-Goals

**Goals:**
- 統一 runtime 為 Bun，消除 Python 依賴
- 保持所有 CLI 指令介面（名稱、參數、行為）向後相容
- 以 `@valorvie/ai-dev` 發佈到 npm，支援 `bun add -g` 和 `npm i -g` 安裝
- 架構分層：`cli/`（指令定義）、`core/`（業務邏輯）、`utils/`（工具函式）、`tui/`（UI）
- TUI 完整移植到 Ink，使用視圖切換取代 Modal overlay

**Non-Goals:**
- 不重新設計 CLI 指令結構（僅內部重寫）
- 不修改非程式碼資源（skills/、commands/、agents/、docs/）
- 不修改 claude-mem-sync 服務端
- 不支援 Node.js 直接執行（僅 Bun runtime）
- 不在 v2.0.0 加入新功能（純遷移）

## Decisions

### D1: CLI 框架 — Commander.js

**選擇**: Commander.js
**替代方案**: Citty (UnJS 生態，較輕量)、Clipanion (Yarn 使用，類型安全但生態小)
**理由**: 最成熟穩定的 Node CLI 框架，生態系最大，子命令組支援完整，與 Typer 功能對等。

### D2: TUI 框架 — Ink (React for CLI)

**選擇**: Ink + @inkjs/ui
**替代方案**: Neo-Blessed (widget 覆蓋率 80%，但原始 blessed 已停更)、自建 ANSI wrapper
**理由**: React 元件模型讓狀態驅動 UI 更易維護；生態活躍；與 Bun 相容佳。缺少內建 Modal，以視圖切換模式取代。

### D3: TUI Modal → 視圖切換

**選擇**: 整個畫面切換 (`useState<Screen>`)
**替代方案**: Overlay 模擬（條件渲染疊加 Box）
**理由**: Ink 設計為線性輸出流，不支援真正的圖層疊加。視圖切換與 Ink 設計理念一致，穩定性高。

### D4: 架構分層 — cli / core / utils

**選擇**: 三層分離，core 為純函式
**理由**: core 不依賴 Commander.js 或 Ink，可獨立單元測試。CLI 層僅負責參數解析和輸出格式化。

### D5: SQLite 存取 — better-sqlite3

**選擇**: better-sqlite3（同步 API）
**替代方案**: bun:sqlite (Bun 原生，API 略不同)
**理由**: 同步 API 更適合 CLI 工具；社群成熟；跨平台支援佳。

### D6: Git 分支策略

**選擇**: `v1` 分支保存、`v2` 分支開發、完成後合併回 `main`
**理由**: v1 可隨時回溯；v2 開發不影響現有 main；合併後 main 即為 v2。

## Risks / Trade-offs

- **[Risk] Ink TUI 複雜度**: Textual 的 widget 生態比 Ink 豐富，部分元件需自建
  → **Mitigation**: 先完成 CLI 指令（Phase 1-3），TUI 放到 Phase 5，可分階段交付

- **[Risk] better-sqlite3 原生綁定**: 需要 C++ 編譯，可能在某些環境失敗
  → **Mitigation**: 備選使用 `bun:sqlite` 原生 API；mem 功能降級為純 HTTP 模式

- **[Risk] Bun 相容性**: 部分 npm 套件可能與 Bun runtime 不完全相容
  → **Mitigation**: 在開發初期建立 CI smoke test，及早發現不相容

- **[Risk] 遷移期間功能凍結**: v2 開發期間 v1 不再加新功能
  → **Mitigation**: bug fix 可在 v1 分支進行並 cherry-pick

## Migration Plan

1. 建立 `v1` 分支保存現有程式碼
2. 建立 `v2` 分支，移除 Python 檔案，初始化 Bun 專案
3. 按 Phase 順序實作（Utils → CLI → 子命令 → Manifest → TUI → 整合測試）
4. 全部測試通過後合併 v2 → main
5. 打 `v2.0.0` tag，發佈到 npm
6. 更新 README 安裝指南

**Rollback**: 如果 v2 開發遇到阻塞性問題，`v1` 分支仍為完整可用版本，隨時可切回。

## Open Questions

- bun:sqlite 是否已足夠成熟取代 better-sqlite3？（需實測）
- Ink fullscreen 模式在 Windows Terminal 的表現是否穩定？（需跨平台測試）
