"""
Manifest 機制：追蹤分發檔案並管理孤兒清理與衝突檢測。

Schema v2：以 file 為單位記錄 base hash + src commit + decision，支援 3-way
衝突分類（clean / local-only / both-changed / no-base）與 skip 記憶。

v1 向下相容：v1 manifest 在第一次讀取時自動 migration；下游若需要 v1 view
可呼叫 `v2_to_v1_view()`。
"""

import hashlib
import shutil
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Literal
import yaml
from rich.console import Console

console = Console()

# 類型定義
from .shared import TargetType, ResourceType

RESOURCE_TYPES: tuple[ResourceType, ...] = (
    "skills",
    "commands",
    "agents",
    "workflows",
)

SCHEMA_VERSION = 2

ConflictClass = Literal["clean", "local-only", "both-changed", "no-base"]


# ============================================================
# Hash 計算
# ============================================================


def compute_file_hash(path: Path) -> str:
    """計算單檔案的 SHA-256 hash。

    Args:
        path: 檔案路徑

    Returns:
        str: 格式為 "sha256:<hex_digest>"
    """
    sha256 = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return f"sha256:{sha256.hexdigest()}"


def _is_excluded_for_hash(file_path: Path) -> bool:
    """檢查檔案是否應被 hash 計算排除。"""
    if "__pycache__" in file_path.parts:
        return True
    if file_path.suffix in {".pyc", ".pyo"}:
        return True
    return False


def compute_skill_file_map(path: Path) -> dict[str, str]:
    """對 skill 目錄內每個檔案計算 sha256，回傳 rel_path → sha256 對照表。

    使用與 compute_dir_hash 相同的排除規則。
    """
    if not path.is_dir():
        return {}
    out: dict[str, str] = {}
    for file_path in sorted(path.rglob("*"), key=lambda p: str(p.relative_to(path))):
        if not file_path.is_file() or _is_excluded_for_hash(file_path):
            continue
        rel = str(file_path.relative_to(path))
        out[rel] = compute_file_hash(file_path)
    return out


def compute_dir_hash(path: Path) -> str:
    """遞迴計算目錄的組合 hash。

    遍歷目錄內所有檔案，計算每個檔案的 hash，
    按檔案相對路徑排序後組合成總 hash。

    排除不應影響分發內容的快取目錄與編譯產物。

    Args:
        path: 目錄路徑

    Returns:
        str: 格式為 "sha256:<hex_digest>"
    """
    if not path.is_dir():
        return compute_file_hash(path)

    sha256 = hashlib.sha256()
    # 收集所有檔案並排序
    files = sorted(path.rglob("*"), key=lambda p: str(p.relative_to(path)))

    for file_path in files:
        if file_path.is_file():
            if "__pycache__" in file_path.parts:
                continue
            if file_path.suffix in {".pyc", ".pyo"}:
                continue
            # 將相對路徑加入 hash 計算（確保檔案結構變化也會影響 hash）
            rel_path = str(file_path.relative_to(path))
            sha256.update(rel_path.encode("utf-8"))
            # 計算檔案內容 hash
            file_hash = compute_file_hash(file_path)
            sha256.update(file_hash.encode("utf-8"))

    return f"sha256:{sha256.hexdigest()}"


# ============================================================
# Dataclasses
# ============================================================


