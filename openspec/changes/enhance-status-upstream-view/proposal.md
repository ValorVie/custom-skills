## Why

`ai-dev status` 目前的「設定儲存庫」表只檢查 4 個 repo 是否為 Git 目錄，缺少 obsidian-skills、anthropic-skills、everything-claude-code。更重要的是，開發者同時身為使用者，但「本地環境是否最新」與「上游是否需要同步進本專案」這兩個不同關注點混在一起，難以一目了然。需要在 `ai-dev status` 中分離顯示，讓使用者快速判斷自己該做什麼。

## What Changes

- 補齊「設定儲存庫」表的 repo 清單，從 4 個擴充為 `REPOS` 字典定義的全部 6 個
- 改善「設定儲存庫」表的本地狀態顯示，加入 git HEAD vs origin HEAD 的比對（是否有可用更新）
- 新增「上游同步狀態」表，讀取 `upstream/last-sync.yaml` 並與各 repo 的 git HEAD 比對，顯示同步時間與落後 commit 數

## Capabilities

### New Capabilities
- `status-upstream-sync`: 在 `ai-dev status` 中顯示上游同步狀態表，比對 `last-sync.yaml` 記錄的 commit 與各 repo 目前的 HEAD，顯示是否落後及落後 commit 數

### Modified Capabilities
- `upstream-skills`: 補齊設定儲存庫表的 repo 清單至 6 個，並改善本地狀態顯示為 git commit 比對結果

## Impact

- 修改檔案：`script/commands/status.py`
- 新增依賴：需讀取 `upstream/last-sync.yaml`（YAML 解析）
- 需引用 `script/utils/shared.py` 的 `REPOS` 字典或 `upstream/sources.yaml` 來取得完整 repo 清單
- 需對各 repo 執行 `git rev-parse HEAD` 和 `git rev-list --count` 等 git 指令
