"""`ai-dev ecc` 子命令群：管理 ECC（everything-claude-code）白名單與 catalog。"""

from __future__ import annotations

import sys
from datetime import date
from difflib import SequenceMatcher
from pathlib import Path

import typer

from script.utils.shared import console, get_custom_skills_dir


app = typer.Typer(help="ECC（everything-claude-code）白名單與 catalog 管理")


ECC_ROOT = Path("~/.config/everything-claude-code").expanduser()


def _load_catalog() -> tuple[dict | None, Path]:
    """讀取 upstream/ecc-catalog.yaml。回傳 (data | None, path)。"""
    import yaml

    path = get_custom_skills_dir() / "upstream" / "ecc-catalog.yaml"
    if not path.exists():
        return None, path
    try:
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f), path
    except (yaml.YAMLError, OSError) as e:
        console.print(f"[red]無法解析 {path}: {e}[/red]")
        return None, path


def _catalog_skill_names(catalog: dict | None) -> set[str]:
    """從 catalog 取出所有 skill 名稱（包含 uncategorized）。"""
    if not catalog or "categories" not in catalog:
        return set()
    names: set[str] = set()
    for cat in catalog["categories"].values():
        for entry in cat.get("skills") or []:
            if isinstance(entry, dict) and "name" in entry:
                names.add(entry["name"])
            elif isinstance(entry, str):
                names.add(entry)
    return names


def _catalog_skill_to_category(catalog: dict | None) -> dict[str, str]:
    """skill 名稱 → 所屬 category key 對照表。"""
    if not catalog or "categories" not in catalog:
        return {}
    mapping: dict[str, str] = {}
    for cat_key, cat in catalog["categories"].items():
        for entry in cat.get("skills") or []:
            name = entry["name"] if isinstance(entry, dict) else entry
            mapping[name] = cat_key
    return mapping


def _ecc_skill_names() -> set[str]:
    """掃描 ECC 來源目錄取得所有 skill 目錄名稱。"""
    skills_dir = ECC_ROOT / "skills"
    if not skills_dir.exists():
        return set()
    return {
        p.name for p in skills_dir.iterdir()
        if p.is_dir() and not p.name.startswith(".")
    }


def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def _common_prefix_len(a: str, b: str) -> int:
    n = min(len(a), len(b))
    for i in range(n):
        if a[i] != b[i]:
            return i
    return n


def _detect_renamed(new_names: list[str], gone_names: list[str]) -> list[tuple[str, str, float]]:
    """配對 NEW 與 GONE 找出疑似重命名。回傳 [(gone, new, similarity), ...]。"""
    pairs: list[tuple[str, str, float]] = []
    for gone in gone_names:
        for new in new_names:
            sim = _similarity(gone, new)
            cp = _common_prefix_len(gone, new)
            if sim >= 0.7 or cp >= 5:
                pairs.append((gone, new, sim))
    return sorted(pairs, key=lambda p: -p[2])


