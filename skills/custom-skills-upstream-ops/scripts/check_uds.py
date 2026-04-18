#!/usr/bin/env python3
"""
UDS Update Checker

比對 ~/.config/universal-dev-standards 上游與本專案的
`.standards/`（ai/standards → .standards）與 `skills/<uds-origin>/`，
輸出 commit 差異、檔案漂移與建議動作。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[3]
UDS_LOCAL_DEFAULT = Path.home() / ".config" / "universal-dev-standards"
LAST_SYNC_PATH = PROJECT_ROOT / "upstream" / "last-sync.yaml"
SOURCES_PATH = PROJECT_ROOT / "upstream" / "sources.yaml"
REPORT_DIR = PROJECT_ROOT / "upstream" / "reports" / "uds-update"

STANDARDS_LOCAL = PROJECT_ROOT / ".standards"
STANDARDS_UPSTREAM_REL = Path("ai/standards")
SKILLS_LOCAL = PROJECT_ROOT / "skills"
SKILLS_UPSTREAM_REL = Path("skills")

UDS_KEY = "universal-dev-standards"


class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    CYAN = "\033[36m"


def run_git(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git"] + args,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def get_uds_path() -> Path:
    sources = load_yaml(SOURCES_PATH)
    entry = sources.get("sources", {}).get(UDS_KEY, {})
    local = entry.get("local_path")
    if local:
        return Path(local).expanduser()
    return UDS_LOCAL_DEFAULT


def walk_files(root: Path) -> dict[str, str]:
    """回傳 {相對路徑: sha256}。跳過 .git 與 .DS_Store。"""
    out: dict[str, str] = {}
    if not root.exists():
        return out
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        parts = p.relative_to(root).parts
        if parts and parts[0] == ".git":
            continue
        if p.name == ".DS_Store":
            continue
        rel = p.relative_to(root).as_posix()
        out[rel] = sha256(p)
    return out


def diff_trees(
    local_map: dict[str, str], upstream_map: dict[str, str]
) -> dict[str, list[str]]:
    local_keys = set(local_map)
    upstream_keys = set(upstream_map)
    modified = sorted(
        k for k in local_keys & upstream_keys if local_map[k] != upstream_map[k]
    )
    added_upstream = sorted(upstream_keys - local_keys)
    only_local = sorted(local_keys - upstream_keys)
    return {
        "modified": modified,
        "added_upstream": added_upstream,
        "only_local": only_local,
    }


def check_commits(uds_path: Path) -> dict:
    last_sync = load_yaml(LAST_SYNC_PATH)
    entry = last_sync.get(UDS_KEY, {}) if isinstance(last_sync, dict) else {}
    last_commit = entry.get("commit")

    head = run_git(["rev-parse", "HEAD"], uds_path).stdout.strip()
    result = {
        "last_synced_commit": last_commit,
        "upstream_head": head,
        "is_up_to_date": bool(last_commit) and last_commit == head,
        "commits": [],
    }
    if not last_commit or last_commit == head:
        return result
    log = run_git(
        ["log", "--oneline", "--no-merges", f"{last_commit}..HEAD"], uds_path
    ).stdout.strip()
    if log:
        result["commits"] = [line for line in log.splitlines() if line.strip()]
    return result


def check_standards(uds_path: Path) -> dict:
    local_map = walk_files(STANDARDS_LOCAL)
    upstream_root = uds_path / STANDARDS_UPSTREAM_REL
    upstream_map = walk_files(upstream_root)
    diff = diff_trees(local_map, upstream_map)
    return {
        "local_root": str(STANDARDS_LOCAL),
        "upstream_root": str(upstream_root),
        "counts": {
            "local": len(local_map),
            "upstream": len(upstream_map),
            "modified": len(diff["modified"]),
            "added_upstream": len(diff["added_upstream"]),
            "only_local": len(diff["only_local"]),
        },
        "diff": diff,
    }


def check_skills(uds_path: Path) -> dict:
    upstream_skills_root = uds_path / SKILLS_UPSTREAM_REL
    if not upstream_skills_root.exists():
        return {"error": f"upstream skills root missing: {upstream_skills_root}"}

    upstream_skill_ids = {
        p.name for p in upstream_skills_root.iterdir() if p.is_dir()
    }
    local_skill_ids = (
        {p.name for p in SKILLS_LOCAL.iterdir() if p.is_dir()}
        if SKILLS_LOCAL.exists()
        else set()
    )
    mirrored = sorted(upstream_skill_ids & local_skill_ids)
    upstream_only = sorted(upstream_skill_ids - local_skill_ids)

    per_skill: dict[str, dict] = {}
    drift_count = 0
    for sid in mirrored:
        local_map = walk_files(SKILLS_LOCAL / sid)
        upstream_map = walk_files(upstream_skills_root / sid)
        diff = diff_trees(local_map, upstream_map)
        has_drift = any(diff[k] for k in diff)
        if has_drift:
            drift_count += 1
        per_skill[sid] = {
            "counts": {
                "local": len(local_map),
                "upstream": len(upstream_map),
                "modified": len(diff["modified"]),
                "added_upstream": len(diff["added_upstream"]),
                "only_local": len(diff["only_local"]),
            },
            "diff": diff,
            "has_drift": has_drift,
        }

    return {
        "mirrored_count": len(mirrored),
        "upstream_only_count": len(upstream_only),
        "upstream_only": upstream_only,
        "drift_count": drift_count,
        "skills": per_skill,
    }


def check_manifest(uds_path: Path) -> dict:
    manifest_path = uds_path / "uds-manifest.json"
    if not manifest_path.exists():
        return {}
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    return {
        "version": data.get("version"),
        "last_updated": data.get("last_updated"),
        "stats": data.get("stats", {}),
    }


def recommend(report: dict) -> list[str]:
    recs: list[str] = []
    commits = report["commits"]
    standards = report["standards"]
    skills = report["skills"]

    if commits["is_up_to_date"] and not (
        standards["counts"]["modified"]
        or standards["counts"]["added_upstream"]
        or skills.get("drift_count", 0)
        or skills.get("upstream_only_count", 0)
    ):
        recs.append("✅ 完全同步，不需更新。")
        return recs

    if not commits["is_up_to_date"]:
        recs.append(
            f"🔄 有 {len(commits['commits'])} 個新 commit，先 `ai-dev update --only repos` 拉取上游。"
        )

    if standards["counts"]["modified"] or standards["counts"]["added_upstream"]:
        recs.append(
            f"📐 `.standards/` 有漂移（modified={standards['counts']['modified']}, "
            f"added_upstream={standards['counts']['added_upstream']}），"
            "執行 `ai-dev clone` 同步，或逐檔 diff 合併。"
        )

    if skills.get("drift_count"):
        recs.append(
            f"🧩 {skills['drift_count']} 個鏡像 skill 內容有差異，"
            "以 `ai-dev clone` 重新分發，或針對個別 skill 比對差異。"
        )

    if skills.get("upstream_only_count"):
        recs.append(
            f"➕ 上游有 {skills['upstream_only_count']} 個本地未安裝的 skill，"
            "可評估是否加入（見 upstream_only 列表）。"
        )

    if standards["counts"]["only_local"]:
        recs.append(
            f"⚠️  `.standards/` 有 {standards['counts']['only_local']} 個本地獨有檔案（可能為客製化，勿直接覆寫）。"
        )

    recs.append(
        "🗂  套用完成後更新 `upstream/last-sync.yaml[universal-dev-standards].commit` 為最新 HEAD。"
    )
    return recs


def print_report(report: dict, verbose: bool) -> None:
    C = Colors
    commits = report["commits"]
    standards = report["standards"]
    skills = report["skills"]
    manifest = report["manifest"]

    print(f"{C.BOLD}UDS Update Check{C.RESET}")
    print(f"{C.DIM}generated_at: {report['generated_at']}{C.RESET}\n")

    print(f"{C.BOLD}【Commit 狀態】{C.RESET}")
    print(f"  last_synced : {commits['last_synced_commit'] or '(unset)'}")
    print(f"  upstream    : {commits['upstream_head']}")
    status = (
        f"{C.GREEN}up-to-date{C.RESET}"
        if commits["is_up_to_date"]
        else f"{C.YELLOW}behind ({len(commits['commits'])} commits){C.RESET}"
    )
    print(f"  狀態        : {status}")
    if commits["commits"] and verbose:
        for line in commits["commits"][:20]:
            print(f"    - {line}")
        if len(commits["commits"]) > 20:
            print(f"    ... ({len(commits['commits']) - 20} more)")
    print()

    if manifest:
        print(f"{C.BOLD}【UDS Manifest】{C.RESET}")
        print(f"  version       : {manifest.get('version')}")
        print(f"  last_updated  : {manifest.get('last_updated')}")
        stats = manifest.get("stats", {})
        if stats:
            print(
                f"  stats         : standards={stats.get('core_standards')}, "
                f"skills={stats.get('skills')}, commands={stats.get('slash_commands')}"
            )
        print()

    print(f"{C.BOLD}【.standards/ 漂移】{C.RESET}")
    c = standards["counts"]
    print(
        f"  local={c['local']}  upstream={c['upstream']}  "
        f"modified={C.YELLOW}{c['modified']}{C.RESET}  "
        f"added_upstream={C.CYAN}{c['added_upstream']}{C.RESET}  "
        f"only_local={C.DIM}{c['only_local']}{C.RESET}"
    )
    if verbose:
        d = standards["diff"]
        for label, key, color in [
            ("modified", "modified", C.YELLOW),
            ("added_upstream", "added_upstream", C.CYAN),
            ("only_local", "only_local", C.DIM),
        ]:
            if d[key]:
                print(f"  {color}{label}:{C.RESET}")
                for f in d[key]:
                    print(f"    - {f}")
    print()

    print(f"{C.BOLD}【skills/ 漂移（UDS 鏡像）】{C.RESET}")
    print(
        f"  mirrored={skills.get('mirrored_count', 0)}  "
        f"upstream_only={skills.get('upstream_only_count', 0)}  "
        f"drift_count={C.YELLOW}{skills.get('drift_count', 0)}{C.RESET}"
    )
    per_skill = skills.get("skills", {})
    drifted = [sid for sid, s in per_skill.items() if s["has_drift"]]
    if drifted:
        print(f"  {C.YELLOW}有差異的 skill:{C.RESET}")
        for sid in drifted:
            cnt = per_skill[sid]["counts"]
            print(
                f"    - {sid}  (mod={cnt['modified']}, add={cnt['added_upstream']}, local_only={cnt['only_local']})"
            )
            if verbose:
                d = per_skill[sid]["diff"]
                for key in ("modified", "added_upstream", "only_local"):
                    for f in d[key]:
                        print(f"        [{key}] {f}")
    if skills.get("upstream_only"):
        print(f"  {C.CYAN}僅上游存在的 skill（尚未安裝）:{C.RESET}")
        for sid in skills["upstream_only"][:20]:
            print(f"    - {sid}")
        if len(skills["upstream_only"]) > 20:
            print(f"    ... ({len(skills['upstream_only']) - 20} more)")
    print()

    print(f"{C.BOLD}【建議動作】{C.RESET}")
    for r in report["recommendations"]:
        print(f"  {r}")


def build_report(uds_path: Path) -> dict:
    commits = check_commits(uds_path)
    manifest = check_manifest(uds_path)
    standards = check_standards(uds_path)
    skills = check_skills(uds_path)

    report = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "uds_path": str(uds_path),
        "commits": commits,
        "manifest": manifest,
        "standards": standards,
        "skills": skills,
    }
    report["recommendations"] = recommend(report)
    return report


def needs_update(report: dict) -> bool:
    return not (
        report["commits"]["is_up_to_date"]
        and report["standards"]["counts"]["modified"] == 0
        and report["standards"]["counts"]["added_upstream"] == 0
        and report["skills"].get("drift_count", 0) == 0
    )


def write_report(report: dict) -> Path:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    date = datetime.now().strftime("%Y-%m-%d")
    path = REPORT_DIR / f"uds-update-{date}.yaml"
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(report, f, allow_unicode=True, sort_keys=False)
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Check UDS upstream drift.")
    parser.add_argument("--verbose", "-v", action="store_true", help="列出所有差異檔案")
    parser.add_argument("--report", action="store_true", help="額外輸出 YAML 報告")
    parser.add_argument("--json", action="store_true", help="以 JSON 輸出（腳本串接用）")
    parser.add_argument(
        "--uds-path",
        type=Path,
        default=None,
        help="覆寫 UDS 上游路徑（預設讀 upstream/sources.yaml）",
    )
    parser.add_argument(
        "--exit-nonzero-on-drift",
        action="store_true",
        help="偵測到需更新時以 exit 1 離開（CI 用）",
    )
    args = parser.parse_args()

    uds_path = args.uds_path or get_uds_path()
    if not (uds_path / ".git").exists():
        print(
            f"❌ UDS 上游路徑不是 git repo：{uds_path}",
            file=sys.stderr,
        )
        return 2

    report = build_report(uds_path)

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print_report(report, verbose=args.verbose)

    if args.report:
        out = write_report(report)
        if not args.json:
            print(f"\n📄 報告已寫入: {out.relative_to(PROJECT_ROOT)}")

    if args.exit_nonzero_on_drift and needs_update(report):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
