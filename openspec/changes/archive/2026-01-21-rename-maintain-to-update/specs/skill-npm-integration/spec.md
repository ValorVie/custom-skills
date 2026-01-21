# skill-npm-integration Spec Delta

## MODIFIED Requirements

### Requirement: Skills NPM Package Maintenance (Skills NPM 套件維護)

腳本 MUST (必須) 在 `install` 與 `update` 指令中包含 `skills` npm 套件的安裝與更新。

> **變更說明**：將 `maintain` 指令參考改為 `update`。

#### Scenario: 安裝 skills 套件
給定使用者執行 `install` 指令
當安裝全域 NPM 套件時
則應該包含 `skills` 套件的安裝。

#### Scenario: 更新 skills 套件
給定使用者執行 `update` 指令
當更新全域 NPM 套件時
則應該更新 `skills` 套件到最新版本。
