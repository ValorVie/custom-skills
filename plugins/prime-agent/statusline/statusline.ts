import { execFile } from "node:child_process";
import path from "node:path";
import { stripVTControlCharacters } from "node:util";
import type { ExtensionAPI, ExtensionContext } from "@earendil-works/pi-coding-agent";

export interface UsageTotals {
	input: number;
	output: number;
	cacheRead: number;
	cacheWrite: number;
	cost: number;
}

export interface SessionSnapshot {
	modelId: string;
	fast: boolean;
	usage: UsageTotals;
}

interface BranchEntryLike {
	type: string;
	modelId?: string;
	serviceTier?: string | null;
	message?: {
		role: string;
		usage?: {
			input?: number;
			output?: number;
			cacheRead?: number;
			cacheWrite?: number;
			cost?: { total?: number };
		};
	};
}

interface StatusSegmentsInput {
	rlmDepth: number;
	modelId: string;
	thinkingLevel: string;
	fast: boolean;
	project: string;
	branch: string | null;
	contextPercent: number | null | undefined;
	usage: UsageTotals;
	idle: boolean;
	pending: boolean;
	activeTools: readonly string[];
	extensionStatuses: readonly string[];
}

type TruncateToWidth = (text: string, width: number) => string;

const GRAPHEME_SEGMENTER = new Intl.Segmenter(undefined, { granularity: "grapheme" });
const EXTENDED_PICTOGRAPHIC = /\p{Extended_Pictographic}/u;

const EMPTY_USAGE: UsageTotals = {
	input: 0,
	output: 0,
	cacheRead: 0,
	cacheWrite: 0,
	cost: 0,
};

function finiteNonNegative(value: unknown): number {
	return typeof value === "number" && Number.isFinite(value) && value > 0 ? value : 0;
}

function isZeroWidth(codePoint: number): boolean {
	return (
		codePoint === 0x200d ||
		(codePoint >= 0x0300 && codePoint <= 0x036f) ||
		(codePoint >= 0x1ab0 && codePoint <= 0x1aff) ||
		(codePoint >= 0x1dc0 && codePoint <= 0x1dff) ||
		(codePoint >= 0x20d0 && codePoint <= 0x20ff) ||
		(codePoint >= 0xfe00 && codePoint <= 0xfe0f) ||
		(codePoint >= 0xfe20 && codePoint <= 0xfe2f) ||
		(codePoint >= 0xe0100 && codePoint <= 0xe01ef)
	);
}

function isWide(codePoint: number): boolean {
	return (
		codePoint >= 0x1100 &&
		(codePoint <= 0x115f ||
			codePoint === 0x2329 ||
			codePoint === 0x232a ||
			(codePoint >= 0x2e80 && codePoint <= 0xa4cf && codePoint !== 0x303f) ||
			(codePoint >= 0xac00 && codePoint <= 0xd7a3) ||
			(codePoint >= 0xf900 && codePoint <= 0xfaff) ||
			(codePoint >= 0xfe10 && codePoint <= 0xfe19) ||
			(codePoint >= 0xfe30 && codePoint <= 0xfe6f) ||
			(codePoint >= 0xff00 && codePoint <= 0xff60) ||
			(codePoint >= 0xffe0 && codePoint <= 0xffe6) ||
			(codePoint >= 0x1f300 && codePoint <= 0x1faff) ||
			(codePoint >= 0x20000 && codePoint <= 0x3fffd))
	);
}

export function graphemeWidth(grapheme: string): number {
	if (EXTENDED_PICTOGRAPHIC.test(grapheme) || grapheme.includes("\ufe0f")) return 2;
	let width = 0;
	for (const character of grapheme) {
		const codePoint = character.codePointAt(0) ?? 0;
		if (isZeroWidth(codePoint) || codePoint < 0x20 || (codePoint >= 0x7f && codePoint < 0xa0)) continue;
		width += isWide(codePoint) ? 2 : 1;
	}
	return width;
}

export function visibleWidth(text: string): number {
	let width = 0;
	for (const { segment } of GRAPHEME_SEGMENTER.segment(text)) width += graphemeWidth(segment);
	return width;
}

export function truncatePlainText(text: string, maxWidth: number): string {
	const limit = Math.max(0, Math.trunc(maxWidth));
	if (limit === 0) return "";
	if (visibleWidth(text) <= limit) return text;

	let output = "";
	let width = 0;
	for (const { segment } of GRAPHEME_SEGMENTER.segment(text)) {
		const nextWidth = graphemeWidth(segment);
		if (width + nextWidth + 1 > limit) break;
		output += segment;
		width += nextWidth;
	}
	return `${output}…`;
}

