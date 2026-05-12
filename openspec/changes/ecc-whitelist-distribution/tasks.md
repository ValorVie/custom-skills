# Tasks: ECC 白名單分發機制

## 1. Catalog 與 Seed Data

- [ ] 1.1 撰寫 `script/cli/_internal/generate_ecc_catalog_seed.py`（一次性腳本），從目前 `distribution.yaml` 的 exclude 註解分組產生 `ecc-catalog.yaml` 初版
- [ ] 1.2 依 explore 階段的 13 個 category 分類產生初始 catalog（133 項分類好，uncategorized 留空）
- [ ] 1.3 為每個 skill 補 `added` 欄位（用 `git log --diff-filter=A` 取首次出現日期；取不到留空）
- [ ] 1.4 提交 `upstream/ecc-catalog.yaml`

## 2. distribution.yaml 改寫

- [ ] 2.1 在 `distribute.skills` 下新增 `enabled` 欄位，填入 133 個目前實際分發的 skill 名稱
- [ ] 2.2 移除 `exclude.skills` 區塊
- [ ] 2.3 保留 `exclude.commands`、`exclude.agents`（不變）
- [ ] 2.4 用註解說明 enabled 為白名單，引導使用者參考 `ecc-catalog.yaml`

## 3. Runtime 邏輯改寫

- [ ] 3.1 `script/utils/shared.py::_load_distribution_config` 移除 `ecc-profile.yaml` 合併邏輯
- [ ] 3.2 `_load_distribution_config` 偵測到 `~/.config/ai-dev/ecc-profile.yaml` 存在時印出一次性 deprecation 警告
- [ ] 3.3 `_prescan_ecc` 將 skills 的 `item.name not in exclude_skills` 改為 `item.name in enabled_skills`
- [ ] 3.4 `_distribute_ecc_selective` 對應修改（同樣的白名單判斷）
- [ ] 3.5 enabled 中列出但 ECC 不存在的項目，印黃色警告

## 4. ai-dev ecc audit 子命令

- [ ] 4.1 新增 `script/commands/ecc.py`，含 `audit` 子命令
- [ ] 4.2 實作 ECC 目錄掃描 → 與 catalog 比對 → 產生 NEW / GONE 清單
- [ ] 4.3 實作 RENAMED? 偵測（Levenshtein ≤ 3 或共同前綴 ≥ 5）
- [ ] 4.4 輸出格式化 patch（yaml 片段，可直接複製）
- [ ] 4.5 退出碼：0 無差異、1 有差異、2 ECC 缺失
- [ ] 4.6 註冊到 CLI（`script/cli/parser.py` 或對等位置）

## 5. install / clone 警告

- [ ] 5.1 在 `_load_distribution_config` 後新增廉價 catalog 落後檢查
- [ ] 5.2 偵測到 NEW 時印黃色非阻塞警告
- [ ] 5.3 catalog 不存在時印一次性提示（用 `~/.cache/ai-dev/ecc-catalog-hint-shown` flag 避免每次重複）

## 6. 測試

- [ ] 6.1 單元測試：`_prescan_ecc` 白名單過濾（在/不在 enabled、空 enabled、enabled 列了不存在的名稱）
- [ ] 6.2 單元測試：catalog 解析（缺漏、格式錯誤、uncategorized 空/非空）
- [ ] 6.3 單元測試：audit 命令的 NEW / GONE / RENAMED? 偵測
- [ ] 6.4 整合測試：`ai-dev clone` 完整流程以白名單分發 ECC（mock ECC 目錄）
- [ ] 6.5 整合測試：install 偵測到 catalog 落後時印警告且不阻塞
- [ ] 6.6 回歸測試：commands / agents 黑名單分發不受影響
- [ ] 6.7 全套測試 `pytest`（含現有 42 個 manifest/clone 測試）

## 7. 文件

- [ ] 7.1 更新 `openspec/specs/ecc-selective-distribution/spec.md`（archive 階段由工具同步）
- [ ] 7.2 新增 `openspec/specs/ecc-catalog/spec.md`（archive 階段）
- [ ] 7.3 更新 `README.md` 或 `docs/` 對應段落，說明白名單機制與 audit 使用
- [ ] 7.4 在 `upstream/CLAUDE.md` 中說明 catalog 與 distribution.yaml 的關係
- [ ] 7.5 為 `ai-dev ecc audit` 寫使用範例

## 8. 遷移與相容

- [ ] 8.1 撰寫 CHANGELOG 條目，標註 `exclude.skills` 與 `ecc-profile.yaml` 行為變更
- [ ] 8.2 若有現存 `~/.config/ai-dev/ecc-profile.yaml`，第一次執行印出遷移指引
- [ ] 8.3 驗證升級路徑：舊版 → 新版執行 `ai-dev clone` 結果與升級前一致（133 個 skill 分發不變）

## 9. 收尾

- [ ] 9.1 執行 `openspec validate ecc-whitelist-distribution --strict`
- [ ] 9.2 PR review
- [ ] 9.3 合併後執行 `/opsx:archive`
