"""
Manifest 機制：追蹤分發檔案並管理孤兒清理與衝突檢測。
"""

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
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
class FileRecord:
    """記錄單一檔案/目錄的資訊。"""

    name: str
    hash: str
    source: str = "custom-skills"
    source_path: Path | None = None


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
        self, name: str, source_path: Path, source: str = "custom-skills"
    ) -> None:
        """記錄已複製的 skill。"""
        hash_value = compute_dir_hash(source_path)
        self.skills[name] = FileRecord(
            name=name, hash=hash_value, source=source, source_path=source_path
        )

    def record_command(
        self, name: str, source_path: Path, source: str = "custom-skills"
    ) -> None:
        """記錄已複製的 command。"""
        hash_value = compute_file_hash(source_path)
        self.commands[name] = FileRecord(
            name=name, hash=hash_value, source=source, source_path=source_path
        )

    def record_agent(
        self, name: str, source_path: Path, source: str = "custom-skills"
    ) -> None:
        """記錄已複製的 agent。"""
        hash_value = compute_file_hash(source_path)
        self.agents[name] = FileRecord(
            name=name, hash=hash_value, source=source, source_path=source_path
        )

    def record_workflow(
        self, name: str, source_path: Path, source: str = "custom-skills"
    ) -> None:
        """記錄已複製的 workflow。"""
        hash_value = compute_file_hash(source_path)
        self.workflows[name] = FileRecord(
            name=name, hash=hash_value, source=source, source_path=source_path
        )

    def to_manifest(self, version: str) -> dict:
        """轉換為 manifest 字典格式。"""
        return {
            "managed_by": "ai-dev",
            "version": version,
            "last_sync": datetime.now().astimezone().isoformat(),
            "target": self.target,
            "files": {
                "skills": {
                    name: {"hash": record.hash, "source": record.source}
                    for name, record in self.skills.items()
                },
                "commands": {
                    name: {"hash": record.hash, "source": record.source}
                    for name, record in self.commands.items()
                },
                "agents": {
                    name: {"hash": record.hash, "source": record.source}
                    for name, record in self.agents.items()
                },
                "workflows": {
                    name: {"hash": record.hash, "source": record.source}
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
        target: 目標平台名稱 (claude, opencode, antigravity, codex, gemini)

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
