# Prime Agent statusline 可顯示資料指南

> 核對版本：Prime Agent 0.7.2，2026-08-12。
>
> 這份文件整理目前公開 Extension API 能安全取得的資料。它是能力清單與實作指南，不包含可直接載入的 Extension。

## 結論

Prime Agent 沒有 Claude Code `statusLine.command` 這類宣告式設定。statusline 要用 TypeScript Extension 實作。

目前版本還有一個容易誤判的地方：

- Prime Agent 的 `README.md` 明確說明內建 footer 預設為空。
- `FooterComponent.render()` 實際固定回傳 `[]`。
- `ctx.ui.setStatus()` 仍會把文字存入 `footerData`，但內建空 footer 不會把它畫出來。
- 要看見 statusline，應使用 `ctx.ui.setFooter()`；若要整合其他 Extension 的 `setStatus()`，再由 custom footer 呼叫 `footerData.getExtensionStatuses()`。

因此，單獨複製官方 `examples/extensions/status-line.ts` 在 Prime Agent 0.7.2 上可能沒有可見輸出。完整 custom footer 才是可靠做法。

## 可用的 UI 入口

| API | 顯示位置 | 目前行為 | 適用情境 |
|---|---|---|---|
| `ctx.ui.setFooter()` | 輸入框下方 | 完整取代內建 footer | 建立真正的 statusline，建議使用 |
| `ctx.ui.setStatus(key, text)` | 交由 footer 決定 | 只保存狀態；預設空 footer 不顯示 | 讓多個 Extension 提供狀態，再由 custom footer 彙整 |
| `ctx.ui.setWidget(..., { placement: "belowEditor" })` | 輸入框下方、footer 上方 | 可見，可多行 | 狀態內容太長、不適合塞成一行時 |
| `ctx.ui.setWorkingMessage()` | 回應生成中的 loader | 只在串流期間出現 | 顯示目前工作階段，不是常駐 statusline |
| `ctx.ui.setWorkingIndicator()` | 回應生成中的 loader | 可換圖示、動畫或隱藏 | 調整工作中提示，不承載 session 統計 |
| `ctx.ui.setTitle()` | Terminal 視窗或分頁標題 | 改 Terminal title | 顯示專案或 session 名稱的輔助位置 |

`setFooter()` 一次只能有一個生效。若多個 Extension 都呼叫它，最後設定者會取代前一個 footer。較好的組合方式是由其他 Extension 使用 `setStatus()`，再由單一 footer 統一渲染。

## 直接可取得的資料

### Extension context

每個事件 handler 都會收到 `ctx: ExtensionContext`。下列資料不需執行外部命令。

| 可顯示資訊 | API 或欄位 | 值與限制 |
|---|---|---|
| 工作目錄 | `ctx.cwd` 或 `ctx.sessionManager.getCwd()` | 可顯示完整路徑或只顯示最後一段；通常只顯示專案名稱較安全 |
| 是否有互動 UI | `ctx.hasUI` | print／部分 RPC 模式可能為 `false`；這些模式沒有可見 footer |
| 目前模型 | `ctx.model` | 沒有已選模型時為 `undefined` |
| Context 使用量 | `ctx.getContextUsage()` | 回傳 `tokens`、`contextWindow`、`percent` |
| Agent 是否閒置 | `ctx.isIdle()` | `false` 代表正在處理，但不等於能取得精確工作名稱 |
| 是否有待處理訊息 | `ctx.hasPendingMessages()` | 只有布林值，沒有公開的 queue 長度 |
| Session 名稱 | `ctx.sessionManager.getSessionName()` 或 `pi.getSessionName()` | 使用者尚未命名時為 `undefined` |
| Session ID | `ctx.sessionManager.getSessionId()` | 技術上可顯示；通常不值得占用狀態列空間 |
| Session 檔案 | `ctx.sessionManager.getSessionFile()` | in-memory session 可能為 `undefined`；不建議預設顯示完整私人路徑 |
| Session 目錄 | `ctx.sessionManager.getSessionDir()` | 可用，但同樣不建議顯示完整路徑 |
| 目前 branch leaf | `getLeafId()`、`getLeafEntry()` | 適合除錯 session tree，不適合一般狀態列 |
| Session header | `ctx.sessionManager.getHeader()` | 可取得原始 `cwd`、parent session、`rlmDepth` 與建立時 Git 快照 |
| Session branch／entries | `getBranch()`、`getEntries()` | 可衍生訊息、token、費用、工具與 compaction 統計 |
| Abort 狀態 | `ctx.signal?.aborted` | 只有 Agent 執行期間通常才有 signal；適合除錯，不等於一般 working 狀態 |
| Effective system prompt | `ctx.getSystemPrompt()` | 技術上可讀，但可能含規則、路徑與私人脈絡，禁止放進 statusline |

