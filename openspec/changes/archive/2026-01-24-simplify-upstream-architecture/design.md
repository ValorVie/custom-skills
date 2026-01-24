# Design: Simplify Upstream Architecture

## Architecture Overview

### Before (目前狀態)

```
┌────────────────────────────────────────────────────────────────────┐
│                          ai-dev update                              │
├────────────────────────────────────────────────────────────────────┤
│  1. 更新 Claude Code                                                │
│  2. 更新 NPM 套件                                                   │
│  3. 拉取 ~/.config/ repos                                          │
│  4. Stage 1.5: 同步到 sources/  ← 複雜且不必要                      │
│  5. Stage 2: 整合到 custom-skills                                   │
│  6. Stage 3: 分發到各工具                                           │
└────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────────┐
│  sources/                   │  ~/.config/<repo>/                    │
│  ├── ecc/                   │  ├── everything-claude-code/          │
│  ├── obsidian/              │  ├── obsidian-skills/                │
│  ├── anthropic/             │  ├── anthropic-skills/               │
│  ├── superpowers/           │  ├── superpowers/                    │
│  └── uds/                   │  └── universal-dev-standards/        │
└────────────────────────────────────────────────────────────────────┘
        ↑                                    ↑
        │ 重複存放！                          │ 上游原始內容
        └────────────────────────────────────┘
```

**問題**:
- `sources/` 與 `~/.config/` 內容重複
- 流程過於複雜
- 職責不清

### After (新架構)

```
┌────────────────────────────────────────────────────────────────────┐
│                          ai-dev update                              │
├────────────────────────────────────────────────────────────────────┤
│  1. 更新 Claude Code                                                │
│  2. 更新 NPM 套件                                                   │
│  3. 拉取 ~/.config/ repos                                          │
└────────────────────────────────────────────────────────────────────┘
                              │
                              │ 僅拉取，不分發
                              ▼
┌────────────────────────────────────────────────────────────────────┐
│  ~/.config/                                                         │
│  ├── custom-skills/         ← 主要來源                              │
│  ├── everything-claude-code/                                       │
│  ├── obsidian-skills/                                              │
│  ├── anthropic-skills/                                             │
│  ├── superpowers/                                                  │
│  └── universal-dev-standards/                                      │
└────────────────────────────────────────────────────────────────────┘
                              │
         ┌────────────────────┴────────────────────┐
         │                                         │
         ▼                                         ▼
┌─────────────────────┐               ┌─────────────────────────────┐
│   ai-dev clone      │               │   upstream-sync/compare     │
├─────────────────────┤               ├─────────────────────────────┤
│ Stage 2: 整合       │               │ 追蹤差異、品質比較          │
│ Stage 3: 分發       │               │ 不做檔案操作                │
└─────────────────────┘               └─────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────────────────────────────────┐
│  各工具目錄                                                         │
│  ├── ~/.claude/skills/                                             │
│  ├── ~/.config/opencode/skills/                                    │
│  ├── ~/.gemini/skills/                                             │
│  └── ...                                                           │
└────────────────────────────────────────────────────────────────────┘
```

## Component Design

### ai-dev update

```python
@app.command()
def update(
    skip_npm: bool = False,
    skip_repos: bool = False,
):
    """更新工具與拉取 repo。"""
    # 1. 更新 Claude Code
    # 2. 更新 NPM 套件
    # 3. 拉取 ~/.config/ repos
    # 不再執行 copy_skills()
```

### ai-dev clone

```python
# script/commands/clone.py

@app.command()
def clone(
    sync_project: bool = True,
):
    """分發 Skills 到各工具目錄。

    將 ~/.config/custom-skills 的內容分發到：
    - Claude Code (~/.claude/)
    - OpenCode (~/.config/opencode/)
    - Gemini CLI (~/.gemini/)
    - Codex (~/.codex/)
    - Antigravity (~/.gemini/antigravity/)
    """
    copy_skills(sync_project=sync_project)
```

### upstream-sync skill

**職責**: 追蹤差異、快速檢視

```markdown
## Quick Commands

/upstream-sync --check    # 檢查有哪些更新
/upstream-sync --diff     # 顯示差異摘要
/upstream-sync --assess   # 初步整合建議
```

**不做**:
- 不同步到 sources/
- 不做深度品質分析

### upstream-compare skill

**職責**: 深度分析、報告生成

```markdown
## Quick Commands

/upstream-compare                    # 完整比較報告
/upstream-compare --resource tdd     # 比較特定資源
/upstream-compare --proposal         # 生成 OpenSpec 提案
```

**特色**:
- 詳細的品質評分
- AI 分析建議
- OpenSpec 整合

## Data Flow

### 典型使用流程

```
1. ai-dev update --skip-npm
   └─→ 拉取最新 repo

2. /upstream-sync --check
   └─→ 檢視有哪些更新

3. /upstream-compare --resource tdd
   └─→ 深度比較 tdd skill

4. 人工審核報告，決定是否整合

5. 手動整合或使用 /openspec:proposal

6. ai-dev clone
   └─→ 分發更新後的 skills
```

## File Changes Summary

| 檔案 | 動作 | 說明 |
|------|------|------|
| `script/commands/update.py` | 修改 | 移除 copy_skills 呼叫 |
| `script/commands/clone.py` | 新增 | 新指令 |
| `script/main.py` | 修改 | 註冊 clone 指令 |
| `script/utils/shared.py` | 修改 | 移除 sources 相關邏輯 |
| `sources/` | 刪除 | 整個目錄 |
| `upstream/sources.yaml` | 修改 | 移除 target_dir |
| `skills/upstream-sync/SKILL.md` | 修改 | 重新定義職責 |
| `skills/upstream-compare/SKILL.md` | 修改 | 重新定義職責 |

## Trade-offs

### 優點
- 架構簡單易懂
- 減少重複資料
- 職責分明
- 維護成本低

### 考量
- 需要分開執行 update 和 clone
- 失去「一鍵完成」的便利性

### 緩解措施
- 可在文件中建議組合使用：`ai-dev update && ai-dev clone`
- 或後續考慮加入 `--clone` 選項到 update
