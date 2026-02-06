from pathlib import Path

from script.utils import paths, shared


def test_get_opencode_plugin_dir_uses_plural(monkeypatch):
    monkeypatch.setattr(paths, "get_home_dir", lambda: Path("/tmp/test-home"))
    assert paths.get_opencode_plugin_dir() == Path(
        "/tmp/test-home/.config/opencode/plugins"
    )


def test_copy_targets_opencode_plugins_matches_path_helper():
    assert shared.COPY_TARGETS["opencode"]["plugins"] == paths.get_opencode_plugin_dir()


def test_migrate_opencode_plugin_dir_moves_legacy_when_modern_missing(
    tmp_path, monkeypatch
):
    opencode_root = tmp_path / "opencode"
    legacy_dir = opencode_root / "plugin"
    modern_dir = opencode_root / "plugins"
    legacy_dir.mkdir(parents=True)
    (legacy_dir / "legacy.ts").write_text("export const x = 1\n", encoding="utf-8")

    monkeypatch.setattr(shared, "get_opencode_config_dir", lambda: opencode_root)
    monkeypatch.setattr(shared, "get_opencode_plugin_dir", lambda: modern_dir)

    shared._migrate_opencode_plugin_dir_if_needed()

    assert not legacy_dir.exists()
    assert modern_dir.exists()
    assert (modern_dir / "legacy.ts").exists()


def test_migrate_opencode_plugin_dir_keeps_both_when_modern_exists(
    tmp_path, monkeypatch
):
    opencode_root = tmp_path / "opencode"
    legacy_dir = opencode_root / "plugin"
    modern_dir = opencode_root / "plugins"
    legacy_dir.mkdir(parents=True)
    modern_dir.mkdir(parents=True)
    (legacy_dir / "legacy.ts").write_text("legacy\n", encoding="utf-8")
    (modern_dir / "modern.ts").write_text("modern\n", encoding="utf-8")

    monkeypatch.setattr(shared, "get_opencode_config_dir", lambda: opencode_root)
    monkeypatch.setattr(shared, "get_opencode_plugin_dir", lambda: modern_dir)

    shared._migrate_opencode_plugin_dir_if_needed()

    assert legacy_dir.exists()
    assert modern_dir.exists()
    assert (legacy_dir / "legacy.ts").exists()
    assert (modern_dir / "modern.ts").exists()


def test_ensure_opencode_plugin_entry_file_creates_js_entry(tmp_path):
    dst = tmp_path / "plugins"
    dst.mkdir(parents=True)
    plugin_ts = dst / "plugin.ts"
    plugin_ts.write_text("export const EccHooksPlugin = {}\n", encoding="utf-8")

    shared._ensure_opencode_plugin_entry_file(dst)

    js_entry = dst / "ecc-hooks-opencode.js"
    assert js_entry.exists()
    js_content = js_entry.read_text(encoding="utf-8")
    assert 'import { EccHooksPlugin } from "./plugin.ts";' in js_content
    assert "export default EccHooksPlugin;" in js_content
