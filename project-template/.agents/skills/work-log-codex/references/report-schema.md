# Report Schema

`work-log-codex` now renders three Markdown layers with different audiences.

## 1. Report

Primary human-facing deliverable.

```md
## 工作日誌 <區段>

### 當日總結

### 逐專案摘要
#### <project>
- 2-5 個重點條列

### 工時統計

### 每日摘要
```

Rules:
- 每個專案保留可讀摘要，不折成 `其他`
- 每個專案摘要控制在約 500 字內
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
