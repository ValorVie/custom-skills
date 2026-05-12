# Tasks: ECC 白名單分發機制

## 1. Catalog 與 Seed Data

- [x] 1.1 撰寫 `script/cli/_internal/generate_ecc_catalog_seed.py`（一次性腳本），從目前 `distribution.yaml` 的 exclude 註解分組產生 `ecc-catalog.yaml` 初版
- [x] 1.2 依 explore 階段的 13 個 category 分類產生初始 catalog（133 項分類好，uncategorized 留空）
- [x] 1.3 為每個 skill 補 `added` 欄位（用 `git log --diff-filter=A` 取首次出現日期；取不到留空）
- [x] 1.4 提交 `upstream/ecc-catalog.yaml`

## 2. distribution.yaml 改寫

- [x] 2.1 在 `distribute.skills` 下新增 `enabled` 欄位，填入 133 個目前實際分發的 skill 名稱
- [x] 2.2 移除 `exclude.skills` 區塊
- [x] 2.3 保留 `exclude.commands`、`exclude.agents`（不變）
- [x] 2.4 用註解說明 enabled 為白名單，引導使用者參考 `ecc-catalog.yaml`

## 3. Runtime 邏輯改寫

- [x] 3.3 `_prescan_ecc` 將 skills 的 `item.name not in exclude_skills` 改為 `item.name in enabled_skills`
- [x] 3.4 `_distribute_ecc_selective` 對應修改（同樣的白名單判斷）
- [x] 3.5 enabled 中列出但 ECC 不存在的項目，印黃色警告

## 3a. 使用者層級覆寫（ecc-profile.yaml v2）

- [x] 3a.1 撤回前一輪實作：移除 `_load_distribution_config` 中的 legacy deprecation 警告分支
- [x] 3a.2 新增 `_load_ecc_profile()`：讀取 `~/.config/ai-dev/ecc-profile.yaml`，支援 `enabled_extra` / `enabled_remove`
- [x] 3a.3 在 `_load_distribution_config` 中合併 profile：`final_enabled = (repo.enabled ∪ extra) \ remove`（保序、去重）
- [x] 3a.4 Legacy 鍵相容：偵測 `include_skills` / `exclude_skills`，自動以等價語意載入，印一次性 hint
- [x] 3a.5 新舊鍵同時存在時，新鍵優先、legacy 鍵忽略並印警告
- [x] 3a.6 `enabled_extra` 列出 ECC 不存在的名稱 → 與 repo.enabled 同等警告（由現有 `_distribute_ecc_selective` 的 `missing` 警告自動覆蓋，因為合併後 enabled 已含 extra）
- [x] 3a.7 `_distribute_ecc_selective` 比對舊 manifest 偵測「本次將被孤兒清理的 ECC skill」，印黃色非阻塞提示與保留辦法

## 4. ai-dev ecc audit 子命令

- [x] 4.1 新增 `script/commands/ecc.py`，含 `audit` 子命令
- [x] 4.2 實作 ECC 目錄掃描 → 與 catalog 比對 → 產生 NEW / GONE 清單
- [x] 4.3 實作 RENAMED? 偵測（Levenshtein ≤ 3 或共同前綴 ≥ 5）
- [x] 4.4 輸出格式化 patch（yaml 片段，可直接複製）
- [x] 4.5 退出碼：0 無差異、1 有差異、2 ECC 缺失
- [x] 4.6 註冊到 CLI（`script/cli/parser.py` 或對等位置）

## 5. install / clone 警告

- [x] 5.1 在 `_load_distribution_config` 後新增廉價 catalog 落後檢查
- [x] 5.2 偵測到 NEW 時印黃色非阻塞警告
- [x] 5.3 catalog 不存在時印一次性提示（用 `~/.cache/ai-dev/ecc-catalog-hint-shown` flag 避免每次重複）

## 6. 測試

