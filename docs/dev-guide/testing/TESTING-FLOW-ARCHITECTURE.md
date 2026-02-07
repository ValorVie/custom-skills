# 完整測試流程架構（Testing Flow Architecture）

本文件用「測試金字塔 + CI/CD 流水線」的角度，說明一套成熟團隊常見的完整測試流程架構：測什麼（層次）、什麼時候測（流程）、測試結果如何變成可追蹤的品質訊號（產物與關卡）。

> 適用對象：需要維護或整合測試框架（特別是 E2E）的人；想建立一套可落地的測試流程的人。

---

## 1. 核心概念

### 1.1 測試金字塔：測試層級與投資比例

一個實用的分層方式（Industry Pyramid）通常是：

- 單元測試（UT）：最多、最快、最便宜
- 整合測試（IT/SIT）：驗證模組之間是否能正確協作
- 端對端測試（E2E）：最慢最貴，但最貼近真實使用者

關鍵原則：越接近 UI/真實環境的測試，維護成本越高，應該越精準聚焦「關鍵旅程」而不是「覆蓋所有路徑」。

### 1.2 CI/CD：把測試放到「可重複的自動化生產線」

測試若只靠人記得去跑，品質訊號會不穩定。成熟流程會把測試「嵌進」CI/CD：

- 每次提交/PR 都會觸發基本檢查
- 需要部署到測試環境的測試（E2E/ST）在環境就緒後自動執行
- 測試結果、報告、關卡（gate）會決定能否合併/發布

---

## 2. 全貌：層次（測什麼）

### 2.1 單元測試（Unit Testing, UT）

- 目標：驗證最小邏輯單位（函式/方法/類別）
- 特性：快、穩、可大量執行；依賴通常以 mock/stub 隔離
- 適合測：資料轉換、驗證規則、分支條件、錯誤處理

### 2.2 整合測試（Integration Testing, IT/SIT）

- 目標：驗證模組/服務/資料層的整合行為
- 特性：比 UT 慢，但能抓出「邊界契約」與「真實依賴」問題
- 適合測：資料庫 CRUD、Repository + DB、Service + 外部依賴（以測試替身或容器化依賴）

### 2.3 系統測試（System Testing, ST）

- 目標：在接近實際的部署型態下驗證系統需求
- 特性：偏「需求驗證」；可包含安全、可靠性、回復等

### 2.4 端對端測試（End-to-End, E2E）

- 目標：從使用者視角驗證完整旅程（UI -> API -> DB -> 外部服務）
- 特性：慢、容易受環境與網路影響；但能提供「最終信心」
- 適合測：登入/註冊、結帳/付款、核心交易/工作流等高風險路徑

---

## 3. 全貌：流程（什麼時候測）

下面是一個常見且可落地的流程切分。你可以把它視為「品質檢測流水線」：

### 3.1 本地迴圈（Developer Local Loop）

目標：在最早的時間點攔截錯誤。

- 靜態檢查（Lint/Format/Type Check）
- UT / IT（可選）
- 針對變更影響的「最小回歸集」

### 3.2 PR 迴圈（Pull Request Loop）

目標：在合併前提供一致的品質訊號。

- 靜態檢查 + UT（必跑）
- IT（常見：針對關鍵模組必跑）
- E2E Smoke（建議：快速確認環境活著、關鍵頁可到達）

### 3.3 部署後驗證（Post-Deploy Validation / Staging）

目標：在接近生產的環境上驗證「真實整合」。

- E2E Regression（主要旅程、P1/P2）
- Gate（關卡）：例如失敗率、跳過率（skip ratio）、不穩定測試（flaky）比例
- 報告產出（HTML / JUnit / Trace / Screenshot）供追查

### 3.4 發布後監控（Production Monitoring）

目標：測試不是結束，而是回饋。

- Canary / 合成監控（synthetic checks）
- 事故回歸：每次事故都要沉澱成 regression 測試或手動清單

---

## 4. 測試策略：如何把 E2E 變成「可維護」的最後防線

### 4.1 測試套件分群（推薦）

一套 E2E 測試通常會切成多個「目的不同」的集合：

- Smoke：30-60 秒，確認環境與最關鍵路徑沒有整體性故障
- Regression（P1/P2）：10-30 分鐘，覆蓋主要旅程與高風險功能
- Mutation / Data-writing：會改資料的測試，通常隔離執行、避免污染環境
- Quarantine：已知不穩定（flaky）或待修的測試，獨立管理與追蹤

### 4.2 環境與資料策略（E2E 成敗關鍵）

- 測試環境要「可重建」：固定版本、固定設定、可回滾
- 測試資料要「可控」：
  - 測試帳號/權限模型明確
  - 盡量避免依賴共享狀態
  - 若必須寫入資料，需有清理/重置策略

### 4.3 關卡（Gates）：避免測試形同虛設

常見的 gate 類型：

- Fail Gate：核心旅程失敗就阻斷合併/發布
- Skip Ratio Gate：允許因環境不完美而 skip，但限制跳過比例
- Flaky Gate：不穩定測試需隔離，避免污染主線訊號
- Duration Gate：時間過長意味著維護成本失控或環境退化

