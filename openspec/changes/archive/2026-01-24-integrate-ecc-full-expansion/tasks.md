# Tasks: 全面整合 everything-claude-code 並擴展標準體系

**狀態**: ✅ 已完成
**完成日期**: 2026-01-24

## 1. Hook 系統整合

- [x] 1.1 建立 `sources/ecc/hooks/` 目錄結構
- [x] 1.2 建立 `sources/ecc/hooks/memory-persistence/` 目錄
- [x] 1.3 重寫 `session-start.py` — 載入先前 context 與偵測 package manager
- [x] 1.4 重寫 `session-end.py` — 持久化 session 狀態
- [x] 1.5 重寫 `pre-compact.py` — compact 前儲存狀態
- [x] 1.6 建立 `sources/ecc/hooks/strategic-compact/` 目錄
- [x] 1.7 重寫 `suggest-compact.py` — 策略性 compact 建議
- [x] 1.8 建立 `hooks.json` 配置（保持原格式，路徑使用 Python）
- [x] 1.9 建立 `sources/ecc/hooks/README.md` 使用說明
- [x] 1.10 建立 `sources/ecc/hooks/utils.py` 共用工具函式

## 2. Skills 整合

- [x] 2.1 複製 `skills/continuous-learning/` 到 `sources/ecc/skills/`
- [x] 2.2 複製 `skills/strategic-compact/` 到 `sources/ecc/skills/`
- [x] 2.3 複製 `skills/eval-harness/` 到 `sources/ecc/skills/`
- [x] 2.4 複製 `skills/security-review/` 到 `sources/ecc/skills/`
- [x] 2.5 複製 `skills/tdd-workflow/` 到 `sources/ecc/skills/`（TDD 補充）
- [x] 2.6 為每個 skill 新增 upstream 標頭註解

## 3. Agents 整合

- [x] 3.1 複製 `agents/build-error-resolver.md` 到 `sources/ecc/agents/`
- [x] 3.2 複製 `agents/e2e-runner.md` 到 `sources/ecc/agents/`
- [x] 3.3 複製 `agents/doc-updater.md` 到 `sources/ecc/agents/`
- [x] 3.4 複製 `agents/security-reviewer.md` 到 `sources/ecc/agents/`
- [x] 3.5 為每個 agent 新增 upstream 標頭註解

## 4. Commands 整合

- [x] 4.1 複製 `commands/checkpoint.md` 到 `sources/ecc/commands/`
- [x] 4.2 複製 `commands/build-fix.md` 到 `sources/ecc/commands/`
- [x] 4.3 複製 `commands/e2e.md` 到 `sources/ecc/commands/`
- [x] 4.4 複製 `commands/learn.md` 到 `sources/ecc/commands/`
- [x] 4.5 複製 `commands/test-coverage.md` 到 `sources/ecc/commands/`
- [x] 4.6 複製 `commands/eval.md` 到 `sources/ecc/commands/`
- [x] 4.7 為每個 command 新增 upstream 標頭註解

## 5. OpenCode & MCP 參考資源

- [x] 5.1 建立 `sources/ecc/plugins/` 目錄
- [x] 5.2 建立 `sources/ecc/plugins/README.md`
- [x] 5.3 建立 `sources/ecc/mcp-configs/` 目錄
- [x] 5.4 建立 `sources/ecc/mcp-configs/mcp-servers.json`
- [x] 5.5 建立 `sources/ecc/mcp-configs/README.md` 使用說明

## 6. 標準體系架構

- [x] 6.1 建立 `.standards/profiles/` 目錄
- [x] 6.2 建立 `.standards/profiles/uds.yaml` — UDS 體系定義
- [x] 6.3 建立 `.standards/profiles/ecc.yaml` — ECC 體系定義
- [x] 6.4 建立 `.standards/profiles/minimal.yaml` — Minimal 體系定義
- [x] 6.5 建立 `.standards/active-profile.yaml` — 預設啟用 uds
- [x] 6.6 建立 `script/commands/standards.py` — 標準切換指令
- [ ] 6.7 更新 `script/ai_dev_cli.py` 整合 standards 命令（保留供後續整合）
- [x] 6.8 測試 standards.py 切換流程

