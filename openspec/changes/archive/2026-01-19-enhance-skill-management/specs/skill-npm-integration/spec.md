# skill-npm-integration Specification

## Purpose
維護 `skills` npm 套件並提示使用者可用的第三方 skill 管理指令。

## ADDED Requirements

### Requirement: Skills NPM Package Maintenance (Skills NPM 套件維護)
腳本 MUST (必須) 在 `install` 與 `maintain` 指令中包含 `skills` npm 套件的安裝與更新。

#### Scenario: 安裝 skills 套件
給定使用者執行 `install` 指令
當安裝全域 NPM 套件時
則應該包含 `skills` 套件的安裝。

#### Scenario: 更新 skills 套件
給定使用者執行 `maintain` 指令
當更新全域 NPM 套件時
則應該更新 `skills` 套件到最新版本。

### Requirement: Skills Command Hints (Skills 指令提示)
腳本 MUST (必須) 在適當時機提示使用者 `npx skills` 的可用指令。

#### Scenario: 安裝完成後提示
給定使用者執行 `install` 指令
當所有步驟完成時
則應該顯示 `npx skills` 的可用指令提示：
- `npx skills add <package>` - 安裝 skill 套件
- `npx skills install <package>` - 同上（別名）
- `npx skills list` - 列出已安裝套件
- 並附上範例：`npx skills add vercel-labs/agent-skills`

#### Scenario: Status 指令顯示提示
給定使用者執行 `status` 指令
當顯示環境狀態時
則應該包含 `skills` 套件的安裝狀態與可用指令提示。