### Extension API 與 model registry

除了事件 context，Extension factory 的 `pi` 與 `ctx.modelRegistry` 也能提供摘要資料。

| 可顯示資訊 | API | 限制 |
|---|---|---|
| 目前 thinking level | `pi.getThinkingLevel()` | 最直接且會反映目前值 |
| Session 名稱 | `pi.getSessionName()` | 未命名時為 `undefined` |
| 已啟用工具名稱／數量 | `pi.getActiveTools()` | 是允許模型使用的工具清單，不是此刻正在執行的工具 |
| 所有已設定工具 | `pi.getAllTools()` | 含參數 schema 與來源 metadata，狀態列通常只需要數量 |
| Slash command 清單／數量 | `pi.getCommands()` | 適合除錯 Extension 載入，不建議常駐列出名稱 |
| 自訂 CLI flag | `pi.getFlag(name)` | 只能讀取已由 Extension 註冊的 flag |
| 所有模型／模型數 | `ctx.modelRegistry.getAll()` | 可能很多，只顯示數量或經篩選結果 |
| 有 auth 設定的模型 | `ctx.modelRegistry.getAvailable()` | 是快速本機檢查，不代表 provider 當下健康 |
| Provider 顯示名稱 | `ctx.modelRegistry.getProviderDisplayName()` | 可把內部 provider ID 轉成顯示名稱 |

不要為了 statusline 呼叫 `getApiKeyAndHeaders()`、`getApiKeyForProvider()` 或其他 credential 解析 API。這些方法不是顯示用途，也可能取得敏感值或觸發額外工作。

### 模型資料

`ctx.model` 的公開欄位如下。

| 欄位 | 可顯示內容 | 備註 |
|---|---|---|
| `id` | 模型 ID | statusline 最常用，通常比 `name` 短 |
| `name` | 顯示名稱 | 終端寬度足夠時使用 |
| `provider` | Provider 名稱 | 可與模型 ID 組成 `provider/model` |
| `api` | API 類型 | 例如 Anthropic Messages 或 OpenAI Responses 的內部識別值 |
| `reasoning` | 是否支援 reasoning | 只是能力，不代表目前 thinking level |
| `thinkingLevelMap` | 模型支援的 thinking level 映射 | 適合除錯，不建議整段顯示 |
| `input` | 支援 `text`／`image` | 可顯示是否支援圖片 |
| `contextWindow` | 模型 context window 上限 | 是模型容量，不是目前用量 |
| `maxTokens` | 單次最大輸出 token | 不是剩餘 context |
| `cost` | input／output／cache 費率 | 單位為每百萬 token；不是本 session 已花費金額 |
| `baseUrl` | Provider endpoint | 技術上可讀，但可能暴露內部服務位置，不建議顯示 |
| `headers` | 自訂 HTTP headers | 可能含 credential，禁止顯示或寫入 log |

目前 thinking level 應使用 `pi.getThinkingLevel()`，可能值為：

```text
minimal · low · medium · high · xhigh · max
```

模型不一定支援全部等級。Prime Agent 會依模型能力限制實際值。

### Context 使用量

`ctx.getContextUsage()` 回傳：

```typescript
interface ContextUsage {
  tokens: number | null;
  contextWindow: number;
  percent: number | null;
}
```

建議顯示 `percent`，例如 `ctx:37%`。需要注意：

- 沒有模型或 context window 無效時，整個結果可能是 `undefined`。
- compaction 完成後、下一個有效模型回應前，`tokens` 與 `percent` 會是 `null`。
- 這是目前送入模型的 context 估算，不是 session 累積 token。
- 互動模式會嘗試把正在串流的輸出加入估算，但仍應視為即時估計值。

### Footer 專用資料

`ctx.ui.setFooter()` 的第三個參數是 `ReadonlyFooterDataProvider`。

| API | 內容 | 反應方式 |
|---|---|---|
| `getGitBranch()` | Git branch；非 repo 為 `null`，detached HEAD 為 `"detached"` | 內建 cache |
| `onBranchChange(callback)` | branch 或工作目錄變化通知 | 回傳 unsubscribe，應在 `dispose()` 呼叫 |
| `getExtensionStatuses()` | 所有 `ctx.ui.setStatus(key, text)` 狀態 | `ReadonlyMap<string, string>` |
| `getAvailableProviderCount()` | 目前有可用模型的唯一 provider 數量 | 是 provider 數，不是模型數 |

