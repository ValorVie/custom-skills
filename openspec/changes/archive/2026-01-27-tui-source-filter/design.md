# Design: tui-source-filter

## Context

TUI 目前已有 Target 和 Type 兩個篩選器，Source 篩選器將遵循相同的 UI pattern。

現有架構：
- `app.py` 中的 `SkillManagerApp` 管理所有狀態
- `refresh_resource_list()` 負責根據篩選條件重新渲染清單
- `list_installed_resources()` 已回傳包含 `source` 欄位的資源資料

## Goals / Non-Goals

**Goals:**
- 在篩選列新增 Source 下拉選單
- 選擇來源後即時篩選資源清單
- 與現有 Target/Type 篩選器協同運作

**Non-Goals:**
- 多選來源（本次只支援單選或全選）
- 動態偵測可用來源（使用固定清單）
- 顯示各來源的資源數量統計

## Decisions

### D1: 來源清單使用固定配置

**選擇:** 硬編碼 `SOURCE_FILTER_OPTIONS` 常數

**理由:**
- 來源種類穩定，新增來源頻率極低
- 避免每次開啟 TUI 都掃描所有資源來動態建立清單
- 程式碼簡單，維護成本低

**替代方案:**
- 動態掃描：啟動慢、實作複雜
- 配置檔：對此簡單需求過度設計

### D2: 來源值使用縮寫

**選擇:** 內部值使用縮寫（uds, custom, obsidian, anthropic, ecc, user）

**理由:**
- 與現有 `list_installed_resources()` 回傳的 source 欄位相容
- 縮寫易於程式處理
- 顯示名稱與內部值分離，支援未來 i18n

### D3: 篩選邏輯放在 `refresh_resource_list()` 中

**選擇:** 在現有 `refresh_resource_list()` 中加入 source 篩選條件

**理由:**
- 遵循現有架構 pattern（Target/Type 也在此處理）
- 集中管理篩選邏輯
- 保持 `list_installed_resources()` API 不變

## Risks / Trade-offs

### R1: 來源清單與實際資源可能不一致

**風險:** 硬編碼清單可能漏掉未來新增的來源

**緩解:**
- 新增來源時同步更新 `SOURCE_FILTER_OPTIONS`
- 「All」選項永遠顯示所有資源，不受影響

### R2: 篩選器列可能過寬

**風險:** 三個篩選器加上 checkbox 可能超出畫面寬度

**緩解:**
- 使用較短的顯示名稱
- CSS 設定適當的 Select 寬度
- 測試不同終端機寬度

## Implementation Notes

修改範圍：
1. `app.py` - 新增 SOURCE_FILTER_OPTIONS、current_source 狀態、事件處理
2. `styles.tcss` - 調整篩選列樣式（如需要）

預估程式碼變更：~30 行
