import { randomUUID as createRandomUUID } from "node:crypto";
import {
	closeSync,
	constants,
	lstatSync,
	mkdirSync,
	openSync,
	writeSync,
} from "node:fs";
import { dirname } from "node:path";
import { performance } from "node:perf_hooks";

export type RuleLevel = "warn" | "block";

export type Rule = {
	id: string;
	level?: RuleLevel;
	pattern: string;
	flags?: string;
	message?: string;
	reason?: string;
};

export type BlacklistConfig = {
	version: 1 | 2;
	softBlock?: {
		confirmWithinSeconds?: number;
		allowForSeconds?: number;
	};
	pathPatterns: Rule[];
	fileNamePatterns: Rule[];
};

export type CompiledRule = {
	id: string;
	level: RuleLevel;
	pattern: string;
	flags: string;
	message: string;
	regex: RegExp;
};

export type CompiledBlacklist = {
	version: 2;
	softBlock: {
		confirmWithinMs: number;
		allowForMs: number;
	};
	pathPatterns: CompiledRule[];
	fileNamePatterns: CompiledRule[];
};

export type BlacklistMatch = {
	kind: "path" | "fileName";
	rule: CompiledRule;
	target: string;
	matchedValue: string;
};

export type AccessLogEntry = {
	access_id: string;
	logged_at: string;
	access_time: string;
	location: string;
	reason: string;
	level: RuleLevel;
	rule_ids: string[];
};

export type AccessRecordInput = {
	accessId: string;
	accessTime: string;
	location: string;
	reason: string;
};

export type Clock = {
	wallNow: () => number;
	monotonicNow: () => number;
};

export type PendingRequest = {
	accessId: string;
	key: string;
	location: string;
	matches: BlacklistMatch[];
	createdAtWall: number;
	confirmUntilWall: number;
	confirmUntilMonotonic: number;
	allowForMs: number;
};

export type AllowedState = {
	key: string;
	location: string;
	allowedUntilWall: number;
	allowedUntilMonotonic: number;
};

export type GateDecision =
	| { kind: "allowed"; state: AllowedState }
	| { kind: "blocked"; request: PendingRequest };

export class AccessGateError extends Error {
	readonly code: string;

	constructor(code: string, message: string) {
		super(`${code}：${message}`);
		this.name = "AccessGateError";
		this.code = code;
	}
}

const defaultWindowSeconds = 3600;
const maximumAccessTimeSkewMs = 5 * 60 * 1000;

function assertPlainObject(value: unknown, label: string): asserts value is Record<string, unknown> {
	if (!value || typeof value !== "object" || Array.isArray(value)) {
		throw new Error(`${label} 必須是物件`);
	}
}

function positiveSeconds(value: unknown, label: string, fallback: number): number {
	const seconds = value ?? fallback;
	if (typeof seconds !== "number" || !Number.isFinite(seconds) || seconds <= 0) {
		throw new Error(`${label} 必須是大於 0 的數字`);
	}
	return seconds;
}

function compileRule(value: unknown, group: string, index: number): CompiledRule {
	assertPlainObject(value, `${group}[${index}]`);
	const id = value.id;
	const pattern = value.pattern;
	const level = value.level ?? "block";
	const flags = value.flags ?? "";
	const message = value.message ?? value.reason ?? "此目標受存取規範限制。";

	if (typeof id !== "string" || id.trim() === "") {
		throw new Error(`${group}[${index}].id 必須是非空字串`);
	}
	if (typeof pattern !== "string" || pattern === "") {
		throw new Error(`${group}[${index}].pattern 必須是非空字串`);
	}
	if (level !== "warn" && level !== "block") {
		throw new Error(`${group}[${index}].action／level 必須是 warn 或 block`);
	}
	if (typeof flags !== "string") {
		throw new Error(`${group}[${index}].flags 必須是字串`);
	}
	if (typeof message !== "string" || message.trim() === "") {
		throw new Error(`${group}[${index}].message 必須是非空字串`);
	}

	try {
		return {
			id,
			level,
			pattern,
			flags,
			message,
			regex: new RegExp(pattern, flags),
		};
	} catch (error) {
		const detail = error instanceof Error ? error.message : String(error);
		throw new Error(`${group} 規則 ${id} 的正規表達式無效：${detail}`);
	}
}

