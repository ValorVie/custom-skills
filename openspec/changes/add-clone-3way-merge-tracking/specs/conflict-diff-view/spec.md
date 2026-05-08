## ADDED Requirements

### Requirement: Per-file 衝突 prompt（取代 batch 5-option for clone）

系統 SHALL 提供 `prompt_file_decision(skill_name, rel_path, src_path, dst_path, base_blob_getter) -> Literal["overwrite", "skip"]`，於 `copy_custom_skills_to_targets` 內每筆 `both-changed` 檔案時呼叫一次。

prompt 內容：

- 開頭印三段摘要：「來源動 +N -M」「你動 +P -Q」「重疊改動 +R -S」。行數從 unified diff 的 `+`/`-` 計數推算（重疊段以 src vs dst 中同時出現於 src vs base 與 dst vs base 的 hunks 估算）。
- 提示文字：「Diff: [Ds]/[Dl]/[Dc] | Action: [O] overwrite / [S] skip」。
- 接受輸入大小寫不敏感。

回傳：

- `O` → `"overwrite"`（呼叫端負責覆蓋與寫 base）。
- `S` → `"skip"`（呼叫端負責寫 skipped 記憶）。
- `Ds` / `Dl` / `Dc` → 顯示對應 diff 後重新顯示 prompt（不退出）。

`base_blob_getter(rel_path) -> bytes | None` 由呼叫端提供，內部以 `git -C <source-repo> show <src_commit>:<rel>` 取得 base 內容；若失敗回 `None`。

#### Scenario: 顯示三段摘要
- **WHEN** 進入 prompt 且 base 可取得
- **THEN** console SHALL 出現三行摘要，其中 `+`/`-` 行數來自 unified diff

#### Scenario: O 回傳 overwrite
- **WHEN** 使用者輸入 `o` 或 `O`
- **THEN** 函式 SHALL 回傳 `"overwrite"`

#### Scenario: S 回傳 skip
- **WHEN** 使用者輸入 `s` 或 `S`
- **THEN** 函式 SHALL 回傳 `"skip"`

#### Scenario: Ds 顯示 src vs base
- **WHEN** 使用者輸入 `Ds`
- **THEN** 系統 SHALL 透過 `base_blob_getter(rel_path)` 取得 base，與 src_path 內容做 unified diff 並印出，然後重新顯示 prompt

#### Scenario: Dl 顯示 dst vs base
- **WHEN** 使用者輸入 `Dl`
- **THEN** 系統 SHALL 取得 base 與 dst_path 內容做 unified diff 並印出，然後重新顯示 prompt

#### Scenario: Dc 顯示 src vs dst
- **WHEN** 使用者輸入 `Dc`
- **THEN** 系統 SHALL 對 src_path 與 dst_path 做 unified diff 並印出，然後重新顯示 prompt

#### Scenario: base 取不到時 Ds / Dl 退回提示
- **GIVEN** `base_blob_getter(rel_path)` 回傳 `None`
- **WHEN** 使用者輸入 `Ds` 或 `Dl`
- **THEN** 系統 SHALL 顯示「無法取得 base 內容（commit 已失效）」、保留 prompt 不退出

#### Scenario: Dc 在 base 失效時仍可用
- **GIVEN** base 取不到
- **WHEN** 使用者輸入 `Dc`
- **THEN** 系統 SHALL 仍能輸出 src vs dst diff（不依賴 base）

## MODIFIED Requirements

### Requirement: 互動選單包含查看差異選項

`prompt_conflict_action()` SHALL 顯示 5 個選項，順序為：強制覆蓋（1）、跳過（2）、備份後覆蓋（3）、查看差異（4）、取消分發（5）。選擇「查看差異」時回傳 `"diff"`。

該函式 SHALL 保留並仍可被呼叫（用於 `no-base` fallback、未來其他指令、或測試），但 `copy_custom_skills_to_targets` 在 v2 路徑下對 `clean` / `local-only` / `both-changed` 三類 SHALL 不再呼叫此函式；僅 `no-base` 退回 batch 路徑時才會觸發。

#### Scenario: 使用者選擇查看差異
- **WHEN** 使用者在衝突選單中輸入 `4`
- **THEN** 函式回傳 `"diff"`

#### Scenario: 選項順序正確
- **WHEN** 顯示衝突處理選單
- **THEN** 選項依序為：1=強制覆蓋、2=跳過、3=備份後覆蓋、4=查看差異、5=取消分發

#### Scenario: clone v2 路徑不呼叫 batch UI
- **GIVEN** `copy_custom_skills_to_targets` 跑在 v2 manifest 模式
- **AND** 所有 file 皆有 base（無 no-base）
- **WHEN** 出現 both-changed 檔案
- **THEN** 系統 SHALL 呼叫 `prompt_file_decision()`，**不**呼叫 `prompt_conflict_action()`

#### Scenario: no-base fallback 仍呼叫 batch UI
- **GIVEN** 某 file 在 manifest 內無 FileEntry
- **WHEN** 出現衝突且未指定 `--force` / `--skip-conflicts`
- **THEN** 系統 SHALL 退回 batch UI 並呼叫 `prompt_conflict_action()`
