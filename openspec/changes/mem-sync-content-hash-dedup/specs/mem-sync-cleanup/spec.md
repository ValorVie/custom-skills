## ADDED Requirements

### Requirement: Cleanup 指令掃描並刪除本地重複

系統 SHALL 提供 `ai-dev mem cleanup` 子命令，掃描本地 claude-mem SQLite 中具有相同 content hash 的 observations，保留 id 最小的，刪除其餘。

#### Scenario: 有重複時刪除
- **WHEN** 本地有 3 筆 observations 具有相同 content hash（id=10, 20, 30）
- **THEN** 保留 id=10，刪除 id=20 和 id=30，輸出「移除 2 筆重複」

#### Scenario: 無重複時提示
- **WHEN** 本地所有 observations 的 content hash 都唯一
- **THEN** 輸出「無重複 observations」

#### Scenario: 無 observations 時提示
- **WHEN** 本地 claude-mem 資料庫無任何 observations
- **THEN** 輸出「本地無 observations」

### Requirement: Status 顯示去重統計

`ai-dev mem status` SHALL 增加顯示以下本地統計：
- Local observations 數量
- Local duplicates 數量（相同 hash 的多餘行數）
- Pulled hashes tracked 數量（pulled-hashes.txt 中的 hash 數）

#### Scenario: 有重複時顯示
- **WHEN** 本地有 100 筆 observations 其中 3 筆為重複
- **THEN** Status 顯示 Local observations: 100, Local duplicates: 3

#### Scenario: 有 pulled hashes 時顯示
- **WHEN** pulled-hashes.txt 中有 50 個 hash
- **THEN** Status 顯示 Pulled hashes tracked: 50

#### Scenario: 無 pulled-hashes.txt 時顯示 0
- **WHEN** pulled-hashes.txt 不存在
- **THEN** Status 顯示 Pulled hashes tracked: 0
