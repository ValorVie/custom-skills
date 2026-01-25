# Design: dynamic-profile-loading

## Architecture Overview

此設計文件描述動態 Profile 載入功能的完整架構，包括標準檔案庫、載入流程、安全機制與整合方式。

### 系統層級

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Interface                           │
│  ┌──────────────────┐        ┌──────────────────────────────┐  │
│  │   CLI Commands   │        │       TUI Interface          │  │
│  │  - switch        │        │  - Profile Selector          │  │
│  │  - sync          │        │  - Quick Switch (t key)      │  │
│  │  - status        │        │  - Toast Notifications       │  │
│  └────────┬─────────┘        └──────────┬───────────────────┘  │
│           │                              │                      │
└───────────┼──────────────────────────────┼──────────────────────┘
            │                              │
            └──────────────┬───────────────┘
                           │
           ┌───────────────▼───────────────┐
           │     Profile Activation        │
           │  ┌─────────────────────────┐  │
           │  │  activate_profile()     │  │
           │  │  - load_profile()       │  │
           │  │  - clear_managed()      │  │
           │  │  - copy_standards()     │  │
           │  │  - apply_overrides()    │  │
           │  │  - update_active()      │  │
           │  └───────────┬─────────────┘  │
           └──────────────┼────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│   profiles/   │ │   profiles/   │ │  .standards/  │
│   *.yaml      │ │   standards/  │ │  (目標目錄)   │
│  (定義檔)     │ │  (來源庫)     │ │               │
└───────────────┘ └───────────────┘ └───────────────┘
```

### 資料流

1. **Profile 切換流程**：
   ```
   User → switch(name) → activate_profile(name)
        → load_profile(name)                    # 載入定義（含繼承）
        → clear_managed_standards()             # 清除舊檔案
        → for std in includes:
             src = resolve_standard_source()    # 解析來源
             copy_standard_file(src, dst)       # 複製檔案
        → apply_overrides()                     # 套用覆寫
        → update_active_yaml()                  # 更新狀態
        → return result
   ```

2. **同步流程**：
   ```
   User → sync() → get_active_profile()
        → activate_profile(active)
   ```

---

## Directory Structure

### 完整目錄結構

```
profiles/
├── active.yaml                      # 目前啟用的 Profile 狀態
├── uds.yaml                         # UDS Profile 定義
├── ecc.yaml                         # ECC Profile 定義
├── minimal.yaml                     # Minimal Profile 定義
└── standards/                       # 標準檔案庫
    ├── uds/                         # UDS 專屬標準
    │   ├── commit-message.ai.yaml
    │   ├── traditional-chinese.ai.yaml
    │   ├── test-driven-development.ai.yaml
    │   ├── behavior-driven-development.ai.yaml
    │   ├── acceptance-test-driven-development.ai.yaml
    │   ├── spec-driven-development.ai.yaml
    │   ├── code-review.ai.yaml
    │   ├── checkin-standards.ai.yaml
    │   ├── testing.ai.yaml
    │   ├── git-workflow.ai.yaml
    │   ├── documentation-structure.ai.yaml
    │   ├── documentation-writing-standards.ai.yaml
    │   ├── error-codes.ai.yaml
    │   ├── logging.ai.yaml
    │   ├── versioning.ai.yaml
    │   └── changelog.ai.yaml
    ├── minimal/                     # Minimal 專屬標準
    │   ├── commit-message.ai.yaml   # 與 UDS 相同
    │   ├── checkin-standards.ai.yaml
    │   └── testing.ai.yaml
    ├── ecc/                         # ECC 專屬標準
    │   ├── commit-message.ai.yaml   # ECC 版本（英文類型）
    │   └── code-review.ai.yaml      # ECC 額外標準
    └── shared/                      # 共用標準（預留）
        └── (空，未來使用)

.standards/                          # 目標目錄（動態生成）
├── commit-message.ai.yaml           # ← 從 profiles/standards/{profile}/ 複製
├── testing.ai.yaml                  # ←
├── checkin-standards.ai.yaml        # ←
├── ...                              # ← 其他標準
├── manifest.json                    # (保留，不由 Profile 管理)
└── options/                         # (保留，不由 Profile 管理)
    └── ...
