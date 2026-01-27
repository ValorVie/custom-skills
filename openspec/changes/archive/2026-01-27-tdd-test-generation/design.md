## Context

已完成 `tdd-test-execution` 和 `tdd-coverage-python` 兩個子提案，建立了 TestRunner 架構和「腳本只負責執行，AI 負責分析」的架構原則。現在需要完成最後一個子提案 `tdd-test-generation`，從 OpenSpec specs 生成完整測試程式碼。

## Goals / Non-Goals

**Goals:**
- 建立 `/custom-skills-derive-tests` Claude Code 命令
- 建立 `ai-dev derive-tests` CLI 命令
- **腳本只負責讀取 specs 檔案，AI 負責理解和生成測試**

**Non-Goals:**
- ~~在腳本中解析 WHEN/THEN 語法~~（改由 AI 理解）
- ~~在腳本中生成測試程式碼~~（改由 AI 生成）
- 其他語言支援（僅 Python/pytest）
- 複雜的 mock 自動生成

## Architecture Principle | 架構原則

```
┌─────────────────────────────────────────────────────────────┐
│                 Claude Code Command                          │
│  /custom-skills-derive-tests                                 │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ Prompt 定義：                                            ││
│  │ 1. 執行 CLI 讀取 specs 內容                              ││
│  │ 2. AI 理解 WHEN/THEN 場景語義                           ││
│  │ 3. AI 讀取專案程式碼結構                                ││
│  │ 4. AI 生成完整測試程式碼並寫入檔案                      ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 CLI 命令 (ai-dev derive-tests)              │
│  - 找到指定路徑的 specs 檔案                                │
│  - 讀取並輸出 specs 內容                                    │
│  - 不做解析或生成（交給 AI）                                │
└─────────────────────────────────────────────────────────────┘
```

**原則**：
- 腳本只負責「讀取」specs 檔案
- 語義理解和程式碼生成交給 AI（更有彈性、能理解上下文）

## Decisions

### 1. CLI 命令只讀取 specs

**選擇**：CLI 只負責找到並輸出 specs 內容，不做任何解析。

```python
# script/commands/derive_tests.py
@app.command("derive-tests")
def derive_tests(path: str = typer.Argument(...)):
    """讀取 specs 檔案內容。"""
    spec_files = find_spec_files(path)
    for spec_file in spec_files:
        content = spec_file.read_text()
        console.print(f"--- {spec_file} ---")
        console.print(content)
```

**理由**：
- 與 test-execution、coverage-python 保持一致架構
- AI 能更好地理解語義和上下文
- 不需要寫死解析邏輯

### 2. Spec 檔案搜尋邏輯

**選擇**：支援目錄和單一檔案輸入。

```python
def find_spec_files(path: str) -> list[Path]:
    p = Path(path)
    if p.is_file():
        return [p]
    if p.is_dir():
        return list(p.glob("**/*.md"))
    return []
```

**理由**：
- 靈活性：可指定單一 spec 或整個目錄
- 簡單：只用 glob 不做複雜過濾

### 3. Claude Code 命令負責生成

**選擇**：在 prompt 中定義 AI 生成流程。

```markdown
### Step 1: 讀取 specs
執行 `ai-dev derive-tests <path>` 取得 specs 內容

### Step 2: 理解場景
分析 WHEN/THEN 場景的業務語義

### Step 3: 讀取專案程式碼
找到被測函數/類別的位置和簽名

### Step 4: 生成測試
根據場景生成完整的 pytest 測試程式碼

### Step 5: 寫入檔案
將測試寫入適當的位置（如 tests/ 目錄）
```

**理由**：
- AI 能理解場景語義，不是單純的文字替換
- AI 能讀取專案程式碼，生成正確的 import 和呼叫
- 易於調整生成風格

### 4. 測試檔案命名

**選擇**：由 AI 根據專案慣例決定。

**理由**：
- 不同專案有不同的測試檔案組織方式
- AI 可以參考現有測試檔案的結構

## Risks / Trade-offs

**[風險] specs 路徑不存在**
→ 緩解：CLI 檢查路徑存在，不存在時顯示錯誤訊息

**[風險] 生成的測試需要微調**
→ 緩解：這是預期行為，AI 生成的測試作為起點，開發者可微調

**[取捨] 不在腳本中解析 specs**
→ 理由：AI 語義理解比正規表達式更準確，能處理各種格式變體
