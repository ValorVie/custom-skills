# Design: implement-profile-system

## Architecture Overview

此設計文件描述 Standards Profile 系統的完整架構，包括 profile 定義格式、載入邏輯、繼承機制與 CLI/TUI 整合。

### 系統層級

```
┌─────────────────────────────────────────────────────┐
│                   User Interface                    │
│  ┌──────────────────┐  ┌──────────────────────────┐ │
│  │   CLI Commands   │  │      TUI Interface       │ │
│  │  - list          │  │  - Profile Selector      │ │
│  │  - show          │  │  - Quick Switch (t key)  │ │
│  │  - switch        │  │                          │ │
│  │  - status        │  │                          │ │
│  └────────┬─────────┘  └──────────┬───────────────┘ │
│           │                       │                  │
└───────────┼───────────────────────┼──────────────────┘
            │                       │
            └───────────┬───────────┘
                        │
        ┌───────────────▼──────────────────┐
        │       Profile Management         │
        │  ┌────────────────────────────┐  │
        │  │  list_profiles()           │  │
        │  │  load_profile(name)        │  │
        │  │  merge_profiles(p, c)      │  │
        │  │  get_active_profile()      │  │
        │  └────────────┬───────────────┘  │
        │               │                   │
        └───────────────┼───────────────────┘
                        │
        ┌───────────────▼──────────────────┐
        │     Profile Storage Layer        │
        │  ┌────────────────────────────┐  │
        │  │  profiles/ (專案根目錄)   │  │
        │  │    uds.yaml                │  │
        │  │    ecc.yaml                │  │
        │  │    minimal.yaml            │  │
        │  │    active.yaml             │  │
        │  └────────────────────────────┘  │
        └──────────────────────────────────┘
```

### 資料流

1. **Profile 列表載入**：
   ```
   CLI/TUI → list_profiles() → 掃描 profiles/*.yaml → 返回名稱列表
   ```

2. **Profile 詳細資訊載入**：
   ```
   CLI/TUI → load_profile(name) → 讀取 {name}.yaml
           → 檢查 inherits → 遞迴載入父 profile
           → merge_profiles(parent, child) → 返回合併後的 profile
   ```

3. **Profile 切換**：
   ```
   CLI/TUI → switch(name) → 驗證 profile 存在
           → 更新 profiles/active.yaml 的 active 欄位
           → 顯示成功訊息
   ```

---

## Profile Definition Format

### 完整欄位說明

```yaml
# Profile 定義檔案格式 (v1.0.0)

# === 必要欄位 ===
name: "profile-id"                 # Profile 識別碼（唯一，與檔名一致）
display_name: "Human Readable Name" # 顯示名稱（供 UI 使用）
description: "詳細描述此 profile 的用途與特色"
version: "1.0.0"                   # Profile 定義格式版本（語意化版本）

# === 核心欄位 ===
includes:                          # 包含的標準檔案清單
  - "standard-file-1.ai.yaml"
  - "standard-file-2.ai.yaml"
  - "standard-file-3.md"

# === 選用欄位 ===
inherits: "parent-profile-name"    # 繼承的父 profile（單繼承）

overrides:                         # 覆寫設定（YAML 結構）
  standard-file-key:
    setting-key: value
  another-standard:
    nested:
      setting: value

# === 元資料欄位（選用）===
author: "Profile 作者"
created: "2026-01-25"
updated: "2026-01-25"
tags:
  - "tag1"
  - "tag2"
```

### 欄位驗證規則

| 欄位 | 必要 | 類型 | 驗證規則 |
|------|------|------|----------|
| `name` | ✓ | string | 必須與檔名一致（去掉 `.yaml`），僅允許 `[a-z0-9-]` |
| `display_name` | ✓ | string | 非空字串，長度 1-100 |
| `description` | ✓ | string | 非空字串，長度 10-500 |
| `version` | ✓ | string | 語意化版本格式（如 `1.0.0`） |
| `includes` | ✓ | list[string] | 至少包含 1 個標準檔案，所有檔案必須存在於 `.standards/` |
| `inherits` | ✗ | string \| null | 若指定，必須是有效的 profile 名稱（不可循環繼承） |
| `overrides` | ✗ | dict | 任意 YAML 結構，用於覆寫標準設定 |

---

## Profile Loading Logic

### load_profile() 函式

**目的**：載入並解析 profile 定義檔案，處理繼承關係。

**演算法**：

