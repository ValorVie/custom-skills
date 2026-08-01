# 知識庫目錄與索引規則

## 目標

當文件數量增加時，同時保留兩種查找方式：

- 我現在要執行、理解、規劃，還是查證過去的結果？
- 我正在處理哪一個服務、產品或技術主題？

目錄只能提供一個主要排列順序。另一個視角用索引與 metadata 提供，不複製、鏡像或 symlink 同一份文件。

## 推薦結構

預設採用「文件用途優先、穩定主題其次」：

```text
docs/
├── INDEX.md
├── architecture.md
├── external-references/
│   └── <topic>/
├── maintenance/
│   └── <topic>/
├── report/
│   └── <topic>/
├── guide/
│   └── <topic>/
├── research/
│   └── <topic>/
├── plans/
│   └── <topic>/
├── runbook/             # 只在專案已分離 runbook 時使用
│   └── <topic>/
└── superpowers/         # 只放明確由 Superpowers 工作流產生的工件
```

不要預先建立全部目錄。沿用專案現有的單複數命名，例如 `plan/` 或 `plans/`、`external-reference/` 或 `external-references/`。
`<type>` 代表目錄的文件用途，不是直接把 `report/investigation` 這類 frontmatter 複合值轉成兩層路徑。

## 兩種方案的取捨

| 方案 | 優點 | 主要問題 | 適用情境 |
|------|------|----------|----------|
| `<topic>/<type>/` | 同一主題的所有資料集中，服務負責人容易瀏覽 | 每個主題重複一套目錄；共用文件難放；跨主題查所有 runbook 或 report 較麻煩 | 各主題幾乎是獨立產品、讀者群與維護團隊很少重疊 |
| `<type>/<topic>/` | 文件用途清楚；所有執行指南、報告或計畫有固定位置；容易定義保留與審閱規則 | 若第二層主題過寬，會形成新的雜物區；同主題文件會分散在多個類型 | 共用同一 repo 與維運流程、需要按工作目的快速導航的工程知識庫 |

對一般工程 repo，預設選擇第二種。若某主題對使用者而言已是獨立產品，可以在該專案中改採第一種，但不要在同一層混用兩種主軸。

## 文件用途定義

| 目錄 | 回答的問題 | 內容邊界 |
|------|--------------|----------|
| `external-references/` | 外部資料原文是什麼？ | 保留來源與原始格式；不為了統一 frontmatter 改寫原檔 |
| `maintenance/` | 這個 repo 或服務長期怎麼維護？ | 維護原則、清單、盤點與定期作業；不取代一次性執行報告 |
| `report/` | 某個時點發生、調查或驗證了什麼？ | 保留證據、結果與限制；原則上不改寫歷史結論 |
| `guide/` | 如何完成一個目標？ | 可操作、可驗證的步驟；背景只留執行所需的最少說明 |
| `research/` | 這個問題有哪些外部證據、可能性與未知？ | 探索型分析與資料整理；尚未代表專案決策 |
| `plans/` | 接下來打算做什麼？ | 未來工作、依賴、驗收與停止點；不把已執行結果當成計畫 |
| `runbook/` | 某項可能高風險或重複操作如何安全執行？ | 前置檢查、影響邊界、完整指令、成功條件、停止點、驗證與 rollback；專案未分離時可放 `guide/` |
| `superpowers/` | 明確啟用的 Superpowers 流程產生了什麼？ | 只放該工作流的 plan、spec、design 或 report；不是通用文件型別 |

`tutorial`、`record`、`standard`、`adr` 等專案既有類型可繼續使用。不要為了統一外觀而破壞現有慣例。

## 主題命名

主題應該是讀者可預期長期查找的領域、服務或工作流，例如：

- `image-cdn`
- `mysql84-migration`
- `register`
- `observability`
- `deployment-auth`

避免：

- `misc`、`other`、`temp`、`new`。
- 只用 repo 名作為所有問題的統一主題。
- 用單次 ticket、日期或階段名稱作為長期主題。
- 同義名稱並存，例如 `mysql-upgrade`、`mysql84`、`db-migration`同時代表同一件事。

若一份文件同時關聯多個主題，路徑放在「誰會長期維護它」的主要主題，其他關聯放在 `related_topics` 或 `tags`，不建立副本。

## 何時分目錄與建索引

先保持簡單。出現以下任一情況再分類：

- 同一清單超過約 7 項，已難以一眼掃過。
- 同一主題在某種文件類型下累積多份文件。
- 同一主題跨越三種以上文件用途，需要一個總覽入口。
- 文件帶有 artifacts 或其他必須共同管理的附件。

索引分兩層：

1. `docs/INDEX.md` 提供專案級導航，以主題為主，連結到各類文件的穩定入口。
2. `docs/<type>/<topic>/INDEX.md` 只在該目錄已有多份文件時建立，用「目前有效」、「執行中」、「歷史證據」或其他符合主題的小節分組，不要只產生無說明的長清單。

新增文件時，更新最近且能幫讀者找到它的索引；不必機械式改寫每一層索引。

## 檔名與生命週期

| 文件性質 | 檔名 | 維護方式 |
|----------|--------|----------|
| 時點證據 | `YYYYMMDDhh-NN-<title>.md` | 保留歷史，後續結果建新文件並串接關係 |
| 長期真相或入口 | `<stable-name>.md` | 在原檔更新，依 Git 保留歷史 |
| 已被取代的長期文件 | 保留原名或移入專案已有 archive | 標記 `status: superseded` 與 `superseded_by`，不讓讀者誤用 |

時點證據包含調查、階段、事件、會議、執行結果與短期計畫。長期入口包含架構、規範、索引、狀態看板、參考手冊與會持續更新的 runbook。

## Frontmatter 建議

保留原有必填欄位，大型知識庫再增加少量可檢索 metadata：

```yaml
---
title: MySQL 8.4 店家遷移操作指南
type: guide
topic: mysql84-migration
status: active
date: 20260801
author: Team
related_topics:
  - cloud-sql
---
```

只使用專案會真正維護與搜尋的欄位。不建立完整 taxonomy 後卻沒有索引、檢查或維護流程。

## 既有知識庫調整原則

- 從新文件開始套用新規則。
- 只在本次已需要修改的文件上補 metadata 或更新索引。
- 不為了目錄整齊批次搬移歷史文件。
- 必須搬移時，先用全 repo 搜尋找出內部連結，使用 Git rename，再驗證舊路徑沒有殘留引用。

## 外部依據

- [Diátaxis](https://diataxis.fr/) 將技術文件依讀者需求區分為 tutorial、how-to、reference 與 explanation，重點是避免不同用途混在同一份文件。
- [Diátaxis in complex hierarchies](https://diataxis.fr/complex-hierarchies/) 明確說明文件類型與主題會形成二維問題，不需把方法誤解為必須強制套用的固定四格目錄。該文也建議過長的內容清單應拆分成較小分組並由 landing page 提供脈絡。

## 快速決策流程

```text
先讀專案慣例與 docs/INDEX.md
  -> 判定文件用途
  -> 選擇穩定 topic
  -> 沿用 docs/<type>/<topic>/
  -> 判定是時點證據或長期入口
  -> 選擇時間戳或穩定檔名
  -> 更新最近的索引與取代關係
```
