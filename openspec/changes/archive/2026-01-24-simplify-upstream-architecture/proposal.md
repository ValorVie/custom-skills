# Proposal: Simplify Upstream Architecture

## Summary

簡化上游同步架構，明確分離 CLI 指令與 Skill 的職責，移除不必要的 `sources/` 中間層。

## Problem Statement

目前的架構混淆了多個概念：

1. **`sources/` 目錄職責不明確**
   - 與 `~/.config/<repo>/` 重複存放上游內容
   - 增加維護複雜度
   - 同步流程過於複雜（Stage 1.5）

2. **`ai-dev update` 職責過多**
   - 混合了工具更新、repo 拉取、內容分發
   - 難以理解每個步驟的作用

3. **兩個 upstream skill 職責重疊**
   - `upstream-sync` 和 `upstream-compare` 界限模糊
   - 使用者不清楚何時使用哪個

## Proposed Solution

### 新架構設計

```
~/.config/<repo>/           # 上游 repo（ai-dev update 拉取）
        │
        ├─── ai-dev clone ──→ 各工具目錄分發
        │
        └─── Skills 比較 ──→ upstream-sync (快速檢視)
                           ──→ upstream-compare (深度分析)
```

### 職責分離

| 元件 | 職責 | 觸發方式 |
|------|------|----------|
| `ai-dev update` | 更新工具 + 拉取所有 repo | 手動執行 |
| `ai-dev clone` | 分發 `~/.config/custom-skills` 到各工具目錄 | 手動執行 |
| `upstream-sync` skill | 追蹤上游差異、顯示更新、初步建議 | `/upstream-sync` |
| `upstream-compare` skill | 深度品質比較、完整分析報告、OpenSpec 提案 | `/upstream-compare` |

### 目錄結構（簡化後）

```
~/.config/
├── custom-skills/          # 主要來源（整合後的內容）
├── universal-dev-standards/  # UDS 上游
├── superpowers/            # superpowers 上游
├── obsidian-skills/        # obsidian 上游
├── anthropic-skills/       # anthropic 上游
└── everything-claude-code/ # ecc 上游

# 不再需要 sources/ 目錄
```

## Changes Required

### 1. CLI 指令修改

#### `ai-dev update`（修改）
- 移除 `copy_skills()` 呼叫
- 只負責：
  1. 更新 Claude Code
  2. 更新 NPM 套件
  3. 拉取所有 `~/.config/` repo

#### `ai-dev clone`（新增）
- 執行 `copy_skills()` 分發內容
- 從 `~/.config/custom-skills` 分發到各工具目錄

### 2. shared.py 修改

- 移除 `sync_repos_to_sources()` 函數
- 移除 `_get_source_path()` fallback 邏輯
- 還原 `copy_sources_to_custom_skills()` 直接從 `~/.config/<repo>/` 讀取

### 3. Skill 重新定義

#### upstream-sync（追蹤差異）
- **用途**：快速檢視上游有哪些更新
- **輸出**：簡潔的差異摘要、初步建議
- **不做**：深度品質分析

#### upstream-compare（深度分析）
- **用途**：詳細比較品質、生成分析報告
- **輸出**：完整報告、OpenSpec 提案
- **不做**：檔案同步操作

### 4. 移除項目

- 刪除 `sources/` 目錄
- 移除 `upstream/sources.yaml` 中的 `target_dir` 欄位
- 移除 shared.py 中的 Stage 1.5 邏輯

## Benefits

1. **簡化架構**：移除不必要的中間層
2. **職責清晰**：CLI 指令和 Skill 各司其職
3. **減少混淆**：使用者明確知道何時用哪個工具
4. **維護容易**：減少程式碼複雜度

## Migration Path

1. 刪除 `sources/` 目錄（無資料損失，內容來自 `~/.config/`）
2. 更新 CLI 指令
3. 更新 Skill 文件
4. 重新安裝 `ai-dev`

## Related Changes

- 需要更新 `cli-distribution` spec
- 需要更新 `project-commands` spec（新增 clone 指令）
