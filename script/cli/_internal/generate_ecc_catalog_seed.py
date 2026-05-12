"""一次性腳本：產生 upstream/ecc-catalog.yaml 初版。

從 ECC 來源目錄 (~/.config/everything-claude-code/) 掃描所有 skill，
依嵌入的分類表分組，並以 `git log --diff-filter=A` 取每個 skill 的首次出現日期。

使用方式：
    python -m script.cli._internal.generate_ecc_catalog_seed > upstream/ecc-catalog.yaml
"""

from __future__ import annotations

import subprocess
import sys
from datetime import date
from pathlib import Path


CATEGORIES: dict[str, dict] = {
    "engineering-methods": {
        "description": "通用工程方法論：開發、審查、品質、TDD、重構等跨專案適用流程",
        "skills": [
            "agentic-engineering", "ai-first-engineering", "architecture-decision-records",
            "coding-standards", "context-budget", "council", "error-handling",
            "hexagonal-architecture", "iterative-retrieval", "plankton-code-quality",
            "santa-method", "search-first", "skill-stocktake",
            "strategic-compact", "tdd-workflow", "verification-loop",
        ],
    },
    "agent-llm": {
        "description": "Agent 與 LLM 系統建構：harness、eval、orchestration、prompt 工程",
        "skills": [
            "agent-architecture-audit", "agent-eval", "agent-harness-construction",
            "agent-introspection-debugging", "agent-sort", "agentic-os",
            "autonomous-agent-harness", "autonomous-loops", "claude-devfleet",
            "continuous-agent-loop", "continuous-learning", "continuous-learning-v2",
            "enterprise-agent-ops", "eval-harness", "gan-style-harness",
            "mcp-server-patterns", "mle-workflow", "plan-orchestrate",
            "prompt-optimizer", "team-builder",
        ],
    },
    "frontend-ui": {
        "description": "前端、UI、設計系統、動畫",
        "skills": [
            "accessibility", "angular-developer", "design-system", "frontend-patterns",
            "ios-icon-gen", "motion-foundations", "motion-patterns", "motion-advanced",
            "motion-ui", "nextjs-turbopack", "nuxt4-patterns", "ui-demo", "ui-to-vue",
            "vite-patterns",
        ],
    },
    "backend-frameworks": {
        "description": "後端語言、框架、執行期",
        "skills": [
            "backend-patterns", "bun-runtime", "fastapi-patterns", "fsharp-testing",
            "nestjs-patterns", "python-patterns", "python-testing", "quarkus-patterns",
            "quarkus-security", "quarkus-tdd", "quarkus-verification", "tinystruct-patterns",
        ],
    },
    "data-storage": {
        "description": "資料儲存、資料庫與遷移",
        "skills": [
            "database-migrations", "mysql-patterns", "postgres-patterns", "redis-patterns",
        ],
    },
    "network-infra": {
        "description": "網路、Homelab、基礎設施、部署",
        "skills": [
            "cisco-ios-patterns", "deployment-patterns",
            "docker-patterns", "flox-environments", "homelab-network-readiness",
            "homelab-network-setup", "netmiko-ssh-automation", "network-bgp-diagnostics",
            "network-config-validation", "network-interface-health", "windows-desktop-e2e",
        ],
    },
    "testing-qa": {
        "description": "測試策略、QA、E2E、效能、回歸",
        "skills": [
            "ai-regression-testing", "benchmark", "browser-qa", "canary-watch",
            "e2e-testing", "production-audit",
        ],
    },
    "docs-knowledge": {
        "description": "文件、知識管理、研究、品牌語氣",
        "skills": [
            "brand-voice", "code-tour", "codebase-onboarding", "deep-research",
            "documentation-lookup", "exa-search", "knowledge-ops", "market-research",
            "research-ops",
        ],
    },
    "scientific": {
        "description": "科學、學術、文獻、資料庫整合",
        "skills": [
            "scientific-db-pubmed-database", "scientific-db-uspto-database",
            "scientific-pkg-gget", "scientific-thinking-literature-review",
            "scientific-thinking-scholar-evaluation",
        ],
    },
    "tools-ops": {
        "description": "工具、運維、整合、自動化",
        "skills": [
            "api-connector-builder", "api-design", "automation-audit-ops", "ck",
            "dashboard-builder", "data-scraper-agent", "dmux-workflows",
            "ecc-guide", "gateguard", "github-ops", "hookify-rules", "jira-integration",
            "nanoclaw-repl", "opensource-pipeline", "safety-guard", "terminal-ops",
            "workspace-surface-audit",
        ],
    },
    "process-rfc": {
        "description": "規範、流程、RFC、PR、產品/能力定義",
        "skills": [
            "blueprint", "git-workflow", "hermes-imports", "laravel-plugin-discovery",
            "product-capability", "product-lens", "project-flow-ops",
            "ralphinho-rfc-pipeline",
        ],
    },
    "security": {
        "description": "安全、漏洞獵尋、合規",
        "skills": [
            "regex-vs-llm-structured-text", "rules-distill", "security-bounty-hunter",
            "security-review", "security-scan",
        ],
    },
    "ai-cost-tooling": {
        "description": "AI 工具、Token 預算、成本控制、媒體生成",
        "skills": [
            "click-path-audit", "content-hash-cache-pattern",
            "cost-aware-llm-pipeline", "remotion-video-creation", "repo-scan",
            "token-budget-advisor",
        ],
    },
    "uncategorized": {
        "description": "尚未分類：audit 偵測到 ECC 新增、未在 catalog 中的項目",
        "skills": [],
    },
}