@app.command()
def audit() -> None:
    """偵測 ECC 來源與 ecc-catalog.yaml 的差異並輸出建議 patch。

    退出碼：
      0 - 無差異
      1 - 有 NEW / GONE / RENAMED?
      2 - ECC 來源目錄不存在
    """
    if not ECC_ROOT.exists():
        console.print(
            f"[red]ECC 來源目錄不存在: {ECC_ROOT}[/red]\n"
            "[yellow]請先執行 `ai-dev update` 拉取 ECC。[/yellow]"
        )
        raise typer.Exit(code=2)

    ecc_names = _ecc_skill_names()
    catalog, catalog_path = _load_catalog()

    if catalog is None:
        console.print(
            f"[yellow]ecc-catalog.yaml 不存在或無法解析: {catalog_path}[/yellow]\n"
            "[yellow]建議先建立 catalog（可由 generate_ecc_catalog_seed 產生初版）。[/yellow]"
        )
        # catalog 缺失視為「全部都是 NEW」
        catalog_names = set()
    else:
        catalog_names = _catalog_skill_names(catalog)

    new_set = ecc_names - catalog_names
    gone_set = catalog_names - ecc_names

    new_sorted = sorted(new_set)
    gone_sorted = sorted(gone_set)
    renamed_pairs = _detect_renamed(new_sorted, gone_sorted) if (new_sorted and gone_sorted) else []

    if not new_sorted and not gone_sorted:
        console.print("[green]✓ 無差異：ECC 與 ecc-catalog.yaml 已同步[/green]")
        raise typer.Exit(code=0)

    console.print(f"[bold]ECC catalog 差異報告[/bold]   (ECC: {ECC_ROOT})\n")

    skill_to_cat = _catalog_skill_to_category(catalog)

    if new_sorted:
        console.print(f"[cyan][NEW] {len(new_sorted)} 個 skill 在 ECC 但未在 catalog[/cyan]")
        for n in new_sorted:
            console.print(f"  [green]+[/green] {n}   [dim](建議歸入: uncategorized)[/dim]")
        console.print()

    if gone_sorted:
        console.print(f"[cyan][GONE] {len(gone_sorted)} 個 skill 在 catalog 但已從 ECC 移除[/cyan]")
        for n in gone_sorted:
            cat = skill_to_cat.get(n, "?")
            console.print(f"  [red]-[/red] {n}   [dim](原 category: {cat})[/dim]")
        console.print()

    if renamed_pairs:
        console.print(f"[cyan][RENAMED?] {len(renamed_pairs)} 個疑似重命名（人工確認）[/cyan]")
        for gone, new, sim in renamed_pairs:
            console.print(f"  [yellow]?[/yellow] {gone} → {new}   [dim](similarity: {sim:.2f})[/dim]")
        console.print()

    # 建議 patch（YAML 片段）
    if new_sorted:
        today = date.today().isoformat()
        console.print("[bold]建議 patch（複製至 upstream/ecc-catalog.yaml 的 categories.uncategorized.skills）[/bold]")
        console.print("[dim]---[/dim]")
        for n in new_sorted:
            console.print(f"  - name: {n}")
            console.print(f'    added: "{today}"')
        console.print("[dim]---[/dim]\n")

    if gone_sorted:
        console.print(
            "[bold]建議移除（從 catalog 對應 category 刪除以下項目）[/bold]"
        )
        for n in gone_sorted:
            cat = skill_to_cat.get(n, "?")
            console.print(f"  - {n}   (in category: {cat})")
        console.print()

    console.print(
        "[dim]下一步：\n"
        "  1. 編輯 upstream/ecc-catalog.yaml，將 NEW 項目移到適合的 category\n"
        "  2. 若要啟用分發，編輯 upstream/distribution.yaml 將項目加入 distribute.skills.enabled\n"
        "  3. 重新執行 ai-dev clone[/dim]"
    )

    raise typer.Exit(code=1)


def check_catalog_lag() -> None:
    """install / clone / update 共用的廉價 catalog 落後檢查。

    僅比較名稱集合，不阻塞流程。若偵測到 ECC 有但 catalog 沒有的 skill，
    印出黃色警告引導使用者執行 `ai-dev ecc audit`。
    """
    if not ECC_ROOT.exists():
        return

    ecc_names = _ecc_skill_names()
    catalog, catalog_path = _load_catalog()

    if catalog is None:
        if catalog_path.exists():
            return  # 解析失敗，已在 _load_catalog 印錯誤
        # catalog 不存在：一次性提示（透過 marker file 避免每次重複）
        marker = Path("~/.cache/ai-dev/ecc-catalog-hint-shown").expanduser()
        if marker.exists():
            return
        console.print(
            f"  [yellow]提示：未建立 {catalog_path}，"
            "建議建立後執行 `ai-dev ecc audit` 追蹤 ECC 變動[/yellow]"
        )
        try:
            marker.parent.mkdir(parents=True, exist_ok=True)
            marker.touch()
        except OSError:
            pass
        return

    catalog_names = _catalog_skill_names(catalog)
    new_count = len(ecc_names - catalog_names)
    if new_count:
        console.print(
            f"  [yellow]⚠ ECC 上游新增 {new_count} 個 skill 未在 ecc-catalog.yaml 審視（預設不分發）[/yellow]\n"
            "  [yellow]  執行 `ai-dev ecc audit` 查看詳情[/yellow]"
        )