`footerData` 只直接提供 Git branch，不提供 dirty、ahead、behind、stash 數或目前 commit。這些資訊需要另行執行 Git 命令。

## 可從 session 衍生的資料

`ctx.sessionManager.getBranch()` 回傳目前 branch 從 root 到 leaf 的 entries。statusline 可在 `render()` 時做輕量統計。

| 可衍生資訊 | 來源 | 計算注意事項 |
|---|---|---|
| User／assistant 訊息數 | `message` entries 的 `message.role` | Tool result 也是獨立 message role |
| Tool call 數 | assistant message 的 `content[type="toolCall"]` | 不要只算 tool result，失敗或中斷時可能不對稱 |
| Tool result 與錯誤數 | `toolResult` message 的 `isError` | 可顯示最近錯誤或總錯誤數 |
| 累積 input token | `assistantMessage.usage.input` | 對所有 assistant message 加總 |
| 累積 output token | `assistantMessage.usage.output` | 對所有 assistant message 加總 |
| Cache read／write token | `usage.cacheRead`、`usage.cacheWrite` | 可評估 prompt cache 使用情況 |
| Session 累積 token | input + output + cacheRead + cacheWrite | 這是 Prime Agent `SessionStats` 採用的算法；不要和 context 使用量混用 |
| Session 估算費用 | `assistantMessage.usage.cost.total` 加總 | 是 client 依模型費率計算的估值，不是帳單真相來源 |
| 目前模型紀錄 | 最後一個 `model_change` entry | 可避免 footer 捕捉舊 event context 後顯示舊模型 |
| Fast mode | 最後一個 `service_tier_change` entry | `serviceTier === "priority"` 代表目前 `/fast` 為開啟狀態 |
| Thinking level 歷史 | `thinking_level_change` entries | 目前值直接用 `pi.getThinkingLevel()` 較簡單 |
| Compaction 次數 | `compaction` entries | 可另顯示最後一次的 `tokensBefore` |
| Session tree 深度／分支 | `getTree()`、entry parent 關係 | 計算較重，通常不適合每次 render |
| Session label | `getLabel(entryId)` 或 tree node label | 適合顯示目前 bookmark |
| Agent 最近摘要 | 最後一個 `agent_status` entry | 有 `summary` 與 `taskState`，但不保證每個互動 session 都會產生 |
| RLM 深度 | `getHeader()?.rlmDepth` | 代表 spawn depth，不是目前活躍子 Agent 數量 |
| Parent session | `getHeader()?.parentSession` | 適合除錯；可能包含私人檔案路徑 |
| 最後停止原因 | 最後一個 assistant message 的 `stopReason` | `stop`、`length`、`toolUse`、`error`、`aborted` |

RLM child usage 已折入 parent assistant message 的 aggregate usage。若同時再把 `child_usage_attributed` entry 加到總數，會重複計算。

## 可透過事件自行追蹤的資料

以下資料不是單一 getter，但可以在 Extension 內維護少量 state，再要求 TUI 重新渲染。

| 可追蹤資訊 | 建議事件 |
|---|---|
| Agent working／idle | `agent_start`、`agent_end` |
| Turn 編號與耗時 | `turn_start`、`turn_end` |
| 目前執行中的工具名稱與數量 | `tool_execution_start`、`tool_execution_end`，用 `toolCallId` 維護 `Map` |
| Tool 是否失敗 | `tool_execution_end.isError` |
| 串流中的 partial usage | `message_update` 的 assistant message |
| 最後回應時間與 stop reason | `message_end` 或 `turn_end` |
| 模型切換 | `model_select` |
| Thinking level 切換 | `thinking_level_select` |
| Compaction 完成 | `session_compact` |
| Session reload／new／resume／fork | `session_start.reason` |

不要在 `render(width)` 裡執行 shell、網路請求或大量 tree traversal。`render()` 可能頻繁執行，應只讀取已快取資料並完成字串格式化。

## 可經外部命令補充的資料

這些資料可以顯示，但不是 Prime Agent statusline API 直接提供的。

