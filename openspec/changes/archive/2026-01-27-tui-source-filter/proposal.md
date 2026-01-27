# Proposal: tui-source-filter

## Summary

在 TUI 介面新增「來源篩選」功能，讓使用者可以依據資源來源（UDS、Custom、Obsidian、Anthropic、ECC、User）篩選顯示的資源清單。

## Motivation

目前 TUI 顯示所有已安裝的資源，隨著資源數量增加：

1. **清單過長**：難以快速找到特定來源的資源
2. **管理困難**：想要統一啟用/停用某個來源的所有資源時，需要逐一操作
3. **來源識別**：雖然每個資源旁都有來源標籤，但無法快速查看「某來源有哪些資源」

新增來源篩選功能可以：
- 快速定位特定來源的資源
- 方便批次管理同一來源的資源
- 更清楚地了解各來源的貢獻

## Scope

### In Scope

- 在篩選列新增「Source」下拉選單
- 支援篩選至單一來源
- 支援「All」選項顯示所有來源
- 篩選狀態與 Target/Type 篩選器協同運作

### Out of Scope

- 多選來源篩選（只支援單選或全選）
- 來源的增刪改管理
- 來源統計儀表板

## Design

### TUI 介面變更

```
┌─────────────────────────────────────────────────────────────────────────┐
│  AI Development Environment Manager                           v0.x.x   │
├─────────────────────────────────────────────────────────────────────────┤
│  [Install] [Update] [Clone] [Status] [Add Skills] [Quit]               │
├─────────────────────────────────────────────────────────────────────────┤
│  Target: [Claude Code ▼]   Type: [Skills ▼]   Source: [All ▼]          │
│                                               ^^^^^^^^^^^^^^^^          │
│                                               新增的篩選器              │
├─────────────────────────────────────────────────────────────────────────┤
│  ☑ ai-collaboration-standards     (universal-dev-standards)            │
│  ☑ custom-skills-dev              (custom-skills)                      │
│  ☑ json-canvas                    (obsidian-skills)                    │
│  ☑ skill-creator                  (anthropic-skills)                   │
│  ☑ coding-standards               (everything-claude-code)             │
│  ...                                                                    │
└─────────────────────────────────────────────────────────────────────────┘
```

### Source 下拉選單選項

```python
SOURCE_FILTER_OPTIONS = [
    ("All", "all"),                              # 顯示所有來源
    ("universal-dev-standards", "uds"),          # UDS 來源
    ("custom-skills", "custom"),                 # 本專案原創
    ("obsidian-skills", "obsidian"),             # Obsidian 社群
    ("anthropic-skills", "anthropic"),           # Anthropic 官方
    ("everything-claude-code", "ecc"),           # ECC 社群
    ("user", "user"),                            # 使用者自建
]
```

### 篩選邏輯

```python
def refresh_resource_list(self) -> None:
    """重新載入資源列表（含來源篩選）。"""
    resources = list_installed_resources(self.current_target, self.current_type)

    target_resources = resources.get(self.current_target, {})
    type_resources = target_resources.get(self.current_type, [])

    for item in type_resources:
        # 來源篩選
        if self.current_source != "all":
            expected_source = SOURCE_NAMES.get(self.current_source, self.current_source)
            if item["source"] != expected_source:
                continue

        # 渲染資源項目
        container.mount(ResourceItem(...))
```

### 狀態管理

```python
class SkillManagerApp(App):
    def __init__(self) -> None:
        super().__init__()
        self.current_target = "claude"
        self.current_type = "skills"
        self.current_source = "all"  # 新增：來源篩選狀態
```

### 事件處理

```python
def on_select_changed(self, event: Select.Changed) -> None:
    if event.select.id == "source-select":
        self.current_source = str(event.value)
        self.refresh_resource_list()
```

### 介面佈局

修改 `compose()` 方法中的 filter-bar：

```python
# 篩選列
with Horizontal(id="filter-bar"):
    yield Label("Target:")
    yield Select(TARGET_OPTIONS, value="claude", id="target-select", allow_blank=False)

    yield Label("Type:")
    yield Select(TYPE_OPTIONS_BY_TARGET["claude"], value="skills", id="type-select", allow_blank=False)

    yield Label("Source:")  # 新增
    yield Select(SOURCE_FILTER_OPTIONS, value="all", id="source-select", allow_blank=False)

    yield Checkbox("Sync to Project", value=True, id="cb-sync-project")
```

### 樣式調整

可能需要調整 `styles.tcss` 以適應新增的篩選器：

```css
#filter-bar {
    height: auto;
    padding: 1;
}

#filter-bar Label {
    margin-right: 1;
}

#filter-bar Select {
    width: 25;  /* 調整寬度以容納較長的來源名稱 */
    margin-right: 2;
}
```

## 進階功能（未來考慮）

### 來源統計顯示

可在篩選器旁顯示各來源的資源數量：

```
Source: [All (47) ▼]
        [universal-dev-standards (25)]
        [custom-skills (12)]
        [obsidian-skills (3)]
        ...
```

### 快捷鍵支援

```python
BINDINGS = [
    ...
    Binding("1", "filter_source_all", "All Sources"),
    Binding("2", "filter_source_uds", "UDS"),
    Binding("3", "filter_source_custom", "Custom"),
    ...
]
```

## Related Specs

- `skill-tui`: TUI 介面規格
- `source-identification`: 資源來源識別邏輯

## Dependencies

- 現有 `list_installed_resources()` 函數（已包含 source 欄位）
- Textual 框架
