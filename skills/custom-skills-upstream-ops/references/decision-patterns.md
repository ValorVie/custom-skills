# Decision Patterns | Audit 結果判讀規則

audit mode 產出的 commit 清單與 diff stat 如何判斷優先級與動作。取代舊 `custom-skills-upstream-compare` 的 reading guide。

## 優先級判斷

讀 commit subject 與 `git diff --stat` 輸出後，自行判斷優先級，不套死分數：

| 判斷依據 | 優先級 |
|---------|-------|
| 多個新 skill / 多個新 standards / 新框架支援 | **High**（建議近期整合） |
| 有價值的改進、文件更新、新配置模式 | **Medium**（評估後整合） |
| 小幅調整、維護性變更 | **Low**（選擇性） |
| 無變更或僅微調 | **Skip** |

判斷示例：
- 「add 6 standards」→ High
- 「fix typo in README」→ Skip
- 「refactor sources-schema」→ Medium（影響文件閱讀）
- 「chore(release): v5.1.0-beta.7」→ Low（通常是 bump）

## 變更分類

依檔案路徑歸類：

- `skills/` — skill 變更（直接影響 AI 行為）
- `agents/` 或 `.claude/agents/` — agent 變更
- `commands/` — slash command 變更
- `.standards/` 或 `ai/standards/` — 標準文件
- `hooks/` — hook 變更
- `*.md`（根目錄）— 文件
- `*.json` / `*.yaml`（配置）— 配置變更

優先序：**新框架 > skills > agents > commands > hooks > 配置 > docs**。

## install_method 對應動作

參考 `install-methods.md`。每個 audit 條目輸出的「同步」命令必須對應該來源的 install_method，不要建議錯誤方式（例：對 plugin 類型說要手動複製檔案）。

## 新架構偵測

若 commit 涉及：
- 新目錄（例如從未出現的 `prompts/`、`hooks/`、`.claude-plugin/`）
- 新檔案類型（`.codex`、`.gitattributes` 等）
- 新配置檔（`plugin.json`、`hooks.json`）

應在 audit 輸出中**特別標註**「新架構偵測」，即使整體 commit 量不高也可能是 High 優先級。

## 輸出語氣

- 每個上游一個段落，開頭一句「Xxx 落後 N commits」
- 主要變更摘要 **3 句內**（AI 讀 commit subject 後自行濃縮）
- 結尾給一條明確命令（one-liner）
- 不輸出 YAML、不輸出評分數字