| 資訊 | 取得方式 | 建議 |
|---|---|---|
| Git dirty／ahead／behind／commit | `git status --porcelain=v2 --branch` 等 | 在事件或低頻 timer 非同步更新；不要每次 render 執行 Git |
| Beads issue／工作狀態 | `bd show`、`bd ready` 等 | 只保存簡短摘要，不要把完整 issue 描述塞入 footer |
| 時鐘 | `Date` | 每秒更新會持續重繪；通常每 30–60 秒已足夠 |
| 主機名、CPU、load、memory | Node `os` 標準函式庫 | 先確認真的有操作需求，避免把 statusline 變成監控面板 |
| Prime Agent 版本 | package metadata 或 `prime-agent --version` | 啟動時查一次並快取 |
| 自訂工作模式 | Extension 自己的 state | 用 `setStatus()` 發布給共用 footer 最合適 |
| Provider quota／rate limit | Provider response headers 或額外 API | 沒有統一公開格式；不要假設所有 provider 都能取得 |

若使用 `pi.exec()` 查外部資料，應在事件 handler 或受控 timer 執行，設定 timeout，失敗時保留舊值或顯示未知。不要在狀態列暴露命令輸出原文。

## 目前沒有穩定公開 API 的資訊

Prime Agent 互動 UI 內部雖然持有更多狀態，但 Extension API 0.7.2 沒有正式暴露下列資料：

- 精確的 pending message queue 長度；公開 API 只有 `hasPendingMessages()`。
- 目前活躍子 Agent 數量、名稱與個別 context。
- Goal 的完整狀態與使用量。
- Heartbeat 清單與下一次執行時間。
- 自動 retry 次數與倒數。
- 內建 activity tracker 的精確分類與 in-flight token counter。
- Provider 帳戶剩餘 quota、信用額度或真實帳單。
- Git dirty、ahead／behind、stash 與 commit；`footerData` 只有 branch。

不建議直接 import `prime-agent/dist/...` 私有模組取得這些欄位。內部路徑與物件不是 Extension 相容性契約，升級後容易失效。若某項狀態很重要，優先使用公開事件自行追蹤，或等待 Prime Agent 提供正式 API。

## 不應顯示的內容

即使技術上可以讀取，也不應放進 statusline：

- API key、OAuth token、cookie、credential 或 `model.headers`。
- 完整 system prompt、使用者 prompt、工具參數或工具結果。
- 可能含帳號、店家、專案機密的完整絕對路徑。
- Provider response headers 原文。
- Session JSONL 內容、原始錯誤 payload 或環境變數全集。

狀態列會長時間留在畫面，也可能被 terminal scrollback、截圖或錄影保存。只顯示短、低敏感度、對當下操作有用的摘要。

## 建議的預設內容

一行狀態列的實用順序：

```text
model · effort/fast · project:branch · ctx% · session tokens/cost · working/tool · extension statuses
```

例如：

```text
gpt-5.4 · high/fast · custom-skills:main · ctx:37% · tok:128k/$0.42 · idle · bead:6bo
```

窄終端建議依序移除：

1. Session token 與費用。
2. Extension statuses。
3. project，只保留 branch。
4. thinking level，只保留 model、context 與 working state。

所有輸出都要使用 `truncateToWidth()`，不能用字串長度直接裁切含 ANSI 色碼或寬字元的內容。

## 最小 custom footer 範例

下面範例顯示：目前模型、thinking level、fast mode、專案、Git branch、context、session 累積 token／費用、working 狀態，以及其他 Extension 用 `setStatus()` 發布的內容。

