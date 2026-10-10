# Report Schema

`work-log-codex` now renders three Markdown layers with different audiences.

## 1. Report

Primary human-facing deliverable.

```md
## 工作日誌 <區段>

### 當日總結

### 逐專案摘要
#### <project>
- **一行重點：** <一句可獨立閱讀的任務重點>
  - **重點脈絡：** <300 字以內，說明起因、處理、結果與證據邊界>
  - **來源：** <正式文件路徑及／或 repo@commit>

### 工時統計

### 每日摘要
```

Rules:
- 每個專案保留可讀摘要，不折成 `其他`
- 每個專案整理 2 至 5 個任務；不足時不硬湊
- 每個任務都保留「一行重點／重點脈絡／來源」三層
- 重點脈絡不超過 300 個 Unicode 字元，不重複一行重點
- 沒有 commit 或正式文件時，標成研究／規劃並如實寫出證據缺口
- 不得包含 `Token 消耗`、`工具使用`、`Commit 明細`、`Session 明細`

## 2. Appendix

Project evidence attachment.

```md
## 工作日誌附件 <區段>

### 專案證據附錄
#### <project>
- 狀態
- Commit 證據
- 代表檔案
- 必要補充
```

Rules:
- 面向人類驗證，不是 raw dump
- 可以列 commit 主題與代表檔案
- 來源需直接支持主報告的相鄰任務，不以原始 session JSONL 代替正式完成證據
- 不得包含 token / tool / session audit

## 3. Debug

Machine-oriented audit output.

```md
## 工作日誌偵錯 <區段>

### 工時統計
### 每日摘要
### Token 消耗
### 工具使用
### Commit 明細
### Session 明細
### Codex Sessions
```

Rules:
- 只有明確要求時才輸出
- 原始稽核資訊只出現在這裡

## File Paths

- Report: `docs/work-logs/YYYY-MM-DD.md` or `docs/work-logs/YYYY-MM-DD--YYYY-MM-DD.md`
- Appendix: `docs/work-logs/YYYY-MM-DD.appendix.md` or `docs/work-logs/YYYY-MM-DD--YYYY-MM-DD.appendix.md`
- Debug: `docs/work-logs/YYYY-MM-DD.debug.md` or `docs/work-logs/YYYY-MM-DD--YYYY-MM-DD.debug.md`

`docs/work-logs/` 是可重建的本機輸出。repository 若已忽略此目錄，formatter 不改變其
Git 追蹤狀態；需要版本化的正式報告時，另用該專案的正式報告路徑。
