# Personal Wiki Skill — 個人知識編譯

## 概述

Personal Wiki Skill 是一個 Claude Code skill，將個人資料（日記、筆記、訊息等）編譯成結構化的知識 wiki。它實作了 [LLM Wiki 設計哲學](2026040910-01-LLM-Wiki-設計哲學.md)中「LLM 增量建構持久 wiki」的核心理念，專門應用在個人知識領域。

核心定位：**你是一個作家，不是檔案管理員。** 讀懂每則記錄的意義，寫出捕捉理解的文章。wiki 是一張心智地圖。

## 前置條件

- Claude Code 環境
- 將 `SKILL.md` 放置於 `.claude/skills/wiki/` 目錄
- 準備好要匯入的資料檔案

## 快速開始

```bash
/wiki ingest        # 將原始資料轉為 markdown 條目
/wiki absorb all    # 將條目編譯成 wiki 文章
/wiki query <問題>  # 查詢 wiki 內容
```

## 指令總覽

| 指令 | 用途 | 說明 |
|------|------|------|
| `/wiki ingest` | 資料匯入 | 自動偵測格式，產生 Python 腳本，將每則記錄轉為獨立 markdown |
| `/wiki absorb [範圍]` | 編譯文章 | 核心步驟。將條目織入 wiki，而非機械歸檔 |
| `/wiki query <問題>` | 知識查詢 | 唯讀。以自然語言查詢 wiki |
| `/wiki cleanup` | 品質稽核 | 平行子代理批次審查文章結構、語調、引用密度 |
| `/wiki breakdown` | 擴展覆蓋 | 找出被提及但尚未建頁的實體，依引用次數建立新文章 |
| `/wiki status` | 狀態檢視 | 顯示吸收率、文章數量、最多連結的文章 |
| `/wiki rebuild-index` | 重建索引 | 重建 `_index.md` 和 `_backlinks.json` |
| `/wiki reorganize` | 結構重整 | 重新思考 wiki 的整體組織方式 |

## 目錄結構

```
your-project/
  data/                  # 原始資料（匯入後不修改）
  raw/entries/            # 每則記錄一個 .md（由 ingest 產生）
  wiki/                   # 編譯後的知識庫
    _index.md             # 主索引（含別名）
    _backlinks.json       # 反向連結索引
    _absorb_log.json      # 吸收記錄追蹤
    people/               # 目錄從資料中自然浮現
    projects/
    patterns/
    philosophies/
    ...
```

## 完整流程

### 步驟 1: 匯入資料 (ingest)

ingest 會自動偵測資料格式，產生 `ingest.py` 腳本。每則邏輯記錄轉為一個 markdown 檔案，存放於 `raw/entries/`。

支援的資料格式：

| 格式 | 來源 |
|------|------|
| Day One JSON | 日記應用程式匯出 |
| Apple Notes | 備忘錄匯出 (.html/.txt/.md) |
| Obsidian Vault | Obsidian 筆記庫 (.md 資料夾) |
| Notion Export | Notion 頁面匯出 (.md/.csv) |
| 純文字 / Markdown | 一般文字檔 |
| iMessage | 訊息匯出 (.csv/聊天記錄) |
| CSV / 試算表 | 表格資料 |
| Email | 電子郵件匯出 (.mbox/.eml) |
| Twitter/X | 社群媒體封存 (tweet.js) |

> 匯入腳本具冪等性。未知格式會自動分析結構並撰寫自訂解析器。

### 步驟 2: 編譯文章 (absorb)

核心步驟。逐條按時間順序處理條目，每則條目經過五個階段：

1. **閱讀** — 文字、frontmatter、附件圖片
2. **理解** — 這則記錄的「意義」，而非它包含的「事實」
3. **比對索引** — 與既有文章配對
4. **更新/建立文章** — 將新維度融入既有文章，或建立新頁面
5. **串連脈絡** — 跨條目辨識共通主題，為重複模式建立專頁

日期範圍格式：

| 範圍 | 範例 |
|------|------|
| 預設（最近 30 天） | `/wiki absorb` |
| 特定月份 | `/wiki absorb 2026-03` |
| 全部 | `/wiki absorb all` |

每處理 15 則條目執行一次檢查點：重建索引、稽核新文章數量、檢查品質。

### 步驟 3: 查詢知識 (query)

| 問法 | 查找範圍 |
|------|----------|
| 「告訴我關於 [某人]」 | `people/`、backlinks、相關文章 |
| 「[專案] 發生了什麼？」 | 專案文章、相關時期、決策 |
| 「為什麼 [某個決定]？」 | `decisions/`、`transitions/` |
| 「[主題] 的模式是什麼？」 | `patterns/`、`philosophies/` |

> query 只讀取 wiki 文章，不接觸 `raw/entries/`。

## 寫作規範

### 核心原則

- **語調**：維基百科風格 — 平實、客觀、百科式。直接引用承載情感重量
- **結構**：以主題組織，不按日期排列
- **引用**：每篇最多 2 段直接引用，選最有衝擊力的
- **連結**：文章間使用 `[[wikilinks]]`，frontmatter 中以 entry ID 標註來源
- **長度**：最短 15 行，人物頁 20-80 行，時代頁 60-100 行

### 禁止用語

破折號、浮誇詞（legendary、visionary）、社論語氣、修辭問句、漸進敘事（would go on to）。

### 文章結構依類型而異