```

### active.yaml 格式

```yaml
# profiles/active.yaml
active: uds                          # 目前啟用的 Profile
managed_files:                       # 由 Profile 系統管理的檔案
  - commit-message.ai.yaml
  - traditional-chinese.ai.yaml
  - test-driven-development.ai.yaml
  - behavior-driven-development.ai.yaml
  - acceptance-test-driven-development.ai.yaml
  - spec-driven-development.ai.yaml
  - code-review.ai.yaml
  - checkin-standards.ai.yaml
  - testing.ai.yaml
  - git-workflow.ai.yaml
  - documentation-structure.ai.yaml
  - documentation-writing-standards.ai.yaml
  - error-codes.ai.yaml
  - logging.ai.yaml
  - versioning.ai.yaml
  - changelog.ai.yaml
last_activated: "2026-01-25T10:30:00+08:00"
```

---

## Core Functions

### activate_profile()

**主要啟用函式**：

```python
def activate_profile(name: str) -> dict:
    """
    啟用指定的 Profile，載入對應的標準檔案到 .standards/

    Args:
        name: Profile 名稱（如 "uds", "ecc", "minimal"）

    Returns:
        dict: 啟用結果
        {
            "success": True,
            "profile": "ecc",
            "copied_files": ["commit-message.ai.yaml", ...],
            "removed_files": ["old-standard.ai.yaml", ...],
            "preserved_files": ["user-custom.ai.yaml", ...],
            "overrides_applied": ["commit-message"],
            "warnings": [],
            "duration_ms": 150
        }

    Raises:
        ValueError: Profile 不存在
        FileNotFoundError: 標準檔案不存在
    """
    start_time = time.time()
    result = {
        "success": False,
        "profile": name,
        "copied_files": [],
        "removed_files": [],
        "preserved_files": [],
        "overrides_applied": [],
        "warnings": [],
    }

    try:
        # 1. 載入 Profile 定義（含繼承處理）
        profile = load_profile(name)
        includes = profile.get('includes', [])

        # 2. 清除舊的 managed 檔案
        removed = clear_managed_standards()
        result["removed_files"] = removed

        # 3. 偵測使用者自訂檔案（不在 managed 但在 .standards/ 中）
        preserved = detect_user_standards()
        result["preserved_files"] = preserved
        if preserved:
            result["warnings"].append(
                f"保留了 {len(preserved)} 個使用者自訂檔案"
            )

        # 4. 複製新 Profile 的標準檔案
        copied = []
        for std_file in includes:
            src = resolve_standard_source(name, std_file, profile)
            dst = get_standards_dir() / std_file
            copy_standard_file(src, dst)
            copied.append(std_file)
        result["copied_files"] = copied

        # 5. 套用 overrides
        if 'overrides' in profile and profile['overrides']:
            applied = apply_overrides(profile['overrides'])
            result["overrides_applied"] = applied

        # 6. 更新 active.yaml
        update_active_yaml(name, copied)

        result["success"] = True

    except Exception as e:
        result["success"] = False
        result["error"] = str(e)
        # 可選：回復到原狀態
        raise

    finally:
        result["duration_ms"] = int((time.time() - start_time) * 1000)

    return result
```

### resolve_standard_source()

**標準檔案來源解析**：

```python
def resolve_standard_source(
    profile_name: str,
    std_file: str,
    profile: dict = None
) -> Path:
    """
    解析標準檔案的來源路徑

    優先順序：
    1. profiles/standards/{profile_name}/{std_file}  (Profile 專屬版本)
    2. 若有繼承，查找父 Profile 的版本
    3. profiles/standards/shared/{std_file}          (共用版本)
    4. raise FileNotFoundError

    Args:
        profile_name: Profile 名稱
        std_file: 標準檔案名稱
        profile: Profile 定義（可選，用於繼承查找）

    Returns:
        Path: 標準檔案的來源路徑
    """
    profiles_dir = get_profiles_dir()

    # 1. 檢查 Profile 專屬版本
    profile_specific = profiles_dir / 'standards' / profile_name / std_file
    if profile_specific.exists():
        return profile_specific

    # 2. 若有繼承，檢查父 Profile
    if profile and 'inherits' in profile and profile['inherits']:
        parent_name = profile['inherits']
        parent_specific = profiles_dir / 'standards' / parent_name / std_file
        if parent_specific.exists():
            return parent_specific

    # 3. 檢查共用版本
    shared = profiles_dir / 'standards' / 'shared' / std_file
    if shared.exists():
        return shared

    # 4. 找不到
    raise FileNotFoundError(
        f"Standard file '{std_file}' not found for profile '{profile_name}'"
    )
