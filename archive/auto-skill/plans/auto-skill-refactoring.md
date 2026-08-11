---
title: Auto-Skill 架構重構計畫：從無效觸發到 Hook 驅動
type: plan/refactoring
date: 2026-02-12
author: ValorVie
status: draft
---

# Auto-Skill 架構重構計畫：從無效觸發到 Hook 驅動

## 摘要

auto-skill 設計為「每次對話自動載入知識庫與經驗」的自進化系統，但在 Claude Code 架構下從未實際運作。根本原因是 Claude Code 的 skill 機制不支援自動觸發——skill 必須被明確呼叫（`/auto-skill`）才會載入 SKILL.md 的完整內容。本計畫將 auto-skill 的核心功能從「skill 自觸發」重構為「Hook 注入 + CLAUDE.md 指令」的混合架構，讓知識庫與經驗系統在每次對話中自動生效。

## 現況分析

### 問題描述

1. **觸發機制完全失效**：auto-skill 的 SKILL.md description 欄位寫了「CRITICAL PROTOCOL ... 嚴禁跳過」，期望 AI 看到描述後自動執行。但 Claude Code 只會在 skill 列表中顯示這段描述文字，不會自動讀取並執行 SKILL.md 的完整內容
2. **Step 0.5 自動加固從未執行**：`~/.claude/CLAUDE.md` 不存在，代表「任務啟動協議」從未被寫入全局規則
3. **知識庫幾乎空白**：5 個分類中只有 `writing.md` 有 1 筆條目，其餘 count 均為 0
4. **經驗索引是空模板**：`experience/_index.json` 的 skills 陣列只有空白佔位，`skill-remotion-best-practices.md` 看起來是手動建立的範例
5. **與 claude-mem MCP 功能重疊**：使用者已安裝 `claude-mem@thedotmack` 插件（提供 search、save_memory 等 MCP 工具），auto-skill 的知識庫系統與之部分重疊

### 影響範圍

| 模組/檔案 | 問題 | 嚴重度 |
|-----------|------|--------|
| `skills/auto-skill/SKILL.md` | 整份 167 行的協議從未被載入執行 | 高 |
| `skills/auto-skill/knowledge-base/` | 5 個分類檔幾乎全空，索引維護邏輯未觸發 | 高 |
| `skills/auto-skill/experience/` | 空模板，跨技能經驗記錄機制未運作 | 高 |
| `plugins/auto-skill-hooks/hooks/hooks.json` | 現有 hook 架構可複用，但未包含知識注入 | 低（機會） |
| `~/.claude/CLAUDE.md` | 不存在，全局行為指令缺失 | 中 |

### 架構對比

```
目前（失效）                              目標（Hook 驅動）
┌─────────────────────┐                  ┌─────────────────────┐
│ SKILL.md            │                  │ SessionStart Hook   │
│ description:        │                  │ ├── 注入 _index.json│
│ "CRITICAL..."       │                  │ └── 注入 experience │
│       ↓             │                  │       ↓             │
│ (期望 AI 自動讀取)   │                  │ (自動出現在 context) │
│       ↓             │                  │       ↓             │
│ (實際：從未觸發) ✗   │                  │ CLAUDE.md 指令      │
└─────────────────────┘                  │ ├── 如何用索引      │
                                         │ ├── 何時讀詳情      │
                                         │ └── 何時記錄經驗    │
                                         │       ↓             │
                                         │ Claude 自行判斷     │
                                         │ 讀取對應 .md 檔 ✓   │
                                         └─────────────────────┘
```

## 重構策略

### 方案選擇

| 方案 | 做法 | 優點 | 缺點 | 風險 |
|------|------|------|------|------|
| A: 純 CLAUDE.md | 把知識庫指令和索引內容直接寫入 CLAUDE.md | 最簡單、永遠在 context | 佔用 CLAUDE.md token；分類多時膨脹；靜態無法更新 | 低 |
| B: 純 Hook 注入 | SessionStart hook 輸出索引 JSON | 動態、自動 | 只能在對話開始注入；Claude 不一定知道怎麼用 | 中 |
| **C: Hook + CLAUDE.md 混合** | Hook 注入索引資料；CLAUDE.md 寫行為指令 | 動態資料 + 穩定指令；職責清晰；可擴展 | 需改兩處設定 | 低 |
| D: 遷移至 claude-mem | 放棄 auto-skill，全部用 claude-mem MCP | 已有基礎設施 | 失去分類結構；依賴第三方插件 | 中 |

**選擇方案 C** — Hook + CLAUDE.md 混合。理由：

1. Claude Code 支援同一 repo 下多個獨立插件，建立 `auto-skill-hooks` 與 ecc-hooks 職責分離
2. CLAUDE.md 是 Claude Code 的原生機制，行為指令放這裡最可靠
3. 索引資料和行為指令分離，各自可獨立演進
4. 不依賴第三方插件，也不排斥未來與 claude-mem 整合

