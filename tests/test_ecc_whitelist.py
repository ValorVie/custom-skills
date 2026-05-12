"""Tests for ECC whitelist distribution mechanism and `ai-dev ecc audit` command."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
import yaml
from typer.testing import CliRunner


@pytest.fixture
def fake_ecc(tmp_path: Path) -> Path:
    """Create a fake ECC source directory with several skill dirs."""
    ecc = tmp_path / "ecc"
    skills = ecc / "skills"
    skills.mkdir(parents=True)
    for name in ["alpha", "beta", "gamma", "delta"]:
        (skills / name).mkdir()
        (skills / name / "SKILL.md").write_text(f"# {name}\n")
    return ecc


@pytest.fixture
def fake_catalog(tmp_path: Path) -> Path:
    """Create a catalog yaml at the tmp custom-skills root."""
    root = tmp_path / "custom-skills"
    (root / "upstream").mkdir(parents=True)
    catalog = root / "upstream" / "ecc-catalog.yaml"
    catalog.write_text(yaml.safe_dump({
        "version": 1,
        "last_synced": "2026-05-01",
        "last_synced_ecc_commit": "abc123",
        "categories": {
            "engineering-methods": {
                "description": "test",
                "skills": [
                    {"name": "alpha", "added": "2026-01-01"},
                    {"name": "beta"},
                ],
            },
            "uncategorized": {"description": "uncat", "skills": []},
        },
    }))
    return root


def test_prescan_ecc_uses_whitelist(fake_ecc: Path):
    """_prescan_ecc should only record skills listed in distribute.skills.enabled."""
    from script.utils.shared import _prescan_ecc

    recorded: list[str] = []

    def record(name, path, source):
        recorded.append(name)

    dist_config = {
        "source_path": str(fake_ecc),
        "distribute": {
            "skills": {
                "source_path": "skills/",
                "targets": ["claude"],
                "enabled": ["alpha", "gamma"],  # 只有這兩個會被分發
            }
        },
        "skip_directories": [],
        "exclude": {},
    }

    with patch("script.services.npx_skills.get_npx_managed_skill_names", return_value=set()):
        _prescan_ecc("claude", {"skills": record}, dist_config)

    assert set(recorded) == {"alpha", "gamma"}
    assert "beta" not in recorded
    assert "delta" not in recorded


def test_prescan_ecc_empty_enabled(fake_ecc: Path):
    """空 enabled 應該不分發任何 skill。"""
    from script.utils.shared import _prescan_ecc

    recorded: list[str] = []

    def record(name, path, source):
        recorded.append(name)

    dist_config = {
        "source_path": str(fake_ecc),
        "distribute": {
            "skills": {
                "source_path": "skills/",
                "targets": ["claude"],
                "enabled": [],
            }
        },
        "skip_directories": [],
        "exclude": {},
    }

    with patch("script.services.npx_skills.get_npx_managed_skill_names", return_value=set()):
        _prescan_ecc("claude", {"skills": record}, dist_config)

    assert recorded == []


def test_prescan_ecc_skip_directories_respected(fake_ecc: Path):
    """skip_directories 即使在 enabled 中也應該被跳過。"""
    from script.utils.shared import _prescan_ecc

    recorded: list[str] = []

    def record(name, path, source):
        recorded.append(name)

    dist_config = {
        "source_path": str(fake_ecc),
        "distribute": {
            "skills": {
                "source_path": "skills/",
                "targets": ["claude"],
                "enabled": ["alpha", "beta"],
            }
        },
        "skip_directories": ["beta"],
        "exclude": {},
    }

    with patch("script.services.npx_skills.get_npx_managed_skill_names", return_value=set()):
        _prescan_ecc("claude", {"skills": record}, dist_config)

    assert recorded == ["alpha"]


def test_audit_no_difference(fake_ecc: Path, fake_catalog: Path):
    """ECC 與 catalog 完全一致時，audit 應退出 0。"""
    # 建立 catalog 列出全部 ECC skills
    catalog = fake_catalog / "upstream" / "ecc-catalog.yaml"
    catalog.write_text(yaml.safe_dump({
        "version": 1,
        "categories": {
            "main": {
                "description": "all",
                "skills": [{"name": n} for n in ["alpha", "beta", "gamma", "delta"]],
            },
        },
    }))

    from script.commands import ecc as ecc_module
    runner = CliRunner()

    with patch.object(ecc_module, "ECC_ROOT", fake_ecc), \
         patch("script.commands.ecc.get_custom_skills_dir", return_value=fake_catalog):
        result = runner.invoke(ecc_module.app, [])

    assert result.exit_code == 0
    assert "無差異" in result.stdout


def test_audit_detects_new_and_gone(fake_ecc: Path, fake_catalog: Path):
    """偵測 NEW（ECC 有 catalog 沒）與 GONE（catalog 有 ECC 沒）。"""
    # catalog 中含已不存在的 zeta，但缺 gamma 與 delta
    catalog = fake_catalog / "upstream" / "ecc-catalog.yaml"
    catalog.write_text(yaml.safe_dump({
        "version": 1,
        "categories": {
            "main": {
                "description": "x",
                "skills": [{"name": "alpha"}, {"name": "beta"}, {"name": "zeta"}],
            },
        },
    }))

    from script.commands import ecc as ecc_module
    runner = CliRunner()

    with patch.object(ecc_module, "ECC_ROOT", fake_ecc), \
         patch("script.commands.ecc.get_custom_skills_dir", return_value=fake_catalog):
        result = runner.invoke(ecc_module.app, [])

    assert result.exit_code == 1
    assert "gamma" in result.stdout
    assert "delta" in result.stdout
    assert "zeta" in result.stdout


def test_audit_ecc_missing(tmp_path: Path, fake_catalog: Path):
    """ECC 來源不存在時 audit 應退出 2。"""
    missing_ecc = tmp_path / "no-such-dir"
    from script.commands import ecc as ecc_module
    runner = CliRunner()

    with patch.object(ecc_module, "ECC_ROOT", missing_ecc), \
         patch("script.commands.ecc.get_custom_skills_dir", return_value=fake_catalog):
        result = runner.invoke(ecc_module.app, [])

    assert result.exit_code == 2


def test_audit_catalog_missing_treats_all_as_new(fake_ecc: Path, tmp_path: Path):
    """catalog 不存在時應把所有 ECC skill 視為 NEW，退出 1。"""
    root = tmp_path / "custom-skills"
    (root / "upstream").mkdir(parents=True)

    from script.commands import ecc as ecc_module
    runner = CliRunner()

    with patch.object(ecc_module, "ECC_ROOT", fake_ecc), \
         patch("script.commands.ecc.get_custom_skills_dir", return_value=root):
        result = runner.invoke(ecc_module.app, [])

    assert result.exit_code == 1
    assert "alpha" in result.stdout
    assert "delta" in result.stdout


def test_check_catalog_lag_silent_when_synced(fake_ecc: Path, fake_catalog: Path, capsys):
    """ECC 與 catalog 同步時 check_catalog_lag 不應輸出警告。"""
    catalog = fake_catalog / "upstream" / "ecc-catalog.yaml"
    catalog.write_text(yaml.safe_dump({
        "version": 1,
        "categories": {
            "main": {
                "description": "all",
                "skills": [{"name": n} for n in ["alpha", "beta", "gamma", "delta"]],
            },
        },
    }))

    from script.commands import ecc as ecc_module

    with patch.object(ecc_module, "ECC_ROOT", fake_ecc), \
         patch("script.commands.ecc.get_custom_skills_dir", return_value=fake_catalog):
        ecc_module.check_catalog_lag()

    out = capsys.readouterr().out
    assert "未審視" not in out


def test_check_catalog_lag_warns_when_behind(fake_ecc: Path, fake_catalog: Path, capsys):
    """ECC 新增未在 catalog 時應印警告。"""
    catalog = fake_catalog / "upstream" / "ecc-catalog.yaml"
    catalog.write_text(yaml.safe_dump({
        "version": 1,
        "categories": {
            "main": {
                "description": "partial",
                "skills": [{"name": "alpha"}],  # 只有 alpha，缺 beta/gamma/delta
            },
        },
    }))

    from script.commands import ecc as ecc_module

    with patch.object(ecc_module, "ECC_ROOT", fake_ecc), \
         patch("script.commands.ecc.get_custom_skills_dir", return_value=fake_catalog):
        ecc_module.check_catalog_lag()

    out = capsys.readouterr().out
    assert "ECC 上游新增 3 個" in out


def test_distribution_yaml_has_enabled_field():
    """確保現行 upstream/distribution.yaml 已包含白名單欄位。"""
    repo_root = Path(__file__).resolve().parent.parent
    yaml_path = repo_root / "upstream" / "distribution.yaml"
    if not yaml_path.exists():
        pytest.skip("distribution.yaml 不存在於開發樹")
    data = yaml.safe_load(yaml_path.read_text())
    skills_cfg = data["distribute"]["skills"]
    assert "enabled" in skills_cfg
    assert isinstance(skills_cfg["enabled"], list)
    assert len(skills_cfg["enabled"]) >= 50  # sanity check：白名單非空且具規模
    # exclude.skills 已移除
    assert "skills" not in data.get("exclude", {})


def test_ecc_catalog_yaml_structure():
    """確保 ecc-catalog.yaml 結構正確。"""
    repo_root = Path(__file__).resolve().parent.parent
    catalog_path = repo_root / "upstream" / "ecc-catalog.yaml"
    if not catalog_path.exists():
        pytest.skip("ecc-catalog.yaml 不存在")
    data = yaml.safe_load(catalog_path.read_text())
    assert data["version"] == 1
    assert "categories" in data
    assert "uncategorized" in data["categories"]
    # 至少包含一個 category 有 skills
    has_skills = any(
        cat.get("skills") for cat in data["categories"].values()
    )
    assert has_skills


def test_renamed_detection():
    """RENAMED? 偵測：相似名稱應該被配對。"""
    from script.commands.ecc import _detect_renamed

    new = ["new-flow-engine", "completely-different"]
    gone = ["old-flow-engine"]
    pairs = _detect_renamed(new, gone)
    # 應該配對 old-flow-engine ↔ new-flow-engine (common prefix ≥ 5)
    matched = {(g, n) for g, n, _ in pairs}
    assert ("old-flow-engine", "new-flow-engine") in matched


# ---------------------------------------------------------------------------
# §6.8–6.13: ecc-profile.yaml v2 使用者層級覆寫測試
# ---------------------------------------------------------------------------


@pytest.fixture
def reset_profile_flags():
    """每個測試前後重置一次性警告 flag。"""
    from script.utils import shared

    shared._ECC_PROFILE_LEGACY_HINT_SHOWN = False
    shared._ECC_PROFILE_LEGACY_CONFLICT_SHOWN = False
    yield
    shared._ECC_PROFILE_LEGACY_HINT_SHOWN = False
    shared._ECC_PROFILE_LEGACY_CONFLICT_SHOWN = False


def _write_profile(tmp_path: Path, content: dict | None) -> Path:
    """寫一個假的 ai-dev config dir，回傳 dir path。"""
    config_dir = tmp_path / "ai-dev-config"
    config_dir.mkdir(parents=True, exist_ok=True)
    if content is not None:
        (config_dir / "ecc-profile.yaml").write_text(yaml.safe_dump(content))
    return config_dir


def test_load_ecc_profile_returns_none_when_missing(tmp_path, reset_profile_flags):
    """profile 不存在 → 回傳 None。"""
    from script.utils import shared

    config_dir = _write_profile(tmp_path, None)
    with patch("script.utils.shared.get_ai_dev_config_dir", return_value=config_dir):
        assert shared._load_ecc_profile() is None


def test_load_ecc_profile_extra_only(tmp_path, reset_profile_flags):
    """只有 enabled_extra。"""
    from script.utils import shared

    config_dir = _write_profile(tmp_path, {"enabled_extra": ["django-pro"]})
    with patch("script.utils.shared.get_ai_dev_config_dir", return_value=config_dir):
        profile = shared._load_ecc_profile()

    assert profile == {"enabled_extra": ["django-pro"], "enabled_remove": []}


def test_load_ecc_profile_remove_only(tmp_path, reset_profile_flags):
    """只有 enabled_remove。"""
    from script.utils import shared

    config_dir = _write_profile(tmp_path, {"enabled_remove": ["angular-developer"]})
    with patch("script.utils.shared.get_ai_dev_config_dir", return_value=config_dir):
        profile = shared._load_ecc_profile()

    assert profile == {"enabled_extra": [], "enabled_remove": ["angular-developer"]}


def test_merge_user_overrides_formula(reset_profile_flags):
    """final = (repo.enabled ∪ extra) \\ remove；保序、去重。"""
    from script.utils.shared import _merge_user_overrides

    skills_cfg = {"enabled": ["a", "b", "c"]}
    profile = {"enabled_extra": ["d", "b"], "enabled_remove": ["c"]}
    _merge_user_overrides(skills_cfg, profile)

    # 順序：repo 先，extra 後；c 被移除；b 已存在不重複加
    assert skills_cfg["enabled"] == ["a", "b", "d"]


def test_merge_user_overrides_conflict_remove_wins(reset_profile_flags):
    """同名衝突：remove 勝出。"""
    from script.utils.shared import _merge_user_overrides

    skills_cfg = {"enabled": ["a", "b"]}
    profile = {"enabled_extra": ["c"], "enabled_remove": ["c"]}
    _merge_user_overrides(skills_cfg, profile)

    assert skills_cfg["enabled"] == ["a", "b"]


def test_merge_user_overrides_remove_not_in_enabled(reset_profile_flags):
    """remove 列出不在 repo.enabled 的名稱 → 靜默忽略。"""
    from script.utils.shared import _merge_user_overrides

    skills_cfg = {"enabled": ["a"]}
    profile = {"enabled_extra": [], "enabled_remove": ["does-not-exist"]}
    _merge_user_overrides(skills_cfg, profile)

    assert skills_cfg["enabled"] == ["a"]


def test_load_ecc_profile_legacy_compat(tmp_path, capsys, reset_profile_flags):
    """legacy include_skills/exclude_skills 自動相容並印 hint。"""
    from script.utils import shared

    config_dir = _write_profile(tmp_path, {
        "include_skills": ["django-pro"],
        "exclude_skills": ["angular"],
    })
    with patch("script.utils.shared.get_ai_dev_config_dir", return_value=config_dir):
        profile = shared._load_ecc_profile()

    assert profile == {"enabled_extra": ["django-pro"], "enabled_remove": ["angular"]}
    out = capsys.readouterr().out
    assert "include_skills" in out
    assert "已自動相容" in out


def test_load_ecc_profile_new_keys_win_over_legacy(tmp_path, capsys, reset_profile_flags):
    """新舊鍵同時存在：新鍵優先，legacy 被忽略並印警告。"""
    from script.utils import shared

    config_dir = _write_profile(tmp_path, {
        "enabled_extra": ["new-name"],
        "include_skills": ["legacy-name"],
    })
    with patch("script.utils.shared.get_ai_dev_config_dir", return_value=config_dir):
        profile = shared._load_ecc_profile()

    assert profile["enabled_extra"] == ["new-name"]
    assert "legacy-name" not in profile["enabled_extra"]
    out = capsys.readouterr().out
    assert "優先" in out or "忽略" in out


def test_load_distribution_config_merges_profile(tmp_path, reset_profile_flags):
    """_load_distribution_config 整合：合併 profile 進 enabled。"""
    from script.utils import shared

    custom_skills = tmp_path / "custom-skills"
    upstream = custom_skills / "upstream"
    upstream.mkdir(parents=True)
    (upstream / "distribution.yaml").write_text(yaml.safe_dump({
        "version": 1,
        "source": "ecc",
        "source_path": str(tmp_path / "ecc"),
        "distribute": {
            "skills": {
                "source_path": "skills/",
                "targets": ["claude"],
                "enabled": ["repo-skill"],
            }
        },
    }))
    config_dir = _write_profile(tmp_path, {
        "enabled_extra": ["user-skill"],
        "enabled_remove": ["repo-skill"],
    })

    with patch("script.utils.shared.get_custom_skills_dir", return_value=custom_skills), \
         patch("script.utils.shared.get_ai_dev_config_dir", return_value=config_dir):
        cfg = shared._load_distribution_config()

    assert cfg["distribute"]["skills"]["enabled"] == ["user-skill"]


def test_distribute_ecc_selective_warns_on_orphan(tmp_path, fake_ecc, capsys, reset_profile_flags):
    """_distribute_ecc_selective 收到 old_manifest 有 ECC skill 但不在新 enabled → 印警告。"""
    from script.utils import shared
    from script.utils.manifest import ManifestTracker

    dst = tmp_path / "dst-skills"
    dst.mkdir()

    dist_config = {
        "source_path": str(fake_ecc),
        "distribute": {
            "skills": {
                "source_path": "skills/",
                "targets": ["claude"],
                "enabled": ["alpha"],   # beta 從 enabled 拿掉了
            }
        },
        "skip_directories": [],
        "exclude": {},
    }

    old_manifest = {
        "files": {
            "skills": {
                "alpha": {"hash": "x", "source": "ecc"},
                "beta": {"hash": "y", "source": "ecc"},      # 將被孤兒清理
                "local-only": {"hash": "z", "source": "custom-skills"},  # 不該被列入
            }
        }
    }

    tracker = ManifestTracker(target="claude")
    with patch.dict(shared.COPY_TARGETS, {"claude": {"skills": dst}}, clear=False):
        shared._distribute_ecc_selective(
            target="claude",
            target_name="Claude Code",
            tracker=tracker,
            skip_names=set(),
            dist_config=dist_config,
            old_manifest=old_manifest,
        )

    out = capsys.readouterr().out
    assert "本次分發將移除" in out
    assert "beta" in out
    # 非 ECC 的不該被列入
    assert "local-only" not in out
