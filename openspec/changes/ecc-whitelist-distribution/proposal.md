## Why

目前 ECC（everything-claude-code）分發採黑名單機制：`distribution.yaml` 的 `exclude.skills` 列出不要的，其餘預設分發。實際使用後出現三個結構性問題：

- **預設分發 = 被動接受**：ECC 每次 upstream sync 都會悄悄帶入新 skill，需要事後人工 audit 才能追加 exclude（近一次偵測就有 53 個未審視已自動分發）。
- **控制邏輯反向**：想要的不需要列、不要的要列，與 review 直覺相反，新增 skill 時容易漏審。
- **沒有分類視角**：扁平 exclude 清單靠註解區分群組，無法批次切換、無法在審視時提供「這屬於哪一類」的上下文。

同時 `ecc-profile.yaml` 的 user-level include/exclude 是黑名單時代的補丁，白名單化後可一併簡化。

## What Changes

- **改為純白名單**：`distribution.yaml` 的 `distribute.skills` 改用扁平 `enabled: [...]` 清單，僅列出名稱即分發。
- **新增 ECC catalog（純資料）**：新增 `upstream/ecc-catalog.yaml`，記錄 ECC 上游所有 skill 的分類、加入日期、備註。catalog 純文件化，不參與 runtime 邏輯，僅作為人類審視 / 維護白名單時的參考。
- **新增 `ai-dev ecc audit` 子命令**：偵測 `~/.config/everything-claude-code/skills/` 與 `ecc-catalog.yaml` 的差異，輸出建議 patch（NEW / GONE / RENAMED?）。不自動寫檔，不掛 install/clone/update。
- **移除 `exclude.skills` 區塊**：白名單已能完整表達意圖，黑名單冗餘。
- **移除 `ecc-profile.yaml` 的 `include_skills` / `exclude_skills` 合併邏輯**：白名單就在 repo 內，跨機器需求由 git 解決。
- **預設拒絕未列入名單者**：ECC 新增 skill 預設**不分發**；install/clone 過程若偵測到 catalog 落後（ECC 有但 catalog 沒收錄）時，印出**非阻塞**的黃色警告引導使用者執行 `ai-dev ecc audit`。
- **初始白名單**：將目前實際被分發的 133 個 skill 全部加入 `enabled`，行為兼容，後續使用者自行調整。
- **commands / agents 暫不變動**：量小、變動少，保留現有 exclude 邏輯（YAGNI）。

## Capabilities

### Modified Capabilities

- `ecc-selective-distribution`：分發邏輯從黑名單改為白名單，`exclude.skills` 移除，`distribute.skills.enabled` 新增。

### New Capabilities

- `ecc-catalog`：ECC 上游 skill 清單與分類管理，提供 audit 工具偵測 catalog 與 ECC 實際內容的差異。
