# Spec: skill-toggle

## ADDED Requirements

### Requirement: toggle 指令整合檔案移動機制 (MUST)

修改現有 `toggle` 指令，MUST 整合檔案移動機制而非僅更新配置檔。

#### Scenario: toggle --disable 觸發檔案移動

**Given** 使用者執行 toggle 指令帶 --disable 參數
**When** 指令執行
**Then** 系統應呼叫 `disable_resource()` 函式移動檔案
**And** 不再呼叫 `copy_skills()` 進行全量同步

#### Scenario: toggle --enable 觸發檔案還原

**Given** 使用者執行 toggle 指令帶 --enable 參數
**When** 指令執行
**Then** 系統應呼叫 `enable_resource()` 函式還原檔案
**And** 不再呼叫 `copy_skills()` 進行全量同步
