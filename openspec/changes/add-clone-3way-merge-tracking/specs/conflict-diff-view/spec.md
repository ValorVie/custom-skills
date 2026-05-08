## ADDED Requirements

### Requirement: 三向 diff 摘要列

當 `smart_merge.merge_file()` 進入 `both-changed` 互動 prompt 時，系統 SHALL 在等待輸入前先輸出三行摘要，分別表示：

- 來源相對 base 的新增 / 移除行數（src vs base）。
- 本地相對 base 的新增 / 移除行數（dst vs base）。
- 兩邊重疊改動的行數（src vs dst 中在前兩段都出現的差異）。

摘要 SHALL 使用 rich console 輸出、行數來自 `difflib.unified_diff` 的 `+`/`-` 計數。

#### Scenario: 顯示三段摘要
- **WHEN** 進入 `both-changed` prompt 且 base 存在
- **THEN** console SHALL 出現「來源動 +N -M」「你動 +P -Q」「兩邊重疊 +R -S」三行

#### Scenario: 無 base 時退回現行單一摘要
- **WHEN** 進入 `no-base` prompt（理論上不該發生於 both-changed，但測試保險）
- **THEN** 系統 SHALL 退回現行行為，只顯示 src vs dst 的 unified diff（透過 `[D]`）

### Requirement: 三向 diff 互動指令拆分

`smart_merge._prompt_conflict()` SHALL 將原 `[D]` 指令拆為三組：

- `[Ds]`：顯示 src vs base 的 unified diff。
- `[Dl]`：顯示 dst vs base 的 unified diff。
- `[Dc]`：顯示 src vs dst 的 unified diff。

`[A] [I] [O] [S]` 行為不變。`_prompt_hint()` SHALL 同步更新文字以分組顯示「Diff: [Ds]/[Dl]/[Dc] | Action: [A]/[I]/[O]/[S]」。

#### Scenario: Ds 顯示 src vs base
- **GIVEN** 進入 `both-changed` prompt
- **WHEN** 使用者輸入 `Ds`
- **THEN** 系統 SHALL 輸出 src 與 base（base 內容透過 git `cat-file blob <src_commit>:<rel-path>` 取得）的 unified diff，然後重新顯示 prompt

#### Scenario: Dl 顯示 dst vs base
- **WHEN** 使用者輸入 `Dl`
- **THEN** 系統 SHALL 輸出 dst 與 base 的 unified diff，然後重新顯示 prompt

#### Scenario: Dc 顯示 src vs dst（保留現行 [D] 視角）
- **WHEN** 使用者輸入 `Dc`
- **THEN** 系統 SHALL 輸出 src 與 dst 的 unified diff，然後重新顯示 prompt

#### Scenario: hint 文字更新
- **WHEN** prompt hint 顯示
- **THEN** 文字 SHALL 同時包含 `[Ds]` `[Dl]` `[Dc]` 三個 diff 指令、與 `[A]` `[I]` `[O]` `[S]` 四個 action 指令

#### Scenario: base 取不到時 Ds / Dl 退回提示
- **GIVEN** base 對應 src_commit 在來源 git 中已不存在
- **WHEN** 使用者輸入 `Ds` 或 `Dl`
- **THEN** 系統 SHALL 顯示「無法取得 base 內容（commit 已失效）」、保留 prompt 不退出
