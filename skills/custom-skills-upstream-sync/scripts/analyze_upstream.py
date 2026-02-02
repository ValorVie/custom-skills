#!/usr/bin/env python3
"""
Upstream Analysis Script

深度分析上游 repo 的 commit 變更，生成結構化報告。
支援分析已註冊的上游 repo，或評估新的本地 repo。
"""

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

import yaml


def run_git(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    """執行 git 指令，處理 Windows 編碼問題。"""
    return subprocess.run(
        ["git"] + args,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


@dataclass
class CommitInfo:
    """單一 commit 的資訊。"""
    hash: str
    short_hash: str
    subject: str
    author: str
    date: str
    files_changed: list[str] = field(default_factory=list)
    insertions: int = 0
    deletions: int = 0
    change_type: str = "other"  # feat, fix, refactor, docs, chore, other


@dataclass
class FileChange:
    """檔案變更資訊。"""
    path: str
    status: str  # A=Added, M=Modified, D=Deleted, R=Renamed
    category: str  # skills, agents, commands, rules, hooks, contexts, other
    old_path: Optional[str] = None


@dataclass
class RepoAnalysis:
    """單一 repo 的分析結果。"""
    name: str
    local_path: str
    last_synced_commit: str
    current_commit: str
    commits: list[CommitInfo] = field(default_factory=list)
    file_changes: list[FileChange] = field(default_factory=list)
    summary: dict = field(default_factory=dict)
    recommendation: str = "Skip"  # High, Medium, Low, Skip
    reasoning: str = ""


def get_project_root() -> Path:
    """取得專案根目錄。"""
    current = Path.cwd()
    while current != current.parent:
        if (current / "upstream").exists() or (current / "pyproject.toml").exists():
            return current
        current = current.parent
    return Path.cwd()


def load_sources(project_root: Path) -> dict:
    """載入 sources.yaml。"""
    sources_file = project_root / "upstream" / "sources.yaml"
    if not sources_file.exists():
        return {}
    with open(sources_file, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_last_sync(project_root: Path) -> dict:
    """載入上次同步狀態。"""
    last_sync_file = project_root / "upstream" / "last-sync.yaml"
    if not last_sync_file.exists():
        return {}
    with open(last_sync_file, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def save_last_sync(project_root: Path, data: dict) -> None:
    """儲存同步狀態。"""
    last_sync_file = project_root / "upstream" / "last-sync.yaml"
    last_sync_file.parent.mkdir(parents=True, exist_ok=True)
    with open(last_sync_file, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False)


def get_current_commit(repo_path: Path) -> str:
    """取得目前 HEAD commit hash。"""
    result = run_git(["rev-parse", "HEAD"], repo_path)
    return result.stdout.strip() if result.returncode == 0 else ""


def parse_commit_type(subject: str) -> str:
    """從 commit 訊息解析變更類型。"""
    subject_lower = subject.lower()

    # Conventional commits
    if subject_lower.startswith(("feat", "feature", "功能", "新增")):
        return "feat"
    if subject_lower.startswith(("fix", "bugfix", "修正", "修復")):
        return "fix"
    if subject_lower.startswith(("refactor", "重構")):
        return "refactor"
    if subject_lower.startswith(("docs", "doc", "文件")):
        return "docs"
    if subject_lower.startswith(("chore", "維護", "雜項")):
        return "chore"
    if subject_lower.startswith(("test", "測試")):
        return "test"
    if subject_lower.startswith(("style", "樣式")):
        return "style"
    if subject_lower.startswith(("perf", "效能")):
        return "perf"

    # 關鍵字檢測
    if any(kw in subject_lower for kw in ["add", "new", "create", "implement"]):
        return "feat"
    if any(kw in subject_lower for kw in ["fix", "bug", "issue", "error"]):
        return "fix"
    if any(kw in subject_lower for kw in ["update", "improve", "enhance"]):
        return "refactor"
    if any(kw in subject_lower for kw in ["readme", "doc", "comment"]):
        return "docs"

    return "other"


def categorize_file(file_path: str) -> str:
    """分類檔案所屬類別。"""
    path_lower = file_path.lower()

    if "/skills/" in path_lower or path_lower.startswith("skills/"):
        return "skills"
    if "/agents/" in path_lower or path_lower.startswith("agents/"):
        return "agents"
    if "/commands/" in path_lower or path_lower.startswith("commands/"):
        return "commands"
    if "/rules/" in path_lower or path_lower.startswith("rules/"):
        return "rules"
    if "/hooks/" in path_lower or path_lower.startswith("hooks/"):
        return "hooks"
    if "/contexts/" in path_lower or path_lower.startswith("contexts/"):
        return "contexts"
    if "/workflows/" in path_lower or path_lower.startswith("workflows/"):
        return "workflows"
    if path_lower.endswith((".md", ".txt")):
        return "docs"

    return "other"


# ============================================================
# 新架構/框架偵測
# ============================================================

# 本專案已有的結構（用於比對）
KNOWN_STRUCTURES = {
    "skills",
    "agents",
    "commands",
    "hooks",
    "contexts",
    "rules",
    "workflows",
    "docs",
    "lib",
    "scripts",
    "tests",
    ".standards",
    "openspec",
    "upstream",
}

# 特殊配置檔案/框架標誌（值得關注的新模式）
NOTABLE_PATTERNS = {
    # Claude Code 相關
    ".claude-plugin/": "Claude Plugin 架構",
    "plugin.json": "Plugin 配置",
    "marketplace.json": "Marketplace 配置",
    # OpenCode 相關
    ".opencode/": "OpenCode 配置",
    "plugins/": "Plugin 目錄",
    # Codex 相關
    ".codex/": "Codex 配置",
    # 配置檔案
    "hooks.json": "Hooks 配置檔",
    "mcp_config.json": "MCP 配置",
    "mcp-configs/": "MCP 配置目錄",
    # 腳本/自動化
    "run-hook.cmd": "Windows Hook 腳本",
    "run-hook.sh": "Unix Hook 腳本",
    "session-start.sh": "Session 啟動腳本",
    # 特殊結構
    "lib/": "共用函式庫",
    "examples/": "範例目錄",
    "tests/": "測試目錄",
    "assets/": "靜態資源",
    "templates/": "範本目錄",
    "prompts/": "Prompt 目錄",
    "references/": "參考資料目錄",
}


# ============================================================
# 重疊偵測
# ============================================================

def load_overlaps_yaml(project_root: Path) -> dict:
    """載入現有的 overlaps.yaml。"""
    overlaps_file = project_root / ".standards" / "profiles" / "overlaps.yaml"
    if not overlaps_file.exists():
        return {}
    with open(overlaps_file, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def get_existing_items(project_root: Path) -> dict:
    """取得本專案已有的 skills, commands, agents 名稱。"""
    existing = {
        "skills": set(),
        "commands": set(),
        "agents": set(),
    }

    # 掃描 skills/
    skills_dir = project_root / "skills"
    if skills_dir.exists():
        for item in skills_dir.iterdir():
            if item.is_dir() and (item / "SKILL.md").exists():
                existing["skills"].add(item.name)

    # 掃描 commands/
    commands_dir = project_root / "commands" / "claude"
    if commands_dir.exists():
        for item in commands_dir.iterdir():
            if item.suffix == ".md":
                existing["commands"].add(item.stem)

    # 掃描 agents/
    agents_dir = project_root / "agents" / "claude"
    if agents_dir.exists():
        for item in agents_dir.iterdir():
            if item.suffix == ".md":
                existing["agents"].add(item.stem)

    # 也掃描 sources/ 中的項目
    for source_dir in (project_root / "sources").iterdir() if (project_root / "sources").exists() else []:
        if not source_dir.is_dir():
            continue
        for subdir_name in ["skills", "commands", "agents"]:
            subdir = source_dir / subdir_name
            if subdir.exists():
                for item in subdir.iterdir():
                    if subdir_name == "skills" and item.is_dir() and (item / "SKILL.md").exists():
                        existing["skills"].add(item.name)
                    elif item.suffix == ".md":
                        existing[subdir_name].add(item.stem)

    return existing


def compute_similarity(name1: str, name2: str) -> float:
    """計算兩個名稱的相似度 (Levenshtein distance based)。"""
    # 簡易 Levenshtein distance 實作
    if name1 == name2:
        return 1.0

    len1, len2 = len(name1), len(name2)
    if len1 == 0 or len2 == 0:
        return 0.0

    # 使用動態規劃計算編輯距離
    dp = [[0] * (len2 + 1) for _ in range(len1 + 1)]
    for i in range(len1 + 1):
        dp[i][0] = i
    for j in range(len2 + 1):
        dp[0][j] = j

    for i in range(1, len1 + 1):
        for j in range(1, len2 + 1):
            cost = 0 if name1[i - 1] == name2[j - 1] else 1
            dp[i][j] = min(dp[i - 1][j] + 1, dp[i][j - 1] + 1, dp[i - 1][j - 1] + cost)

    distance = dp[len1][len2]
    max_len = max(len1, len2)
    return 1.0 - (distance / max_len)


# 功能關鍵字對應表（用於偵測功能相似的項目）
FUNCTIONAL_KEYWORDS = {
    "tdd": ["tdd", "test-driven", "testing", "test"],
    "bdd": ["bdd", "behavior", "gherkin", "cucumber"],
    "commit": ["commit", "git-commit", "conventional"],
    "review": ["review", "code-review", "checkin"],
    "documentation": ["doc", "docs", "documentation", "readme"],
    "refactor": ["refactor", "refactoring", "simplify"],
    "security": ["security", "audit", "vulnerability"],
    "logging": ["log", "logging", "logger"],
    "spec": ["spec", "specification", "requirement"],
}


def get_functional_category(name: str) -> Optional[str]:
    """根據名稱判斷功能類別。"""
    name_lower = name.lower().replace("-", "").replace("_", "")
    for category, keywords in FUNCTIONAL_KEYWORDS.items():
        for kw in keywords:
            if kw.replace("-", "") in name_lower:
                return category
    return None


def detect_overlaps(upstream_items: dict, existing_items: dict, overlaps_config: dict) -> dict:
    """偵測上游項目與本專案的重疊。

    Args:
        upstream_items: 上游 repo 的 {skills: [...], commands: [...], agents: [...]}
        existing_items: 本專案已有的 {skills: set(), commands: set(), agents: set()}
        overlaps_config: 現有 overlaps.yaml 配置

    Returns:
        dict: {
            "exact_matches": [...],      # 名稱完全相同
            "similar_names": [...],      # 名稱相似 (similarity > 0.7)
            "functional_overlaps": [...], # 功能關鍵字匹配
            "new_items": [...],          # 全新項目（無重疊）
            "already_defined": [...],    # 已在 overlaps.yaml 定義
            "suggested_groups": {...},   # 建議的群組分類
        }
    """
    result = {
        "exact_matches": [],
        "similar_names": [],
        "functional_overlaps": [],
        "new_items": [],
        "already_defined": [],
        "suggested_groups": {},
    }

    # 取得已在 overlaps.yaml 定義的項目
    defined_items = set()
    for group_name, group_def in overlaps_config.get("groups", {}).items():
        for system in ["uds", "ecc", "minimal"]:
            system_def = group_def.get(system, {})
            if isinstance(system_def, dict):
                for item_type in ["skills", "commands", "agents"]:
                    for item in system_def.get(item_type, []):
                        defined_items.add(f"{item_type}:{item}")

    for item_type in ["skills", "commands", "agents"]:
        upstream_list = upstream_items.get(item_type, [])
        existing_set = existing_items.get(item_type, set())

        for upstream_name in upstream_list:
            item_key = f"{item_type}:{upstream_name}"

            # 1. 檢查是否已在 overlaps.yaml 定義
            if item_key in defined_items:
                result["already_defined"].append({
                    "type": item_type,
                    "name": upstream_name,
                    "note": "已在 overlaps.yaml 定義"
                })
                continue

            # 2. 檢查完全匹配
            if upstream_name in existing_set:
                result["exact_matches"].append({
                    "type": item_type,
                    "name": upstream_name,
                    "local_name": upstream_name,
                    "similarity": 1.0,
                })
                continue

            # 3. 檢查名稱相似
            best_match = None
            best_similarity = 0.0
            for existing_name in existing_set:
                sim = compute_similarity(upstream_name.lower(), existing_name.lower())
                if sim > best_similarity:
                    best_similarity = sim
                    best_match = existing_name

            if best_similarity > 0.7:
                result["similar_names"].append({
                    "type": item_type,
                    "name": upstream_name,
                    "local_name": best_match,
                    "similarity": round(best_similarity, 2),
                })
                continue

            # 4. 檢查功能關鍵字匹配
            upstream_category = get_functional_category(upstream_name)
            if upstream_category:
                # 找本地同類別的項目
                local_same_category = [
                    n for n in existing_set
                    if get_functional_category(n) == upstream_category
                ]
                if local_same_category:
                    result["functional_overlaps"].append({
                        "type": item_type,
                        "name": upstream_name,
                        "category": upstream_category,
                        "local_similar": local_same_category[:3],  # 最多列 3 個
                    })
                    # 建議的群組分類
                    if upstream_category not in result["suggested_groups"]:
                        result["suggested_groups"][upstream_category] = {"uds": [], "ecc": []}
                    result["suggested_groups"][upstream_category]["ecc"].append({
                        "type": item_type,
                        "name": upstream_name,
                    })
                    continue

            # 5. 全新項目
            result["new_items"].append({
                "type": item_type,
                "name": upstream_name,
            })

    return result


def generate_overlaps_yaml_snippet(overlap_result: dict, upstream_name: str) -> str:
    """生成可直接加入 overlaps.yaml 的 YAML 片段。"""
    lines = [f"# 建議新增：來自 {upstream_name} 的重疊定義"]
    lines.append("")

    # 按建議群組輸出
    for category, items in overlap_result.get("suggested_groups", {}).items():
        lines.append(f"  # {category} 群組建議新增：")
        ecc_items = items.get("ecc", [])
        if ecc_items:
            lines.append(f"  # ecc:")
            for item in ecc_items:
                lines.append(f"  #   {item['type']}:")
                lines.append(f"  #     - {item['name']}")
        lines.append("")

    # 新增獨有項目（exclusive）
    new_items = overlap_result.get("new_items", [])
    if new_items:
        lines.append("# 建議新增到 exclusive.ecc:")
        by_type = {}
        for item in new_items:
            t = item["type"]
            if t not in by_type:
                by_type[t] = []
            by_type[t].append(item["name"])

        for t, names in by_type.items():
            lines.append(f"#   {t}:")
            for name in names:
                lines.append(f"#     - {name}")

    return "\n".join(lines)


def detect_novel_structures(file_changes: list[FileChange]) -> dict:
    """偵測上游 repo 中本專案沒有的新結構/框架。

    Returns:
        dict: {
            "new_directories": [...],  # 本專案沒有的頂層目錄
            "notable_patterns": [...],  # 值得關注的特殊模式
            "new_file_types": [...],   # 新的檔案類型
            "framework_indicators": [...],  # 框架/架構指標
        }
    """
    result = {
        "new_directories": [],
        "notable_patterns": [],
        "new_file_types": [],
        "framework_indicators": [],
    }

    seen_dirs = set()
    seen_patterns = set()
    seen_extensions = set()

    for change in file_changes:
        path = change.path

        # 1. 偵測新的頂層目錄
        top_dir = path.split("/")[0] if "/" in path else None
        if top_dir and top_dir not in seen_dirs:
            seen_dirs.add(top_dir)
            # 排除隱藏目錄和已知結構
            if not top_dir.startswith(".") and top_dir.lower() not in KNOWN_STRUCTURES:
                result["new_directories"].append({
                    "name": top_dir,
                    "example_files": [],
                })

        # 2. 偵測特殊模式
        for pattern, description in NOTABLE_PATTERNS.items():
            if pattern in path and pattern not in seen_patterns:
                seen_patterns.add(pattern)
                result["notable_patterns"].append({
                    "pattern": pattern,
                    "description": description,
                    "example_path": path,
                })

        # 3. 偵測新的檔案類型
        if "." in path:
            ext = "." + path.rsplit(".", 1)[-1].lower()
            if ext not in seen_extensions:
                seen_extensions.add(ext)
                # 關注非常見的檔案類型
                common_exts = {".md", ".txt", ".json", ".yaml", ".yml", ".js", ".ts", ".py", ".sh", ".cmd", ".ps1"}
                if ext not in common_exts:
                    result["new_file_types"].append(ext)

    # 填充新目錄的範例檔案
    for new_dir in result["new_directories"]:
        dir_name = new_dir["name"]
        examples = [c.path for c in file_changes if c.path.startswith(f"{dir_name}/")][:5]
        new_dir["example_files"] = examples

    # 4. 偵測框架指標（基於整體結構判斷）
    all_paths = [c.path for c in file_changes]

    # 偵測是否有 Plugin 架構
    if any(".claude-plugin/" in p for p in all_paths):
        result["framework_indicators"].append({
            "framework": "Claude Plugin System",
            "description": "支援 Claude Code Plugin 架構，可作為獨立插件發布",
            "files": [p for p in all_paths if ".claude-plugin/" in p][:5],
        })

    # 偵測是否有 OpenCode 支援
    if any(".opencode/" in p or "plugins/" in p for p in all_paths):
        result["framework_indicators"].append({
            "framework": "OpenCode Support",
            "description": "支援 OpenCode 整合",
            "files": [p for p in all_paths if ".opencode/" in p or "plugins/" in p][:5],
        })

    # 偵測是否有 Codex 支援
    if any(".codex/" in p for p in all_paths):
        result["framework_indicators"].append({
            "framework": "Codex Support",
            "description": "支援 Codex CLI 整合",
            "files": [p for p in all_paths if ".codex/" in p][:5],
        })

    # 偵測是否有 Hook 系統
    if any("hooks/" in p or "hooks.json" in p for p in all_paths):
        result["framework_indicators"].append({
            "framework": "Hook System",
            "description": "包含自動化 Hook 機制",
            "files": [p for p in all_paths if "hooks/" in p or "hooks.json" in p][:5],
        })

    # 偵測是否有 MCP 配置
    if any("mcp" in p.lower() for p in all_paths):
        result["framework_indicators"].append({
            "framework": "MCP Integration",
            "description": "包含 MCP (Model Context Protocol) 配置",
            "files": [p for p in all_paths if "mcp" in p.lower()][:5],
        })

    # 偵測是否有測試框架
    if any("tests/" in p or "test_" in p or "_test." in p for p in all_paths):
        result["framework_indicators"].append({
            "framework": "Test Framework",
            "description": "包含測試結構",
            "files": [p for p in all_paths if "tests/" in p or "test_" in p or "_test." in p][:5],
        })

    return result


def get_commits_between(repo_path: Path, old_commit: str, new_commit: str) -> list[CommitInfo]:
    """取得兩個 commit 之間的所有 commit。"""
    commits = []

    # 取得 commit 列表
    range_spec = f"{old_commit}..{new_commit}" if old_commit else new_commit
    result = run_git(["log", range_spec, "--pretty=format:%H|%h|%s|%an|%ai", "--no-merges"], repo_path)

    if result.returncode != 0 or not result.stdout or not result.stdout.strip():
        return commits

    for line in result.stdout.strip().split("\n"):
        if not line:
            continue
        parts = line.split("|")
        if len(parts) < 5:
            continue

        commit = CommitInfo(
            hash=parts[0],
            short_hash=parts[1],
            subject=parts[2],
            author=parts[3],
            date=parts[4],
            change_type=parse_commit_type(parts[2]),
        )

        # 取得該 commit 變更的檔案
        files_result = run_git(["show", "--name-only", "--pretty=format:", commit.hash], repo_path)
        if files_result.returncode == 0 and files_result.stdout:
            commit.files_changed = [f for f in files_result.stdout.strip().split("\n") if f]

        # 取得統計
        stat_result = run_git(["show", "--stat", "--pretty=format:", commit.hash], repo_path)
        if stat_result.returncode == 0 and stat_result.stdout:
            # 解析 "X insertions(+), Y deletions(-)"
            match = re.search(r"(\d+) insertion", stat_result.stdout)
            if match:
                commit.insertions = int(match.group(1))
            match = re.search(r"(\d+) deletion", stat_result.stdout)
            if match:
                commit.deletions = int(match.group(1))

        commits.append(commit)

    return commits


def get_file_changes(repo_path: Path, old_commit: str, new_commit: str) -> list[FileChange]:
    """取得兩個 commit 之間的檔案變更。"""
    changes = []

    if old_commit:
        # 有舊 commit，比較差異
        result = run_git(["diff", "--name-status", f"{old_commit}..{new_commit}"], repo_path)
    else:
        # 沒有舊 commit（初始同步），列出 HEAD 的所有檔案
        result = run_git(["ls-tree", "-r", "--name-only", new_commit], repo_path)
        if result.returncode == 0 and result.stdout:
            for line in result.stdout.strip().split("\n"):
                if line:
                    changes.append(FileChange(
                        path=line,
                        status="A",  # 視為新增
                        category=categorize_file(line),
                    ))
        return changes

    if result.returncode != 0 or not result.stdout:
        return changes

    for line in result.stdout.strip().split("\n"):
        if not line:
            continue
        parts = line.split("\t")
        if len(parts) < 2:
            continue

        status = parts[0][0]  # A, M, D, R, C
        path = parts[-1]  # 最後一個是目標路徑
        old_path = parts[1] if len(parts) > 2 else None  # Rename 的情況

        changes.append(FileChange(
            path=path,
            status=status,
            category=categorize_file(path),
            old_path=old_path,
        ))

    return changes


def analyze_repo(name: str, config: dict, last_sync: dict) -> Optional[RepoAnalysis]:
    """分析單一 repo。"""
    local_path = Path(config.get("local_path", "")).expanduser()

    if not local_path.exists():
        return None

    current_commit = get_current_commit(local_path)
    if not current_commit:
        return None

    last_synced = last_sync.get(name, {}).get("commit", "")

    analysis = RepoAnalysis(
        name=name,
        local_path=str(local_path),
        last_synced_commit=last_synced,
        current_commit=current_commit,
    )

    # 如果沒有新 commit
    if current_commit == last_synced:
        analysis.recommendation = "Skip"
        analysis.reasoning = "沒有新的 commit"
        return analysis

    # 取得 commit 列表
    analysis.commits = get_commits_between(local_path, last_synced, current_commit)

    # 取得檔案變更
    analysis.file_changes = get_file_changes(local_path, last_synced, current_commit)

    # 統計摘要
    summary = {
        "total_commits": len(analysis.commits),
        "by_type": {},
        "by_category": {},
        "files_added": 0,
        "files_modified": 0,
        "files_deleted": 0,
        "total_insertions": 0,
        "total_deletions": 0,
    }

    for commit in analysis.commits:
        summary["by_type"][commit.change_type] = summary["by_type"].get(commit.change_type, 0) + 1
        summary["total_insertions"] += commit.insertions
        summary["total_deletions"] += commit.deletions

    for change in analysis.file_changes:
        summary["by_category"][change.category] = summary["by_category"].get(change.category, 0) + 1
        if change.status == "A":
            summary["files_added"] += 1
        elif change.status == "M":
            summary["files_modified"] += 1
        elif change.status == "D":
            summary["files_deleted"] += 1

    # 偵測新架構/框架
    novel = detect_novel_structures(analysis.file_changes)
    summary["novel_structures"] = novel

    analysis.summary = summary

    # 生成建議
    analysis.recommendation, analysis.reasoning = generate_recommendation(analysis)

    return analysis


def generate_recommendation(analysis: RepoAnalysis) -> tuple[str, str]:
    """根據分析結果生成整合建議。"""
    summary = analysis.summary

    # 沒有變更
    if summary["total_commits"] == 0:
        return "Skip", "沒有新的變更"

    # 計算分數
    score = 0
    reasons = []

    # 新功能加分
    feat_count = summary["by_type"].get("feat", 0)
    if feat_count > 0:
        score += feat_count * 3
        reasons.append(f"{feat_count} 個新功能")

    # 修復加分
    fix_count = summary["by_type"].get("fix", 0)
    if fix_count > 0:
        score += fix_count * 2
        reasons.append(f"{fix_count} 個修復")

    # Skills 變更重要
    skills_count = summary["by_category"].get("skills", 0)
    if skills_count > 0:
        score += skills_count * 2
        reasons.append(f"{skills_count} 個 skill 變更")

    # Agents 變更重要
    agents_count = summary["by_category"].get("agents", 0)
    if agents_count > 0:
        score += agents_count * 2
        reasons.append(f"{agents_count} 個 agent 變更")

    # Commands 變更
    commands_count = summary["by_category"].get("commands", 0)
    if commands_count > 0:
        score += commands_count
        reasons.append(f"{commands_count} 個 command 變更")

    # 新增檔案加分
    if summary["files_added"] > 0:
        score += summary["files_added"]
        reasons.append(f"新增 {summary['files_added']} 個檔案")

    # 新架構/框架加分（重要！）
    novel = summary.get("novel_structures", {})

    # 新框架指標加分
    framework_indicators = novel.get("framework_indicators", [])
    if framework_indicators:
        score += len(framework_indicators) * 5  # 每個框架指標 +5
        framework_names = [f["framework"] for f in framework_indicators]
        reasons.append(f"新框架: {', '.join(framework_names)}")

    # 新目錄結構加分
    new_dirs = novel.get("new_directories", [])
    if new_dirs:
        score += len(new_dirs) * 2
        dir_names = [d["name"] for d in new_dirs[:3]]
        if len(new_dirs) > 3:
            reasons.append(f"新結構: {', '.join(dir_names)} 等 {len(new_dirs)} 個")
        else:
            reasons.append(f"新結構: {', '.join(dir_names)}")

    # 特殊模式加分
    notable_patterns = novel.get("notable_patterns", [])
    if notable_patterns:
        score += len(notable_patterns) * 2

    # 判斷建議等級
    if score >= 10:
        return "High", "、".join(reasons) + "。建議優先整合。"
    elif score >= 5:
        return "Medium", "、".join(reasons) + "。值得評估整合。"
    elif score > 0:
        return "Low", "、".join(reasons) + "。可選擇性整合。"
    else:
        return "Skip", "主要是文件或維護變更，可跳過。"


def generate_structured_report(analyses: list[RepoAnalysis], project_root: Path) -> Path:
    """生成結構化 YAML 報告。"""
    report_dir = project_root / "upstream" / "reports" / "structured"
    report_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d")
    report_file = report_dir / f"analysis-{timestamp}.yaml"

    data = {
        "generated_at": datetime.now().isoformat(),
        "summary": {
            "total_repos": len(analyses),
            "repos_with_updates": len([a for a in analyses if a.summary.get("total_commits", 0) > 0]),
            "recommendations": {
                "High": len([a for a in analyses if a.recommendation == "High"]),
                "Medium": len([a for a in analyses if a.recommendation == "Medium"]),
                "Low": len([a for a in analyses if a.recommendation == "Low"]),
                "Skip": len([a for a in analyses if a.recommendation == "Skip"]),
            },
        },
        "repos": {},
    }

    for analysis in analyses:
        data["repos"][analysis.name] = {
            "local_path": analysis.local_path,
            "last_synced_commit": analysis.last_synced_commit or "(none)",
            "current_commit": analysis.current_commit,
            "recommendation": analysis.recommendation,
            "reasoning": analysis.reasoning,
            "summary": analysis.summary,
            "commits": [
                {
                    "hash": c.short_hash,
                    "subject": c.subject,
                    "author": c.author,
                    "date": c.date,
                    "type": c.change_type,
                    "files_count": len(c.files_changed),
                }
                for c in analysis.commits[:20]  # 最多 20 個
            ],
            "file_changes": [
                {
                    "path": f.path,
                    "status": f.status,
                    "category": f.category,
                }
                for f in analysis.file_changes[:50]  # 最多 50 個
            ],
        }

    with open(report_file, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    return report_file


def analyze_new_repo(repo_path: Path, project_root: Optional[Path] = None) -> Optional[RepoAnalysis]:
    """分析新的本地 repo（全量分析，非 commit 差異）。"""
    if not repo_path.exists():
        return None

    # 確認是 git repo
    if not (repo_path / ".git").exists():
        return None

    current_commit = get_current_commit(repo_path)
    if not current_commit:
        return None

    # 取得 repo 名稱
    name = repo_path.name

    # 嘗試取得遠端 URL
    remote_result = run_git(["remote", "get-url", "origin"], repo_path)
    remote_url = remote_result.stdout.strip() if remote_result.returncode == 0 else ""

    analysis = RepoAnalysis(
        name=name,
        local_path=str(repo_path),
        last_synced_commit="",  # 新 repo 沒有上次同步
        current_commit=current_commit,
    )

    # 取得所有檔案（全量）
    analysis.file_changes = get_file_changes(repo_path, "", current_commit)

    # 取得最近 50 個 commit
    analysis.commits = get_commits_between(repo_path, "", current_commit)[:50]

    # 統計摘要
    summary = {
        "total_commits": len(analysis.commits),
        "by_type": {},
        "by_category": {},
        "files_added": len(analysis.file_changes),  # 全量分析視為新增
        "files_modified": 0,
        "files_deleted": 0,
        "total_insertions": 0,
        "total_deletions": 0,
        "remote_url": remote_url,
        "is_new_repo": True,
    }

    for commit in analysis.commits:
        summary["by_type"][commit.change_type] = summary["by_type"].get(commit.change_type, 0) + 1
        summary["total_insertions"] += commit.insertions
        summary["total_deletions"] += commit.deletions

    for change in analysis.file_changes:
        summary["by_category"][change.category] = summary["by_category"].get(change.category, 0) + 1

    # 偵測新架構/框架（對新 repo 評估很重要）
    novel = detect_novel_structures(analysis.file_changes)
    summary["novel_structures"] = novel

    # 偵測重疊（若提供了 project_root）
    if project_root:
        # 從檔案變更中提取 skills, commands, agents 名稱
        upstream_items = extract_items_from_file_changes(analysis.file_changes)
        existing_items = get_existing_items(project_root)
        overlaps_config = load_overlaps_yaml(project_root)
        overlap_analysis = detect_overlaps(upstream_items, existing_items, overlaps_config)
        summary["overlap_analysis"] = overlap_analysis

    analysis.summary = summary

    # 生成建議（針對新 repo 的特殊評估）
    analysis.recommendation, analysis.reasoning = generate_new_repo_recommendation(analysis)

    return analysis


def extract_items_from_file_changes(file_changes: list[FileChange]) -> dict:
    """從檔案變更中提取 skills, commands, agents 名稱。"""
    items = {
        "skills": [],
        "commands": [],
        "agents": [],
    }

    seen = {"skills": set(), "commands": set(), "agents": set()}

    for change in file_changes:
        path = change.path

        # skills: skills/xxx/SKILL.md -> xxx
        if "/skills/" in path or path.startswith("skills/"):
            parts = path.split("/")
            if "skills" in parts:
                idx = parts.index("skills")
                if idx + 1 < len(parts):
                    skill_name = parts[idx + 1]
                    if skill_name not in seen["skills"]:
                        seen["skills"].add(skill_name)
                        items["skills"].append(skill_name)

        # commands: commands/xxx.md -> xxx (去除 .md)
        if "/commands/" in path or path.startswith("commands/"):
            parts = path.split("/")
            if "commands" in parts:
                idx = parts.index("commands")
                if idx + 1 < len(parts):
                    cmd_file = parts[idx + 1] if idx + 1 < len(parts) else ""
                    # 可能是目錄下的檔案
                    if cmd_file and not cmd_file.endswith(".md"):
                        # 繼續找
                        for p in parts[idx + 1:]:
                            if p.endswith(".md"):
                                cmd_file = p
                                break
                    if cmd_file.endswith(".md"):
                        cmd_name = cmd_file[:-3]  # 去除 .md
                        if cmd_name not in seen["commands"]:
                            seen["commands"].add(cmd_name)
                            items["commands"].append(cmd_name)

        # agents: agents/xxx.md -> xxx
        if "/agents/" in path or path.startswith("agents/"):
            parts = path.split("/")
            if "agents" in parts:
                idx = parts.index("agents")
                for p in parts[idx + 1:]:
                    if p.endswith(".md"):
                        agent_name = p[:-3]
                        if agent_name not in seen["agents"]:
                            seen["agents"].add(agent_name)
                            items["agents"].append(agent_name)
                        break

    return items


def generate_new_repo_recommendation(analysis: RepoAnalysis) -> tuple[str, str]:
    """針對新 repo 生成整合建議。"""
    summary = analysis.summary
    reasons = []
    score = 0

    # 檢查是否有 skills
    skills_count = summary["by_category"].get("skills", 0)
    if skills_count > 0:
        score += skills_count * 3
        reasons.append(f"包含 {skills_count} 個 skill 檔案")

    # 檢查是否有 agents
    agents_count = summary["by_category"].get("agents", 0)
    if agents_count > 0:
        score += agents_count * 3
        reasons.append(f"包含 {agents_count} 個 agent 檔案")

    # 檢查是否有 commands
    commands_count = summary["by_category"].get("commands", 0)
    if commands_count > 0:
        score += commands_count * 2
        reasons.append(f"包含 {commands_count} 個 command 檔案")

    # 檢查是否有 hooks
    hooks_count = summary["by_category"].get("hooks", 0)
    if hooks_count > 0:
        score += hooks_count * 2
        reasons.append(f"包含 {hooks_count} 個 hook 檔案")

    # 檢查活躍度（最近 commit 數量）
    if summary["total_commits"] > 0:
        reasons.append(f"近期有 {summary['total_commits']} 個 commit")

    # 新架構/框架評估（重要！）
    novel = summary.get("novel_structures", {})

    # 新框架指標（高價值）
    framework_indicators = novel.get("framework_indicators", [])
    if framework_indicators:
        score += len(framework_indicators) * 5
        framework_names = [f["framework"] for f in framework_indicators]
        reasons.append(f"新框架: {', '.join(framework_names)}")

    # 新目錄結構（值得關注）
    new_dirs = novel.get("new_directories", [])
    if new_dirs:
        score += len(new_dirs) * 2
        dir_names = [d["name"] for d in new_dirs[:3]]
        if len(new_dirs) > 3:
            reasons.append(f"新結構: {', '.join(dir_names)} 等 {len(new_dirs)} 個")
        elif new_dirs:
            reasons.append(f"新結構: {', '.join(dir_names)}")

    # 特殊模式
    notable_patterns = novel.get("notable_patterns", [])
    if notable_patterns:
        score += len(notable_patterns) * 2
        pattern_desc = [p["description"] for p in notable_patterns[:3]]
        if len(notable_patterns) > 3:
            reasons.append(f"特殊模式: {', '.join(pattern_desc)} 等")
        elif notable_patterns:
            reasons.append(f"特殊模式: {', '.join(pattern_desc)}")

    # 判斷是否值得整合
    if score >= 15:
        return "Evaluate", "、".join(reasons) + "。高價值，建議詳細評估內容品質與整合價值。"
    elif score >= 8:
        return "Evaluate", "、".join(reasons) + "。建議詳細評估內容品質與整合價值。"
    elif score >= 3:
        return "Review", "、".join(reasons) + "。可參考其中部分內容。"
    else:
        return "Skip", "沒有發現可整合的 skills/agents/commands 或新架構。"


def generate_new_repo_report(analysis: RepoAnalysis, project_root: Path, generate_overlaps: bool = False) -> Path:
    """生成新 repo 評估報告。"""
    report_dir = project_root / "upstream" / "reports" / "new-repos"
    report_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    report_file = report_dir / f"eval-{analysis.name}-{timestamp}.yaml"

    data = {
        "generated_at": datetime.now().isoformat(),
        "report_type": "new_repo_evaluation",
        "repo": {
            "name": analysis.name,
            "local_path": analysis.local_path,
            "remote_url": analysis.summary.get("remote_url", ""),
            "current_commit": analysis.current_commit,
            "recommendation": analysis.recommendation,
            "reasoning": analysis.reasoning,
            "summary": analysis.summary,
            "recent_commits": [
                {
                    "hash": c.short_hash,
                    "subject": c.subject,
                    "author": c.author,
                    "date": c.date,
                    "type": c.change_type,
                }
                for c in analysis.commits[:20]
            ],
            "file_structure": {
                "skills": [f.path for f in analysis.file_changes if f.category == "skills"][:30],
                "agents": [f.path for f in analysis.file_changes if f.category == "agents"][:20],
                "commands": [f.path for f in analysis.file_changes if f.category == "commands"][:20],
                "hooks": [f.path for f in analysis.file_changes if f.category == "hooks"][:10],
                "docs": [f.path for f in analysis.file_changes if f.category == "docs"][:10],
                "other_count": len([f for f in analysis.file_changes if f.category == "other"]),
            },
        },
    }

    # 加入 overlap_analysis（若有）
    overlap_analysis = analysis.summary.get("overlap_analysis")
    if overlap_analysis:
        data["repo"]["overlap_analysis"] = overlap_analysis

    with open(report_file, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    # 若 generate_overlaps，另外生成 overlaps.yaml 草稿
    if generate_overlaps and overlap_analysis:
        draft_file = report_dir / f"overlaps-draft-{analysis.name}-{timestamp}.yaml"
        snippet = generate_overlaps_yaml_snippet(overlap_analysis, analysis.name)
        with open(draft_file, "w", encoding="utf-8") as f:
            f.write(snippet)
        print(f"重疊定義草稿: {draft_file}")

    return report_file


def main():
    parser = argparse.ArgumentParser(description="分析上游 repository 變更")
    parser.add_argument("--source", type=str, action="append", help="只分析特定 source（可多次指定）")
    parser.add_argument("--update-sync", action="store_true", help="更新 last-sync.yaml")
    parser.add_argument("--new-repo", type=str, metavar="PATH", help="分析新的本地 repo（評估是否適合整合）")
    parser.add_argument("--detect-overlaps", action="store_true", help="偵測重疊並加入報告")
    parser.add_argument("--generate-overlaps", action="store_true", help="生成 overlaps.yaml 草稿（需配合 --new-repo 或 --detect-overlaps）")
    args = parser.parse_args()

    project_root = get_project_root()
    print(f"專案根目錄: {project_root}")

    # 新 repo 評估模式
    if args.new_repo:
        repo_path = Path(args.new_repo).expanduser().resolve()
        print(f"\n評估新 repo: {repo_path}")

        if not repo_path.exists():
            print(f"錯誤: 路徑不存在: {repo_path}")
            sys.exit(1)

        if not (repo_path / ".git").exists():
            print(f"錯誤: 不是 git repository: {repo_path}")
            sys.exit(1)

        # 若 --detect-overlaps 或 --generate-overlaps，傳入 project_root 以執行重疊偵測
        detect = args.detect_overlaps or args.generate_overlaps
        analysis = analyze_new_repo(repo_path, project_root if detect else None)
        if not analysis:
            print("錯誤: 無法分析 repo")
            sys.exit(1)

        print(f"\n分析完成:")
        print(f"  名稱: {analysis.name}")
        print(f"  檔案數: {len(analysis.file_changes)}")
        print(f"  Skills: {analysis.summary['by_category'].get('skills', 0)}")
        print(f"  Agents: {analysis.summary['by_category'].get('agents', 0)}")
        print(f"  Commands: {analysis.summary['by_category'].get('commands', 0)}")
        print(f"  建議: {analysis.recommendation}")
        print(f"  原因: {analysis.reasoning}")

        # 顯示重疊分析（若有）
        overlap_analysis = analysis.summary.get("overlap_analysis")
        if overlap_analysis:
            print(f"\n=== 重疊分析 ===")
            print(f"  完全匹配: {len(overlap_analysis.get('exact_matches', []))} 個")
            print(f"  名稱相似: {len(overlap_analysis.get('similar_names', []))} 個")
            print(f"  功能重疊: {len(overlap_analysis.get('functional_overlaps', []))} 個")
            print(f"  全新項目: {len(overlap_analysis.get('new_items', []))} 個")
            print(f"  已定義: {len(overlap_analysis.get('already_defined', []))} 個")

        # 生成報告
        report_file = generate_new_repo_report(analysis, project_root, args.generate_overlaps)
        print(f"\n報告已生成: {report_file}")
        print(f"\n下一步: 執行 /upstream-compare --new-repo {report_file.name}")
        return

    # 一般模式：分析已註冊的上游 repo
    sources = load_sources(project_root)
    if not sources.get("sources"):
        print("錯誤: 未找到 upstream/sources.yaml 或內容為空")
        sys.exit(1)

    last_sync = load_last_sync(project_root)

    # 篩選特定 source
    if args.source:
        missing = [s for s in args.source if s not in sources["sources"]]
        if missing:
            print(f"錯誤: Source 不存在: {', '.join(missing)}")
            sys.exit(1)
        sources["sources"] = {k: v for k, v in sources["sources"].items() if k in args.source}

    print(f"\n分析 {len(sources['sources'])} 個 repository...\n")

    analyses = []
    for name, config in sources["sources"].items():
        print(f"  [{name}] 分析中...")
        analysis = analyze_repo(name, config, last_sync)
        if analysis:
            analyses.append(analysis)
            commits = analysis.summary.get("total_commits", 0)
            print(f"  [{name}] {commits} 個新 commit, 建議: {analysis.recommendation}")
        else:
            print(f"  [{name}] 無法分析（可能未 clone）")

    print("\n生成報告...")

    # 生成結構化報告
    structured_file = generate_structured_report(analyses, project_root)
    print(f"  結構化報告: {structured_file}")

    # 更新 last-sync.yaml
    if args.update_sync:
        for analysis in analyses:
            if analysis.current_commit:
                last_sync[analysis.name] = {
                    "commit": analysis.current_commit,
                    "synced_at": datetime.now().isoformat(),
                }
        save_last_sync(project_root, last_sync)
        print(f"\n已更新 last-sync.yaml")

    # 顯示摘要
    high_count = len([a for a in analyses if a.recommendation == "High"])
    medium_count = len([a for a in analyses if a.recommendation == "Medium"])

    print(f"\n=== 摘要 ===")
    print(f"建議優先整合: {high_count} 個")
    print(f"建議評估整合: {medium_count} 個")
    print(f"\n查看報告: {structured_file}")


if __name__ == "__main__":
    main()