export function compactNumber(value: number): string {
	const safe = finiteNonNegative(value);
	if (safe < 1_000) return Math.round(safe).toString();
	if (safe < 1_000_000) return `${(safe / 1_000).toFixed(1)}k`;
	if (safe < 1_000_000_000) return `${(safe / 1_000_000).toFixed(1)}m`;
	return `${(safe / 1_000_000_000).toFixed(1)}b`;
}

export function formatCost(value: number): string {
	const safe = finiteNonNegative(value);
	const digits = safe > 0 && safe < 0.0001 ? 6 : safe > 0 && safe < 0.01 ? 4 : 2;
	return `$${safe.toFixed(digits)}`;
}

export function oneLine(value: unknown, fallback = "-"): string {
	const text = stripVTControlCharacters(String(value ?? ""))
		.replace(/[\u0000-\u001f\u007f-\u009f]+/g, " ")
		.replace(/\s+/g, " ")
		.trim();
	return text || fallback;
}

export function summarizeBranch(
	entries: readonly BranchEntryLike[],
	fallbackModel = "no-model",
): SessionSnapshot {
	let modelId = oneLine(fallbackModel, "no-model");
	let fast = false;
	const usage = { ...EMPTY_USAGE };

	for (const entry of entries) {
		if (entry.type === "model_change" && entry.modelId) {
			modelId = oneLine(entry.modelId, modelId);
		}
		if (entry.type === "service_tier_change") {
			fast = entry.serviceTier === "priority";
		}
		if (entry.type !== "message" || entry.message?.role !== "assistant" || !entry.message.usage) {
			continue;
		}

		usage.input += finiteNonNegative(entry.message.usage.input);
		usage.output += finiteNonNegative(entry.message.usage.output);
		usage.cacheRead += finiteNonNegative(entry.message.usage.cacheRead);
		usage.cacheWrite += finiteNonNegative(entry.message.usage.cacheWrite);
		usage.cost += finiteNonNegative(entry.message.usage.cost?.total);
	}

	return { modelId, fast, usage };
}

function formatWorking(input: StatusSegmentsInput): string {
	const tools = [...new Set(input.activeTools.map((tool) => oneLine(tool)).filter((tool) => tool !== "-"))];
	if (tools.length > 0) {
		const shown = tools.slice(0, 2).join(",");
		return `work:${shown}${tools.length > 2 ? `+${tools.length - 2}` : ""}`;
	}
	if (!input.idle) return "work:-";
	return input.pending ? "idle:+queued" : "idle";
}

export function buildStatusSegments(input: StatusSegmentsInput): string[] {
	const total = input.usage.input + input.usage.output + input.usage.cacheRead + input.usage.cacheWrite;
	const context =
		typeof input.contextPercent === "number" && Number.isFinite(input.contextPercent)
			? `${Math.round(input.contextPercent)}%`
			: "?";
	const statuses = input.extensionStatuses
		.map((status) => oneLine(status))
		.filter((status) => status !== "-")
		.join(",");
	const location = input.branch
		? `${oneLine(input.project)}:${oneLine(input.branch)}`
		: oneLine(input.project);

	return [
		`rlm:${Math.max(0, Math.trunc(finiteNonNegative(input.rlmDepth)))}`,
		`model:${oneLine(input.modelId, "no-model")}`,
		`eff:${oneLine(input.thinkingLevel)}${input.fast ? "/fast" : ""}`,
		location,
		`ctx:${context}`,
		`sess:↑${compactNumber(input.usage.input)}/↓${compactNumber(input.usage.output)}/${formatCost(input.usage.cost)}`,
		formatWorking(input),
		`ext:${statuses || "-"}`,
		`cache:R${compactNumber(input.usage.cacheRead)}/W${compactNumber(input.usage.cacheWrite)}`,
		`total:${compactNumber(total)}`,
		`cost:~${formatCost(input.usage.cost)}`,
	];
}

export type ReadBranch = (cwd: string) => Promise<string | null>;

export function readGitBranch(cwd: string): Promise<string | null> {
	return new Promise((resolve) => {
		execFile(
			"git",
			["-C", cwd, "branch", "--show-current"],
			{ timeout: 1_000, maxBuffer: 4_096, windowsHide: true },
			(_error, stdout) => resolve(oneLine(stdout, "") || null),
		);
	});
}

