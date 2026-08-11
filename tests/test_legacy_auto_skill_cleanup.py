from __future__ import annotations

import json
import os
from pathlib import Path

from script.utils.legacy_auto_skill_cleanup import (
    cleanup_global_auto_skill,
    cleanup_project_auto_skill,
)

LEGACY_PROTOCOL = """## 任務啟動協議 (強制)

* 當開啟新任務或觸發任何技能時，必須先讀取並執行 auto-skill 技能的 SKILL.md。
"""


def _write(path: Path, content: str = "legacy") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _seed_global_install(home: Path) -> dict[str, Path]:
    distribution_source = _write(
        home / ".config" / "custom-skills" / "skills" / "auto-skill" / "SKILL.md"
    ).parent
    canonical = _write(
        home / ".config" / "ai-dev" / "skills" / "auto-skill" / "SKILL.md"
    ).parent
    upstream = _write(home / ".config" / "auto-skill" / "SKILL.md").parent
    shadow = _write(
        home
        / ".config"
        / "ai-dev"
        / "projections"
        / "claude"
        / "auto-skill"
        / "SKILL.md"
    ).parent
    state = _write(
        home
        / ".config"
        / "ai-dev"
        / "projections"
        / "claude"
        / "auto-skill.state.json",
        "{}",
    )
    projection = home / ".claude" / "skills" / "auto-skill"
    projection.parent.mkdir(parents=True)
    projection.symlink_to(shadow, target_is_directory=True)
    broken_projection = home / ".agents" / "skills" / "auto-skill"
    broken_projection.parent.mkdir(parents=True)
    broken_projection.symlink_to(
        home / ".config" / "ai-dev" / "projections" / "codex" / "auto-skill",
        target_is_directory=True,
    )

    instructions = _write(
        home / ".codex" / "instructions.md",
        f"""# Personal rules

{LEGACY_PROTOCOL}
Keep me.
""",
    )

    plugin_cache = _write(
        home
        / ".claude"
        / "plugins"
        / "cache"
        / "custom-skills"
        / "auto-skill-hooks"
        / "1.2.6"
        / "hooks"
        / "hooks.json",
        "{}",
    ).parents[1]
    installed_plugins = _write(
        home / ".claude" / "plugins" / "installed_plugins.json",
        json.dumps(
            {
                "version": 2,
                "plugins": {
                    "auto-skill-hooks@custom-skills": [
                        {
                            "scope": "user",
                            "installPath": str(plugin_cache),
                            "version": "1.2.6",
                        }
                    ]
                },
            }
        ),
    )
    return {
        "distribution_source": distribution_source,
        "canonical": canonical,
        "upstream": upstream,
        "shadow": shadow,
        "state": state,
        "projection": projection,
        "broken_projection": broken_projection,
        "instructions": instructions,
        "plugin_cache": plugin_cache,
        "installed_plugins": installed_plugins,
    }


def test_global_cleanup_dry_run_never_prompts_or_writes(tmp_path: Path) -> None:
    home = tmp_path / "home"
    paths = _seed_global_install(home)

    result = cleanup_global_auto_skill(
        home=home,
        dry_run=True,
        interactive=True,
        confirm=lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("dry-run must not prompt")
        ),
        plugin_uninstaller=lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("dry-run must not uninstall")
        ),
    )

    assert result.status == "dry-run"
    assert paths["distribution_source"].exists()
    assert paths["canonical"].exists()
    assert os.path.lexists(paths["broken_projection"])
    assert LEGACY_PROTOCOL.strip() in paths["instructions"].read_text(encoding="utf-8")
    assert result.backup_dir is None


def test_global_cleanup_noninteractive_and_declined_both_preserve_data(
    tmp_path: Path,
) -> None:
    home = tmp_path / "home"
    paths = _seed_global_install(home)

    noninteractive = cleanup_global_auto_skill(
        home=home,
        interactive=False,
        confirm=lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("non-interactive cleanup must not prompt")
        ),
    )
    declined = cleanup_global_auto_skill(
        home=home,
        interactive=True,
        confirm=lambda *_args, **_kwargs: False,
    )

    assert noninteractive.status == "non-interactive"
    assert declined.status == "declined"
    assert paths["canonical"].exists()
    assert paths["plugin_cache"].exists()
    assert not (home / ".config" / "ai-dev" / "backups" / "auto-skill-removal").exists()


