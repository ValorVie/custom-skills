# Design: 整合 everything-claude-code

## Context

整合 [everything-claude-code](https://github.com/affaan-m/everything-claude-code) (ecc) 到本專案，採用靜態整合模式：直接修改本專案檔案，並建立上游追蹤機制。

## Goals

1. 選擇性整合 ecc 有價值的內容
2. 建立上游追蹤機制，便於後續同步更新
3. Hooks 使用 Python 實作確保跨平台
4. 此模式可複用於其他上游專案

## Decisions

### Decision 1: 靜態整合模式

**What**: 直接將 ecc 內容轉換後 commit 到本專案，而非動態同步

**Why**:
- 可深度客製化（格式轉換、翻譯、合併）
- 版本控制清晰
- 不需額外的執行時同步機制

**Trade-off**: 需要手動追蹤上游更新

### Decision 2: 上游追蹤機制

**What**: 建立 `upstream/` 目錄記錄上游來源和檔案對照

**結構**:
```
upstream/
├── sources.yaml          # 所有上游來源註冊
├── ecc/
│   ├── last-sync.yaml   # 最後同步 commit
│   └── mapping.yaml     # 檔案對照表
├── superpowers/         # 未來其他上游
│   └── ...
└── README.md
```

**追蹤流程**:
1. 記錄整合時的 commit hash
2. 定期檢查上游是否有新 commits
3. 有更新時，透過 OpenSpec 建立審核提案
4. 人工審核後選擇性同步

### Decision 3: Hooks 使用 Python

**What**: 將 ecc 的 Node.js hooks 重寫為 Python

**Why**:
- 本專案技術棧以 Python 為主
- Python 跨平台支援一致
- 減少 Node.js 相依性

**實作架構**:
```python
# hooks/memory_persistence.py
"""Claude Code 記憶持久化 Hook"""
import json
from pathlib import Path
from datetime import datetime

class MemoryPersistence:
    def __init__(self, storage_dir: Path = None):
        self.storage_dir = storage_dir or Path.home() / ".claude" / "memory"
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def save(self, session_id: str, context: dict) -> None:
        """保存對話上下文"""
        file_path = self.storage_dir / f"{session_id}.json"
        data = {
            "saved_at": datetime.now().isoformat(),
            "context": context
        }
        file_path.write_text(json.dumps(data, ensure_ascii=False, indent=2))

    def load(self, session_id: str) -> dict | None:
        """載入對話上下文"""
        file_path = self.storage_dir / f"{session_id}.json"
        if file_path.exists():
            return json.loads(file_path.read_text())
        return None
```

### Decision 4: UDS 格式統一

**What**: 所有整合的 agents 需轉換為 UDS AGENT.md 格式

**格式對照**:
```yaml
# ecc 格式
agentConfig:
  model: "opus"
  tools: ["Read", "Grep", "Glob", "Bash"]

# UDS 格式
---
name: security-reviewer
version: 1.0.0
description: |
  安全審查專家。執行程式碼安全分析。
  Keywords: security, vulnerability, OWASP.

role: reviewer
expertise:
  - security-analysis
  - vulnerability-detection

allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash(git:*)

triggers:
  keywords:
    - security review
    - 安全審查
  commands:
    - /security-review
---
```

### Decision 5: Attribution 標注

**What**: 所有整合檔案需在頭部標注來源

**格式**:
```markdown
<!--
Upstream: everything-claude-code
Source: https://github.com/affaan-m/everything-claude-code/blob/main/agents/security-reviewer.md
Synced: 2026-01-24
Commit: abc1234
License: MIT
-->
```

## Risks / Trade-offs

| 風險 | 等級 | 緩解措施 |
|------|------|----------|
| 上游更新遺漏 | 中 | 定期檢查機制 + OpenSpec 審核流程 |
| 合併衝突 | 中 | 保留本地化優勢，逐一比對 |
| Hooks 功能差異 | 低 | 重寫時確保功能等價 |

## Open Questions

1. **上游檢查頻率**：每週？每月？還是手動觸發？
2. **自動化程度**：是否需要 GitHub Actions 自動檢查？
3. **其他上游**：superpowers、obsidian-skills 是否也採用此機制？
