## ADDED Requirements

### Requirement: package.json 配置正確的 bin 和 files
`package.json` SHALL 設定 `"bin": { "ai-dev": "./src/cli.ts" }`，`"files"` 包含 `src/`、`dist/`、`skills/`、`commands/`、`agents/`。

#### Scenario: 全域安裝後可執行
- **WHEN** 使用者執行 `bun add -g @valorvie/ai-dev`
- **THEN** `ai-dev` 指令可在終端全域使用

#### Scenario: npm 安裝也可用
- **WHEN** 使用者執行 `npm install -g @valorvie/ai-dev`
- **THEN** `ai-dev` 指令可在終端全域使用

### Requirement: scoped package 公開發佈
套件 SHALL 使用 `@valorvie/ai-dev` 作為 scoped name，`publishConfig.access` 設為 `"public"`。

#### Scenario: npm publish 成功
- **WHEN** 執行 `npm publish`
- **THEN** 套件發佈到 npm registry，任何人可安裝

### Requirement: 建置腳本
`package.json` SHALL 提供 `build` script，使用 `bun build` 產生 `dist/cli.js`。

#### Scenario: 建置輸出
- **WHEN** 執行 `bun run build`
- **THEN** `dist/cli.js` 被產生