@dataclass
class FileEntry:
    """單一檔案的 v2 base 紀錄。"""

    src_hash: str
    src_commit: str
    src_source: str
    dst_hash_at_sync: str
    decision: str
    decided_at: str

    def to_dict(self) -> dict:
        return {
            "src_hash": self.src_hash,
            "src_commit": self.src_commit,
            "src_source": self.src_source,
            "dst_hash_at_sync": self.dst_hash_at_sync,
            "decision": self.decision,
            "decided_at": self.decided_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "FileEntry | None":
        required = ("src_hash", "src_commit", "src_source", "dst_hash_at_sync")
        if not all(k in data for k in required):
            return None
        return cls(
            src_hash=data["src_hash"],
            src_commit=data["src_commit"],
            src_source=data["src_source"],
            dst_hash_at_sync=data["dst_hash_at_sync"],
            decision=data.get("decision", "accepted"),
            decided_at=data.get("decided_at", ""),
        )


@dataclass
class SkippedEntry:
    """skip 記憶。"""

    src_commit: str
    decided_at: str

    def to_dict(self) -> dict:
        return {"src_commit": self.src_commit, "decided_at": self.decided_at}

    @classmethod
    def from_dict(cls, data: dict) -> "SkippedEntry | None":
        if "src_commit" not in data:
            return None
        return cls(src_commit=data["src_commit"], decided_at=data.get("decided_at", ""))


@dataclass
class FileRecord:
    """記錄單一檔案/目錄的資訊。

    v2 擴充：
    - `files`: skill 內 rel_path → sha256 對照（單檔資源為空 dict）。
    - `src_path`: 真正的 src 來源路徑（用於查 git commit；不寫 manifest）。
    - `src_commit`: 預先解析的 src commit（不寫到本欄，會落到 FileEntry）。
    """

    name: str
    hash: str
    source: str = "custom-skills"
    source_path: Path | None = None
    files: dict[str, str] = field(default_factory=dict)
    src_path: Path | None = None
    src_commit: str | None = None


@dataclass
class ConflictInfo:
    """衝突資訊。"""

    name: str
    resource_type: ResourceType
    old_hash: str
    current_hash: str
    source_path: Path | None = None
    target_path: Path | None = None


@dataclass
class ManifestTracker:
    """追蹤分發過程中的檔案。"""

    target: str
    skills: dict[str, FileRecord] = field(default_factory=dict)
    commands: dict[str, FileRecord] = field(default_factory=dict)
    agents: dict[str, FileRecord] = field(default_factory=dict)
    workflows: dict[str, FileRecord] = field(default_factory=dict)

    def record_skill(
        self,
        name: str,
        source_path: Path,
        source: str = "custom-skills",
        src_path: Path | None = None,
    ) -> None:
        """記錄已複製的 skill。

        Args:
            source_path: 用於 hash / file map 計算的路徑（通常是 dst 副本）。
            src_path: 真正的 src 來源路徑（用於查 git commit）。
        """
        hash_value = compute_dir_hash(source_path)
        files_map = compute_skill_file_map(source_path)
        self.skills[name] = FileRecord(
            name=name,
            hash=hash_value,
            source=source,
            source_path=source_path,
            files=files_map,
            src_path=src_path or source_path,
        )

    def record_command(
        self,
        name: str,
        source_path: Path,
        source: str = "custom-skills",
        src_path: Path | None = None,
    ) -> None:
        """記錄已複製的 command。"""
        hash_value = compute_file_hash(source_path)
        self.commands[name] = FileRecord(
            name=name,
            hash=hash_value,
            source=source,
            source_path=source_path,
            src_path=src_path or source_path,
        )

    def record_agent(
        self,
        name: str,
        source_path: Path,
        source: str = "custom-skills",
        src_path: Path | None = None,
    ) -> None:
        """記錄已複製的 agent。"""
        hash_value = compute_file_hash(source_path)
        self.agents[name] = FileRecord(
            name=name,
            hash=hash_value,
            source=source,
            source_path=source_path,
            src_path=src_path or source_path,
        )

    def record_workflow(
        self,
        name: str,
        source_path: Path,
        source: str = "custom-skills",
        src_path: Path | None = None,
    ) -> None:
        """記錄已複製的 workflow。"""
        hash_value = compute_file_hash(source_path)
        self.workflows[name] = FileRecord(
            name=name,
            hash=hash_value,
            source=source,
            source_path=source_path,
            src_path=src_path or source_path,
        )

    def to_manifest(
        self,
        version: str,
        *,
        previous_manifest: dict | None = None,
        last_sync_commit_by_source: dict[str, str] | None = None,
    ) -> dict:
        """轉換為 v2 manifest 字典格式。

        Args:
            version: 專案版本（保留 v1 的 `version` 欄位）。
            previous_manifest: 既有 manifest，用於保留現有 FileEntry 與 skipped。
            last_sync_commit_by_source: 本輪結束時各 source 的 HEAD commit。
        """
        prev_files = (previous_manifest or {}).get("files", {})

        def build_skill_entry(name: str, record: FileRecord) -> dict:
            entry: dict = {"hash": record.hash, "source": record.source}
            prev = prev_files.get("skills", {}).get(name, {})
            existing_files = prev.get("files", {}) if isinstance(prev, dict) else {}
            existing_skipped = prev.get("skipped", {}) if isinstance(prev, dict) else {}
            files_block: dict = {}
            for rel, file_hash in record.files.items():
                base = existing_files.get(rel)
                if isinstance(base, dict):
                    files_block[rel] = base
            if files_block:
                entry["files"] = files_block
            if existing_skipped:
                entry["skipped"] = existing_skipped
            return entry

        def build_single_entry(record: FileRecord, prev_section: dict) -> dict:
            entry: dict = {"hash": record.hash, "source": record.source}
            prev = prev_section.get(record.name, {})
            for k in ("src_hash", "src_commit", "src_source", "dst_hash_at_sync", "decision", "decided_at"):
                if isinstance(prev, dict) and k in prev:
                    entry[k] = prev[k]
            if isinstance(prev, dict) and "skipped" in prev:
                entry["skipped"] = prev["skipped"]
            return entry

        prev_commit_map = (previous_manifest or {}).get("last_sync_commit_by_source", {}) or {}
        merged_commit_map = dict(prev_commit_map)
        if last_sync_commit_by_source:
            merged_commit_map.update(last_sync_commit_by_source)

        return {
            "schema_version": SCHEMA_VERSION,
            "managed_by": "ai-dev",
            "version": version,
            "last_sync": datetime.now().astimezone().isoformat(),
            "target": self.target,
            "last_sync_commit_by_source": merged_commit_map,
            "files": {
                "skills": {
                    name: build_skill_entry(name, record)
                    for name, record in self.skills.items()
                },
                "commands": {
                    name: build_single_entry(record, prev_files.get("commands", {}))
                    for name, record in self.commands.items()
                },
                "agents": {
                    name: build_single_entry(record, prev_files.get("agents", {}))
                    for name, record in self.agents.items()
                },
                "workflows": {
                    name: build_single_entry(record, prev_files.get("workflows", {}))
                    for name, record in self.workflows.items()
                },
            },
        }


# ============================================================
# Manifest 讀寫
# ============================================================


def get_manifest_dir() -> Path:
    """返回 manifest 目錄路徑。"""
    return Path.home() / ".config" / "ai-dev" / "manifests"


def get_manifest_path(target: TargetType) -> Path:
    """返回指定平台的 manifest 路徑。

    Args:
        target: 目標平台名稱 (claude, opencode, antigravity, codex, agy)

    Returns:
        Path: manifest 檔案路徑
    """
    return get_manifest_dir() / f"{target}.yaml"


def read_manifest(target: TargetType) -> dict | None:
    """讀取 manifest 檔案。

    Args:
        target: 目標平台名稱

    Returns:
        dict | None: manifest 內容，不存在或損壞時返回 None
    """
    manifest_path = get_manifest_path(target)

    if not manifest_path.exists():
        return None

    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            if data is None or not isinstance(data, dict):
                console.print(
                    f"[yellow]警告：manifest 檔案格式無效，將視為首次分發[/yellow]"
                )
                return None
            return data
    except yaml.YAMLError as e:
        console.print(f"[yellow]警告：manifest 檔案損壞 ({e})，將視為首次分發[/yellow]")
        return None
    except Exception as e:
        console.print(
            f"[yellow]警告：讀取 manifest 失敗 ({e})，將視為首次分發[/yellow]"
        )
        return None


def write_manifest(target: TargetType, manifest: dict) -> None:
    """寫入 manifest 檔案。

    Args:
        target: 目標平台名稱
        manifest: manifest 內容
    """
    manifest_path = get_manifest_path(target)

    # 自動建立目錄
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    with open(manifest_path, "w", encoding="utf-8") as f:
        yaml.dump(
            manifest, f, allow_unicode=True, default_flow_style=False, sort_keys=False
        )


# ============================================================
# 衝突檢測
# ============================================================


def _get_target_resource_path(
    target: TargetType, resource_type: ResourceType, name: str
) -> Path | None:
    """取得目標檔案/目錄的路徑。"""
    # 延遲導入避免循環依賴
    from .shared import get_target_path

    base_path = get_target_path(target, resource_type)
    if not base_path:
        return None

    if resource_type == "skills":
        return base_path / name
    else:
        return base_path / f"{name}.md"


def detect_conflicts(
    target: TargetType,
    old_manifest: dict | None,
    new_tracker: ManifestTracker,
) -> list[ConflictInfo]:
    """檢測衝突。

    比對目標檔案 hash 與 manifest 記錄的 hash。

    Args:
        target: 目標平台名稱
        old_manifest: 舊的 manifest（可為 None）
        new_tracker: 新的 ManifestTracker（包含即將分發的檔案清單）

    Returns:
        list[ConflictInfo]: 衝突清單
    """
    if old_manifest is None:
        # 首次分發，不報告衝突
        return []

    conflicts = []
    old_files = old_manifest.get("files", {})

    # 檢查各資源類型
    for resource_type in RESOURCE_TYPES:
        old_records = old_files.get(resource_type, {})
        new_records = getattr(new_tracker, resource_type, {})

        for name in new_records:
            if name not in old_records:
                # 新檔案，不是衝突
                continue

            old_hash = old_records[name].get("hash", "")
            target_path = _get_target_resource_path(target, resource_type, name)

            if target_path is None or not target_path.exists():
                # 目標不存在，不是衝突
                continue

            # 計算目標檔案當前 hash
            if resource_type == "skills":
                current_hash = compute_dir_hash(target_path)
            else:
                current_hash = compute_file_hash(target_path)

            # 比對
            if current_hash != old_hash:
                # 從 tracker 取得來源路徑
                file_record = new_records.get(name)
                src_path = file_record.source_path if file_record else None
                conflicts.append(
                    ConflictInfo(
                        name=name,
                        resource_type=resource_type,
                        old_hash=old_hash,
                        current_hash=current_hash,
                        source_path=src_path,
                        target_path=target_path,
                    )
                )

    return conflicts


def display_conflicts(conflicts: list[ConflictInfo]) -> None:
    """格式化顯示衝突清單。

    Args:
        conflicts: 衝突清單
    """
    if not conflicts:
        return

    console.print()
    console.print("[bold yellow]偵測到以下檔案已被修改：[/bold yellow]")
    console.print()

    for conflict in conflicts:
        console.print(f"  [yellow]•[/yellow] {conflict.resource_type}/{conflict.name}")
        console.print(f"    [dim]原始: {conflict.old_hash[:20]}...[/dim]")
        console.print(f"    [dim]目前: {conflict.current_hash[:20]}...[/dim]")

    console.print()


def prompt_conflict_action(conflicts: list[ConflictInfo] | None = None) -> str:
    """互動式詢問用戶衝突處理方式。

    Args:
        conflicts: 衝突清單（用於查看差異功能）

    Returns:
        str: "force", "skip", "backup", "diff", 或 "abort"
    """
    console.print("[bold]請選擇處理方式：[/bold]")
    console.print("  [cyan]1[/cyan]. 強制覆蓋所有衝突檔案")
    console.print("  [cyan]2[/cyan]. 跳過衝突檔案")
    console.print("  [cyan]3[/cyan]. 備份後覆蓋")
    console.print("  [cyan]4[/cyan]. 查看差異")
    console.print("  [cyan]5[/cyan]. 取消分發")
    console.print()

    while True:
        try:
            choice = input("請輸入選項 (1-5): ").strip()
            if choice == "1":
                return "force"
            elif choice == "2":
                return "skip"
            elif choice == "3":
                return "backup"
            elif choice == "4":
                return "diff"
            elif choice == "5":
                return "abort"
            else:
                console.print("[red]無效選項，請輸入 1-5[/red]")
        except (EOFError, KeyboardInterrupt):
            return "abort"


def show_conflict_diff(conflicts: list[ConflictInfo]) -> None:
    """顯示衝突檔案的來源與目標差異。

    Args:
        conflicts: 衝突清單
    """
    import subprocess

    for conflict in conflicts:
        console.print()
        console.print(
            f"[bold cyan]=== {conflict.resource_type}/{conflict.name} 差異 ===[/bold cyan]"
        )

        if conflict.source_path is None or conflict.target_path is None:
            console.print("[yellow]  無法取得路徑，跳過此項差異[/yellow]")
            continue

        if not conflict.source_path.exists() or not conflict.target_path.exists():
            console.print("[yellow]  來源或目標路徑不存在，跳過此項差異[/yellow]")
            continue

        # Skills 為目錄，使用遞迴 diff；其餘為單檔
        if conflict.resource_type == "skills":
            cmd = ["diff", "-ruN", str(conflict.source_path), str(conflict.target_path)]
        else:
            cmd = ["diff", "-u", str(conflict.source_path), str(conflict.target_path)]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            # diff 回傳 1 表示有差異（正常），回傳 2 表示錯誤
            if result.stdout:
                console.print(result.stdout)
            elif result.returncode == 0:
                console.print("[dim]  無差異[/dim]")
            elif result.stderr:
                console.print(f"[red]  {result.stderr.strip()}[/red]")
        except FileNotFoundError:
            console.print("[yellow]  diff 工具未安裝，無法顯示差異[/yellow]")

    console.print()


# ============================================================
# 備份功能
# ============================================================


def get_backup_dir(target: TargetType) -> Path:
    """返回備份目錄路徑。

    Args:
        target: 目標平台名稱

    Returns:
        Path: 備份目錄路徑
    """
    return Path.home() / ".config" / "ai-dev" / "backups" / target


def backup_file(
    target: TargetType,
    resource_type: ResourceType,
    name: str,
) -> Path | None:
    """備份單個檔案/目錄。

    Args:
        target: 目標平台名稱
        resource_type: 資源類型
        name: 資源名稱

    Returns:
        Path | None: 備份路徑，若失敗則返回 None
    """
    import shutil

    target_path = _get_target_resource_path(target, resource_type, name)
    if target_path is None or not target_path.exists():
        return None

    backup_dir = get_backup_dir(target) / resource_type
    backup_dir.mkdir(parents=True, exist_ok=True)

    # 備份檔名格式：<name>.<timestamp>
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{name}.{timestamp}"
    backup_path = backup_dir / backup_name

    try:
        if target_path.is_dir():
            shutil.copytree(target_path, backup_path)
        else:
            shutil.copy2(target_path, backup_path)
        console.print(f"  [dim]已備份: {name} → {backup_path.name}[/dim]")
        return backup_path
    except Exception as e:
        console.print(f"[red]備份失敗 ({name}): {e}[/red]")
        return None


# ============================================================
# 孤兒檔案處理
# ============================================================


def find_orphans(
    old_manifest: dict | None,
    new_manifest: dict,
) -> dict[ResourceType, list[str]]:
    """比對新舊 manifest，識別孤兒檔案。

    孤兒檔案：存在於舊 manifest 但不存在於新 manifest 的檔案。

    Args:
        old_manifest: 舊的 manifest（可為 None）
        new_manifest: 新的 manifest

    Returns:
        dict[str, list[str]]: 按資源類型分組的孤兒檔案清單
    """
    if old_manifest is None:
        # 無舊 manifest，不產生孤兒清單
        return {key: [] for key in RESOURCE_TYPES}

    old_files = old_manifest.get("files", {})
    new_files = new_manifest.get("files", {})

    orphans: dict[ResourceType, list[str]] = {}
    for resource_type in RESOURCE_TYPES:
        old_names = set(old_files.get(resource_type, {}).keys())
        new_names = set(new_files.get(resource_type, {}).keys())
        orphans[resource_type] = sorted(old_names - new_names)

    return orphans


def cleanup_orphans(target: TargetType, orphans: dict[ResourceType, list[str]]) -> None:
    """清理孤兒檔案。

    Args:
        target: 目標平台名稱
        orphans: 按資源類型分組的孤兒檔案清單
    """
    import shutil

    total = sum(len(names) for names in orphans.values())
    if total == 0:
        return

    console.print()
    console.print(f"[bold cyan]清理孤兒檔案 ({total} 個)...[/bold cyan]")

    for resource_type, names in orphans.items():
        for name in names:
            target_path = _get_target_resource_path(target, resource_type, name)
            if target_path is None:
                continue

            if not target_path.exists():
                console.print(f"  [dim]跳過（不存在）: {resource_type}/{name}[/dim]")
                continue

            try:
                if target_path.is_dir():
                    shutil.rmtree(target_path)
                else:
                    target_path.unlink()
                console.print(f"  [green]已刪除: {resource_type}/{name}[/green]")
            except Exception as e:
                console.print(f"  [red]刪除失敗 ({resource_type}/{name}): {e}[/red]")


# ============================================================
# 版本號讀取
# ============================================================


def get_project_version() -> str:
    """從 pyproject.toml 讀取專案版本號。

    Returns:
        str: 版本號，讀取失敗時返回 "unknown"
    """
    try:
        # 嘗試從 importlib.metadata 讀取（已安裝的套件）
        from importlib.metadata import version

        return version("ai-dev")
    except Exception:
        pass

    # 嘗試從 pyproject.toml 讀取
    try:
        from .paths import get_project_root

        pyproject_path = get_project_root() / "pyproject.toml"
        if pyproject_path.exists():
            import tomllib

            with open(pyproject_path, "rb") as f:
                data = tomllib.load(f)
                return data.get("project", {}).get("version", "unknown")
    except Exception:
        pass

    return "unknown"


# ============================================================
# v2: 3-way merge tracking helpers
# ============================================================


def _builtin_source_paths() -> dict[str, Path]:
    from .paths import get_custom_skills_dir, get_ecc_dir

    return {
        "custom-skills": get_custom_skills_dir(),
        "ecc": get_ecc_dir(),
    }


SOURCE_REPO_PATHS: dict[str, Path] = _builtin_source_paths()


def get_source_repo_path(source: str) -> Path | None:
    """回傳指定 source 的本地 git repo 路徑。"""
    if source in SOURCE_REPO_PATHS:
        path = SOURCE_REPO_PATHS[source]
        return path if path.exists() else None
    # custom repo：從 repos.yaml 取
    try:
        from .custom_repos import expand_local_path, load_custom_repos

        repos = load_custom_repos().get("repos", {})
        info = repos.get(source)
        if info:
            local_path = expand_local_path(info)
            if local_path.exists():
                return local_path
    except Exception:
        return None
    return None


def _git(repo: Path, *args: str) -> str | None:
    """執行 git 指令並回傳 stdout strip 後的字串；失敗回 None。"""
    try:
        result = subprocess.run(
            ["git", "-C", str(repo), *args],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            return None
        return result.stdout.strip()
    except Exception:
        return None


def get_repo_head(source: str) -> str | None:
    """取得指定 source 當前 HEAD commit。"""
    repo = get_source_repo_path(source)
    if not repo:
        return None
    return _git(repo, "rev-parse", "HEAD")


def get_file_commit(source: str, rel_path: str, before: str | None = None) -> str | None:
    """取得 source repo 內指定 rel_path 的最後 commit。

    Args:
        before: ISO 時間戳，若提供則取該時間之前最新的 commit。
    """
    repo = get_source_repo_path(source)
    if not repo:
        return None
    args = ["log", "-1", "--format=%H"]
    if before:
        args.extend(["--before", before])
    args.extend(["--", rel_path])
    return _git(repo, *args)


def get_repo_blob(source: str, commit: str, rel_path: str) -> bytes | None:
    """取得 source repo 內指定 commit:rel_path 的 blob 內容。"""
    repo = get_source_repo_path(source)
    if not repo:
        return None
    try:
        result = subprocess.run(
            ["git", "-C", str(repo), "show", f"{commit}:{rel_path}"],
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            return None
        return result.stdout
    except Exception:
        return None


def is_commit_valid(source: str, commit: str) -> bool:
    """檢查 commit 是否仍存在於 source repo。"""
    repo = get_source_repo_path(source)
    if not repo:
        return False
    try:
        result = subprocess.run(
            ["git", "-C", str(repo), "cat-file", "-e", f"{commit}^{{commit}}"],
            capture_output=True,
            check=False,
        )
        return result.returncode == 0
    except Exception:
        return False


def list_changed_files(source: str, last_commit: str, head: str) -> list[str]:
    """回傳 last_commit..head 之間變動的檔案清單。"""
    repo = get_source_repo_path(source)
    if not repo:
        return []
    out = _git(repo, "diff", "--name-only", f"{last_commit}..{head}")
    if not out:
        return []
    return [line.strip() for line in out.splitlines() if line.strip()]


# ------------------------------------------------------------
# Schema 偵測 / file entry 存取
# ------------------------------------------------------------


def is_v2(manifest: dict | None) -> bool:
    return bool(manifest) and int(manifest.get("schema_version", 0) or 0) >= 2


def get_file_entry(
    manifest: dict | None,
    resource_type: ResourceType,
    name: str,
    rel_path: str | None = None,
) -> FileEntry | None:
    """取得 v2 manifest 內某 file 的 FileEntry。

    對 commands/agents/workflows 不傳 rel_path（單檔）。
    """
    if not is_v2(manifest):
        return None
    section = manifest.get("files", {}).get(resource_type, {})
    entry_block = section.get(name)
    if not isinstance(entry_block, dict):
        return None
    if resource_type == "skills":
        if rel_path is None:
            return None
        files = entry_block.get("files", {})
        raw = files.get(rel_path)
        return FileEntry.from_dict(raw) if isinstance(raw, dict) else None
    return FileEntry.from_dict(entry_block)


def get_skipped_entry(
    manifest: dict | None,
    resource_type: ResourceType,
    name: str,
    rel_path: str | None = None,
) -> SkippedEntry | None:
    if not is_v2(manifest):
        return None
    section = manifest.get("files", {}).get(resource_type, {})
    entry_block = section.get(name)
    if not isinstance(entry_block, dict):
        return None
    skipped = entry_block.get("skipped", {})
    if resource_type == "skills":
        if rel_path is None:
            return None
        raw = skipped.get(rel_path) if isinstance(skipped, dict) else None
    else:
        raw = skipped if isinstance(skipped, dict) else None
    return SkippedEntry.from_dict(raw) if isinstance(raw, dict) else None


# ------------------------------------------------------------
# 3-way 分類
# ------------------------------------------------------------


def classify_file(
    file_entry: FileEntry | None,
    src_hash: str,
    dst_hash: str,
) -> ConflictClass:
    """3-way 衝突分類。"""
    if file_entry is None:
        return "no-base"
    if not file_entry.src_hash or not file_entry.dst_hash_at_sync:
        return "no-base"
    src_eq_base = src_hash == file_entry.src_hash
    dst_eq_base = dst_hash == file_entry.dst_hash_at_sync
    if src_eq_base and dst_eq_base:
        return "clean"  # 無變動，由呼叫端決定不動作
    if dst_eq_base and not src_eq_base:
        return "clean"
    if src_eq_base and not dst_eq_base:
        return "local-only"
    return "both-changed"


def is_skipped(
    manifest: dict | None,
    resource_type: ResourceType,
    name: str,
    rel_path: str | None,
    current_src_commit: str,
) -> bool:
    """檢查 (rel, current_src_commit) 是否命中 skipped 記憶。"""
    skipped = get_skipped_entry(manifest, resource_type, name, rel_path)
    if skipped is None:
        return False
    return skipped.src_commit == current_src_commit


def is_base_valid(file_entry: FileEntry | None) -> bool:
    """檢查 base 是否仍可用（src_commit 仍存在於來源 git）。"""
    if file_entry is None:
        return False
    return is_commit_valid(file_entry.src_source, file_entry.src_commit)


# ------------------------------------------------------------
# v2 寫入：file decision / skip
# ------------------------------------------------------------


def _ensure_resource_section(manifest: dict, resource_type: ResourceType) -> dict:
    files = manifest.setdefault("files", {})
    return files.setdefault(resource_type, {})


def _ensure_skill_files(manifest: dict, name: str) -> dict:
    section = _ensure_resource_section(manifest, "skills")
    skill = section.setdefault(name, {})
    return skill.setdefault("files", {})


def _ensure_skill_skipped(manifest: dict, name: str) -> dict:
    section = _ensure_resource_section(manifest, "skills")
    skill = section.setdefault(name, {})
    return skill.setdefault("skipped", {})


def record_file_decision(
    manifest: dict,
    resource_type: ResourceType,
    name: str,
    rel_path: str | None,
    *,
    src_hash: str,
    src_commit: str,
    src_source: str,
    dst_hash: str,
    decision: str,
) -> None:
    """寫入 FileEntry 並順帶清除可能的舊 skip 紀錄。"""
    manifest.setdefault("schema_version", SCHEMA_VERSION)
    entry = FileEntry(
        src_hash=src_hash,
        src_commit=src_commit,
        src_source=src_source,
        dst_hash_at_sync=dst_hash,
        decision=decision,
        decided_at=datetime.now().astimezone().isoformat(),
    )
    if resource_type == "skills":
        if rel_path is None:
            return
        files = _ensure_skill_files(manifest, name)
        files[rel_path] = entry.to_dict()
        clear_skip(manifest, resource_type, name, rel_path)
    else:
        section = _ensure_resource_section(manifest, resource_type)
        block = section.setdefault(name, {})
        block.update(entry.to_dict())
        clear_skip(manifest, resource_type, name, None)


def record_skip(
    manifest: dict,
    resource_type: ResourceType,
    name: str,
    rel_path: str | None,
    src_commit: str,
) -> None:
    manifest.setdefault("schema_version", SCHEMA_VERSION)
    payload = SkippedEntry(
        src_commit=src_commit,
        decided_at=datetime.now().astimezone().isoformat(),
    ).to_dict()
    if resource_type == "skills":
        if rel_path is None:
            return
        skipped = _ensure_skill_skipped(manifest, name)
        skipped[rel_path] = payload
    else:
        section = _ensure_resource_section(manifest, resource_type)
        block = section.setdefault(name, {})
        block["skipped"] = payload


def clear_skip(
    manifest: dict,
    resource_type: ResourceType,
    name: str,
    rel_path: str | None,
) -> None:
    section = manifest.get("files", {}).get(resource_type, {})
    block = section.get(name)
    if not isinstance(block, dict):
        return
    if resource_type == "skills":
        skipped = block.get("skipped")
        if isinstance(skipped, dict) and rel_path in skipped:
            del skipped[rel_path]
            if not skipped:
                block.pop("skipped", None)
    else:
        block.pop("skipped", None)


def update_last_sync_commit(manifest: dict, source: str, commit: str | None) -> None:
    if not commit:
        return
    manifest.setdefault("schema_version", SCHEMA_VERSION)
    manifest.setdefault("last_sync_commit_by_source", {})[source] = commit


# ------------------------------------------------------------
# v1 → v2 Migration
# ------------------------------------------------------------


def _backup_v1_manifest(target: TargetType) -> Path | None:
    src = get_manifest_path(target)
    if not src.exists():
        return None
    backup_dir = get_manifest_dir() / ".backup-v1"
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    dst = backup_dir / f"{target}.yaml.{timestamp}"
    try:
        shutil.copy2(src, dst)
        return dst
    except Exception as e:
        console.print(f"[yellow]警告：v1 manifest 備份失敗 ({e})[/yellow]")
        return None


def migrate_to_v2(v1_manifest: dict, target: TargetType) -> dict:
    """v1 → v2 migration，僅對 dst==src 自動標 base。"""
    if is_v2(v1_manifest):
        return v1_manifest

    last_sync = v1_manifest.get("last_sync")
    new_manifest = dict(v1_manifest)
    new_manifest["schema_version"] = SCHEMA_VERSION
    new_manifest.setdefault("last_sync_commit_by_source", {})
    files = new_manifest.setdefault("files", {})

    for resource_type in RESOURCE_TYPES:
        section = files.get(resource_type, {})
        for name, block in list(section.items()):
            if not isinstance(block, dict):
                continue
            old_hash = block.get("hash", "")
            source = block.get("source", "custom-skills")
            target_path = _get_target_resource_path(target, resource_type, name)
            if target_path is None or not target_path.exists():
                continue
            if resource_type == "skills":
                current_dir_hash = compute_dir_hash(target_path)
                if current_dir_hash != old_hash:
                    continue
                file_map = compute_skill_file_map(target_path)
                files_block: dict = {}
                src_repo_root = get_source_repo_path(source)
                for rel, file_hash in file_map.items():
                    src_commit = None
                    if src_repo_root:
                        src_commit = get_file_commit(
                            source, _resolve_repo_rel(src_repo_root, source, resource_type, name, rel),
                            before=last_sync,
                        )
                    if not src_commit:
                        continue
                    files_block[rel] = FileEntry(
                        src_hash=file_hash,
                        src_commit=src_commit,
                        src_source=source,
                        dst_hash_at_sync=file_hash,
                        decision="accepted",
                        decided_at=last_sync or "",
                    ).to_dict()
                if files_block:
                    block["files"] = files_block
            else:
                current_hash = compute_file_hash(target_path)
                if current_hash != old_hash:
                    continue
                src_commit = None
                src_repo_root = get_source_repo_path(source)
                if src_repo_root:
                    src_commit = get_file_commit(
                        source,
                        _resolve_repo_rel(src_repo_root, source, resource_type, name, None),
                        before=last_sync,
                    )
                if not src_commit:
                    continue
                block.update(
                    FileEntry(
                        src_hash=current_hash,
                        src_commit=src_commit,
                        src_source=source,
                        dst_hash_at_sync=current_hash,
                        decision="accepted",
                        decided_at=last_sync or "",
                    ).to_dict()
                )

    return new_manifest


def _resolve_repo_rel(
    repo_root: Path,
    source: str,
    resource_type: ResourceType,
    name: str,
    rel_path: str | None,
) -> str:
    """推斷 source repo 內某資源的 rel path（用於 git log 查詢）。"""
    if resource_type == "skills":
        base = f"skills/{name}"
        return f"{base}/{rel_path}" if rel_path else base
    if resource_type == "commands":
        return f"commands/{name}.md"
    if resource_type == "agents":
        return f"agents/{name}.md"
    if resource_type == "workflows":
        return f"commands/workflows/{name}.md"
    return name


def maybe_migrate_manifest(target: TargetType) -> dict | None:
    """讀取 manifest，若為 v1 則 migrate 並寫回。回傳 v2 manifest。"""
    raw = read_manifest(target)
    if raw is None:
        return None
    if is_v2(raw):
        return raw
    backup = _backup_v1_manifest(target)
    if backup:
        console.print(
            f"[dim]已備份 v1 manifest → {backup.name}（manifest schema 升級為 v2）[/dim]"
        )
    upgraded = migrate_to_v2(raw, target)
    write_manifest(target, upgraded)
    return upgraded


# ------------------------------------------------------------
# v2 → v1 view（向下相容，給 install / sync 等舊 reader）
# ------------------------------------------------------------


# ------------------------------------------------------------
# Per-file prompt UI
# ------------------------------------------------------------


def _read_text_safe(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def _bytes_to_text(data: bytes | None) -> str:
    if data is None:
        return ""
    try:
        return data.decode("utf-8", errors="replace")
    except Exception:
        return ""


def _count_changes(diff_lines: list[str]) -> tuple[int, int]:
    plus = sum(1 for line in diff_lines if line.startswith("+") and not line.startswith("+++"))
    minus = sum(1 for line in diff_lines if line.startswith("-") and not line.startswith("---"))
    return plus, minus


def _unified_diff(
    a_text: str,
    b_text: str,
    a_label: str,
    b_label: str,
) -> list[str]:
    import difflib

    return list(
        difflib.unified_diff(
            a_text.splitlines(keepends=True),
            b_text.splitlines(keepends=True),
            fromfile=a_label,
            tofile=b_label,
        )
    )


def _print_diff(diff: list[str]) -> None:
    if not diff:
        console.print("[dim]  無差異[/dim]")
        return
    from rich.syntax import Syntax

    syntax = Syntax("".join(diff), "diff", theme="monokai", line_numbers=False)
    console.print(syntax)


def prompt_file_decision(
    skill_name: str,
    rel_path: str,
    src_path: Path,
    dst_path: Path,
    base_blob_getter,
) -> str:
    """per-file 衝突 prompt。回傳 "overwrite" 或 "skip"。

    Args:
        base_blob_getter: callable(rel_path) -> bytes | None
    """
    src_text = _read_text_safe(src_path)
    dst_text = _read_text_safe(dst_path)
    base_text = _bytes_to_text(base_blob_getter(rel_path))

    if base_text:
        src_vs_base = _unified_diff(base_text, src_text, "base", "src")
        dst_vs_base = _unified_diff(base_text, dst_text, "base", "dst")
        src_vs_dst = _unified_diff(dst_text, src_text, "dst", "src")
        sb_p, sb_m = _count_changes(src_vs_base)
        db_p, db_m = _count_changes(dst_vs_base)
        cd_p, cd_m = _count_changes(src_vs_dst)
        console.print(
            f"  [yellow]? 衝突：{skill_name}/{rel_path}[/yellow]"
        )
        console.print(
            f"    [cyan]來源動 +{sb_p} -{sb_m}[/cyan] | "
            f"[magenta]你動 +{db_p} -{db_m}[/magenta] | "
            f"[white]重疊改動 +{cd_p} -{cd_m}[/white]"
        )
    else:
        console.print(
            f"  [yellow]? 衝突：{skill_name}/{rel_path} (base 不可用)[/yellow]"
        )

    while True:
        console.print(
            "    [dim]Diff: [Ds] src vs base  [Dl] dst vs base  [Dc] src vs dst | "
            "Action: [O] overwrite  [S] skip[/dim]"
        )
        try:
            raw = input("    選擇: ").strip()
        except (EOFError, KeyboardInterrupt):
            return "skip"
        choice = raw.upper()
        if choice == "O":
            return "overwrite"
        if choice == "S":
            return "skip"
        if choice == "DS":
            if not base_text:
                console.print("[yellow]  無法取得 base 內容（commit 已失效）[/yellow]")
                continue
            _print_diff(_unified_diff(base_text, src_text, "base", "src"))
        elif choice == "DL":
            if not base_text:
                console.print("[yellow]  無法取得 base 內容（commit 已失效）[/yellow]")
                continue
            _print_diff(_unified_diff(base_text, dst_text, "base", "dst"))
        elif choice == "DC":
            _print_diff(_unified_diff(dst_text, src_text, "dst", "src"))
        else:
            console.print("[red]  無效選項[/red]")


# ------------------------------------------------------------
# Per-source update summary
# ------------------------------------------------------------


def render_source_summary(
    rows: list[dict],
) -> None:
    """印出 per-source update summary。

    Each row 應包含:
      source, status (unchanged/first-sync/updated), last_commit, head_commit,
      total_changed, affected_current, affected_other
    """
    from rich.table import Table

    if not rows:
        return
    table = Table(
        title="來源更新摘要",
        title_style="bold",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("source")
    table.add_column("commit")
    table.add_column("變動", justify="right")
    table.add_column("影響本次 target", justify="right")
    table.add_column("影響其他 target", justify="right", style="dim")

    for row in rows:
        if row["status"] == "unchanged":
            table.add_row(row["source"], "未變更", "-", "-", "-")
        elif row["status"] == "first-sync":
            table.add_row(row["source"], "首次同步", "-", "-", "-")
        else:
            table.add_row(
                row["source"],
                f"{row['last_commit'][:7]} → {row['head_commit'][:7]}",
                str(row["total_changed"]),
                str(row["affected_current"]),
                str(row["affected_other"]),
            )
    console.print(table)


def v2_to_v1_view(manifest: dict | None) -> dict | None:
    """將 v2 manifest 投影回 v1 結構。"""
    if manifest is None:
        return None
    if not is_v2(manifest):
        return manifest
    out: dict = {
        "managed_by": manifest.get("managed_by", "ai-dev"),
        "version": manifest.get("version", "unknown"),
        "last_sync": manifest.get("last_sync", ""),
        "target": manifest.get("target", ""),
        "files": {},
    }
    for resource_type in RESOURCE_TYPES:
        section = manifest.get("files", {}).get(resource_type, {})
        out_section: dict = {}
        for name, block in section.items():
            if not isinstance(block, dict):
                continue
            out_section[name] = {
                "hash": block.get("hash", ""),
                "source": block.get("source", "custom-skills"),
            }
        out["files"][resource_type] = out_section
    return out