```python
def load_profile(name: str, _visited: set = None) -> dict:
    """
    載入並解析 profile 定義

    Args:
        name: Profile 名稱（不含 .yaml 副檔名）
        _visited: 內部參數，追蹤已訪問的 profiles（防止循環繼承）

    Returns:
        解析並合併後的 profile 字典

    Raises:
        ValueError: Profile 不存在或循環繼承
    """
    # 初始化 visited 集合（首次呼叫時）
    if _visited is None:
        _visited = set()

    # 檢測循環繼承
    if name in _visited:
        raise ValueError(f"Circular inheritance detected: {' → '.join(_visited)} → {name}")

    _visited.add(name)

    # 讀取 profile 檔案
    profile_path = get_profiles_dir() / f"{name}.yaml"
    if not profile_path.exists():
        raise ValueError(f"Profile '{name}' not found at {profile_path}")

    profile = load_yaml(profile_path)

    # 驗證必要欄位
    required_fields = ['name', 'display_name', 'description', 'version', 'includes']
    for field in required_fields:
        if field not in profile:
            raise ValueError(f"Profile '{name}' missing required field: {field}")

    # 處理繼承
    if 'inherits' in profile and profile['inherits']:
        parent_name = profile['inherits']
        parent = load_profile(parent_name, _visited.copy())  # 複製 visited 避免污染
        profile = merge_profiles(parent, profile)

    return profile
```

**複雜度分析**：
- 時間複雜度：O(n)，其中 n 為繼承鏈深度
- 空間複雜度：O(n)，遞迴呼叫堆疊與 visited 集合

### merge_profiles() 函式

**目的**：合併父子 profile，處理 includes 與 overrides。

**演算法**：

```python
def merge_profiles(parent: dict, child: dict) -> dict:
    """
    合併父子 profile

    合併規則：
    1. includes: 父 + 子（追加，不去重）
    2. overrides: 子覆蓋父（深度合併）
    3. 其他欄位：子覆蓋父

    Args:
        parent: 父 profile
        child: 子 profile

    Returns:
        合併後的 profile
    """
    merged = {}

    # 合併 includes（追加）
    merged['includes'] = parent.get('includes', []) + child.get('includes', [])

    # 合併 overrides（深度合併）
    merged['overrides'] = deep_merge(
        parent.get('overrides', {}),
        child.get('overrides', {})
    )

    # 其他欄位：子覆蓋父
    for key in ['name', 'display_name', 'description', 'version', 'inherits']:
        merged[key] = child.get(key, parent.get(key))

    # 保留元資料（若存在）
    for key in ['author', 'created', 'updated', 'tags']:
        if key in child:
            merged[key] = child[key]
        elif key in parent:
            merged[key] = parent[key]

    return merged

def deep_merge(dict1: dict, dict2: dict) -> dict:
    """深度合併兩個字典，dict2 優先"""
    result = dict1.copy()
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result
```

**範例**：

```yaml
# minimal.yaml
includes:
  - checkin-standards.ai.yaml
  - testing.ai.yaml

# ecc.yaml
inherits: minimal
includes:
  - code-review.ai.yaml
overrides:
  testing:
    coverage-threshold: 80
```

合併後的 `ecc` profile：

```yaml
includes:
  - checkin-standards.ai.yaml  # from minimal
  - testing.ai.yaml             # from minimal
  - code-review.ai.yaml         # from ecc
overrides:
  testing:
    coverage-threshold: 80
```

---

## CLI Command Design

### list 命令

**功能**：列出所有可用的 profiles。

**實作**：

```python
@app.command(name="list")
def list_cmd():
    """列出所有可用的 profiles"""
    if not is_standards_initialized():
        console.print("[yellow]⚠️  專案尚未初始化標準體系[/yellow]")
        console.print("[dim]請執行 'ai-dev project init' 初始化專案[/dim]")
        return

    profiles = list_profiles()
    if not profiles:
        console.print("[yellow]無可用的 profiles[/yellow]")
        return

    active = get_active_profile()

    table = Table(title="可用的 Standards Profiles")  # 移除「臨時清單模式」
    table.add_column("Profile", style="cyan")
    table.add_column("Display Name", style="white")
    table.add_column("狀態", style="green")

    for name in sorted(profiles):
        try:
            profile = load_profile(name)
            display_name = profile.get('display_name', name)
        except Exception:
            display_name = name  # 載入失敗時使用 name

        status_mark = "✓ 啟用中" if name == active else ""
        table.add_row(name, display_name, status_mark)

    console.print(table)
```

**輸出範例**：

```
可用的 Standards Profiles
┌──────────┬───────────────────────────┬──────────┐
│ Profile  │ Display Name              │ 狀態     │
├──────────┼───────────────────────────┼──────────┤
│ ecc      │ Everything Claude Code    │          │
│ minimal  │ Minimal Standards         │          │
│ uds      │ Universal Dev Standards   │ ✓ 啟用中 │
└──────────┴───────────────────────────┴──────────┘
```

