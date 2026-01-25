# Design: refactor-profile-overlap-detection

## Architecture Overview

此設計描述「基於重疊檢測的 Profile 切換」架構，取代原本的「複製檔案」方式。

### 系統層級

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Interface                           │
│  ┌──────────────────┐        ┌──────────────────────────────┐  │
│  │   CLI Commands   │        │       TUI Interface          │  │
│  │  - switch        │        │  - Profile Selector          │  │
│  │  - show          │        │  - Quick Switch (t key)      │  │
│  │  - list          │        │                              │  │
│  └────────┬─────────┘        └──────────┬───────────────────┘  │
│           │                              │                      │
└───────────┼──────────────────────────────┼──────────────────────┘
            │                              │
            └──────────────┬───────────────┘
                           │
           ┌───────────────▼───────────────┐
           │     Profile Switch Engine     │
           │  ┌─────────────────────────┐  │
           │  │  switch_profile()       │  │
           │  │  - load_overlaps()      │  │
           │  │  - compute_disabled()   │  │
           │  │  - update_disabled()    │  │
           │  │  - update_active()      │  │
           │  └───────────┬─────────────┘  │
           └──────────────┼────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│   profiles/   │ │   profiles/   │ │  .claude/     │
│   *.yaml      │ │   overlaps.   │ │  disabled.    │
│  (定義檔)     │ │   yaml        │ │  yaml         │
└───────────────┘ └───────────────┘ └───────────────┘
```

### 資料流

1. **Profile 切換流程**：
   ```
   User → switch(profile) → load_overlaps()
        → load_profile(profile)
        → compute_disabled_items(overlaps, profile)
        → update_disabled_yaml()
        → update_active_profile()
        → return result
   ```

2. **重疊檢測流程**（與 upstream-sync 整合）：
   ```
   /upstream-compare → analyze_overlaps()
        → compare with existing overlaps.yaml
        → suggest_new_overlaps()
        → output overlap_analysis
   ```

---

## Overlap Definition Format

### overlaps.yaml 完整格式

```yaml
# profiles/overlaps.yaml
version: "1.0.0"
description: "定義各體系間的功能重疊項目"

# 資源類型定義
resource_types:
  - skills      # skills/*/SKILL.md
  - standards   # .standards/*.ai.yaml
  - commands    # commands/claude/*.md
  - agents      # agents/claude/*.md
  - hooks       # hooks/

# 重疊群組定義
groups:
  # 群組 1: TDD 工作流
  tdd-workflow:
    description: "TDD 工作流功能"
    mutual_exclusive: true  # 同時只能啟用一個體系

    uds:
      skills:
        - testing-guide
      standards:
        - testing.ai.yaml
        - test-driven-development.ai.yaml

    ecc:
      skills:
        - tdd-workflow
      commands:
        - tdd

    minimal:
      skills:
        - testing-guide
      standards:
        - testing.ai.yaml

  # 群組 2: 提交訊息規範
  commit-message:
    description: "提交訊息規範"
    mutual_exclusive: true

    uds:
      skills:
        - commit-standards
      standards:
        - commit-message.ai.yaml
        - traditional-chinese.ai.yaml
        - options/traditional-chinese.ai.yaml

    ecc:
      skills:
        - commit-standards
      # 無額外 standards，使用英文類型

    minimal:
      skills:
        - commit-standards
      standards:
        - commit-message.ai.yaml

  # 群組 3: Code Review
  code-review:
    description: "Code Review 功能"
    mutual_exclusive: true

    uds:
      skills:
        - code-review-assistant
        - checkin-assistant
      standards:
        - code-review.ai.yaml
        - checkin-standards.ai.yaml

    ecc:
      skills:
        - code-review-assistant
      agents:
        - code-reviewer
        - security-reviewer

    minimal:
      skills:
        - code-review-assistant
      standards:
        - checkin-standards.ai.yaml

  # 群組 4: 文件規範
  documentation:
    description: "文件撰寫規範"
    mutual_exclusive: true

    uds:
      skills:
        - documentation-guide
        - doc-updater
      standards:
        - documentation-structure.ai.yaml
        - documentation-writing-standards.ai.yaml

    ecc:
      skills:
        - doc-updater
      agents:
        - doc-updater

    minimal: {}  # minimal 不包含文件規範

