"""
AI Development Environment Manager TUI

使用 Textual 框架建立的互動式終端介面。
"""

from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    Checkbox,
    Footer,
    Header,
    Input,
    Label,
    Select,
    Static,
)

from ..main import get_app_version
from ..utils.shared import (
    list_installed_resources,
    load_toggle_config,
    disable_resource,
    enable_resource,
    get_mcp_config_path,
    open_in_editor,
    open_in_file_manager,
)
from ..commands.standards import (
    is_standards_initialized,
    get_profiles_dir,
    list_profiles,
    get_active_profile,
    get_active_profile_path,
    load_yaml,
    save_yaml,
)


# 目標工具選項
TARGET_OPTIONS = [
    ("Claude Code", "claude"),
    ("Antigravity", "antigravity"),
    ("OpenCode", "opencode"),
    ("Codex", "codex"),
    ("Gemini CLI", "gemini"),
]

# 各工具支援的資源類型
TYPE_OPTIONS_BY_TARGET = {
    "claude": [("Skills", "skills"), ("Commands", "commands")],
    "antigravity": [("Skills", "skills"), ("Workflows", "workflows")],
    "opencode": [("Skills", "skills"), ("Commands", "commands"), ("Agents", "agents")],
    "codex": [("Skills", "skills")],
    "gemini": [("Skills", "skills"), ("Commands", "commands")],
}


def sanitize_widget_id(name: str) -> str:
    """將資源名稱轉換為有效的 Textual widget ID。

    Textual widget ID 只能包含字母、數字、底線和連字符，
    且不能以數字開頭。
    """
    import re

    # 將無效字元替換為底線
    safe_id = re.sub(r"[^a-zA-Z0-9_-]", "_", name)
    # 確保不以數字開頭（加上前綴）
    if safe_id and safe_id[0].isdigit():
        safe_id = f"r{safe_id}"
    # 移除開頭的底線
    safe_id = safe_id.lstrip("_")
    # 如果結果為空，使用預設值
    if not safe_id:
        safe_id = "unnamed"
    return safe_id


class AddSkillsModal(ModalScreen):
    """新增第三方 Skills 的對話框。"""

    BINDINGS = [
        Binding("escape", "dismiss", "Close"),
    ]

    def compose(self) -> ComposeResult:
        with Container(id="add-skills-dialog"):
            yield Static("Add Third-Party Skills", id="title")
            yield Label("Package:")
            yield Input(
                placeholder="vercel-labs/agent-skills",
                id="package-input",
            )
            yield Static(
                "Examples:\n"
                "  - vercel-labs/agent-skills\n"
                "  - anthropics/skills\n"
                "  - your-org/your-skills",
                id="examples",
            )
            with Horizontal(id="button-row"):
                yield Button("Install", id="install-btn", variant="primary")
                yield Button("Close", id="close-btn", variant="default")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "install-btn":
            package = self.query_one("#package-input", Input).value.strip()
            if package:
                self.run_npx_skills_add(package)
        elif event.button.id == "close-btn":
            self.dismiss()

    def run_npx_skills_add(self, package: str) -> None:
        """執行 npx skills add <package>，使用 suspend 暫停 TUI。"""
        import subprocess

        # 使用 suspend 暫停 TUI，讓 npx skills 的互動式介面正常顯示
        with self.app.suspend():
            print(f"\n--- Installing: npx skills add {package} ---\n")
            subprocess.run(["npx", "skills", "add", package], check=False)
            print("\n--- Press Enter to return to TUI ---")
            input()

        # 返回後關閉 Modal
        self.dismiss()