```

### clear_managed_standards()

**清除已管理的標準**：

```python
def clear_managed_standards() -> list[str]:
    """
    清除 .standards/ 中由 Profile 系統管理的檔案

    只刪除 active.yaml 的 managed_files 中列出的檔案，
    保護使用者自訂的標準。

    Returns:
        list[str]: 已刪除的檔案列表
    """
    active_path = get_active_profile_path()
    if not active_path.exists():
        return []

    active = load_yaml(active_path)
    managed_files = active.get('managed_files', [])

    removed = []
    standards_dir = get_standards_dir()

    for filename in managed_files:
        file_path = standards_dir / filename
        if file_path.exists():
            file_path.unlink()
            removed.append(filename)

    return removed
```

### apply_overrides()

**套用覆寫設定**：

```python
def apply_overrides(overrides: dict) -> list[str]:
    """
    套用 Profile 的 overrides 設定到標準檔案

    Args:
        overrides: 覆寫設定
            格式: {"standard-name": {"key": "value", ...}, ...}
            例如: {"commit-message": {"language": "en"}}

    Returns:
        list[str]: 已套用覆寫的標準名稱
    """
    applied = []
    standards_dir = get_standards_dir()

    for std_name, settings in overrides.items():
        # 嘗試多種副檔名
        for ext in ['.ai.yaml', '.yaml', '.md']:
            std_path = standards_dir / f"{std_name}{ext}"
            if std_path.exists():
                try:
                    content = load_yaml(std_path)
                    merged = deep_merge(content, settings)
                    save_yaml(std_path, merged)
                    applied.append(std_name)
                except Exception as e:
                    console.print(f"[yellow]警告: 無法套用 {std_name} 的覆寫: {e}[/yellow]")
                break

    return applied


def deep_merge(base: dict, override: dict) -> dict:
    """深度合併兩個字典，override 優先"""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result
```

---

## CLI Command Updates

### switch 命令

```python
@app.command()
def switch(
    profile_name: str = typer.Argument(..., help="要切換的 Profile 名稱")
):
    """切換到指定的 Standards Profile（會實際載入對應的標準檔案）"""
    if not is_standards_initialized():
        console.print("[red]錯誤: 專案尚未初始化標準體系[/red]")
        raise typer.Exit(1)

    # 驗證 Profile 存在
    available = list_profiles()
    if profile_name not in available:
        console.print(f"[red]錯誤: Profile '{profile_name}' 不存在[/red]")
        console.print(f"可用的 Profiles: {', '.join(available)}")
        raise typer.Exit(1)

    # 啟用 Profile
    console.print(f"正在切換到 [cyan]{profile_name}[/cyan] Profile...")

    try:
        result = activate_profile(profile_name)

        if result["success"]:
            console.print(f"[green]✓ 成功切換到 {profile_name}[/green]")
            console.print(f"  複製了 {len(result['copied_files'])} 個標準檔案")
            if result["removed_files"]:
                console.print(f"  移除了 {len(result['removed_files'])} 個舊檔案")
            if result["preserved_files"]:
                console.print(f"  保留了 {len(result['preserved_files'])} 個使用者自訂檔案")
            if result["overrides_applied"]:
                console.print(f"  套用了 {len(result['overrides_applied'])} 個覆寫設定")
            console.print(f"  耗時 {result['duration_ms']} ms")
        else:
            console.print(f"[red]✗ 切換失敗: {result.get('error', '未知錯誤')}[/red]")
            raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]✗ 切換失敗: {e}[/red]")
        raise typer.Exit(1)
```

### sync 命令

```python
@app.command()
def sync():
    """重新同步當前 Profile 的標準檔案（用於 UDS 更新後）"""
    if not is_standards_initialized():
        console.print("[red]錯誤: 專案尚未初始化標準體系[/red]")
        raise typer.Exit(1)

    active = get_active_profile()
    if not active:
        console.print("[yellow]警告: 沒有啟用的 Profile[/yellow]")
        console.print("請先執行 'ai-dev standards switch <profile>'")
        raise typer.Exit(1)

    console.print(f"正在重新同步 [cyan]{active}[/cyan] Profile...")

    try:
        result = activate_profile(active)

        if result["success"]:
            console.print(f"[green]✓ 同步完成[/green]")
            console.print(f"  更新了 {len(result['copied_files'])} 個標準檔案")
        else:
            console.print(f"[red]✗ 同步失敗: {result.get('error')}[/red]")
            raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]✗ 同步失敗: {e}[/red]")
        raise typer.Exit(1)