def get_added_date(ecc_root: Path, skill_name: str) -> str:
    """取得 skill 首次出現於 ECC 的日期（YYYY-MM-DD）。取不到回傳空字串。"""
    try:
        result = subprocess.run(
            [
                "git", "log", "--diff-filter=A", "--follow",
                "--format=%ad", "--date=short", "--",
                f"skills/{skill_name}",
            ],
            cwd=ecc_root,
            capture_output=True,
            text=True,
            check=False,
        )
        dates = [d.strip() for d in result.stdout.splitlines() if d.strip()]
        return dates[-1] if dates else ""
    except (subprocess.SubprocessError, OSError):
        return ""


def get_ecc_head_sha(ecc_root: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ecc_root, capture_output=True, text=True, check=False,
        )
        return result.stdout.strip()
    except (subprocess.SubprocessError, OSError):
        return ""


def main() -> int:
    ecc_root = Path("~/.config/everything-claude-code").expanduser()
    if not ecc_root.exists():
        print(f"error: ECC root not found at {ecc_root}", file=sys.stderr)
        return 2

    classified: set[str] = set()
    for cat in CATEGORIES.values():
        classified.update(cat["skills"])

    today = date.today().isoformat()
    head = get_ecc_head_sha(ecc_root)

    out: list[str] = []
    out.append("version: 1")
    out.append(f'last_synced: "{today}"')
    out.append(f'last_synced_ecc_commit: "{head}"')
    out.append("")
    out.append("# ECC 上游 skill 目錄分類")
    out.append("# 純資料檔，不影響 runtime 分發。runtime 白名單在 upstream/distribution.yaml")
    out.append("# 維護方式：ai-dev ecc audit 偵測 ECC 與本檔差異，輸出建議 patch 後人工貼上")
    out.append("")
    out.append("categories:")

    for cat_key, cat_data in CATEGORIES.items():
        out.append(f"  {cat_key}:")
        out.append(f'    description: "{cat_data["description"]}"')
        if not cat_data["skills"]:
            out.append("    skills: []")
            continue
        out.append("    skills:")
        for name in sorted(cat_data["skills"]):
            added = get_added_date(ecc_root, name)
            if added:
                out.append(f"      - name: {name}")
                out.append(f'        added: "{added}"')
            else:
                out.append(f"      - name: {name}")

    print("\n".join(out))

    # 輸出至 stderr：分類覆蓋率自我檢查
    ecc_skills = {p.name for p in (ecc_root / "skills").iterdir() if p.is_dir()}
    missing_from_classification = sorted(classified - ecc_skills)
    if missing_from_classification:
        print(
            f"\nwarning: {len(missing_from_classification)} 個分類表中的 skill 在 ECC 中找不到：",
            file=sys.stderr,
        )
        for n in missing_from_classification:
            print(f"  - {n}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
