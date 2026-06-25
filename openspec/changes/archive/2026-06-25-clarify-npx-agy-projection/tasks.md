## 1. 加上澄清註解

- [x] 1.1 在 `script/services/tools/update.py` 的 `_NPX_PROJECT_AGENTS` 上方加註解：`gemini-cli` 是外部 `npx skills` 工具的 agent（非本專案 target），其路徑 project `.agents/skills` / global `~/.gemini/skills` 正是 agy 讀取處；npx skills v1.5.1 無 `agy` agent，故保留不改名。

## 2. 驗收

- [x] 2.1 `pytest` 全套通過（行為不變）
- [x] 2.2 `openspec validate clarify-npx-agy-projection --strict` 通過
