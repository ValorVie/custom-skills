import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { Type } from "typebox";

import { readFileSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

import {
	AccessGate,
	AccessGateError,
	appendAccessLog,
	collectCandidates,
	compileBlacklist,
	findBlacklistMatches,
	normalizePath,
	type AccessLogEntry,
	type Clock,
	type CompiledBlacklist,
	type PendingRequest,
} from "./policy.ts";

type ExtensionOptions = {
	configPath?: string;
	accessLogPath?: string;
	home?: string;
	clock?: Clock;
	randomUUID?: () => string;
	appendRecord?: (entry: AccessLogEntry) => void;
};

const defaultConfigPath = fileURLToPath(new URL("./blacklist.json", import.meta.url));
const recordToolName = "record_path_access";

function loadBlacklist(path: string): CompiledBlacklist {
	return compileBlacklist(JSON.parse(readFileSync(path, "utf8")) as unknown);
}

function formatRequestPrompt(request: PendingRequest, suggestedAccessTime: string): string {
	const lines = request.matches.map((match) => {
		const label = match.rule.level === "block" ? "禁止" : "警告";
		return `- [${label}][${match.rule.id}] ${match.rule.message}`;
	});
	return [
		"PATH_ACCESS_SOFT_BLOCKED：本次工具呼叫尚未執行。",
		...lines,
		`access ID：${request.accessId}`,
		`存取位置：${request.location}`,
		`記錄期限：${new Date(request.confirmUntilWall).toISOString()}`,
		"若已確認規範且決定繼續，請先呼叫 record_path_access，成功後再重新發出原存取。",
		"必要欄位：",
		`- accessId: ${request.accessId}`,
		`- accessTime: ${suggestedAccessTime}（RFC 3339，請填呼叫工具當下時間）`,
		`- location: ${request.location}`,
		"- reason: 單行、去除前後空白後 1 至 30 個 Unicode 字元",
		"未完成有效記錄前，重試仍會被阻擋。不得以其他 API、shell、symlink、編碼或動態組合方式繞過。",
	].join("\n");
}

type StringLeaf = { key?: string; value: string };

function collectStringLeaves(
	value: unknown,
	key?: string,
	output: StringLeaf[] = [],
): StringLeaf[] {
	if (typeof value === "string") {
		output.push({ key, value });
		return output;
	}
	if (Array.isArray(value)) {
		for (const item of value) collectStringLeaves(item, key, output);
		return output;
	}
	if (value && typeof value === "object") {
		for (const [childKey, item] of Object.entries(value as Record<string, unknown>)) {
			collectStringLeaves(item, childKey, output);
		}
	}
	return output;
}

function inputTargetsAccessLog(input: unknown, accessLogPath: string, home: string): boolean {
	const normalizedLog = normalizePath(accessLogPath, home);
	const logSegments = normalizedLog.split("/").filter(Boolean);
	const logName = logSegments.at(-1) ?? "";
	const parentName = logSegments.at(-2) ?? "";
	const protectedSuffix = `/${parentName}/${logName}`;
	const strings = collectStringLeaves(input);
	const functionOperations =
		"open|openSync|readFile|readFileSync|writeFile|writeFileSync|appendFile|appendFileSync|unlink|unlinkSync|rm|rmSync|remove|rename|renameSync|copyFile|copyFileSync|chmod|chmodSync|chown|chownSync|truncate|truncateSync|stat|statSync|lstat|lstatSync";
	const methodOperations =
		"open|read_text|read_bytes|write_text|write_bytes|unlink|rename|chmod|chown|touch|stat|lstat|exists";
	const shellOperations = "cat|head|tail|less|more|sed|grep|awk|strings|xxd|hexdump|rm|mv|cp|chmod|chown|truncate|tee|shred";
	const directOperation = new RegExp(
		`\\b(?:${functionOperations}|${methodOperations})\\s*\\(|\\b(?:${shellOperations})\\s+|(?:^|\\s)(?:>|>>)\\s*`,
		"i",
	);

	const exactLogLeaves = strings.filter(
		({ value }) => normalizePath(value.trim(), home) === normalizedLog,
	);
	const directTargetKey = /^(?:path|file|filePath|filename|location|target|destination|source|uri)$/i;
	if (exactLogLeaves.some(({ key }) => key && directTargetKey.test(key))) return true;
	if (exactLogLeaves.length > 0 && strings.some(({ value }) => directOperation.test(value))) {
		return true;
	}

	const referencesProtectedLog = (source: string): boolean => {
		const candidates = collectCandidates(source, home);
		const hasParent = candidates.some((candidate) => candidate === parentName);
		const hasName = candidates.some((candidate) => candidate === logName);
		return (
			(hasParent && hasName) ||
			candidates.some(
				(candidate) =>
					candidate === normalizedLog || candidate.endsWith(protectedSuffix),
			)
		);
	};

	for (const { value: source } of strings) {
		const statements = source.split(/[;\n]/);
		if (
			statements.some(
				(statement) => referencesProtectedLog(statement) && directOperation.test(statement),
			)
		) {
			return true;
		}

		const taintedVariables: string[] = [];
		for (const statement of statements) {
			const assignment = statement.match(
				/^\s*(?:(?:const|let|var)\s+)?([A-Za-z_$][\w$]*)\s*=\s*(.+)$/,
			);
			if (assignment && referencesProtectedLog(assignment[2])) {
				taintedVariables.push(assignment[1]);
			}
		}
		for (const variable of taintedVariables) {
			const escaped = variable.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
			const taintedOperation = new RegExp(
				`(?:\\b(?:${functionOperations})\\s*\\(\\s*${escaped}\\b|` +
					`\\b${escaped}\\s*\\.\\s*(?:${methodOperations})\\s*\\(|` +
					`\\b(?:${shellOperations})\\s+(?:["']?\\$?${escaped}\\b))`,
				"i",
			);
			if (taintedOperation.test(source)) return true;
		}
	}
	return false;
}

export function createPathBlacklistExtension(options: ExtensionOptions = {}) {
	return function pathBlacklistExtension(pi: ExtensionAPI) {
		const home = options.home ?? homedir();
		const configPath = options.configPath ?? defaultConfigPath;
		const accessLogPath = normalizePath(options.accessLogPath ?? join(home, ".prime/access.log"), home);
		const wallNow = options.clock?.wallNow ?? (() => Date.now());
		let blacklist: CompiledBlacklist | undefined;
		let configError: string | undefined;

		try {
			blacklist = loadBlacklist(configPath);
		} catch (error) {
			configError = error instanceof Error ? error.message : String(error);
		}

		const gate = new AccessGate({
			clock: options.clock,
			randomUUID: options.randomUUID,
			home,
			appendRecord:
				options.appendRecord ?? ((entry) => appendAccessLog(accessLogPath, entry)),
		});

		pi.registerTool({
			name: recordToolName,
			label: "Record path access",
			description:
				"Record the access ID, current RFC 3339 time, exact prompted location, and a one-line 1–30 character reason. Use only after PATH_ACCESS_SOFT_BLOCKED.",
			promptGuidelines: [
				"When PATH_ACCESS_SOFT_BLOCKED is returned, call record_path_access before retrying the protected access.",
				"Copy the access ID and location exactly; keep reason to one line and at most 30 Unicode characters.",
			],
			executionMode: "sequential",
			parameters: Type.Object(
				{
					accessId: Type.String({ description: "Access ID from the soft-block prompt" }),
					accessTime: Type.String({ description: "Current RFC 3339 timestamp" }),
					location: Type.String({ description: "Exact normalized location from the prompt" }),
					reason: Type.String({ description: "One-line access reason, 1–30 Unicode characters" }),
				},
				{ additionalProperties: false },
			),
			async execute(_toolCallId, params) {
				if (configError || !blacklist) {
					throw new Error(`PATH_BLACKLIST_CONFIG_ERROR：${configError ?? "黑名單未載入"}`);
				}
				try {
					const entry = gate.record(params);
					return {
						content: [
							{
								type: "text",
								text:
									`PATH_ACCESS_RECORDED [${entry.access_id}]：已追加 ${accessLogPath}。` +
									`相同規則與位置放行至 ${entry.allowed_until}；請重新發出原存取。`,
							},
						],
						details: { entry },
					};
				} catch (error) {
					if (error instanceof AccessGateError) {
						throw new Error(error.message);
					}
					const detail = error instanceof Error ? error.message : String(error);
					throw new Error(`ACCESS_LOG_WRITE_FAILED：${detail}`);
				}
			},
		});

		pi.on("session_start", async (_event, ctx) => {
			gate.reset();
			if (configError && ctx.hasUI) {
				ctx.ui.notify(`路徑黑名單設定錯誤，工具將預設阻擋：${configError}`, "error");
			}
		});

		pi.on("session_compact", async (_event, ctx) => {
			gate.reset();
			if (ctx.hasUI) ctx.ui.notify("Context compaction 已清除路徑存取計時；後續命中將重新確認。", "info");
		});

		pi.on("session_shutdown", async () => {
			gate.reset();
		});

		pi.on("tool_call", async (event, ctx) => {
			if (event.toolName === recordToolName) return undefined;
			if (configError || !blacklist) {
				return {
					block: true,
					reason:
						`PATH_BLACKLIST_CONFIG_ERROR：${configError ?? "黑名單未載入"}。` +
						`本次工具呼叫未執行；請修正 ${configPath} 後執行 /reload。`,
				};
			}
			if (inputTargetsAccessLog(event.input, accessLogPath, home)) {
				return {
					block: true,
					reason:
						`ACCESS_LOG_PROTECTED：${accessLogPath} 只能由 ${recordToolName} 追加有效紀錄；` +
						"一般工具不得直接讀取、覆寫、截斷或刪除。",
				};
			}

			const matches = findBlacklistMatches(event.input, blacklist, home);
			if (matches.length === 0) return undefined;
			const decision = gate.check(matches, blacklist.softBlock);
			if (decision.kind === "allowed") return undefined;

			const reason = formatRequestPrompt(
				decision.request,
				new Date(wallNow()).toISOString(),
			);
			if (ctx.hasUI) ctx.ui.notify(reason, "warning");
			return { block: true, reason };
		});
	};
}

export default createPathBlacklistExtension();