# 非重疊但體系特有的項目
exclusive:
  uds:
    description: "UDS 獨有功能（與 ECC 無對應）"
    skills:
      - methodology-system
      - atdd-assistant
      - forward-derivation
      - spec-driven-dev
      - bdd-assistant
    standards:
      - acceptance-test-driven-development.ai.yaml
      - behavior-driven-development.ai.yaml
      - spec-driven-development.ai.yaml
      - forward-derivation-standards.ai.yaml
      - refactoring-standards.ai.yaml
      - reverse-engineering-standards.ai.yaml

  ecc:
    description: "ECC 獨有功能（與 UDS 無對應）"
    skills:
      - eval-harness
      - strategic-compact
      - continuous-learning
    commands:
      - build-fix
      - checkpoint
      - e2e
      - eval
      - learn
      - test-coverage
    agents:
      - build-error-resolver
      - e2e-runner
    hooks:
      - memory-persistence
      - strategic-compact
```

### 欄位說明

| 欄位 | 必要 | 類型 | 說明 |
|------|------|------|------|
| `version` | ✓ | string | 格式版本（語意化版本） |
| `groups` | ✓ | dict | 重疊群組定義 |
| `groups.<name>.mutual_exclusive` | ✗ | bool | 是否互斥（預設 true） |
| `groups.<name>.<system>` | ✓ | dict | 各體系的項目列表 |
| `exclusive` | ✗ | dict | 體系獨有項目（非重疊） |

---

## Profile Definition Format

### 新格式

```yaml
# profiles/uds.yaml
name: uds
display_name: "Universal Dev Standards"
description: "完整的 UDS 標準體系，包含繁體中文提交訊息與完整 SDD/TDD/BDD 整合"
version: "1.0.0"

# 在重疊群組中的偏好
overlap_preference: uds

# 是否啟用 ECC 獨有功能
enable_exclusive:
  ecc: false  # 停用所有 ECC 獨有功能

# 可選：額外啟用的 ECC 項目（例外）
exceptions:
  enable:
    - strategic-compact  # 雖是 ECC 獨有，但 UDS 也想用
```

```yaml
# profiles/ecc.yaml
name: ecc
display_name: "Everything Claude Code"
description: "ECC 標準體系，採用 TypeScript/React 導向的實戰開發標準"
version: "1.0.0"

overlap_preference: ecc

enable_exclusive:
  uds: false  # 停用所有 UDS 獨有功能

exceptions:
  enable:
    - spec-driven-dev  # 雖是 UDS 獨有，但 ECC 也想用
```

```yaml
# profiles/minimal.yaml
name: minimal
display_name: "Minimal Standards"
description: "最小化標準體系，僅包含核心開發規範"
version: "1.0.0"

overlap_preference: minimal

enable_exclusive:
  uds: false
  ecc: false

# 明確列出要啟用的群組（其他群組停用）
enabled_groups:
  - commit-message
  - code-review
```

---

## Core Functions

### switch_profile()

```python
def switch_profile(target_profile: str) -> dict:
    """
    切換到指定的 Profile

    Args:
        target_profile: 目標 profile 名稱

    Returns:
        dict: 切換結果
    """
    result = {
        "success": False,
        "profile": target_profile,
        "disabled_items": [],
        "enabled_items": [],
        "warnings": []
    }

    # 1. 載入配置
    overlaps = load_overlaps()
    profile = load_profile(target_profile)
    current_disabled = load_disabled_yaml()

    # 2. 計算需停用的項目
    to_disable = set()

    # 2a. 處理重疊群組
    enabled_groups = profile.get('enabled_groups', list(overlaps['groups'].keys()))

    for group_name, group_def in overlaps['groups'].items():
        if group_name not in enabled_groups:
            # 停用整個群組
            for system_name, items in group_def.items():
                if system_name not in ['description', 'mutual_exclusive']:
                    to_disable.update(collect_items(items))
        else:
            # 只啟用偏好體系，停用其他
            pref = profile['overlap_preference']
            for system_name, items in group_def.items():
                if system_name not in ['description', 'mutual_exclusive']:
                    if system_name != pref:
                        to_disable.update(collect_items(items))

    # 2b. 處理獨有項目
    for system_name, system_def in overlaps.get('exclusive', {}).items():
        if not profile.get('enable_exclusive', {}).get(system_name, True):
            to_disable.update(collect_items(system_def))

    # 2c. 處理例外
    exceptions = profile.get('exceptions', {})
    for item in exceptions.get('enable', []):
        to_disable.discard(item)

    # 3. 保留手動停用的項目
    manual_disabled = current_disabled.get('_manual', [])

    # 4. 更新 disabled.yaml
    update_disabled_yaml({
        '_profile': target_profile,
        '_profile_disabled': sorted(to_disable),
        '_manual': manual_disabled,
        # 合併為扁平結構供其他工具讀取
        'skills': get_items_by_type(to_disable.union(set(manual_disabled)), 'skills'),
        'commands': get_items_by_type(to_disable.union(set(manual_disabled)), 'commands'),
        'agents': get_items_by_type(to_disable.union(set(manual_disabled)), 'agents'),
        'standards': get_items_by_type(to_disable.union(set(manual_disabled)), 'standards'),
    })

    # 5. 更新 active.yaml
    update_active_profile(target_profile)

    result['success'] = True
    result['disabled_items'] = sorted(to_disable)
    result['enabled_items'] = get_enabled_items(overlaps, to_disable)

    return result