### 重構方法

**Boy Scout Rule + 一次性遷移混合**：核心架構一次到位（新 hook + CLAUDE.md 指令），知識庫內容隨日常使用逐步累積。

### 要保留的功能

| 功能 | 來源 | 保留方式 |
|------|------|----------|
| 知識庫分類系統 | Step 4 | 保留 `knowledge-base/` 目錄結構與 `_index.json` |
| 跨技能經驗記錄 | Step 3 | 保留 `experience/` 目錄結構與 `_index.json` |
| 任務結束主動記錄 | Step 5 | 濃縮為 CLAUDE.md 指令 |
| 條目格式規範 | 條目格式章節 | 保留在 SKILL.md 作為參考 |

### 要捨棄的功能

| 功能 | 來源 | 捨棄理由 |
|------|------|----------|
| Step 0.5 自動加固全局規則 | SKILL.md | 直接手動設定 CLAUDE.md，不需要 AI 去修改設定檔 |
| 逐回合關鍵詞抽取 | Step 1 | 過度工程；Claude 本身就能判斷話題相關性 |
| topic_fingerprint 快取 | Step 2 | Claude Code 無法跨回合持久化變數 |
| 話題切換偵測 | Step 2 | 讓 Claude 自行判斷，不需要形式化規則 |
| 強制分類匹配 | Step 4 | 改為 Claude 根據索引自行決定是否讀取 |
| QMD 升級路徑 | 最後章節 | 尚未到 50 條目，移除過早的預設 |

### 執行步驟

#### 1. 準備階段

- [ ] 確認現有 `knowledge-base/_index.json` 與 `experience/_index.json` 格式
- [ ] 清理 `experience/_index.json` 的空白佔位（目前是無效模板）
- [ ] 盤點現有 ecc-hooks 的 SessionStart hook 輸出格式

#### 2. 建立 SessionStart Hook 腳本

建立 `plugins/auto-skill-hooks/scripts/inject-knowledge-index.py`：

```python
#!/usr/bin/env python3
"""SessionStart hook: 注入 auto-skill 知識庫與經驗索引到對話 context"""

import json
import os
import sys

SKILL_ROOT = os.path.expanduser("~/.claude/skills/auto-skill")
# 若 skill 安裝在其他位置，也支援專案內路徑
PROJECT_SKILL_ROOT = os.path.join(os.getcwd(), "skills", "auto-skill")

def find_skill_root():
    for path in [SKILL_ROOT, PROJECT_SKILL_ROOT]:
        if os.path.isdir(path):
            return path
    return None

def load_json(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None

def main():
    root = find_skill_root()
    if not root:
        return  # auto-skill 未安裝，靜默跳過

    kb_index = load_json(os.path.join(root, "knowledge-base", "_index.json"))
    exp_index = load_json(os.path.join(root, "experience", "_index.json"))

    output_parts = []

    if kb_index and kb_index.get("categories"):
        categories_with_content = [
            c for c in kb_index["categories"] if c.get("count", 0) > 0
        ]
        if categories_with_content:
            output_parts.append("[Auto-Skill Knowledge Base]")
            for cat in categories_with_content:
                output_parts.append(
                    f"  {cat['name']} ({cat['file']}): "
                    f"{cat['count']} entries | "
                    f"keywords: {', '.join(cat.get('keywords', []))}"
                )

    if exp_index and exp_index.get("skills"):
        valid_skills = [
            s for s in exp_index["skills"]
            if s.get("skillId") and s.get("file")
        ]
        if valid_skills:
            output_parts.append("[Auto-Skill Experience]")
            for skill in valid_skills:
                output_parts.append(
                    f"  {skill['skillId']} ({skill['file']}): "
                    f"{skill.get('count', 0)} entries"
                )

    if output_parts:
        print("\n".join(output_parts))

if __name__ == "__main__":
    main()
```

#### 3. 建立插件結構

建立 `plugins/auto-skill-hooks/` 獨立插件：

```
plugins/auto-skill-hooks/
├── .claude-plugin/
│   └── plugin.json          # name: "auto-skill-hooks"
├── hooks/
│   └── hooks.json           # SessionStart hook 配置
└── scripts/
    └── inject-knowledge-index.py
```

`hooks/hooks.json`：

```json
{
  "description": "Auto-Skill Hooks - Knowledge Base & Experience Injection",
  "hooks": {
    "SessionStart": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/scripts/inject-knowledge-index.py\""
          }
        ],
        "description": "Inject auto-skill knowledge-base and experience index into conversation context"
      }
    ]
  }
}
```

#### 4. 建立 CLAUDE.md 行為指令

在專案 `CLAUDE.md` 或 `~/.claude/CLAUDE.md`（全局）新增：