```

---

## Safety Mechanisms

### 使用者自訂標準保護

```python
def detect_user_standards() -> list[str]:
    """
    偵測 .standards/ 中的使用者自訂標準（非 managed）

    Returns:
        list[str]: 使用者自訂的標準檔案列表
    """
    standards_dir = get_standards_dir()
    if not standards_dir.exists():
        return []

    active = load_yaml(get_active_profile_path())
    managed = set(active.get('managed_files', []))

    # 排除的檔案（非標準檔案）
    excluded = {'manifest.json', 'active-profile.yaml'}

    user_standards = []
    for file_path in standards_dir.glob('*.ai.yaml'):
        filename = file_path.name
        if filename not in managed and filename not in excluded:
            user_standards.append(filename)

    # 也檢查 .md 檔案
    for file_path in standards_dir.glob('*.md'):
        filename = file_path.name
        if filename not in managed and filename not in excluded:
            user_standards.append(filename)

    return user_standards
```

### 檔案追蹤更新

```python
def update_active_yaml(profile_name: str, managed_files: list[str]) -> None:
    """
    更新 active.yaml

    Args:
        profile_name: 啟用的 Profile 名稱
        managed_files: 由 Profile 管理的檔案列表
    """
    active_path = get_active_profile_path()

    # 讀取現有內容或建立新的
    if active_path.exists():
        active = load_yaml(active_path)
    else:
        active = {}

    # 更新欄位
    active['active'] = profile_name
    active['managed_files'] = sorted(managed_files)
    active['last_activated'] = datetime.now().isoformat()

    # 寫回檔案
    save_yaml(active_path, active)
```

---

## Profile-Specific Differences

### 各 Profile 的差異比較

| Profile | 標準數量 | commit-message | 特色 |
|---------|----------|----------------|------|
| **minimal** | 3-5 | 繁體中文類型 | 最小化，適合輕量專案 |
| **uds** | 10+ | 繁體中文類型 | 完整，包含 SDD/TDD/BDD |
| **ecc** | 5-7 | **英文類型** | TypeScript/React 導向 |

### ECC commit-message.ai.yaml 差異

```yaml
# profiles/standards/uds/commit-message.ai.yaml (UDS 版本)
types:
  - 功能  # feat
  - 修正  # fix
  - 文件  # docs
  - 樣式  # style
  - 重構  # refactor
  - 測試  # test
  - 雜項  # chore
  - 效能  # perf
  - 整合  # ci

# profiles/standards/ecc/commit-message.ai.yaml (ECC 版本)
types:
  - feat
  - fix
  - docs
  - style
  - refactor
  - test
  - chore
  - perf
  - ci
```

---

## Error Handling

### 錯誤類型與處理

| 錯誤類型 | 情境 | 處理方式 |
|---------|------|----------|
| **ProfileNotFoundError** | Profile 定義檔不存在 | 顯示錯誤 + 列出可用 Profiles |
| **StandardFileNotFoundError** | 標準檔案不存在 | 顯示錯誤 + 建議執行 sync |
| **PermissionError** | 無法寫入 .standards/ | 顯示錯誤 + 檢查權限建議 |
| **YAMLError** | YAML 格式錯誤 | 顯示錯誤 + 指出問題檔案 |

### 錯誤訊息範例

```bash
# ProfileNotFoundError
$ ai-dev standards switch custom
錯誤: Profile 'custom' 不存在
可用的 Profiles: ecc, minimal, uds

# StandardFileNotFoundError
$ ai-dev standards switch uds
錯誤: 找不到標準檔案 'test-driven-development.ai.yaml'
建議: 請執行 'ai-dev standards sync' 重新同步標準檔案庫
```

---

## Performance Considerations

### 效能特徵

- **複製效能**：標準檔案都是文字檔（< 100 KB），複製速度極快
- **預期耗時**：10-20 個檔案的切換約 50-200 ms
- **無需快取**：檔案操作是 I/O bound，不需要記憶體快取

### 優化建議

- 使用 `shutil.copy2()` 保留檔案元資料
- 批次處理檔案操作，減少系統呼叫
- 僅在真正需要時才套用 overrides

---

## Future Enhancements

### Phase 4: 標準檔案自動更新

- 從上游 repo 自動下載最新標準
- `ai-dev standards update` 命令
- 版本追蹤與相容性檢查

### Phase 5: 自訂 Profile

- `ai-dev standards create my-profile` 建立自訂 Profile
- Profile 匯出/匯入功能
- Profile 分享機制

---

## Summary

此設計實現了完整的動態 Profile 載入功能：

- **檔案複製機制**：簡單可靠，跨平台相容
- **安全保護**：使用者自訂標準不會被覆蓋
- **差異化體驗**：各 Profile 有明顯不同的標準內容
- **可追蹤**：`managed_files` 記錄由系統管理的檔案
- **可回復**：`sync` 命令可重新同步

此設計完成了 Profile 系統的最後一塊拼圖，讓 Profile 切換真正名副其實。