```

### collect_items()

```python
def collect_items(items_def: dict) -> set:
    """
    從項目定義收集所有項目名稱

    Args:
        items_def: 項目定義字典，如 {"skills": ["a", "b"], "standards": ["c"]}

    Returns:
        set: 項目名稱集合（含類型前綴）
    """
    result = set()
    for item_type, items in items_def.items():
        if item_type.startswith('_'):  # 跳過 metadata
            continue
        if isinstance(items, list):
            for item in items:
                result.add(f"{item_type}:{item}")
    return result
```

### load_overlaps()

```python
def load_overlaps() -> dict:
    """載入重疊定義"""
    overlaps_path = get_profiles_dir() / 'overlaps.yaml'
    if not overlaps_path.exists():
        raise FileNotFoundError(
            "overlaps.yaml not found. "
            "Run '/upstream-compare --generate-overlaps' to create it."
        )
    return load_yaml(overlaps_path)
```

---

## disabled.yaml Format

### 新格式（含 profile 來源標記）

```yaml
# .claude/disabled.yaml
_profile: uds                    # 當前啟用的 profile
_profile_disabled:               # 由 profile 停用的項目
  - skills:tdd-workflow
  - commands:e2e
  - agents:build-error-resolver
_manual:                         # 使用者手動停用的項目
  - skills:some-skill-i-dont-want

# 扁平結構（供其他工具讀取）
skills:
  - tdd-workflow
  - some-skill-i-dont-want
commands:
  - e2e
agents:
  - build-error-resolver
standards: []
```

### 相容性

- 現有讀取 `disabled.yaml` 的工具只需讀取 `skills`, `commands`, `agents` 欄位
- 新增的 `_profile`, `_profile_disabled`, `_manual` 欄位供 profile 系統使用
- `_` 開頭的欄位被視為 metadata

---

## Integration with upstream-sync/compare

### upstream-compare 輸出增強

```yaml
# 新增 overlap_analysis 欄位
overlap_analysis:
  detected_overlaps:
    - group: tdd-workflow
      description: "兩個 repo 都有 TDD 工作流功能"
      local:
        skills: [testing-guide]
        standards: [testing.ai.yaml, test-driven-development.ai.yaml]
      upstream:
        skills: [tdd-workflow]
        commands: [tdd]
      recommendation: |
        upstream 版本更實戰導向，建議：
        - ECC profile 使用 upstream 版本
        - UDS profile 保留現有版本
      suggested_group:
        name: tdd-workflow
        uds:
          skills: [testing-guide]
          standards: [testing.ai.yaml, test-driven-development.ai.yaml]
        ecc:
          skills: [tdd-workflow]
          commands: [tdd]

  new_items_not_overlapping:
    - type: skill
      name: new-unique-skill
      source: upstream
      recommendation: "加入 skills/，不需在 overlaps.yaml 定義"

  suggested_overlaps_yaml_update: |
    # 建議新增以下內容到 overlaps.yaml
    groups:
      new-detected-overlap:
        uds:
          skills: [...]
        ecc:
          skills: [...]
```

### upstream-sync 腳本更新

```python
# skills/upstream-sync/scripts/analyze_upstream.py 新增功能

def detect_overlaps(local_items: dict, upstream_items: dict) -> list:
    """
    偵測本地與上游的功能重疊

    比對邏輯：
    1. 名稱相似度（Levenshtein distance < 3）
    2. 功能關鍵字匹配（tdd, test, commit, review 等）
    3. 目錄結構相似（都有 SKILL.md 在 tdd-* 目錄）
    """
    overlaps = []

    for upstream_item in upstream_items:
        for local_item in local_items:
            similarity = calculate_similarity(upstream_item, local_item)
            if similarity > 0.7:
                overlaps.append({
                    "local": local_item,
                    "upstream": upstream_item,
                    "similarity": similarity,
                    "reason": get_similarity_reason(upstream_item, local_item)
                })

    return overlaps