class ResourceItem(Horizontal):
    """資源列表項目。"""

    def __init__(
        self,
        name: str,
        source: str,
        enabled: bool,
        target: str,
        resource_type: str,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.resource_name = name
        self.resource_source = source
        self.resource_enabled = enabled
        self.resource_target = target
        self.resource_type = resource_type

    def compose(self) -> ComposeResult:
        # 使用清理過的 ID 避免無效字元（如 .system → _system）
        safe_id = sanitize_widget_id(self.resource_name)
        yield Checkbox(
            self.resource_name,
            value=self.resource_enabled,
            id=f"cb-{safe_id}",
        )
        yield Label(f"({self.resource_source})", classes="resource-source")


class SkillManagerApp(App):
    """AI Development Environment Manager TUI 主程式。"""

    CSS_PATH = "styles.tcss"
    TITLE = "AI Development Environment Manager"
    SUB_TITLE = f"v{get_app_version()}"

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("space", "toggle_selected", "Toggle"),
        Binding("a", "select_all", "Select All"),
        Binding("n", "select_none", "Select None"),
        Binding("s", "save", "Save"),
        Binding("p", "add_package", "Add Package"),
        Binding("e", "open_mcp_editor", "Edit MCP"),
        Binding("f", "open_mcp_finder", "Open Folder"),
        Binding("c", "clone", "Clone"),
        Binding("t", "toggle_profile", "Toggle Profile"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.current_target = "claude"
        self.current_type = "skills"
        self.toggle_config = load_toggle_config()

    def compose(self) -> ComposeResult:
        yield Header()

        # 按鈕列
        with Horizontal(id="button-bar"):
            yield Button("Install", id="btn-install", variant="success")
            yield Button("Update", id="btn-update", variant="warning")
            yield Button("Clone", id="btn-clone", variant="default")
            yield Button("Status", id="btn-status", variant="primary")
            yield Button("Add Skills", id="btn-add-skills", variant="default")
            yield Button("Quit", id="btn-quit", variant="error")

        # 篩選列
        with Horizontal(id="filter-bar"):
            yield Label("Target:")
            yield Select(
                TARGET_OPTIONS,
                value="claude",
                id="target-select",
                allow_blank=False,
            )
            yield Label("Type:")
            yield Select(
                TYPE_OPTIONS_BY_TARGET["claude"],
                value="skills",
                id="type-select",
                allow_blank=False,
            )
            yield Checkbox(
                "Sync to Project",
                value=True,
                id="cb-sync-project",
            )

        # 資源列表
        yield VerticalScroll(id="resource-list")

        # Standards Profile 區塊
        with Container(id="standards-profile-section"):
            yield Static("Standards Profile", id="standards-title")
            with Horizontal(id="standards-row"):
                yield Label("Profile:")
                yield Select(
                    [("載入中...", "loading")],  # 佔位選項，on_mount 時更新
                    id="profile-select",
                    allow_blank=False,
                )
                yield Label("", id="profile-info-label")

        # MCP Config 區塊
        with Container(id="mcp-config-section"):
            yield Static("MCP Config", id="mcp-title")
            yield Label("", id="mcp-path-label")
            with Horizontal(id="mcp-button-row"):
                yield Button("Open in Editor", id="btn-mcp-editor", variant="primary")
                yield Button("Open Folder", id="btn-mcp-folder", variant="default")

        # ECC Hooks Plugin 區塊
        with Container(id="hooks-section"):
            yield Static("ECC Hooks Plugin", id="hooks-title")
            yield Label("", id="hooks-info-label")

        yield Footer()

    def on_mount(self) -> None:
        """初始化時載入資源列表。"""
        self.refresh_resource_list()
        self.update_mcp_config_display()
        self.update_standards_profile_display()
        self.update_hooks_status_display()

    def on_select_changed(self, event: Select.Changed) -> None:
        """處理下拉選單變更。"""
        if event.select.id == "target-select":
            self.current_target = str(event.value)
            # 更新 Type 選單選項
            type_select = self.query_one("#type-select", Select)
            type_options = TYPE_OPTIONS_BY_TARGET.get(self.current_target, [])
            type_select.set_options(type_options)
            if type_options:
                type_select.value = type_options[0][1]
                self.current_type = type_options[0][1]
            self.refresh_resource_list()
            self.update_mcp_config_display()

        elif event.select.id == "type-select":
            self.current_type = str(event.value)
            self.refresh_resource_list()

        elif event.select.id == "profile-select":
            self.switch_standards_profile(str(event.value))

    def _get_sync_project_args(self) -> list[str]:
        """取得 sync-project 參數。"""
        try:
            sync_checkbox = self.query_one("#cb-sync-project", Checkbox)
            if sync_checkbox.value:
                return ["--sync-project"]
            else:
                return ["--no-sync-project"]
        except Exception:
            return []

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """處理按鈕點擊。"""
        button_id = event.button.id

        if button_id == "btn-install":
            self.run_cli_command("install", self._get_sync_project_args())
        elif button_id == "btn-update":
            # update 命令不支援 --sync-project，只更新 repos 和 NPM
            self.run_cli_command("update")
        elif button_id == "btn-clone":
            self.run_cli_command("clone", self._get_sync_project_args())
        elif button_id == "btn-status":
            self.run_cli_command("status")
        elif button_id == "btn-add-skills":
            self.push_screen(AddSkillsModal())
        elif button_id == "btn-quit":
            self.exit()
        elif button_id == "btn-mcp-editor":
            self.action_open_mcp_editor()
        elif button_id == "btn-mcp-folder":
            self.action_open_mcp_finder()
        elif button_id == "btn-hooks-view":
            self.action_view_hooks_config()

    def run_cli_command(self, command: str, extra_args: list[str] | None = None) -> None:
        """在終端機中執行 CLI 指令。

        Args:
            command: CLI 子指令（如 install, update, status）
            extra_args: 額外的命令列參數
        """
        import subprocess
        import shutil

        # 優先使用已安裝的 ai-dev 指令，否則回退到 python -m
        ai_dev_path = shutil.which("ai-dev")
        if ai_dev_path:
            cmd = [ai_dev_path, command]
        else:
            import sys
            cmd = [sys.executable, "-m", "script.main", command]

        # 添加額外參數
        if extra_args:
            cmd.extend(extra_args)

        # 使用 suspend 暫停 TUI，讓終端機正常顯示
        with self.suspend():
            print(f"\n--- Executing: {' '.join(cmd)} ---\n")
            subprocess.run(cmd, check=False)
            print("\n--- Press Enter to return to TUI ---")
            input()

        # 返回 TUI 後刷新畫面
        self.refresh_resource_list()

    def refresh_resource_list(self) -> None:
        """重新載入資源列表。"""
        container = self.query_one("#resource-list", VerticalScroll)
        container.remove_children()

        resources = list_installed_resources(self.current_target, self.current_type)

        # 從 resources 中取得目前 target/type 的資源
        target_resources = resources.get(self.current_target, {})
        type_resources = target_resources.get(self.current_type, [])

        for item in type_resources:
            name = item["name"]
            source = item["source"]
            # 使用 disabled 欄位判斷是否啟用（disabled=True 表示停用）
            enabled = not item.get("disabled", False)
            container.mount(
                ResourceItem(
                    name=name,
                    source=source,
                    enabled=enabled,
                    target=self.current_target,
                    resource_type=self.current_type,
                    classes="resource-item",
                )
            )

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        """處理 checkbox 變更事件，即時停用/啟用資源。"""
        checkbox = event.checkbox

        # 從 checkbox 的 parent (ResourceItem) 取得資源資訊
        parent = checkbox.parent
        if not isinstance(parent, ResourceItem):
            return

        name = parent.resource_name
        target = parent.resource_target
        resource_type = parent.resource_type

        if event.value:
            # 啟用資源
            self.notify(f"Enabling {name}...")
            success = enable_resource(target, resource_type, name)
            if success:
                self.toggle_config = load_toggle_config()
                self.notify(f"Enabled {name}", severity="information")
            else:
                self.notify(f"Failed to enable {name}", severity="error")
                # 還原 checkbox 狀態
                checkbox.value = False
        else:
            # 停用資源
            self.notify(f"Disabling {name}...")
            success = disable_resource(target, resource_type, name)
            if success:
                self.toggle_config = load_toggle_config()
                self.notify(f"Disabled {name}", severity="warning")
            else:
                self.notify(f"Failed to disable {name}", severity="error")
                # 還原 checkbox 狀態
                checkbox.value = True

        # 重新整理列表
        self.refresh_resource_list()

    def action_toggle_selected(self) -> None:
        """切換選中項目的啟用狀態。"""
        focused = self.focused
        if isinstance(focused, Checkbox):
            focused.toggle()

    def action_select_all(self) -> None:
        """啟用所有項目（會逐一移動檔案）。"""
        self.notify("Enabling all resources...", severity="warning")
        for checkbox in self.query(Checkbox):
            if not checkbox.value:
                checkbox.value = True

    def action_select_none(self) -> None:
        """停用所有項目（會逐一移動檔案）。"""
        self.notify("Disabling all resources...", severity="warning")
        for checkbox in self.query(Checkbox):
            if checkbox.value:
                checkbox.value = False

    def action_save(self) -> None:
        """儲存目前的設定（已改為即時生效，此方法保留為重新整理狀態）。"""
        # 重新載入配置以確保同步
        self.toggle_config = load_toggle_config()
        self.refresh_resource_list()
        self.notify("Settings refreshed!", severity="information")

    def action_add_package(self) -> None:
        """開啟新增套件對話框。"""
        self.push_screen(AddSkillsModal())

    def update_mcp_config_display(self) -> None:
        """更新 MCP Config 區塊顯示。"""
        path, exists = get_mcp_config_path(self.current_target)
        path_label = self.query_one("#mcp-path-label", Label)

        # 顯示路徑，使用 ~ 簡化 home 目錄
        display_path = str(path).replace(str(Path.home()), "~")
        status = "✓" if exists else "✗ (not found)"
        path_label.update(f"Path: {display_path}  {status}")

    def action_open_mcp_editor(self) -> None:
        """在編輯器中開啟 MCP 設定檔。"""
        path, exists = get_mcp_config_path(self.current_target)
        if not exists:
            self.notify(f"Config file not found: {path}", severity="warning")
            return

        if open_in_editor(path):
            self.notify(f"Opening {path.name} in editor...", severity="information")
        else:
            self.notify("Failed to open editor", severity="error")

    def action_open_mcp_finder(self) -> None:
        """在檔案管理器中開啟 MCP 設定檔所在目錄。"""
        path, exists = get_mcp_config_path(self.current_target)
        if not exists:
            # 檔案不存在時，開啟父目錄
            path = path.parent
            if not path.exists():
                self.notify(f"Directory not found: {path}", severity="warning")
                return

        if open_in_file_manager(path):
            self.notify("Opening in file manager...", severity="information")
        else:
            self.notify("Failed to open file manager", severity="error")

    def action_clone(self) -> None:
        """執行 Clone 功能（快捷鍵 c）。"""
        self.run_cli_command("clone", self._get_sync_project_args())

    def update_standards_profile_display(self) -> None:
        """更新 Standards Profile 區塊顯示。"""
        from datetime import datetime

        profile_select = self.query_one("#profile-select", Select)
        info_label = self.query_one("#profile-info-label", Label)

        # 使用新的初始化檢查函式
        if not is_standards_initialized():
            # 專案未初始化
            profile_select.set_options([("未初始化", "none")])
            profile_select.value = "none"
            info_label.update("執行 `ai-dev project init` 初始化")
            return

        # 載入可用 profiles（從 active-profile.yaml.available）
        profiles = list_profiles()
        if not profiles:
            profile_select.set_options([("無可用 profile", "none")])
            profile_select.value = "none"
            info_label.update("")
            return

        # 設定下拉選單選項
        profile_options = [(name, name) for name in sorted(profiles)]
        profile_select.set_options(profile_options)

        # 設定目前啟用的 profile
        active = get_active_profile()
        if active in profiles:
            profile_select.value = active
        else:
            profile_select.value = profiles[0]

        # 顯示臨時模式提示
        info_label.update(f"({len(profiles)} profiles 可用，臨時模式)")

    def _update_profile_info_label(self, profile_name: str) -> None:
        """更新 profile 資訊標籤。

        TODO: Phase 2 應讀取 profiles/*.yaml 檔案顯示詳細資訊。
        當前臨時實作只顯示簡單提示。
        """
        info_label = self.query_one("#profile-info-label", Label)
        total_profiles = len(list_profiles())
        info_label.update(f"({total_profiles} profiles 可用，臨時模式)")

    def switch_standards_profile(self, new_profile: str) -> None:
        """切換 Standards Profile。"""
        from datetime import datetime

        # 忽略佔位符和無效值
        if new_profile in ("none", "loading"):
            return

        profiles = list_profiles()
        if new_profile not in profiles:
            self.notify(f"Profile '{new_profile}' 不存在", severity="error")
            return

        active = get_active_profile()
        if new_profile == active:
            return

        # 更新 active-profile.yaml
        active_path = get_active_profile_path()
        active_config = load_yaml(active_path)
        active_config['active'] = new_profile
        active_config['last_updated'] = datetime.now().strftime('%Y-%m-%d')
        save_yaml(active_path, active_config)

        self.notify(f"已切換到 '{new_profile}' profile", severity="information")
        self._update_profile_info_label(new_profile)

    def action_toggle_profile(self) -> None:
        """循環切換 Standards Profile（快捷鍵 t）。"""
        profiles_dir = get_profiles_dir()
        if not profiles_dir.exists():
            self.notify("專案未初始化標準體系", severity="warning")
            return

        profiles = sorted(list_profiles())
        if len(profiles) <= 1:
            self.notify("只有一個可用 profile", severity="warning")
            return

        active = get_active_profile()
        try:
            current_index = profiles.index(active)
            next_index = (current_index + 1) % len(profiles)
            next_profile = profiles[next_index]
        except ValueError:
            next_profile = profiles[0]

        # 更新下拉選單
        profile_select = self.query_one("#profile-select", Select)
        profile_select.value = next_profile

        # 切換 profile
        self.switch_standards_profile(next_profile)

    # =========================================================================
    # ECC Hooks Plugin Methods
    # =========================================================================

    def update_hooks_status_display(self) -> None:
        """更新 ECC Hooks Plugin 安裝資訊顯示。"""
        info_label = self.query_one("#hooks-info-label", Label)

        # 只顯示安裝方式參考，不做狀態偵測
        info_label.update(
            "安裝方式請參考：[cyan]@plugins/ecc-hooks/README.md[/cyan]\n"
            "快速安裝：claude --plugin-dir \"/path/to/custom-skills/plugins/ecc-hooks\""
        )



def main() -> None:
    """TUI 主程式入口。"""
    app = SkillManagerApp()
    app.run()


if __name__ == "__main__":
    main()