export function registerStatusline(
	pi: ExtensionAPI,
	truncateToWidth: TruncateToWidth,
	readBranch: ReadBranch = readGitBranch,
): void {
	const activeTools = new Map<string, string>();
	let requestRender: (() => void) | undefined;
	let snapshot: SessionSnapshot = {
		modelId: "no-model",
		fast: false,
		usage: { ...EMPTY_USAGE },
	};
	let widgetBranch: string | null = null;
	let widgetMode = false;
	let branchReadSequence = 0;

	const refreshSnapshot = (ctx: ExtensionContext) => {
		snapshot = summarizeBranch(ctx.sessionManager.getBranch(), ctx.model?.id ?? "no-model");
	};
	const buildLine = (
		ctx: ExtensionContext,
		branch: string | null,
		extensionStatuses: readonly string[],
	) => {
		const project = path.basename(ctx.sessionManager.getCwd() || ctx.cwd) || "/";
		const context = ctx.getContextUsage();
		const header = ctx.sessionManager.getHeader();
		return buildStatusSegments({
			rlmDepth: header?.rlmDepth ?? 0,
			modelId: snapshot.modelId,
			thinkingLevel: pi.getThinkingLevel(),
			fast: snapshot.fast,
			project,
			branch,
			contextPercent: context?.percent,
			usage: snapshot.usage,
			idle: ctx.isIdle(),
			pending: ctx.hasPendingMessages(),
			activeTools: [...activeTools.values()],
			extensionStatuses,
		}).join(" · ");
	};
	const redraw = () => requestRender?.();
	const refreshAndRedraw = (_event: unknown, ctx: ExtensionContext) => {
		refreshSnapshot(ctx);
		redraw();
	};
	const refreshWidgetBranch = (ctx: ExtensionContext) => {
		if (!widgetMode) return;
		const sequence = ++branchReadSequence;
		const cwd = ctx.sessionManager.getCwd() || ctx.cwd;
		void Promise.resolve()
			.then(() => readBranch(cwd))
			.then((branch) => {
				if (sequence !== branchReadSequence) return;
				widgetBranch = branch;
				try {
					redraw();
				} catch {
					// The captured context becomes stale when a reload wins this race.
				}
			})
			.catch(() => {});
	};

	pi.on("session_start", (_event, ctx) => {
		activeTools.clear();
		requestRender = undefined;
		widgetBranch = null;
		widgetMode = false;
		branchReadSequence++;
		refreshSnapshot(ctx);
		if (!ctx.hasUI) return;

		let footerCreated = false;
		ctx.ui.setFooter((tui, theme, footerData) => {
			footerCreated = true;
			const render = () => tui.requestRender();
			requestRender = render;
			const unsubscribe = footerData.onBranchChange(render);

			return {
				dispose() {
					unsubscribe();
					if (requestRender === render) requestRender = undefined;
				},
				invalidate() {},
				render(width: number): string[] {
					const line = buildLine(
						ctx,
						footerData.getGitBranch(),
						[...footerData.getExtensionStatuses().values()],
					);
					return [theme.fg("dim", truncateToWidth(line, width))];
				},
			};
		});
		if (footerCreated) return;

		// Prime Agent 0.7.2's daemon bridge intentionally ignores setFooter factories.
		// A below-editor widget is the only serializable one-line fallback it exposes.
		const renderWidget = () => {
			ctx.ui.setWidget(
				"prime-agent-statusline",
				[buildLine(ctx, widgetBranch, ["?"])],
				{ placement: "belowEditor" },
			);
		};
		widgetMode = true;
		requestRender = renderWidget;
		renderWidget();
		refreshWidgetBranch(ctx);
	});

	pi.on("before_agent_start", refreshAndRedraw);
	pi.on("agent_start", redraw);
	pi.on("agent_end", refreshAndRedraw);
	pi.on("turn_end", (event, ctx) => {
		refreshAndRedraw(event, ctx);
		refreshWidgetBranch(ctx);
	});
	pi.on("session_compact", refreshAndRedraw);
	pi.on("model_select", refreshAndRedraw);
	pi.on("thinking_level_select", redraw);
	pi.on("tool_execution_start", (event) => {
		activeTools.set(event.toolCallId, event.toolName);
		redraw();
	});
	pi.on("tool_execution_end", (event) => {
		activeTools.delete(event.toolCallId);
		redraw();
	});
}
