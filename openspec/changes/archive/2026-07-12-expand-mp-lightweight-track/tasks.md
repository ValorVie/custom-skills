# Tasks: expand-mp-lightweight-track

## 1. 上游追蹤基準修正

- [x] 1.1 更新 `upstream/mattpocock-skills/mapping.yaml`：`mp-to-issues` 的 upstream_path 改為 `skills/engineering/to-tickets/`、`mp-to-prd` 改為 `skills/engineering/to-spec/`、excluded 的 `diagnose` 改為 `diagnosing-bugs`（路徑 `skills/engineering/diagnosing-bugs/`），並在各條 notes 記錄 rename 歷史
- [x] 1.2 在 `mapping.yaml` 的 excluded 區補記本輪評估不引入的技能與理由：`implement`（opsx:apply 覆蓋）、`code-review`（reviewer agents 覆蓋）、`handoff`（與 claude-mem 重疊，另案評估）、`domain-modeling`（行為併入 mp-grill-with-docs，不另立技能）
- [x] 1.3 更新 `upstream/mattpocock-skills/last-sync.yaml`：commit 改為 `391a270`，notes 補記本次審核範圍與 rename 對照

## 2. 回灌既有技能

- [x] 2.1 `skills/mp-to-issues/SKILL.md` 合併 blocking edges 行為：每張切片宣告阻擋來源（無阻擋者標示可立即開工）、輸出依依賴排序、說明 frontier 平行認領方式（對應 delta spec「Blocking edges declared」）
- [x] 2.2 `skills/mp-to-issues/SKILL.md` 合併 expand–contract 寬重構切法：判斷條件（影響面橫跨大量呼叫點、垂直切片無法保持綠燈）與三段切分規則（對應 delta spec「Wide refactor uses expand-contract」）
- [x] 2.3 `skills/mp-to-prd/SKILL.md` 合併 seam-first 步驟：輸出 brief 前提出建議測試 seam（優先沿用既有 seam、位置越高越好）、與使用者核對後才輸出，brief 的驗證方向引用已確認 seam（對應 delta spec「Seam confirmed before brief」）
- [x] 2.4 檢查 `skills/mp-grill-with-docs/SKILL.md` 的 CONTEXT.md/ADR 沉澱規則是否已對齊上游 `domain-modeling` 原語（詞彙挑戰、情境壓力測試、ADR 三條件），缺漏處補齊，不另立技能

## 3. 新增 mp-wayfinder

- [x] 3.1 建立 `skills/mp-wayfinder/SKILL.md`：改寫上游 `wayfinder`，含地圖結構（目的地、已決索引、尚未成形、範圍外）、四型子項目（research/prototype/grilling/task 與 AFK/HITL 對應）、每 session 一張與先認領後開工規則
- [x] 3.2 對齊本地出口：地圖與子項目放 GitHub issues（引用 `docs/agents/issue-tracker.md` 輔出口與 `docs/agents/triage-states.md` 狀態），結晶成果轉 OpenSpec change、地圖只留連結（對應 design D2）
- [x] 3.3 撰寫觸發語彙與邊界：description 收斂為使用者主動觸發；「已能寫 proposal」時明確拒絕並導向 `/opsx:new`

## 4. 新增 mp-prototype

- [x] 4.1 建立 `skills/mp-prototype/SKILL.md`：改寫上游 `prototype`，含 logic/UI 雙分支判斷與六條通則（丟棄式、一鍵執行、無持久化、略過打磨、外顯狀態、完成即捕捉）
- [x] 4.2 建立 `skills/mp-prototype/references/logic.md` 與 `references/ui.md`：改寫上游 LOGIC.md / UI.md 的分支細節
- [x] 4.3 對齊本地產物處置：原型 commit 到 `experiment/<topic>` 分支、對應工作項目留連結、main 不含原型（對應 design D5）

## 5. 工作流文件

- [x] 5.1 `docs/dev-guide/workflow/DEVELOPMENT-WORKFLOW.md` 新增輕量軌章節：路徑（mp-grill-with-docs 必要時 → mp-to-issues GitHub issue 出口 → superpowers TDD 直接實作 → code review）、三項準入條件、三軌對照表含本專案情境範例
- [x] 5.2 更新同文件快速參考表：加入 `mp-wayfinder`（探索期規劃）與 `mp-prototype`（設計驗證）條目，MP + OpenSpec 完整流程圖補上 wayfinder 前置分支
- [x] 5.3 更新 `docs/agents/mp-workflow.md`：職責清單納入 mp-wayfinder 與 mp-prototype、何時使用/不使用補上兩技能的邊界、確認 canonical 出口描述不變
- [x] 5.4 更新 `docs/agents/triage-states.md`：mp-triage 建議輕量軌時需說明三項準入條件判斷依據（對應 spec「分流時檢查準入」）

## 6. 驗證與收尾

- [x] 6.1 執行 `openspec validate expand-mp-lightweight-track` 確認 change 結構有效
- [x] 6.2 驗證分發來源就位：`skills/mp-wayfinder/SKILL.md`、`skills/mp-prototype/SKILL.md` 存在且 frontmatter 格式與既有 mp-* 一致；投影不入版控（40ab1f1 決策，見 design D7），實際分發待合併推送後由 `ai-dev clone` 產生
- [x] 6.3 更新 `CHANGELOG.md`：記錄第二批 mp-* 技能、回灌內容與輕量軌文件
- [x] 6.4 依 commit 訊息規範提交（英文類型 + 中文訊息，分主變更與知識庫記錄兩個 commit）