### show 命令

**功能**：顯示指定 profile 的詳細內容。

**實作**：

```python
@app.command()
def show(profile_name: str = typer.Argument(..., help="要顯示的 profile 名稱")):
    """顯示指定 profile 的詳細內容"""
    try:
        profile = load_profile(profile_name)
    except ValueError as e:
        console.print(f"[red]錯誤: {e}[/red]")
        console.print(f"可用的 profiles: {', '.join(list_profiles())}")
        raise typer.Exit(1)

    active = get_active_profile()
    is_active = "[green](目前啟用)[/green]" if profile_name == active else ""

    # 顯示基本資訊
    console.print(f"[bold cyan]{profile['display_name']}[/bold cyan] {is_active}")
    console.print(f"[dim]ID: {profile['name']}[/dim]")
    console.print(f"\n{profile['description']}")
    console.print(f"\n[dim]Version: {profile.get('version', 'N/A')}[/dim]")

    # 顯示繼承關係
    if profile.get('inherits'):
        console.print(f"\n[yellow]繼承自:[/yellow] {profile['inherits']}")

    # 顯示包含的標準
    console.print(f"\n[bold]包含的標準 ({len(profile.get('includes', []))}):[/bold]")
    for std in profile.get('includes', []):
        console.print(f"  • {std}")

    # 顯示覆寫設定
    if profile.get('overrides'):
        console.print(f"\n[bold]覆寫設定:[/bold]")
        console.print_json(data=profile['overrides'])
```

**輸出範例**：

```
Everything Claude Code
ID: ecc

ECC 標準體系，採用 TypeScript/React 導向的實戰開發標準

Version: 1.0.0

繼承自: minimal

包含的標準 (5):
  • checkin-standards.ai.yaml
  • testing.ai.yaml
  • code-review.ai.yaml
  • test-driven-development.ai.yaml

覆寫設定:
{
  "testing": {
    "coverage-threshold": 80
  }
}
```

---

## TUI Integration

### Profile Selector 更新

TUI 的 Profile 選單將自動使用更新後的 `list_profiles()` 函式，無需修改程式碼。

**原理**：

```python
# script/tui/app.py (現有程式碼)
def update_standards_profile_display(self) -> None:
    """更新 Standards Profile 區塊顯示"""
    if not is_standards_initialized():
        # 顯示未初始化提示
        return

    profiles = list_profiles()  # ← 已更新為從 profiles/*.yaml 讀取
    active = get_active_profile()

    # 更新 Select widget
    profile_select = self.query_one("#profile-select", Select)
    profile_select.set_options([(p, p) for p in profiles])
    profile_select.value = active
```

**驗證**：
- [ ] Profile 選單顯示三個 profiles（uds, ecc, minimal）
- [ ] 下拉選單切換功能正常
- [ ] 快捷鍵 `t` 循環切換正常

---

## Data Validation

### Profile 定義檔案驗證

建議實作一個驗證函式，在載入 profile 時檢查格式正確性：

```python
def validate_profile(profile: dict, profile_path: Path) -> list[str]:
    """
    驗證 profile 定義檔案

    Returns:
        錯誤訊息列表（空列表表示無錯誤）
    """
    errors = []

    # 檢查必要欄位
    required_fields = ['name', 'display_name', 'description', 'version', 'includes']
    for field in required_fields:
        if field not in profile:
            errors.append(f"Missing required field: {field}")

    # 檢查 name 與檔名一致
    if 'name' in profile and profile['name'] != profile_path.stem:
        errors.append(f"Profile name '{profile['name']}' does not match filename '{profile_path.stem}'")

    # 檢查 version 格式
    if 'version' in profile:
        import re
        if not re.match(r'^\d+\.\d+\.\d+$', profile['version']):
            errors.append(f"Invalid version format: {profile['version']} (expected: x.y.z)")

    # 檢查 includes 檔案存在性
    if 'includes' in profile:
        standards_dir = get_standards_dir()
        for std_file in profile['includes']:
            if not (standards_dir / std_file).exists():
                errors.append(f"Included standard file not found: {std_file}")

    # 檢查 inherits 有效性
    if 'inherits' in profile and profile['inherits']:
        parent_path = get_profiles_dir() / f"{profile['inherits']}.yaml"
        if not parent_path.exists():
            errors.append(f"Parent profile not found: {profile['inherits']}")

    return errors
```

**使用時機**：
- 在 `load_profile()` 中呼叫驗證（開發模式）
- 在 CI/CD 中執行驗證（防止錯誤的 profile 定義被合併）

---

