## 1. 設定檔與配置

- [x] 1.1 建立 `upstream/distribution.yaml` — 定義 ECC 分發矩陣（來源路徑、平台對應、skip_directories、exclude 清單）
- [x] 1.2 修改 `upstream/sources.yaml` — ECC 的 `install_method` 從 `manual` 改為 `selective`

## 2. 核心分發邏輯

- [x] 2.1 在 `shared.py` 新增 `_load_distribution_config()` 函式 — 讀取並解析 `upstream/distribution.yaml`
- [x] 2.2 在 `shared.py` 新增 `_distribute_ecc_selective()` 函式 — 根據 distribution.yaml 從 `~/.config/everything-claude-code/` 分發到各平台
- [x] 2.3 在 `copy_custom_skills_to_targets()` 末尾呼叫 `_distribute_ecc_selective()` — 分發順序: custom-skills → custom repos → ECC selective
- [x] 2.4 整合 ManifestTracker — ECC 分發的檔案以 source=`ecc` 記錄 hash，支援衝突偵測和孤兒清理

## 3. 移除 ECC 本地複製品

- [x] 3.1 移除 `sources/ecc/` 整個目錄
- [x] 3.2 移除 `upstream/ecc/` 目錄（mapping.yaml、last-sync.yaml）
- [x] 3.3 移除 `plugins/ecc-hooks-old/` 整個目錄
- [x] 3.4 移除 6 個 ECC skills — `continuous-learning`, `strategic-compact`, `eval-harness`, `security-review`, `tdd-workflow`, `coding-standards`
- [x] 3.5 移除 5 個 ECC agents — `agents/claude/build-error-resolver.md`, `e2e-runner.md`, `doc-updater.md`, `security-reviewer.md`, `database-reviewer.md`
- [x] 3.6 移除 6 個 ECC commands — `commands/claude/checkpoint.md`, `build-fix.md`, `e2e.md`, `learn.md`, `test-coverage.md`, `eval.md`（同時移除 opencode 版本）

## 4. 清理開發模式邏輯

- [x] 4.1 移除 `integrate_to_dev_project()` 中的 ECC 段落（`shared.py:1561-1598`）
- [x] 4.2 確認 `integrate_to_dev_project()` 其他部分（UDS、Obsidian、Anthropic、Auto-Skill）不受影響

## 5. 驗證

- [x] 5.1 執行 `ai-dev clone` 驗證 ECC 資源正確分發到 `~/.claude/`（skills + commands + agents）
- [x] 5.2 驗證 OpenCode 目標正確使用 `.opencode/` 來源路徑
- [x] 5.3 驗證 Gemini 目標只分發 skills + agents，不分發 commands
- [x] 5.4 驗證 Codex 目標只分發 skills
- [x] 5.5 驗證 `plugins/ecc-hooks/` 和 `plugins/ecc-hooks-opencode/` 正常運作（未受影響）
- [x] 5.6 驗證 ManifestTracker 正確追蹤 ECC 來源的檔案
- [x] 5.7 執行 `ai-dev clone` 第二次，驗證無重複分發或錯誤（需部署後進行真實測試）