## 7. TDD 標準整合

- [x] 7.1 更新 `.standards/test-driven-development.md` 新增「實戰範例附錄」章節
- [x] 7.2 新增 Jest/Vitest 實戰範例
- [x] 7.3 新增 Mock 範例
- [x] 7.4 新增 Playwright E2E 範例
- [x] 7.5 新增 Red-Green-Refactor 實作範例

## 8. Upstream 追蹤更新

- [x] 8.1 確認 `upstream/sources.yaml` 已有 ecc 配置
- [x] 8.2 建立 `upstream/ecc/mapping.yaml` 完整檔案對照
- [x] 8.3 建立 `upstream/ecc/last-sync.yaml` 同步資訊

## 9. 文件與 README 更新

- [x] 9.1 建立 `sources/ecc/README.md` 總覽說明
- [x] 9.2 更新專案 README 說明 ecc 整合
- [x] 9.3 更新專案 README 說明標準體系切換

## 10. OpenSpec 完成

- [x] 10.1 更新 tasks.md 標記完成狀態
- [x] 10.2 確認所有主要功能已實作

---

## 實作摘要

### 新增檔案（共 35 個）

**Hooks（7 個）**:
- `sources/ecc/hooks/utils.py`
- `sources/ecc/hooks/hooks.json`
- `sources/ecc/hooks/README.md`
- `sources/ecc/hooks/memory-persistence/session-start.py`
- `sources/ecc/hooks/memory-persistence/session-end.py`
- `sources/ecc/hooks/memory-persistence/pre-compact.py`
- `sources/ecc/hooks/memory-persistence/evaluate-session.py`
- `sources/ecc/hooks/strategic-compact/suggest-compact.py`

**Skills（6 個）**:
- `sources/ecc/skills/continuous-learning/SKILL.md`
- `sources/ecc/skills/continuous-learning/config.json`
- `sources/ecc/skills/strategic-compact/SKILL.md`
- `sources/ecc/skills/eval-harness/SKILL.md`
- `sources/ecc/skills/security-review/SKILL.md`
- `sources/ecc/skills/tdd-workflow/SKILL.md`

**Agents（4 個）**:
- `sources/ecc/agents/build-error-resolver.md`
- `sources/ecc/agents/e2e-runner.md`
- `sources/ecc/agents/doc-updater.md`
- `sources/ecc/agents/security-reviewer.md`

**Commands（6 個）**:
- `sources/ecc/commands/checkpoint.md`
- `sources/ecc/commands/build-fix.md`
- `sources/ecc/commands/e2e.md`
- `sources/ecc/commands/learn.md`
- `sources/ecc/commands/test-coverage.md`
- `sources/ecc/commands/eval.md`

**Plugins & MCP（3 個）**:
- `sources/ecc/plugins/README.md`
- `sources/ecc/mcp-configs/mcp-servers.json`
- `sources/ecc/mcp-configs/README.md`

**Standards Profiles（5 個）**:
- `.standards/profiles/uds.yaml`
- `.standards/profiles/ecc.yaml`
- `.standards/profiles/minimal.yaml`
- `.standards/active-profile.yaml`
- `script/commands/standards.py`

**Upstream（2 個）**:
- `upstream/ecc/mapping.yaml`
- `upstream/ecc/last-sync.yaml`

**Documentation（1 個）**:
- `sources/ecc/README.md`

### 修改檔案（2 個）

- `.standards/test-driven-development.md` — 新增實戰範例附錄
- `README.md` — 新增資源來源與標準體系章節

### 待後續整合

- `script/ai_dev_cli.py` 整合 standards 命令
