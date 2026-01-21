# skill-npm-integration Spec Delta

## MODIFIED Requirements

### Requirement: NPM Skills Package Integration (NPM Skills 套件整合)

腳本 MUST (必須) 在 `install` 與 `update` 指令中包含 `skills` npm 套件的安裝與更新。

> **變更說明**：將 `maintain` 指令參考改為 `update`。

#### Scenario: Update 時更新 skills 套件

給定使用者執行 `update` 指令
當 NPM 套件更新階段執行時
則應該執行 `npm install -g skills` 以更新 skills 套件