---

## 5. 測試產物（Artifacts）：讓結果可追查、可改善

每一層測試都應該能產出至少一種可追溯的產物：

- 測試輸出（stdout/stderr）與 exit code
- 報告：JUnit XML / HTML report
- 除錯證據：
  - E2E：screenshot、video、trace、console/network log
  - IT/ST：容器 log、DB snapshot

---

## 6.（本專案）測試命令與工作流整合點

此 repo 內建一套「命令只負責執行、分析交給 AI」的測試執行模式：

- `ai-dev test`：自動偵測測試框架（目前支援 pytest）並執行 [Source: Code] script/commands/test.py:15
- `ai-dev coverage`：使用 pytest-cov 進行覆蓋率分析 [Source: Code] script/commands/coverage.py:14
- `ai-dev derive-tests`：讀取 OpenSpec specs 內容，供 AI 生成測試程式碼 [Source: Code] script/commands/derive_tests.py:34

對應的開發流程（含手動測試清單替代方案）可參考：

- `docs/dev-guide/workflow/DEVELOPMENT-WORKFLOW.md`（Phase 5/5A/5.5/5.6）[Source: Code] docs/dev-guide/workflow/DEVELOPMENT-WORKFLOW.md:312

---

## 7. 技術實作範例（可直接複製）

### 7.1 本地開發的最小驗證流程

```bash
# 1) Python 測試（本專案內建）
uv run ai-dev test -v

# 2) 覆蓋率（本專案內建）
uv run ai-dev coverage --source script/

# 3) （如專案有前端/E2E）Playwright smoke
npx playwright test --grep @smoke
```

### 7.2 CI Pipeline 範本（GitHub Actions）

```yaml
name: ci-test-pipeline

on:
  pull_request:
  push:
    branches: [main]

jobs:
  unit-and-integration:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.13"
      - name: Install deps
        run: uv sync
      - name: Run unit/integration tests
        run: uv run ai-dev test -v
      - name: Coverage
        run: uv run ai-dev coverage --source script/

  e2e-smoke:
    runs-on: ubuntu-latest
    needs: unit-and-integration
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
      - name: Install npm deps
        run: npm ci
      - name: Install Playwright browsers
        run: npx playwright install --with-deps
      - name: Run smoke suite
        env:
          BASE_URL: ${{ secrets.STAGING_BASE_URL }}
        run: npx playwright test --grep @smoke
      - name: Upload Playwright report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: playwright-report
          path: playwright-report/
```

### 7.3 Playwright 分群與環境組態範例

```ts
import { defineConfig } from "@playwright/test";

export default defineConfig({
  retries: process.env.CI ? 2 : 0,
  use: {
    baseURL: process.env.BASE_URL ?? "http://127.0.0.1:3000",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
  },
  reporter: [["html"], ["junit", { outputFile: "test-results/junit.xml" }]],
  projects: [
    { name: "smoke", grep: /@smoke/ },
    { name: "regression", grep: /@regression/ },
    { name: "mutation", grep: /@mutation/ },
  ],
});
```

```ts
import { test, expect } from "@playwright/test";

test("@smoke 首頁可開啟", async ({ page }) => {
  await page.goto("/");
  await expect(page).toHaveTitle(/.+/);
});

test("@regression 結帳流程", async ({ page }) => {
  // ...完整旅程
});
```

### 7.4 Skip Ratio Gate 範例（防止測試失效）

當你允許部分測試因環境因素被 skip，建議加上「跳過比例上限」：

```python
from xml.etree import ElementTree as ET

MAX_SKIP_RATIO = 0.15  # 15%

tree = ET.parse("test-results/junit.xml")
root = tree.getroot()

tests = int(root.attrib.get("tests", "0"))
skipped = int(root.attrib.get("skipped", "0"))
ratio = (skipped / tests) if tests else 0.0

print(f"tests={tests}, skipped={skipped}, ratio={ratio:.2%}")
if ratio > MAX_SKIP_RATIO:
    raise SystemExit(f"Skip ratio gate failed: {ratio:.2%} > {MAX_SKIP_RATIO:.2%}")
```

你可以把它放到 CI 的最後一步，作為「是否允許進下一關」的 gate。

### 7.5 E2E 失敗時的排查 Runbook

```bash
# 1) 重跑同一批案例，先確認是否偶發
npx playwright test --grep @smoke

# 2) 開 trace 模式重跑失敗案例
npx playwright test tests/e2e/checkout.spec.ts --trace on

# 3) 開報告檢視錯誤步驟與網路事件
npx playwright show-report
```

建議固定在每個失敗案例輸出：`trace`、`screenshot`、`video`、`console/network log`，並在 bug 單中附上 artifact 連結。

---

## 8. 參考資料

- Test Pyramid（Martin Fowler）
  - https://martinfowler.com/bliki/TestPyramid.html (Accessed: 2026-02-08)
  - https://martinfowler.com/articles/practical-test-pyramid.html (Accessed: 2026-02-08)
- Playwright 官方文件（E2E / traces / reports）
  - https://playwright.dev/docs/intro (Accessed: 2026-02-08)