def test_global_cleanup_confirms_backs_up_then_removes_all_active_parts(
    tmp_path: Path,
) -> None:
    home = tmp_path / "home"
    paths = _seed_global_install(home)
    uninstall_calls: list[tuple[tuple[str, ...], Path]] = []

    def _uninstall(scopes: tuple[str, ...], cwd: Path) -> None:
        uninstall_calls.append((scopes, cwd))
        paths["installed_plugins"].write_text(
            json.dumps({"version": 2, "plugins": {}}), encoding="utf-8"
        )

    result = cleanup_global_auto_skill(
        home=home,
        interactive=True,
        confirm=lambda *_args, **_kwargs: True,
        plugin_uninstaller=_uninstall,
    )

    assert result.status == "removed"
    assert result.backup_dir is not None
    assert (result.backup_dir / "audit.json").exists()
    audit = json.loads((result.backup_dir / "audit.json").read_text(encoding="utf-8"))
    assert audit["scope"] == "global"
    assert any(
        entry["original"] == str(paths["canonical"]) for entry in audit["entries"]
    )
    assert any(
        entry.get("link_target") == str(paths["shadow"])
        for entry in audit["entries"]
        if entry["original"] == str(paths["projection"])
    )
    assert uninstall_calls == [(("user",), home)]

    for name in (
        "distribution_source",
        "canonical",
        "upstream",
        "shadow",
        "state",
        "projection",
        "broken_projection",
    ):
        assert not os.path.lexists(paths[name])
    assert not paths["plugin_cache"].exists()
    instructions = paths["instructions"].read_text(encoding="utf-8")
    assert "auto-skill" not in instructions
    assert "# Personal rules" in instructions
    assert "Keep me." in instructions

    rerun = cleanup_global_auto_skill(home=home, interactive=False)
    assert rerun.status == "not-found"


def test_plugin_uninstall_failure_keeps_active_paths(tmp_path: Path) -> None:
    home = tmp_path / "home"
    paths = _seed_global_install(home)

    def _fail(*_args, **_kwargs) -> None:
        raise RuntimeError("uninstall failed")

    try:
        cleanup_global_auto_skill(
            home=home,
            interactive=True,
            confirm=lambda *_args, **_kwargs: True,
            plugin_uninstaller=_fail,
        )
    except RuntimeError as exc:
        assert "uninstall failed" in str(exc)
    else:
        raise AssertionError("plugin uninstall failure must stop cleanup")

    assert paths["canonical"].exists()
    assert paths["projection"].is_symlink()
    assert LEGACY_PROTOCOL.strip() in paths["instructions"].read_text(encoding="utf-8")


def test_project_cleanup_removes_known_copies_and_exact_legacy_rules(
    tmp_path: Path,
) -> None:
    home = tmp_path / "home"
    project = tmp_path / "project"
    skill = _write(project / "skills" / "auto-skill" / "SKILL.md").parent
    shared_projection = _write(
        project / ".agents" / "skills" / "auto-skill" / "SKILL.md"
    ).parent
    agents = _write(
        project / "AGENTS.md",
        """# Rules

- auto-skill 只負責知識與經驗載入，不構成啟動高階工作流、修改 tracker 或執行其他具副作用操作的授權。
- Keep this rule.
""",
    )

    result = cleanup_project_auto_skill(
        project,
        home=home,
        interactive=True,
        confirm=lambda *_args, **_kwargs: True,
    )

    assert result.status == "removed"
    assert result.backup_dir is not None
    assert not skill.exists()
    assert not shared_projection.exists()
    assert "auto-skill" not in agents.read_text(encoding="utf-8")
    assert "Keep this rule." in agents.read_text(encoding="utf-8")
    assert (
        cleanup_project_auto_skill(project, home=home, interactive=False).status
        == "not-found"
    )
