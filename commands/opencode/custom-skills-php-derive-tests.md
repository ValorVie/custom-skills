---
description: 從 OpenSpec specs 生成完整 PHPUnit 測試程式碼
allowed-tools: Read, Write, Glob, Grep
argument-hint: "<specs-path> [--output <tests-dir>]"
---

# Custom Skills PHP Derive Tests | PHPUnit 測試生成

從 OpenSpec specs 的 WHEN/THEN 場景生成完整可執行的 PHPUnit 測試程式碼。

## Workflow | 工作流程

### Step 1: 讀取 Specs

使用 Read 工具讀取 specs 內容：

1. 使用 Glob 找到 specs 目錄下的所有 `.md` 檔案
2. 使用 Read 讀取每個 spec 檔案

### Step 2: 理解場景語義

分析 specs 中的 WHEN/THEN 格式：

| Spec 元素 | 語義 |
|-----------|------|
| `### Requirement:` | 功能需求，對應測試類別 |
| `#### Scenario:` | 測試場景，對應測試方法 |
| `- **WHEN**` | 前置條件（Arrange） |
| `- **AND**` | 附加條件（Arrange 續） |
| `- **THEN**` | 預期結果（Assert） |

理解場景的業務語義，將其對應到 PHP 程式碼概念。

### Step 3: 讀取專案程式碼

找到被測類別的位置和方法簽名：

1. 使用 Glob 找到相關的 PHP 檔案
2. 使用 Read 讀取被測類別
3. 檢查 `composer.json` 的 autoload-dev 設定確認 namespace

### Step 4: 生成測試程式碼

根據場景生成完整的 PHPUnit 測試程式碼（AAA 格式）：

```php
<?php

namespace Tests\Unit;

use PHPUnit\Framework\TestCase;
use PHPUnit\Framework\Attributes\Test;

class RequirementNameTest extends TestCase
{
    #[Test]
    public function test_scenario_name(): void
    {
        // Arrange
        // WHEN <前置條件>
        // AND <附加條件>
        $sut = new ClassUnderTest();

        // Act
        $result = $sut->methodUnderTest();

        // Assert
        // THEN <預期結果>
        $this->assertEquals($expected, $result);
    }
}
```

**轉換規則：**
- `### Requirement:` → `class {Name}Test extends TestCase`
- `#### Scenario:` → `public function test_{scenario_name}(): void`
- `- **WHEN**` / `- **AND**` → Arrange 區塊
- `- **THEN**` → Assert 區塊

### Step 4.1: 識別互動式場景

識別需要 mock 的場景：

**互動式場景特徵：**
- WHEN 包含「使用者選擇」「使用者輸入」「使用者點擊」
- THEN 包含「系統顯示」「系統提示」

**處理方式：**
1. 為可直接測試的邏輯生成單元測試
2. 將互動式場景標記為「需手動補充」
3. 在摘要中列出這些場景並提供 mock 範例

### Step 5: 決定檔案位置並寫入

1. 檢查專案的測試目錄結構（通常為 `tests/Unit/` 或 `tests/Feature/`）
2. 參考 `composer.json` 的 autoload-dev 設定
3. 決定測試檔案的適當路徑和 namespace
4. 使用 Write 工具寫入測試檔案

如果使用者指定 `--output <dir>`，則寫入指定目錄。

### Step 6: 顯示生成結果摘要

```
## 測試生成完成

**生成檔案:**
- tests/Unit/UserServiceTest.php (3 tests)
- tests/Unit/OrderTest.php (2 tests)

**測試數量:** 5 個測試方法

**下一步:** 執行 `/custom-skills-php-test` 驗證測試（Red Phase）
```

**如有互動式場景，額外顯示：**

```
## 需手動補充的互動式場景

以下場景涉及使用者輸入或 UI 互動，需手動補充測試：

| Requirement | Scenario | 原因 |
|-------------|----------|------|
| 表單驗證 | 顯示驗證錯誤 | 需 mock Request |
| 使用者認證 | 重新導向登入頁 | 需 mock Session |

### Mock 範例

```php
use Mockery;

class UserControllerTest extends TestCase
{
    public function test_redirect_to_login_when_unauthenticated(): void
    {
        // Arrange
        $request = Mockery::mock(Request::class);
        $request->shouldReceive('user')->andReturn(null);

        // Act
        $response = $this->get('/dashboard');

        // Assert
        $response->assertRedirect('/login');
    }
}
```
```

## Example | 範例

### 輸入 Spec

```markdown
### Requirement: 使用者認證

#### Scenario: 正確密碼登入成功
- **WHEN** 使用者提供正確的 email 和密碼
- **THEN** 系統回傳認證 token
- **AND** 系統記錄登入時間
```

### 生成的測試

```php
<?php

namespace Tests\Unit;

use PHPUnit\Framework\TestCase;
use PHPUnit\Framework\Attributes\Test;
use App\Services\AuthService;

class UserAuthenticationTest extends TestCase
{
    #[Test]
    public function test_login_success_with_correct_credentials(): void
    {
        // Arrange
        // WHEN 使用者提供正確的 email 和密碼
        $authService = new AuthService();
        $email = 'user@example.com';
        $password = 'correct-password';

        // Act
        $result = $authService->login($email, $password);

        // Assert
        // THEN 系統回傳認證 token
        $this->assertNotEmpty($result['token']);
        // AND 系統記錄登入時間
        $this->assertNotNull($result['logged_in_at']);
    }
}
```

## TDD Workflow | TDD 工作流程

此命令是 TDD 流程的第一步：

1. **生成測試** (此命令)
   ```
   /custom-skills-php-derive-tests specs/
   ```

2. **Red Phase**: 執行測試，預期失敗
   ```
   /custom-skills-php-test
   ```

3. **實作功能程式碼**

4. **Green Phase**: 執行測試，預期通過
   ```
   /custom-skills-php-test
   ```

5. **覆蓋率驗證**
   ```
   /custom-skills-php-coverage
   ```

## Limitations | 限制

- 生成的測試可能需要微調
- **互動式場景**（使用者輸入、UI 互動）會標記為「需手動補充」並提供 mock 範例
- 複雜的 mock 場景需手動補充
- 依賴 AI 理解場景語義和專案程式碼
- 需要專案已正確設定 composer autoload