```

---

## CLI Command Updates

### switch 命令

```python
@app.command()
def switch(
    profile_name: str = typer.Argument(..., help="要切換的 Profile 名稱"),
    dry_run: bool = typer.Option(False, "--dry-run", help="只顯示變更，不實際執行"),
    force: bool = typer.Option(False, "--force", help="強制覆蓋手動停用的項目")
):
    """切換到指定的 Standards Profile"""

    if dry_run:
        # 模擬切換
        result = compute_switch_changes(profile_name)
        console.print(f"[cyan]模擬切換到 {profile_name}[/cyan]")
        console.print(f"\n[bold]將停用的項目 ({len(result['to_disable'])}):[/bold]")
        for item in sorted(result['to_disable']):
            console.print(f"  - {item}")
        console.print(f"\n[bold]將啟用的項目 ({len(result['to_enable'])}):[/bold]")
        for item in sorted(result['to_enable']):
            console.print(f"  + {item}")
        return

    result = switch_profile(profile_name)

    if result['success']:
        console.print(f"[green]✓ 成功切換到 {profile_name}[/green]")
        console.print(f"  停用了 {len(result['disabled_items'])} 個項目")
        if result['warnings']:
            for warning in result['warnings']:
                console.print(f"[yellow]警告: {warning}[/yellow]")
    else:
        console.print(f"[red]✗ 切換失敗: {result.get('error')}[/red]")
        raise typer.Exit(1)
```

### show 命令增強

```python
@app.command()
def show(profile_name: str = typer.Argument(..., help="要顯示的 Profile 名稱")):
    """顯示指定 Profile 的詳細內容（含重疊分析）"""

    profile = load_profile(profile_name)
    overlaps = load_overlaps()

    console.print(f"[bold cyan]{profile['display_name']}[/bold cyan]")
    console.print(f"[dim]{profile['description']}[/dim]")

    console.print(f"\n[bold]重疊偏好:[/bold] {profile['overlap_preference']}")

    # 顯示各群組的選擇
    console.print(f"\n[bold]重疊群組選擇:[/bold]")
    for group_name in overlaps['groups']:
        pref = profile['overlap_preference']
        items = overlaps['groups'][group_name].get(pref, {})
        console.print(f"  {group_name}: 使用 {pref} 版本")
        for item_type, item_list in items.items():
            if item_type not in ['description', 'mutual_exclusive'] and item_list:
                console.print(f"    {item_type}: {', '.join(item_list)}")

    # 顯示獨有功能啟用狀態
    console.print(f"\n[bold]獨有功能:[/bold]")
    for system, enabled in profile.get('enable_exclusive', {}).items():
        status = "啟用" if enabled else "停用"
        console.print(f"  {system}: {status}")
```

---

## TUI Integration

### Profile Selector 更新

```python
def update_profile_display(self) -> None:
    """更新 Profile 區塊顯示"""
    profiles = list_profiles()
    active = get_active_profile()
    overlaps = load_overlaps()

    # 顯示當前 profile 的重疊選擇摘要
    if active:
        profile = load_profile(active)
        pref = profile['overlap_preference']

        summary = []
        for group_name in overlaps['groups']:
            items = overlaps['groups'][group_name].get(pref, {})
            count = sum(len(v) for v in items.values() if isinstance(v, list))
            summary.append(f"{group_name}: {count}")

        self.profile_summary.update(
            f"當前: {active} ({', '.join(summary[:3])}{'...' if len(summary) > 3 else ''})"
        )
```

---

## Error Handling

| 錯誤類型 | 情境 | 處理方式 |
|---------|------|----------|
| **OverlapsNotFoundError** | `overlaps.yaml` 不存在 | 提示執行 `/upstream-compare --generate-overlaps` |
| **ProfileNotFoundError** | Profile 定義檔不存在 | 顯示可用 profiles |
| **InvalidOverlapPreference** | overlap_preference 值無效 | 顯示可用的體系名稱 |
| **CircularReferenceError** | exceptions 造成循環 | 警告並忽略循環項 |

---

## Migration from Old Design

### 遷移步驟

1. **建立 overlaps.yaml**
   ```bash
   # 手動建立或使用工具生成
   /upstream-compare --generate-overlaps
   ```

2. **更新 profile 定義**
   ```bash
   # 移除舊欄位（includes, inherits, overrides）
   # 新增 overlap_preference, enable_exclusive
   ```

3. **刪除 profiles/standards/ 目錄**
   ```bash
   rm -rf profiles/standards/
   ```

4. **遷移 disabled.yaml**
   ```bash
   # 現有內容移至 _manual
   # 由 switch_profile() 重新生成
   ```

---

## Summary

此設計提供了一個更符合專案本質的 Profile 系統：

- **保留原生格式**：UDS 用 YAML，ECC 用 Markdown
- **基於重疊切換**：切換 = 選擇用哪個體系的功能
- **簡化架構**：不複製檔案，只更新 disabled.yaml
- **整合現有工具**：/upstream-sync 和 /upstream-compare 負責偵測重疊
- **可擴展**：新增體系只需更新 overlaps.yaml

核心理念：**Profile 切換是「選擇」，不是「替換」。**