export function compileBlacklist(value: unknown): CompiledBlacklist {
	assertPlainObject(value, "blacklist.json");
	if (value.version !== 1 && value.version !== 2) {
		throw new Error("blacklist.json.version 必須是 1 或 2");
	}
	if (!Array.isArray(value.pathPatterns) || !Array.isArray(value.fileNamePatterns)) {
		throw new Error("pathPatterns 與 fileNamePatterns 必須是陣列");
	}
	if (value.softBlock !== undefined) assertPlainObject(value.softBlock, "softBlock");
	const softBlock = (value.softBlock ?? {}) as Record<string, unknown>;
	const confirmWithinSeconds = positiveSeconds(
		softBlock.confirmWithinSeconds,
		"softBlock.confirmWithinSeconds",
		defaultWindowSeconds,
	);
	const allowForSeconds = positiveSeconds(
		softBlock.allowForSeconds,
		"softBlock.allowForSeconds",
		defaultWindowSeconds,
	);

	const ids = new Set<string>();
	const compileGroup = (rules: unknown[], group: string): CompiledRule[] =>
		rules.map((rule, index) => {
			const compiled = compileRule(rule, group, index);
			if (ids.has(compiled.id)) throw new Error(`規則 id 重複：${compiled.id}`);
			ids.add(compiled.id);
			return compiled;
		});

	return {
		version: 2,
		softBlock: {
			confirmWithinMs: confirmWithinSeconds * 1000,
			allowForMs: allowForSeconds * 1000,
		},
		pathPatterns: compileGroup(value.pathPatterns, "pathPatterns"),
		fileNamePatterns: compileGroup(value.fileNamePatterns, "fileNamePatterns"),
	};
}

function collectStrings(value: unknown, output: string[], seen: Set<object>): void {
	if (typeof value === "string") {
		output.push(value);
		return;
	}
	if (!value || typeof value !== "object" || seen.has(value)) return;
	seen.add(value);
	if (Array.isArray(value)) {
		for (const item of value) collectStrings(item, output, seen);
		return;
	}
	for (const item of Object.values(value as Record<string, unknown>)) {
		collectStrings(item, output, seen);
	}
}

const quotedStringPattern = /"((?:\\.|[^"\\])*)"|'((?:\\.|[^'\\])*)'|`((?:\\.|[^`\\])*)`/g;