## Error Handling

### 錯誤類型與處理

| 錯誤類型 | 情境 | 處理方式 |
|---------|------|----------|
| **ProfileNotFoundError** | Profile 檔案不存在 | 顯示錯誤訊息 + 列出可用 profiles |
| **CircularInheritanceError** | 循環繼承（A → B → A） | 拋出錯誤，顯示繼承鏈 |
| **InvalidProfileError** | Profile 定義格式錯誤 | 顯示驗證錯誤訊息 |
| **MissingStandardFileError** | `includes` 中的檔案不存在 | 警告訊息，跳過該檔案 |

### 錯誤訊息範例

```bash
# ProfileNotFoundError
$ ai-dev standards show invalid
錯誤: Profile 'invalid' not found
可用的 profiles: ecc, minimal, uds

# CircularInheritanceError
$ ai-dev standards show circular
錯誤: Circular inheritance detected: minimal → ecc → minimal

# InvalidProfileError
$ ai-dev standards show malformed
錯誤: Invalid profile definition for 'malformed':
  - Missing required field: version
  - Included standard file not found: non-existent.ai.yaml
```

---

## Performance Considerations

### Profile 載入效能

- **快取機制（可選）**：實作簡單的記憶體快取，避免重複載入相同 profile
- **延遲載入**：`list` 命令不呼叫 `load_profile()`，僅掃描檔名（快速）
- **並行載入（可選）**：若未來支援大量 profiles，可考慮並行載入

```python
# 簡單快取範例
_profile_cache = {}

def load_profile_cached(name: str) -> dict:
    """載入 profile（含快取）"""
    if name not in _profile_cache:
        _profile_cache[name] = load_profile(name)
    return _profile_cache[name]

def invalidate_cache():
    """清除快取（在 switch 後呼叫）"""
    _profile_cache.clear()
```

---

## Future Enhancements

此設計為未來擴展預留空間：

### Phase 3: 動態標準載入

- **標準檔案複製**：切換 profile 時，實際複製對應的標準檔案到 `.standards/`
- **備份機制**：切換前備份當前標準，支援回復
- **來源管理**：定義標準檔案的來源（從哪個 repo、哪個分支）

### Phase 4: 自訂 Profile

- **Profile 建立 CLI**：`ai-dev standards create my-profile`
- **Profile 編輯 UI**：TUI 中提供 Profile 編輯介面
- **Profile 匯出/匯入**：支援分享自訂 profiles

### Phase 5: Profile 版本控制

- **Profile 升級**：自動偵測 profile 定義格式版本，提示升級
- **相容性檢查**：確保 profile 與專案版本相容

---

## Testing Strategy

### 單元測試（建議）

```python
# tests/test_profile_loading.py

def test_load_profile_uds():
    """測試載入 uds profile"""
    profile = load_profile("uds")
    assert profile['name'] == "uds"
    assert 'includes' in profile
    assert len(profile['includes']) > 0

def test_load_profile_with_inheritance():
    """測試載入含繼承的 profile"""
    profile = load_profile("ecc")
    assert profile['inherits'] == "minimal"
    # 驗證 includes 包含 minimal 的所有項目
    minimal_profile = load_profile("minimal")
    for std in minimal_profile['includes']:
        assert std in profile['includes']

def test_circular_inheritance_detection():
    """測試循環繼承檢測"""
    # 需要建立測試用的循環繼承 profiles
    with pytest.raises(ValueError, match="Circular inheritance"):
        load_profile("circular-a")

def test_merge_profiles():
    """測試 profile 合併邏輯"""
    parent = {
        'includes': ['a.yaml', 'b.yaml'],
        'overrides': {'setting1': 'value1'}
    }
    child = {
        'includes': ['c.yaml'],
        'overrides': {'setting2': 'value2'}
    }
    merged = merge_profiles(parent, child)
    assert len(merged['includes']) == 3
    assert merged['overrides']['setting1'] == 'value1'
    assert merged['overrides']['setting2'] == 'value2'
```

### 手動測試清單

詳見 `tasks.md` Phase 6。

---

## Summary

此設計提供了一個簡潔但可擴展的 Profile 系統架構：

- **清晰的定義格式**：YAML 格式，易於理解與編輯
- **靈活的繼承機制**：支援單繼承與覆寫
- **穩健的載入邏輯**：處理循環繼承、檔案缺失等錯誤
- **友善的 CLI/TUI**：提供完整的 Profile 管理介面
- **為未來預留空間**：可輕鬆擴展至動態載入、自訂 Profiles 等功能

此設計符合「簡單優先、複雜度按需添加」的原則，為 Phase 2 提供了清晰的實作指引。