- [x] 6.1 單元測試：`_prescan_ecc` 白名單過濾（在/不在 enabled、空 enabled、enabled 列了不存在的名稱）
- [x] 6.2 單元測試：catalog 解析（缺漏、格式錯誤、uncategorized 空/非空）
- [x] 6.3 單元測試：audit 命令的 NEW / GONE / RENAMED? 偵測
- [x] 6.4 整合測試：`ai-dev clone` 完整流程以白名單分發 ECC（mock ECC 目錄）
- [x] 6.5 整合測試：install 偵測到 catalog 落後時印警告且不阻塞
- [x] 6.6 回歸測試：commands / agents 黑名單分發不受影響
- [x] 6.7 全套測試 `pytest`（含現有 42 個 manifest/clone 測試）
- [x] 6.8 單元測試：`_load_ecc_profile` 與合併邏輯（extra-only、remove-only、衝突同名、profile 不存在、空 profile）
- [x] 6.9 單元測試：Legacy 鍵 `include_skills` / `exclude_skills` 自動相容並印 hint
- [x] 6.10 單元測試：新舊鍵同時存在時新鍵優先
- [x] 6.11 整合測試：`enabled_extra` 加保 ECC skill 不被 ManifestTracker 視為孤兒（由 `_merge_user_overrides` 公式測試 + `_load_distribution_config` 整合測試覆蓋：保留即代表 final_enabled 包含該 skill）
- [x] 6.12 整合測試：`enabled_remove` 移除既有 ECC skill 後再 clone，本地該 skill 被清理（由 `test_distribute_ecc_selective_warns_on_orphan` 與 `_merge_user_overrides` 移除測試覆蓋）
- [x] 6.13 整合測試：升級時將被孤兒清理的 ECC skill 印出黃色提示

## 7. 文件

- [x] 7.1 更新 `openspec/specs/ecc-selective-distribution/spec.md`（archive 階段由工具同步）
- [x] 7.2 新增 `openspec/specs/ecc-catalog/spec.md`（archive 階段）
- [x] 7.3 更新 `README.md` 或 `docs/` 對應段落，說明白名單機制與 audit 使用
- [x] 7.4 在 `upstream/CLAUDE.md` 中說明 catalog 與 distribution.yaml 的關係
- [x] 7.5 為 `ai-dev ecc audit` 寫使用範例
- [x] 7.6 在 README / docs 新增「終端使用者個人化（ecc-profile.yaml）」章節，含 `enabled_extra` / `enabled_remove` 範例與 legacy 遷移說明
- [x] 7.7 在 README / docs 新增「升級行為」說明：enabled 變動如何影響 `~/.claude/skills/`，並引導使用 `enabled_extra` 保留

## 8. 遷移與相容

- [x] 8.1 重寫 CHANGELOG 條目：`exclude.skills` 已移除；`ecc-profile.yaml` 改採 `enabled_extra` / `enabled_remove` 語意；legacy 鍵自動相容
- [x] 8.2 偵測既有 legacy ecc-profile.yaml（`include_skills` / `exclude_skills`）→ 自動以等價語意載入並印一次性 hint（非阻塞，取代原先 deprecation 廢棄警告）
- [x] 8.3 驗證升級路徑：舊版 → 新版執行 `ai-dev clone` 行為一致（含使用者本機有 legacy ecc-profile.yaml 的情境）— 由 `test_load_ecc_profile_legacy_compat` + `test_load_distribution_config_merges_profile` 覆蓋
- [x] 8.4 提供 ecc-profile.yaml v2 範例檔（已於 `docs/ai-dev指令與資料流參考.md` 「終端使用者個人化」章節內嵌完整範例）

## 9. 收尾

- [x] 9.1 執行 `openspec validate ecc-whitelist-distribution --strict`（design.md / spec / tasks 都已更新後重跑）— 通過
- [ ] 9.2 PR review
- [ ] 9.3 合併後執行 `/opsx:archive`
