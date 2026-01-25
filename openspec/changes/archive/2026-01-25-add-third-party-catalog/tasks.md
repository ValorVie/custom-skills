# Implementation Tasks

## 1. 目錄結構建立

- [x] 1.1 建立 `third-party/` 根目錄
- [x] 1.2 建立 `third-party/templates/` 存放文件模板
- [x] 1.3 建立 `third-party/catalog/` 存放各專案資訊
- [x] 1.4 建立 `third-party/README.md` 作為索引入口

## 2. 文件模板設計

- [x] 2.1 建立 `templates/project-entry.md` 專案資訊模板
  - 專案基本資訊(名稱、授權、GitHub 連結)
  - 功能概述與特色清單
  - 適用場景與目標使用者
  - 手動安裝指南
  - 與 custom-skills 的整合建議
- [x] 2.2 建立 `templates/evaluation-checklist.md` 評估檢查清單

## 3. wshobson/agents 專案資訊建立

- [x] 3.1 使用模板建立 `catalog/wshobson-agents.md`
- [x] 3.2 整理專案功能清單(108 代理、129 技能、72 工具)
- [x] 3.3 撰寫手動安裝指南(如何從 GitHub 取得並整合到自己環境)
- [x] 3.4 標註與 custom-skills 現有功能的對照(可選)

## 4. 索引文件建立

- [x] 4.1 撰寫 `third-party/README.md`
  - 說明第三方目錄的用途與範圍
  - 與 upstream/ 系統的關係
  - 所有已收錄專案的摘要表格
  - 如何提交新專案的指引
- [x] 4.2 建立資源分類體系(如:專案規模、主要功能領域)

## 5. 專案文件更新

- [x] 5.1 更新 `README.md` 加入第三方資源目錄說明
- [x] 5.2 更新 `openspec/project.md` 的目錄結構章節
- [x] 5.3 在 `docs/` 中建立使用指南(可選) - 未實作(資訊已包含在 third-party/README.md)

## 6. 驗證與測試

- [x] 6.1 驗證所有連結有效
- [x] 6.2 確認模板格式正確且易於使用
- [x] 6.3 檢查與現有 upstream/ 系統無衝突
- [x] 6.4 確認 .gitignore 未排除 third-party/ 目錄

## 7. 文件

- [x] 7.1 在 CHANGELOG.md 記錄新增功能
- [x] 7.2 撰寫提交訊息(使用繁體中文 Conventional Commits)
