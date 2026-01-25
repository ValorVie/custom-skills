# Change: 新增 custom-skills-dev Skill

## Why

開發 custom-skills 專案時，需要遵循特定的架構模式、三階段複製流程、語言規範和工具配置。目前這些知識分散在多個文檔中（README.md、copy-architecture.md、project.md），開發者（包括 AI 助手）需要花費大量時間理解專案結構和開發流程。

建立一個專門的 skill 可以：
1. 集中開發流程知識，減少上下文切換
2. 確保開發時遵循正確的架構模式
3. 提供快速參考，加速開發效率

## What Changes

- 新增 `skills/custom-skills-dev/` skill 目錄
- 包含 SKILL.md 主文件和 references 目錄
- 涵蓋：
  - 三階段複製架構（Clone → 整合 → 分發）
  - 專案目錄結構說明
  - CLI 開發流程（Python + uv）
  - 版本發布流程
  - 常見開發任務指南

## Impact

- Affected specs: `skill-integration`
- Affected code: `skills/` 目錄
- 無破壞性變更
