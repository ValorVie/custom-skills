# Third-Party Notices | 第三方授權聲明

本專案整合了以下上游開源專案的內容。感謝所有貢獻者的工作。

---

## 1. everything-claude-code

- **來源**: https://github.com/affaan-m/everything-claude-code
- **授權**: MIT License
- **版權**: Copyright (c) 2026 Affaan Mustafa
- **整合內容**: Skills (continuous-learning, strategic-compact, eval-harness, security-review, tdd-workflow)、Hooks (memory-persistence, strategic-compact 等，Python 重寫版)、Agents (build-error-resolver, e2e-runner, doc-updater, security-reviewer, database-reviewer)、Commands (checkpoint, build-fix, e2e, learn, test-coverage, eval)

<details>
<summary>MIT License 全文</summary>

MIT License

Copyright (c) 2026 Affaan Mustafa

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
</details>

---

## 2. superpowers

- **來源**: https://github.com/obra/superpowers
- **授權**: MIT License
- **版權**: Copyright (c) 2025 Jesse Vincent
- **整合內容**: Skills (brainstorming, dispatching-parallel-agents, executing-plans, finishing-a-development-branch, requesting-code-review, receiving-code-review, subagent-driven-development, systematic-debugging, test-driven-development, using-git-worktrees, using-superpowers, verification-before-completion, writing-plans, writing-skills)

<details>
<summary>MIT License 全文</summary>

MIT License

Copyright (c) 2025 Jesse Vincent

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
</details>

---

## 3. obsidian-skills

- **來源**: https://github.com/kepano/obsidian-skills
- **授權**: MIT License
- **版權**: Copyright (c) 2026 Steph Ango (@kepano)
- **整合內容**: Skills (json-canvas, obsidian-bases, obsidian-markdown)

<details>
<summary>MIT License 全文</summary>

MIT License

Copyright (c) 2026 Steph Ango (@kepano)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
</details>

---

## 4. anthropic-skills (skill-creator)

- **來源**: https://github.com/anthropics/skills
- **授權**: Apache License 2.0
- **版權**: Copyright Anthropic, PBC
- **整合內容**: Skills (skill-creator)
- **注意**: anthropic-skills 倉庫中的開源部分採用 Apache 2.0 授權。文件技能 (docx, pdf, pptx, xlsx) 為 source-available 而非開源，本專案**未整合**這些文件技能。

Apache 2.0 授權全文已包含於 `skills/skill-creator/LICENSE.txt`。

---

## 5. universal-dev-standards

- **來源**: https://github.com/AsiaOstrich/universal-dev-standards
- **授權**: 雙重授權 (Dual License)
  - **文件與規範**: Creative Commons Attribution 4.0 International (CC BY 4.0)
  - **CLI 工具原始碼**: MIT License
- **版權**: Copyright (c) 2025 Universal Development Standards Contributors
- **整合內容**: `.standards/` 目錄下的規範文件 (30+ 個標準模組)、Skills、Agents、Commands、Workflows
- **歸屬要求**: CC BY 4.0 要求標註出處。本專案的 `.standards/` 目錄內容源自 Universal Dev Standards 專案。

CC BY 4.0 全文: https://creativecommons.org/licenses/by/4.0/legalcode

---

## 6. wshobson/agents (僅參考)

- **來源**: https://github.com/wshobson/agents
- **授權**: MIT License
- **狀態**: 收錄於 `third-party/` 目錄作為參考資源，**未直接整合至本專案**。使用者需自行依照原專案授權條款使用。

---

## 授權相容性摘要

| 上游授權 | 與本專案 (MIT) 相容性 | 義務 |
|----------|----------------------|------|
| MIT | ✅ 完全相容 | 保留版權聲明與授權文本 |
| Apache 2.0 | ✅ 相容 | 保留版權聲明、授權文本、NOTICE 檔案、標示修改 |
| CC BY 4.0 | ✅ 相容 (用於文件) | 標註出處、提供授權連結、標示是否修改 |

所有上游授權皆為寬鬆型授權，允許商業使用、修改與再散布。
