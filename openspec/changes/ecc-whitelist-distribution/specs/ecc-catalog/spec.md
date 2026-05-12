## ADDED Requirements

### Requirement: ecc-catalog.yaml 設定檔格式

系統 SHALL 維護 `upstream/ecc-catalog.yaml` 作為 ECC 上游 skill 的分類目錄。catalog 為純資料檔，不影響 runtime 分發行為，僅供人類審視與 audit 工具使用。

#### Scenario: 頂層結構

- **WHEN** 讀取 `upstream/ecc-catalog.yaml`
- **THEN** SHALL 包含 `version`（整數）、`last_synced`（ISO 日期字串）、`last_synced_ecc_commit`（git SHA，可為空字串）、`categories`（物件）

#### Scenario: categories 結構

- **WHEN** 解析 `categories` 區塊
- **THEN** 每個 category SHALL 為物件，包含 `description`（中文說明）與 `skills`（陣列）
- **THEN** `skills` 中每個項目 SHALL 為物件，包含 `name`（必填）、`added`（選填，ISO 日期）、`note`（選填，字串）

#### Scenario: uncategorized 特殊分類

- **WHEN** `categories.uncategorized` 存在
- **THEN** SHALL 視為「audit 偵測到 ECC 新增但未分類」的暫存區
- **THEN** SHALL 不參與分發決策（catalog 本身就不影響分發）
- **THEN** audit 工具 SHALL 將 NEW skill 預設歸入此 category

#### Scenario: catalog 缺漏不影響分發

- **WHEN** `upstream/ecc-catalog.yaml` 不存在或解析失敗
- **THEN** ECC 分發 SHALL 不受影響（白名單以 `distribution.yaml` 為準）
- **THEN** SHALL 在 audit 命令中提示需建立 catalog

### Requirement: ai-dev ecc audit 子命令

`ai-dev ecc audit` SHALL 偵測 ECC 來源目錄與 `ecc-catalog.yaml` 的差異，輸出建議 patch，不自動寫檔。

#### Scenario: 偵測 NEW skills

- **WHEN** ECC 來源目錄存在 skill 目錄，但其名稱未出現在 `ecc-catalog.yaml` 的任何 category 中
- **THEN** SHALL 標記為 `[NEW]`
- **THEN** SHALL 在建議 patch 中將該 skill 歸入 `uncategorized` category
- **THEN** SHALL 標註建議的 `added` 日期為當天

#### Scenario: 偵測 GONE skills

- **WHEN** `ecc-catalog.yaml` 中列出的 skill 名稱在 ECC 來源目錄不存在
- **THEN** SHALL 標記為 `[GONE]`
- **THEN** SHALL 顯示該 skill 原所屬 category
- **THEN** 建議 patch 應包含從 catalog 移除該項目的提示

#### Scenario: 偵測疑似 RENAMED

- **WHEN** 同時存在 NEW 與 GONE，且兩者名稱的 Levenshtein 距離 ≤ 3 或有共同前綴 ≥ 5 字元
- **THEN** SHALL 額外標記為 `[RENAMED?]`
- **THEN** SHALL 顯示「舊名 → 新名」並附距離數值，由人工確認

#### Scenario: 無差異時的行為

- **WHEN** ECC 來源與 catalog 完全一致
- **THEN** SHALL 印出「無差異」訊息
- **THEN** 退出碼 SHALL 為 0

#### Scenario: 有差異時的退出碼

- **WHEN** 偵測到任何 NEW、GONE 或 RENAMED?
- **THEN** 退出碼 SHALL 為 1（供 CI 偵測）
- **THEN** 命令本身 SHALL 不視為失敗（stderr 不輸出錯誤）

#### Scenario: 不自動寫檔

- **WHEN** `ai-dev ecc audit` 執行完成
- **THEN** SHALL 不修改 `ecc-catalog.yaml`
- **THEN** SHALL 不修改 `distribution.yaml`
- **THEN** SHALL 將建議 patch 印到 stdout，由使用者自行貼上

#### Scenario: ECC 來源目錄不存在

- **WHEN** 執行 `ai-dev ecc audit` 但 `~/.config/everything-claude-code/` 不存在
- **THEN** SHALL 印出錯誤訊息提示先執行 `ai-dev update`
- **THEN** 退出碼 SHALL 為 2

### Requirement: install / clone 時的 catalog 落後警告

`ai-dev install`、`ai-dev clone`、`ai-dev update` 在執行 ECC 分發前 SHALL 進行廉價檢查（只比較 skill 目錄名稱集合），若偵測到 catalog 落後，印出非阻塞警告。

#### Scenario: 偵測 catalog 落後

- **WHEN** ECC 來源中存在某個 skill 目錄名稱未出現在 `ecc-catalog.yaml` 的任何 category
- **THEN** SHALL 在標準輸出印出黃色警告：「ECC 上游新增 N 個 skill 未在 ecc-catalog.yaml 審視（預設不分發），執行 `ai-dev ecc audit` 查看詳情」
- **THEN** SHALL 繼續執行原命令（非阻塞）

#### Scenario: catalog 不存在

- **WHEN** `upstream/ecc-catalog.yaml` 不存在
- **THEN** SHALL 印出一次性提示：「建議建立 upstream/ecc-catalog.yaml 以追蹤 ECC skill 變動」
- **THEN** SHALL 不阻塞分發

#### Scenario: 無 ECC 來源

- **WHEN** `~/.config/everything-claude-code/` 不存在
- **THEN** SHALL 跳過 catalog 落後檢查
