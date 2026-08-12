import type { ExtensionAPI, ExtensionContext } from "@earendil-works/pi-coding-agent";

const BD_TIMEOUT_MS = 5_000;
const BEADS_LOADED_MESSAGE = {
	customType: "beads-context-loaded",
	content: "Beads hook 已觸發：已透過 `bd prime` 載入專案工作脈絡。",
	display: true,
};

export default function beadsExtension(pi: ExtensionAPI) {
	let beadsContext: string | undefined;

	async function refreshBeadsContext(ctx: ExtensionContext, recordImmediately: boolean): Promise<boolean> {
		try {
			const result = await pi.exec("bd", ["prime"], {
				cwd: ctx.cwd,
				signal: ctx.signal,
				timeout: BD_TIMEOUT_MS,
			});

			if (result.code !== 0) {
				const detail = result.stderr.trim() || result.stdout.trim() || `exit code ${result.code}`;
				ctx.ui.notify(`Beads 脈絡載入失敗：${detail}`, "warning");
				return false;
			}

			beadsContext = result.stdout.trim() || undefined;
			if (!beadsContext) {
				return false;
			}
			if (recordImmediately) {
				pi.sendMessage(BEADS_LOADED_MESSAGE, { triggerTurn: false });
			}
			return true;
		} catch (error) {
			const detail = error instanceof Error ? error.message : String(error);
			ctx.ui.notify(`Beads 脈絡載入失敗：${detail}`, "warning");
			return false;
		}
	}

	pi.on("session_start", async (_event, ctx) => {
		await refreshBeadsContext(ctx, true);
	});

	pi.on("session_compact", async (_event, ctx) => {
		await refreshBeadsContext(ctx, true);
	});

	pi.on("before_agent_start", async (event, ctx) => {
		const refreshed = await refreshBeadsContext(ctx, false);
		if (!beadsContext) {
			return;
		}

		return {
			message: refreshed ? BEADS_LOADED_MESSAGE : undefined,
			systemPrompt: `${event.systemPrompt}

${beadsContext}
`,
		};
	});
}
