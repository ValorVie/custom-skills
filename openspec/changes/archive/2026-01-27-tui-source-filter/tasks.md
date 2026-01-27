# Tasks: tui-source-filter

## 1. 新增來源篩選常數

- [x] 1.1 在 app.py 新增 `SOURCE_FILTER_OPTIONS` 常數，包含 All 及所有來源選項

## 2. 新增狀態管理

- [x] 2.1 在 `SkillManagerApp.__init__()` 新增 `self.current_source = "all"` 狀態

## 3. 修改介面佈局

- [x] 3.1 在 `compose()` 方法的 filter-bar 中新增 Source Label 和 Select 元件

## 4. 實作事件處理

- [x] 4.1 在 `on_select_changed()` 中新增 `source-select` 的處理邏輯

## 5. 實作篩選邏輯

- [x] 5.1 在 `refresh_resource_list()` 中新增 source 篩選條件

## 6. 驗證

- [x] 6.1 啟動 TUI 確認 Source 下拉選單顯示正確
- [x] 6.2 測試選擇不同來源後清單正確篩選
- [x] 6.3 測試與 Target/Type 組合篩選