function cleanCandidate(value: string): string {
	return value
		.trim()
		.replace(/^[\s"'`()\[\]{}<>,;:]+/, "")
		.replace(/[\s"'`()\[\]{}<>,;:]+$/, "");
}

export function normalizePath(value: string, home: string): string {
	let normalized = cleanCandidate(value)
		.replace(/\$\{HOME(?::-[^}]*)?\}|\$HOME/g, home)
		.replace(/\\/g, "/");
	if (normalized === "~") normalized = home;
	else if (normalized.startsWith("~/")) normalized = `${home}/${normalized.slice(2)}`;
	return normalized.replace(/\/{2,}/g, "/");
}

function quotedValues(source: string): string[] {
	quotedStringPattern.lastIndex = 0;
	return [...source.matchAll(quotedStringPattern)].map(
		(match) => match[1] ?? match[2] ?? match[3] ?? "",
	);
}

function escapeRegExp(value: string): string {
	return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function expandKnownHomeExpressions(source: string, home: string): string {
	return source
		.replace(
			/\{(?:(?:pathlib\.)?Path\.home\(\)|homedir\(\))\}/g,
			home,
		)
		.replace(
			/(?:pathlib\.)?Path\.home\(\)|homedir\(\)|os\.path\.expanduser\(\s*["']~["']\s*\)/g,
			JSON.stringify(home),
		)
		.replace(/\$\{HOME(?::-[^}]*)?\}|\$HOME/g, home);
}

function resolveStaticExpression(
	expression: string,
	variables: Map<string, string>,
	home: string,
): string | undefined {
	let expanded = expandKnownHomeExpressions(expression, home);
	for (const [name, value] of variables) {
		const escaped = escapeRegExp(name);
		expanded = expanded.replace(
			new RegExp(`\\$\\{${escaped}\\}|\\$${escaped}\\b`, "g"),
			() => value,
		);
		expanded = expanded.replace(new RegExp(`\\b${escaped}\\b`, "g"), () => JSON.stringify(value));
	}

	const parts = quotedValues(expanded);
	if (parts.length === 1) return parts[0];
	if (parts.length > 1 && expanded.includes("+")) return parts.join("");
	if (
		parts.length > 1 &&
		/(?:os\.path\.join|\bjoin\s*\(|\s\/\s)/.test(expanded)
	) {
		return parts.join("/");
	}
	if (parts.length === 0) {
		const bare = cleanCandidate(expanded);
		if (/^[A-Za-z0-9_./~:-]+$/.test(bare)) return bare;
	}
	return undefined;
}

function collectStaticCompositions(source: string, home: string): string[] {
	const results: string[] = [];
	const variables = new Map<string, string>();
	for (const statement of source.split(/[;\n]/)) {
		const assignment = statement.match(
			/^\s*(?:(?:const|let|var)\s+)?([A-Za-z_$][\w$]*)\s*=\s*(.+)$/,
		);
		if (assignment) {
			const value = resolveStaticExpression(assignment[2], variables, home);
			if (value !== undefined) {
				variables.set(assignment[1], value);
				results.push(value);
			}
			continue;
		}
		const value = resolveStaticExpression(statement, variables, home);
		if (value !== undefined) results.push(value);
	}
	return results;
}

export function collectCandidates(input: unknown, home: string): string[] {
	const strings: string[] = [];
	collectStrings(input, strings, new Set<object>());
	const candidates = new Set<string>();
	const addNormalized = (value: string) => {
		const candidate = normalizePath(value, home);
		if (candidate) candidates.add(candidate);
	};
	const add = (value: string) => {
		addNormalized(value);
		if (/%[0-9a-f]{2}/i.test(value)) {
			try {
				addNormalized(decodeURIComponent(value));
			} catch {
				// Malformed percent encoding remains an ordinary unmatched candidate.
			}
		}
	};

	for (const value of strings) {
		quotedStringPattern.lastIndex = 0;
		for (const match of value.matchAll(quotedStringPattern)) {
			add(match[1] ?? match[2] ?? match[3] ?? "");
		}
		for (const token of value.split(/\s+/)) add(token);
		for (const composition of collectStaticCompositions(value, home)) add(composition);
		add(value);
	}
	return [...candidates];
}

function regexMatches(regex: RegExp, value: string): boolean {
	regex.lastIndex = 0;
	return regex.test(value);
}

function compareMatches(a: BlacklistMatch, b: BlacklistMatch): number {
	const levelOrder = { block: 0, warn: 1 } as const;
	return levelOrder[a.rule.level] - levelOrder[b.rule.level] || a.rule.id.localeCompare(b.rule.id);
}

export function findBlacklistMatches(
	input: unknown,
	blacklist: CompiledBlacklist,
	home: string,
): BlacklistMatch[] {
	for (const target of collectCandidates(input, home)) {
		const matches: BlacklistMatch[] = [];
		for (const rule of blacklist.pathPatterns) {
			if (regexMatches(rule.regex, target)) {
				matches.push({ kind: "path", rule, target, matchedValue: target });
			}
		}

		const fileName = target.split("/").at(-1) ?? target;
		for (const rule of blacklist.fileNamePatterns) {
			if (regexMatches(rule.regex, fileName)) {
				matches.push({ kind: "fileName", rule, target, matchedValue: fileName });
			}
		}
		if (matches.length > 0) return matches.sort(compareMatches);
	}
	return [];
}

export function buildAccessKey(matches: BlacklistMatch[]): string {
	if (matches.length === 0) throw new Error("無法為空命中集合建立 access key");
	const target = matches[0].target;
	if (matches.some((match) => match.target !== target)) {
		throw new Error("同一 access key 的命中必須指向相同目標");
	}
	const ruleKeys = matches
		.map((match) => `${match.kind}:${match.rule.id}`)
		.sort()
		.join(",");
	return JSON.stringify([target, ruleKeys]);
}

function defaultClock(): Clock {
	return {
		wallNow: () => Date.now(),
		monotonicNow: () => performance.now(),
	};
}

function unicodeLength(value: string): number {
	return [...value].length;
}

export function appendAccessLog(path: string, entry: AccessLogEntry): void {
	const line = `${JSON.stringify(entry)}\n`;
	mkdirSync(dirname(path), { recursive: true, mode: 0o700 });

	try {
		const createFlags = constants.O_CREAT | constants.O_EXCL | constants.O_WRONLY | constants.O_APPEND;
		const fd = openSync(path, createFlags, 0o600);
		try {
			writeSync(fd, line, undefined, "utf8");
		} finally {
			closeSync(fd);
		}
		return;
	} catch (error) {
		if (!(error instanceof Error) || !Object.hasOwn(error, "code") || (error as NodeJS.ErrnoException).code !== "EEXIST") {
			throw error;
		}
	}

	const stat = lstatSync(path);
	if (stat.isSymbolicLink() || !stat.isFile()) {
		throw new Error("access.log 必須是一般檔案且不得是 symlink");
	}
	if ((stat.mode & 0o077) !== 0) {
		throw new Error("access.log 權限必須是 owner-only");
	}

	const noFollow = "O_NOFOLLOW" in constants ? constants.O_NOFOLLOW : 0;
	const fd = openSync(path, constants.O_WRONLY | constants.O_APPEND | noFollow);
	try {
		writeSync(fd, line, undefined, "utf8");
	} finally {
		closeSync(fd);
	}
}

export class AccessGate {
	private readonly clock: Clock;
	private readonly randomUUID: () => string;
	private readonly appendRecord: (entry: AccessLogEntry) => void;
	private readonly home: string;
	private readonly pendingByKey = new Map<string, PendingRequest>();
	private readonly pendingById = new Map<string, PendingRequest>();
	private readonly allowedByKey = new Map<string, AllowedState>();

	constructor(options: {
		clock?: Clock;
		randomUUID?: () => string;
		appendRecord: (entry: AccessLogEntry) => void;
		home?: string;
	}) {
		this.clock = options.clock ?? defaultClock();
		this.randomUUID = options.randomUUID ?? createRandomUUID;
		this.appendRecord = options.appendRecord;
		this.home = options.home ?? process.env.HOME ?? "";
	}

	private cleanupExpired(): void {
		const now = this.clock.monotonicNow();
		for (const [key, request] of this.pendingByKey) {
			if (request.confirmUntilMonotonic <= now) {
				this.pendingByKey.delete(key);
				this.pendingById.delete(request.accessId);
			}
		}
		for (const [key, state] of this.allowedByKey) {
			if (state.allowedUntilMonotonic <= now) this.allowedByKey.delete(key);
		}
	}

	check(matches: BlacklistMatch[], windows: CompiledBlacklist["softBlock"]): GateDecision {
		if (matches.length === 0) throw new Error("AccessGate.check 需要至少一條命中規則");
		this.cleanupExpired();
		const key = buildAccessKey(matches);
		const allowed = this.allowedByKey.get(key);
		if (allowed) return { kind: "allowed", state: allowed };

		const existing = this.pendingByKey.get(key);
		if (existing) return { kind: "blocked", request: existing };

		const wallNow = this.clock.wallNow();
		const monotonicNow = this.clock.monotonicNow();
		const request: PendingRequest = {
			accessId: this.randomUUID(),
			key,
			location: matches[0].target,
			matches,
			createdAtWall: wallNow,
			confirmUntilWall: wallNow + windows.confirmWithinMs,
			confirmUntilMonotonic: monotonicNow + windows.confirmWithinMs,
			allowForMs: windows.allowForMs,
		};
		this.pendingByKey.set(key, request);
		this.pendingById.set(request.accessId, request);
		return { kind: "blocked", request };
	}

	record(input: AccessRecordInput): AccessLogEntry & { allowed_until: string } {
		this.cleanupExpired();
		const request = this.pendingById.get(input.accessId);
		if (!request) throw new AccessGateError("ACCESS_ID_INVALID", "access ID 不存在或已過期");
		if (typeof input.location !== "string") {
			throw new AccessGateError("LOCATION_INVALID", "location 必須是字串");
		}
		const location = normalizePath(input.location, this.home);
		if (location !== request.location) {
			throw new AccessGateError("LOCATION_MISMATCH", `location 必須完全等於 ${request.location}`);
		}

		const accessTime = Date.parse(input.accessTime);
		const wallNow = this.clock.wallNow();
		if (!Number.isFinite(accessTime)) {
			throw new AccessGateError("ACCESS_TIME_INVALID", "accessTime 必須是 RFC 3339 時間");
		}
		if (Math.abs(accessTime - wallNow) > maximumAccessTimeSkewMs || accessTime < request.createdAtWall - 1000) {
			throw new AccessGateError("ACCESS_TIME_NOT_CURRENT", "accessTime 必須是目前時間，且不得早於本次提示");
		}

		if (typeof input.reason !== "string" || /[\r\n]/.test(input.reason)) {
			throw new AccessGateError("REASON_INVALID", "reason 必須是單行字串");
		}
		const reason = input.reason.trim();
		const reasonLength = unicodeLength(reason);
		if (reasonLength < 1 || reasonLength > 30) {
			throw new AccessGateError("REASON_LENGTH", "reason 去除前後空白後必須是 1 至 30 個 Unicode 字元");
		}

		const level: RuleLevel = request.matches.some((match) => match.rule.level === "block")
			? "block"
			: "warn";
		const entry: AccessLogEntry = {
			access_id: request.accessId,
			logged_at: new Date(wallNow).toISOString(),
			access_time: new Date(accessTime).toISOString(),
			location: request.location,
			reason,
			level,
			rule_ids: request.matches.map((match) => match.rule.id),
		};

		this.appendRecord(entry);
		const monotonicNow = this.clock.monotonicNow();
		const allowed: AllowedState = {
			key: request.key,
			location: request.location,
			allowedUntilWall: wallNow + request.allowForMs,
			allowedUntilMonotonic: monotonicNow + request.allowForMs,
		};
		this.pendingById.delete(request.accessId);
		this.pendingByKey.delete(request.key);
		this.allowedByKey.set(request.key, allowed);
		return { ...entry, allowed_until: new Date(allowed.allowedUntilWall).toISOString() };
	}

	reset(): void {
		this.pendingByKey.clear();
		this.pendingById.clear();
		this.allowedByKey.clear();
	}

	snapshot(): {
		pending: PendingRequest[];
		allowed: AllowedState[];
	} {
		this.cleanupExpired();
		return {
			pending: [...this.pendingByKey.values()],
			allowed: [...this.allowedByKey.values()],
		};
	}
}
