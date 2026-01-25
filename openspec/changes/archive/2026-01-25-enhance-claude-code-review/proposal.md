# Change: 增強 Claude Code Review GitHub Action 功能

## Why

目前 GitHub Action 已經設定 Claude Code Review，但存在以下改進需求：
1. 正式 PR 時需要手動 @claude 才會觸發，希望能自動觸發
2. Code Review 時缺少專案特定的審查重點 prompt，需要決定 prompt 的最佳存放位置
3. 缺乏手動/自動觸發的設定說明文件
4. 審查標準需要文件化以利未來維護

## What Changes

### 1. PR 自動觸發 Claude Review
- 修改 `claude-code-review.yml`，在非 Draft PR 開啟/同步時自動觸發 Claude Review
- 排除 Draft PR，僅在 `ready_for_review` 時觸發
- 預留檔案類型過濾機制（透過 `paths` 配置，目前註解保留）

### 2. Code Review Prompt 配置
- 建立 `.github/prompts/code-review.md` 作為審查 prompt
- 指定回覆語言為繁體中文，專有名詞保留原文
- 審查標準獨立文件化，便於維護與異動

### 3. 文件說明
- 建立 `.github/CODE_REVIEW.md` 說明手動/自動觸發設定方式
- 記錄 prompt 配置位置與修改方法

## Impact

- Affected files:
  - `.github/workflows/claude-code-review.yml`（主要修改）
  - `.github/prompts/code-review.md`（新增）
  - `.github/CODE_REVIEW.md`（新增）
- 相關規範：
  - `.standards/code-review.ai.yaml`
  - `CLAUDE.md`
