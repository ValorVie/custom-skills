---
description: 執行 PHPUnit 測試並分析結果
allowed-tools: Bash(phpunit:*), Bash(php:*), Bash(./vendor/bin/phpunit:*), Bash(composer:*)
argument-hint: "[path] [--verbose] [--stop-on-failure] [--filter method]"
---

# Custom Skills PHP Test | PHPUnit 測試執行與分析

執行 PHPUnit 測試並由 AI 分析結果。

## Workflow | 工作流程

### Step 0: 確認前置需求

檢查 PHPUnit 是否已安裝：

```bash
test -f ./vendor/bin/phpunit && echo "PHPUnit OK" || echo "PHPUnit not found"
```

**如果 PHPUnit 未安裝，提示使用者：**

```
⚠️ PHPUnit 未安裝。請執行以下命令安裝：

composer require --dev phpunit/phpunit

安裝完成後再次執行此命令。
```

### Step 1: 執行測試

```bash
./vendor/bin/phpunit [options]
```

**Options:**
- `--verbose`, `-v`: 顯示詳細輸出
- `--stop-on-failure`: 失敗時立即停止
- `--filter <method>`: 過濾測試方法名稱

### Step 2: 分析結果

根據 PHPUnit 輸出，分析並回報：

#### 2.1 測試摘要
從輸出中提取：
- 通過數量（OK）
- 失敗數量（failures）
- 錯誤數量（errors）
- 跳過數量（skipped）
- 執行時間

格式範例：
```
## 測試結果

✓ **通過**: 15  ✗ **失敗**: 2  ⚠ **錯誤**: 0  ○ **跳過**: 1  ⏱ **時間**: 1.23s
```

#### 2.2 失敗分析（如有失敗）
對每個失敗的測試：
1. 識別失敗的測試類別和方法
2. 分析錯誤訊息和 stack trace
3. 推測可能的失敗原因
4. 建議修復方向

格式範例：
```
### 失敗測試分析

#### `UserTest::testLogin` (tests/Unit/UserTest.php:45)
**錯誤**: Failed asserting that 401 matches expected 200
**原因**: 認證 token 可能已過期或格式錯誤
**建議**: 檢查 token 生成邏輯，確認 expiry 設定
```

#### 2.3 整體評估
- 測試是否全部通過
- 如有失敗，優先處理建議

## TDD Workflow | TDD 工作流程

此命令支援 Red-Green 循環：

1. **Red Phase**: 執行測試，預期失敗
   ```
   /custom-skills-php-test
   ```
   → 分析哪些測試失敗，確認是預期的失敗

2. **實作功能程式碼**

3. **Green Phase**: 執行測試，預期通過
   ```
   /custom-skills-php-test
   ```
   → 確認所有測試通過

## Prerequisites | 前置需求

**PHPUnit**（Step 0 會自動檢查）：
```bash
composer require --dev phpunit/phpunit
```
