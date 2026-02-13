# session-context-load Specification

## Purpose
TBD

## Requirements

### Requirement: SessionStart 載入最近會話的結構化事實
session-start.py SHALL 找到最近 7 天內的最新 .tmp 檔，讀取其內容，並透過 stdout 輸出給 Claude 作為上下文。

#### Scenario: 有近期會話檔案
- **WHEN** `~/.claude/sessions/` 中有 7 天內的 .tmp 檔
- **THEN** 讀取最新的 1 個 .tmp 檔，將內容透過 stdout 輸出（Claude 會接收為上下文）

#### Scenario: 沒有近期會話檔案
- **WHEN** `~/.claude/sessions/` 中沒有 7 天內的 .tmp 檔
- **THEN** 僅輸出元資訊提示（「沒有近期會話記錄」），不注入上下文

#### Scenario: .tmp 檔案過大
- **WHEN** 最新的 .tmp 檔大於 10 KB
- **THEN** 只載入前 10 KB 的內容，並在末尾加上 `[內容已截斷]`

### Requirement: SessionStart 保留現有功能
session-start.py SHALL 繼續執行現有的套件管理器偵測和別名顯示功能，新增的上下文載入不影響原有行為。

#### Scenario: 正常啟動流程
- **WHEN** Claude Code 會話啟動
- **THEN** 依序執行：載入上一次會話上下文 → 偵測套件管理器 → 顯示別名清單

### Requirement: SessionStart 輸出格式
載入的會話上下文 SHALL 透過 stdout 輸出，並以清晰的邊界標記包裹，讓 Claude 能區分歷史上下文和新的指示。

#### Scenario: 輸出格式
- **WHEN** 成功載入上一次會話的 .tmp 檔
- **THEN** stdout 輸出格式為：
  ```
  [上次會話摘要 - <日期>]
  <.tmp 檔內容>
  [/上次會話摘要]
  ```