```markdown
## 知識庫與經驗協議

對話開始時，SessionStart hook 會注入 [Auto-Skill Knowledge Base] 和 [Auto-Skill Experience] 索引。

### 讀取規則
- 看到索引中有與當前任務相關的分類或技能經驗時，讀取對應的 .md 檔案
- 知識庫路徑：skills/auto-skill/knowledge-base/{file}
- 經驗路徑：skills/auto-skill/experience/{file}
- 不需要每次都讀，只在判斷相關時讀取

### 記錄規則
- 任務完成且產生了可重用的經驗時，主動詢問使用者是否記錄
- 使用其他 skill 且 experience 索引中無該 skill 記錄時，任務結束前詢問是否記錄
- 記錄格式參考 skills/auto-skill/SKILL.md 的「條目格式」章節
- 記錄後更新對應的 _index.json
```

#### 5. 精簡 SKILL.md

保留 SKILL.md 作為格式參考與手動呼叫入口（`/auto-skill`），但：
- 移除 Step 0.5（自動加固）
- 移除 Step 1-2（關鍵詞/話題切換）
- 簡化 Step 3-4 為「參考 CLAUDE.md 指令」
- 保留 Step 5（記錄判斷準則）和條目格式

#### 6. 驗證階段

- [ ] 啟動新對話，確認 SessionStart hook 輸出索引內容
- [ ] 手動在 knowledge-base 新增一筆條目，確認下次對話能看到
- [ ] 使用其他 skill（如 `/commit`），確認 Claude 能根據 CLAUDE.md 指令查詢 experience
- [ ] 完成一個任務後，確認 Claude 主動詢問是否記錄經驗

## 向下相容性

- **知識庫格式**：完全相容，`_index.json` 和 `.md` 檔案格式不變
- **經驗格式**：完全相容，只需清理空白佔位
- **手動呼叫**：`/auto-skill` 仍可使用，作為手動查看/管理知識庫的入口
- **其他 skill**：不受影響，行為透過 CLAUDE.md 指令驅動而非 skill 間耦合

## 風險評估

| 風險 | 影響程度 | 可能性 | 緩解措施 |
|------|----------|--------|----------|
| Hook 輸出被 Claude 忽略 | 中 | 低 | CLAUDE.md 明確指示如何使用 hook 輸出；與現有 ecc-hooks 的 session-start.py 輸出格式一致 |
| 索引膨脹佔用 context | 低 | 低 | 腳本只輸出有內容的分類（count > 0），空分類不輸出 |
| 經驗記錄品質不一致 | 中 | 中 | 保留 SKILL.md 的判斷準則作為參考；CLAUDE.md 引導 Claude 查閱格式 |
| 與 claude-mem 功能衝突 | 低 | 中 | 兩者定位不同：auto-skill 是結構化領域知識，claude-mem 是通用記憶搜尋；可共存 |

## 回滾方案

1. 從 `hooks.json` 移除新增的 SessionStart hook 條目
2. 從 CLAUDE.md 移除「知識庫與經驗協議」區塊
3. 原有 `knowledge-base/` 和 `experience/` 資料完全不受影響

回滾成本極低，因為新增的都是獨立的設定區塊。

## 驗收標準

- [ ] 新對話啟動時，有內容的知識庫分類自動出現在 context 中
- [ ] Claude 在相關任務中主動讀取對應的知識庫 `.md` 檔案
- [ ] 使用非 auto-skill 技能後，Claude 能查詢並提示相關經驗
- [ ] 任務結束時，Claude 根據判斷準則主動詢問是否記錄
- [ ] `~/.claude/CLAUDE.md` 不再需要（行為指令在專案 CLAUDE.md 中）
- [ ] 既有知識庫資料無損

## 附錄

### 相關檔案

- `skills/auto-skill/SKILL.md` — 現有完整協議（167 行）
- `skills/auto-skill/knowledge-base/_index.json` — 知識庫索引
- `skills/auto-skill/experience/_index.json` — 經驗索引
- `plugins/auto-skill-hooks/hooks/hooks.json` — 現有 hook 設定（207 行）
- `plugins/ecc-hooks/scripts/memory-persistence/session-start.py` — 現有 SessionStart 腳本（可參考實作模式）

### 與 claude-mem 的關係

| 面向 | auto-skill | claude-mem |
|------|-----------|------------|
| 資料結構 | 分類索引 + Markdown 檔案 | MCP 記憶資料庫 |
| 查詢方式 | 檔案讀取 | MCP search/timeline 工具 |
| 適合場景 | 領域知識、技能經驗、操作規範 | 跨 session 記憶、觀察記錄 |
| 觸發方式 | Hook 注入 + CLAUDE.md 指令 | MCP 工具呼叫 |

兩者可共存互補。未來可考慮讓 auto-skill 的記錄同時寫入 claude-mem 作為備份搜尋管道。
