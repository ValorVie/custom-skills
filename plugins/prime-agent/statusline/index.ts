import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { registerStatusline, truncatePlainText } from "./statusline.ts";

export default function statuslineExtension(pi: ExtensionAPI): void {
	registerStatusline(pi, truncatePlainText);
}
