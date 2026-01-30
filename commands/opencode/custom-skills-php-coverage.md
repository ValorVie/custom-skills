---
description: 執行 PHPUnit 覆蓋率分析並提供改善建議
allowed-tools: Bash(phpunit:*), Bash(php:*), Bash(./vendor/bin/phpunit:*), Bash(composer:*)
argument-hint: "[--source dir] [--html path] [--clover path]"
---

# Custom Skills PHP Coverage | PHPUnit 覆蓋率分析

執行 PHPUnit 測試覆蓋率分析並由 AI 分析結果、提供改善建議。

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

### Step 1: 執行覆蓋率分析

```bash
./vendor/bin/phpunit --coverage-text
```

**Options:**
- `--coverage-text`: 輸出文字格式覆蓋率報告
- `--coverage-html <dir>`: 生成 HTML 報告
- `--coverage-clover <file>`: 生成 Clover XML 報告

### Step 2: 分析結果

根據 PHPUnit 覆蓋率輸出，分析並回報：

#### 2.1 整體摘要
從輸出中提取：
- Lines 覆蓋率百分比
- Methods 覆蓋率百分比
- Classes 覆蓋率百分比

格式範例：
```
## 覆蓋率報告

| 類型 | 覆蓋率 |
|------|--------|
| Lines | 75% (150/200) |
| Methods | 80% (16/20) |
| Classes | 85% (17/20) |
```

#### 2.2 各類別覆蓋率
以表格呈現各類別狀態：

```markdown
| 類別 | Lines | Methods | 未覆蓋方法 |
|------|-------|---------|-----------|
| App\Services\UserService | 85% | 90% | handleError |
| App\Models\User | 60% | 75% | validate, normalize |
```

標示規則：
- ≥ 80%: 良好
- 60-79%: 需改善
- < 60%: 警告

#### 2.3 改善建議
針對低覆蓋率類別：
1. 識別未覆蓋的方法
2. 分析這些方法的功能
3. 建議應撰寫的測試類型

格式範例：
```
### 改善建議

#### `App\Services\UserService` (60%)
**未覆蓋方法**:
- `handleError()`: 錯誤處理邏輯
- `validateInput()`: 輸入驗證

**建議測試**:
1. 測試 `handleError()` 處理各種例外狀況
2. 測試 `validateInput()` 的邊界條件和無效輸入
```

#### 2.4 優先順序
根據以下因素排序改善優先級：
1. 類別的重要性（Service > Model > Helper）
2. 覆蓋率差距
3. 未覆蓋方法的風險程度

## 覆蓋率門檻參考

| 等級 | 覆蓋率 | 說明 |
|------|--------|------|
| 優秀 | ≥ 90% | 高品質測試覆蓋 |
| 良好 | 80-89% | 符合一般標準 |
| 及格 | 70-79% | 最低可接受 |
| 不足 | < 70% | 需要改善 |

## Prerequisites | 前置需求

需要安裝覆蓋率驅動（擇一）：

**PCOV（推薦，效能較佳）**:
```bash
pecl install pcov
```

**Xdebug**:
```bash
pecl install xdebug
```

並在 `phpunit.xml` 中設定覆蓋率來源：
```xml
<coverage>
    <include>
        <directory suffix=".php">src</directory>
    </include>
</coverage>
```
