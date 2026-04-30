# First Principles Thinking

系統化第一性原理分析框架：拆解問題到不可化約的事實，從根本重建解法。

## 來源

- **原始 repo**：<https://github.com/danyuchn/first-principles-skill>
- **上游**：<https://github.com/tt-a1i/first-principles-skill>（v0.2.0）
- **目前版本**：v0.3.0
- **授權**：MIT（沿用上游）

此 skill 從原始 repo 直接複製進來，未做修改。如需更新，請從原始 URL 重新拉取。

## 主要差異化

相對於上游，danyuchn 版本新增 **Phase 0「Delete First」**——分析「怎麼解」之前，先嘗試把需求整個刪掉。

> Elon Musk: *"All requirements are dumb to some degree. The stupidest thing is to optimize something that shouldn't exist."*

## 使用方式

觸發語（多語）：

- `/first-principles <檔案路徑>`
- 「這個架構設計合理嗎？」
- 「這個需求合理嗎？」/「先刪除」
- "challenge assumptions"
- "is there a better solution"

## 6 階段流程

| Phase | 名稱 | 核心 |
|-------|------|------|
| 0 | Delete First | 嘗試刪除需求本身 |
| 1 | Problem Essence | 抽離出核心問題 |
| 2 | Challenge Assumptions | 列出並挑戰每個假設 |
| 3 | Ground Truths | 找出不可化約的事實 |
| 4 | Reason Upward | 從 ground truth 重建解法 |
| 5 | Validate | 把每個決策追溯回 ground truth |

## 結構

```
first-principles/
├── SKILL.md                       # 主要 skill 定義（v0.3.0）
├── README.md                      # 本檔
├── LICENSE                        # MIT
├── references/
│   ├── elon-musk-examples.md      # SpaceX/Tesla 真實案例
│   └── software-examples.md       # 軟體工程應用
└── examples/
    └── architecture-review.md     # microservices 完整分析範例
```