```typescript
import path from "node:path";
import type { AssistantMessage } from "@earendil-works/pi-ai";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { truncateToWidth } from "@earendil-works/pi-tui";

function compactNumber(value: number): string {
  if (value < 1_000) return String(value);
  if (value < 1_000_000) return `${(value / 1_000).toFixed(1)}k`;
  return `${(value / 1_000_000).toFixed(1)}m`;
}

export default function (pi: ExtensionAPI) {
  pi.on("session_start", async (_event, ctx) => {
    ctx.ui.setFooter((tui, theme, footerData) => {
      const requestRender = () => tui.requestRender();
      const unsubscribe = footerData.onBranchChange(requestRender);

      return {
        dispose: unsubscribe,
        invalidate() {},

        render(width: number): string[] {
          // ponytail: 最小範例每次 render 掃描 branch；長 session 應改為事件增量快取。
          const branch = ctx.sessionManager.getBranch();
          let model = ctx.model?.id ?? "no-model";
          let fast = false;
          let tokens = 0;
          let cost = 0;

          for (const entry of branch) {
            if (entry.type === "model_change") model = entry.modelId;
            if (entry.type === "service_tier_change") {
              fast = entry.serviceTier === "priority";
            }
            if (entry.type === "message" && entry.message.role === "assistant") {
              const message = entry.message as AssistantMessage;
              tokens +=
                message.usage.input +
                message.usage.output +
                message.usage.cacheRead +
                message.usage.cacheWrite;
              cost += message.usage.cost.total;
            }
          }

          const context = ctx.getContextUsage();
          const contextText =
            context?.percent == null ? "ctx:?" : `ctx:${Math.round(context.percent)}%`;
          const project = path.basename(ctx.sessionManager.getCwd());
          const gitBranch = footerData.getGitBranch();
          const working = ctx.isIdle() ? "idle" : "working";
          const pending = ctx.hasPendingMessages() ? "+queued" : "";

          const base = [
            model,
            `${pi.getThinkingLevel()}${fast ? "/fast" : ""}`,
            gitBranch ? `${project}:${gitBranch}` : project,
            contextText,
            `tok:${compactNumber(tokens)}/$${cost.toFixed(2)}`,
            `${working}${pending}`,
          ];

          const separator = theme.fg("dim", " · ");
          const line = [
            theme.fg("dim", base.join(" · ")),
            ...footerData.getExtensionStatuses().values(),
          ].join(separator);

          return [truncateToWidth(line, width)];
        },
      };
    });
  });
}
```

這個範例刻意不執行外部命令，也不顯示完整路徑或敏感資料。它為了保持短小，每次 render 都掃描目前 branch；session 很長時，應改在 `turn_end`、`session_compact` 與 `session_start` 更新 usage 快取。若要加上目前工具名稱、turn 耗時或 Git dirty，也應另外維護快取狀態，不要把命令塞進 `render()`。

## 安裝與驗證

未來若在此目錄加入 `index.ts`，可把整個目錄複製到使用者層或專案層 Extension 路徑：

```text
~/.prime/agent/extensions/statusline/
<project>/.prime/agent/extensions/statusline/
```

Prime Agent 直接透過 jiti 載入 TypeScript，不需事先編譯。安裝後執行：

```text
/reload
```

手動驗證至少涵蓋：

1. 一般 session 能看見一行 footer，窄終端不破版。
2. 切換模型後 model ID 更新。
3. 執行 `/effort` 與 `/fast` 後狀態更新。
4. 完成一輪對話後 token、費用與 context 更新。
5. `/compact` 後允許暫時顯示 `ctx:?`，下一次模型回應後恢復數值。
6. Git branch 切換後 footer 更新；非 Git 目錄不顯示 branch。
7. 其他 Extension 呼叫 `setStatus()` 後，文字能出現在 custom footer。
8. `/reload`、`/new`、resume 與 fork 後不殘留前一個 session 的 state。
9. 離開 session 或 reload 時，branch watcher 與自訂 timer 都已在 `dispose()` 清理。

需要核對 token、費用與 context 時，以 `/usage` 的輸出作為同一客戶端內的對照。真實費用仍以 provider 帳單為準。

## 來源

本文件以 Prime Agent 0.7.2 安裝包內的下列第一方檔案核對：

- `README.md`：內建 footer 預設為空，`/usage` 顯示 token、費用與 context。
- `docs/extensions.md`：Extension UI、事件、`setStatus()` 與 `setFooter()`。
- `docs/tui.md`：persistent status、custom footer 與 component pattern。
- `examples/extensions/status-line.ts`：官方 `setStatus()` 範例。
- `examples/extensions/custom-footer.ts`：官方 custom footer、usage 與 Git branch 範例。
- `dist/modes/interactive/components/footer.js`：Prime 品牌 footer 的 `render()` 固定回傳空陣列。
- `dist/core/extensions/types.d.ts`：`ExtensionAPI`、`ExtensionContext`、`ContextUsage` 與所有公開事件型別。
- `dist/core/footer-data-provider.d.ts`：custom footer 可讀取的 Git branch、Extension statuses 與 provider count。
- `dist/core/session-manager.d.ts`：read-only session manager、session entries 與 header 型別。
- `dist/core/agent-session.js`：`/session` token／費用加總及 context usage 算法。
- `@earendil-works/pi-ai/dist/types.d.ts`：`Model`、`Usage` 與 `AssistantMessage` 欄位。

Prime Agent 後續版本若恢復非空內建 footer，`setStatus()` 可能重新直接可見。升級後應先重查 `FooterComponent.render()` 與型別檔，再決定是否仍需要完整 custom footer。