| 類型 | 結構方式 |
|------|----------|
| person | 依角色/關係階段 |
| project | 依構想、開發、結果 |
| event | 發生了什麼（簡述）→ 為什麼重要（主體）→ 後果 |
| philosophy | 論點 → 如何發展 → 成敗 |
| pattern | 觸發 → 循環 → 嘗試打破 |
| decision | 情境 → 選項 → 推理 → 選擇 |

## 目錄分類

目錄從資料中自然浮現，不要預先建立。常見類型：

| 類別 | 目錄 | 內容 |
|------|------|------|
| 核心 | `people/` `projects/` `places/` `events/` | 人物、專案、地點、事件 |
| 媒體文化 | `books/` `films/` `music/` `games/` | 影響思維的文化作品 |
| 內在世界 | `philosophies/` `patterns/` `tensions/` | 思想、行為模式、內在矛盾 |
| 敘事結構 | `eras/` `transitions/` `decisions/` | 人生階段、轉折、關鍵決策 |
| 關係 | `relationships/` `mentorships/` `communities/` | 人際動態 |
| 工作策略 | `strategies/` `techniques/` `skills/` | 策略、技術、能力 |

## 進階用法

### 品質稽核 (cleanup)

以平行子代理批次（每批 5 篇）審查每篇文章。常見問題與修正：

| 問題 | 說明 | 修正方式 |
|------|------|----------|
| 日記式結構 | 段落以日期為標題 | 改為主題標題，日期移入內文或時間軸表格 |
| 內容重複 | 多篇文章描述同一事件 | 較短的保留完整描述，較長的精簡為摘要加連結 |
| Wikilink 缺失 | 平行生成的文章互不知道彼此 | 批次掃描並自動包裹 `[[wikilinks]]` |
| 孤立文章 | 反向引用為零 | 在相關主題文章中主動加入引用 |

### 擴展覆蓋 (breakdown)

掃描現有文章中提及但尚未建頁的具體實體（以「具名名詞測試」為準），依引用次數排序，批次建立新文章。加上 `--reorganize` 可重新分類錯放的文章。

### 大型 Vault 分層策略

處理大量檔案（如 4,000+ 的 Obsidian Vault）時，不建議一次全部匯入：

| 層級 | 目錄 | 價值 | 說明 |
|------|------|------|------|
| 第一層 | 個人資料 + 日記 | 高 | wiki 的核心骨架 |
| 第二層 | 工作文件 | 高 | 專案、事件、決策 |
| 第三層 | 技術知識 | 中 | 選擇性匯入有個人見解的筆記 |
| 第四層 | 參考資料 | 中低 | 外部參考，選擇性匯入 |
| 第五層 | 歷史存檔 | 低 | 等前面幾輪穩定後再處理 |

每輪完成後執行 `cleanup` 再繼續下一輪。

## 核心原則

1. **你是作家** — 理解記錄的意義，寫出捕捉理解的文章
2. **每則記錄都有歸宿** — 織入理解的脈絡，而非機械歸檔
3. **文章是知識，不是日記** — 綜合，不是摘要
4. **概念文章不可或缺** — 模式、主題、弧線讓 wiki 成為思想地圖
5. **廣度與深度兼顧** — 積極建頁，但每頁都要有實質內容
6. **結構是活的** — 合併、拆分、重命名，隨時進行

## 與 LLM Wiki 哲學的對應

| LLM Wiki 概念 | Personal Wiki Skill 實作 |
|---------------|--------------------------|
| 原始來源層 | `data/` 目錄（不可變） |
| Wiki 層 | `wiki/` 目錄（LLM 全權維護） |
| 模式定義層 | `SKILL.md`（定義行為規範與寫作標準） |
| 匯入操作 | `/wiki ingest` + `/wiki absorb` |
| 查詢操作 | `/wiki query` |
| 維護操作 | `/wiki cleanup` + `/wiki breakdown` |
| 索引 | `_index.md`（含別名匹配） |
| 日誌 | `_absorb_log.json`（追蹤吸收狀態） |

## 與 Graphify 的差異

| 面向 | Personal Wiki Skill | Graphify |
|------|-------------------|----------|
| 輸入類型 | 個人資料（日記、筆記、訊息） | 程式碼、文件、論文、圖片 |
| 輸出格式 | 敘事性 wiki 文章 (markdown + wikilinks) | 知識圖譜 (NetworkX + HTML 視覺化 + JSON) |
| 處理方式 | LLM 逐條閱讀、理解、綜合 | AST 確定性解析 + LLM 語意提取 |
| 核心價值 | 理解意義、建立敘事連結 | 發現結構、量化關係 |
| 適用場景 | 個人知識管理、人生回顧、研究累積 | 程式碼理解、架構審查、跨文件分析 |
| 維護方式 | 增量 absorb + 定期 cleanup | SHA256 快取 + `--update` 增量更新 |

兩者可以互補：Personal Wiki Skill 處理敘事性內容，Graphify 處理結構性內容。詳見 [Graphify 指南](Graphify-知識圖譜建構.md)。

## 相關資源

- [farzaa 原文 Gist](https://gist.github.com/farzaa/c35ac0cfbeb957788650e36aabea836d)
- [LLM Wiki 設計哲學](LLM-Wiki-設計哲學.md)
- [Graphify 知識圖譜指南](Graphify-知識圖譜建構.md)
