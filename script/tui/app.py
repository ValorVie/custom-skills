"""
AI Development Environment Manager TUI

使用 Textual 框架建立的互動式終端介面。
"""

import asyncio
from pathlib import Path
from typing import Optional

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    Checkbox,
    Footer,
    Header,
    Input,
    Label,
    Log,
    Select,
    Static,
)

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.shared import (
    list_installed_resources,
    load_toggle_config,
    save_toggle_config,
    is_resource_enabled,
    copy_skills,
)


# 目標工具選項
TARGET_OPTIONS = [
    ("Claude Code", "claude"),
    ("Antigravity", "antigravity"),
    ("OpenCode", "opencode"),
]

# 各工具支援的資源類型
TYPE_OPTIONS_BY_TARGET = {
    "claude": [("Skills", "skills"), ("Commands", "commands")],
    "antigravity": [("Skills", "skills"), ("Workflows", "workflows")],
    "opencode": [("Agents", "agents")],
}


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
            yield Static("Output:", id="output-label")
            yield Log(id="output-log")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "install-btn":
            package = self.query_one("#package-input", Input).value.strip()
            if package:
                self.run_worker(self.run_npx_skills_add(package))
        elif event.button.id == "close-btn":
            self.dismiss()

    async def run_npx_skills_add(self, package: str) -> None:
        """執行 npx skills add <package> 並顯示輸出。"""
        log = self.query_one("#output-log", Log)
        log.clear()
        log.write_line(f"$ npx skills add {package}")

        try:
            proc = await asyncio.create_subprocess_exec(
                "npx",
                "skills",
                "add",
                package,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )

            if proc.stdout:
                async for line in proc.stdout:
                    log.write_line(line.decode().rstrip())

            await proc.wait()

            if proc.returncode == 0:
                log.write_line("[green]Installation complete[/green]")
            else:
                log.write_line(f"[red]Installation failed (exit code: {proc.returncode})[/red]")

        except FileNotFoundError:
            log.write_line("[red]Error: npx not found. Please install Node.js.[/red]")
        except Exception as e:
            log.write_line(f"[red]Error: {e}[/red]")


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
        yield Checkbox(
            self.resource_name,
            value=self.resource_enabled,
            id=f"cb-{self.resource_name}",
        )
        yield Label(f"({self.resource_source})", classes="resource-source")


class SkillManagerApp(App):
    """AI Development Environment Manager TUI 主程式。"""

    CSS_PATH = "styles.tcss"
    TITLE = "AI Development Environment Manager"

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("space", "toggle_selected", "Toggle"),
        Binding("a", "select_all", "Select All"),
        Binding("n", "select_none", "Select None"),
        Binding("s", "save", "Save"),
        Binding("p", "add_package", "Add Package"),
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
            yield Button("Maintain", id="btn-maintain", variant="warning")
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

        # 資源列表
        yield VerticalScroll(id="resource-list")

        yield Footer()

    def on_mount(self) -> None:
        """初始化時載入資源列表。"""
        self.refresh_resource_list()

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

        elif event.select.id == "type-select":
            self.current_type = str(event.value)
            self.refresh_resource_list()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """處理按鈕點擊。"""
        button_id = event.button.id

        if button_id == "btn-install":
            self.run_cli_command("install")
        elif button_id == "btn-maintain":
            self.run_cli_command("maintain")
        elif button_id == "btn-status":
            self.run_cli_command("status")
        elif button_id == "btn-add-skills":
            self.push_screen(AddSkillsModal())
        elif button_id == "btn-quit":
            self.exit()

    def run_cli_command(self, command: str) -> None:
        """在終端機中執行 CLI 指令。"""
        import subprocess
        import sys

        script_dir = Path(__file__).parent.parent
        cmd = [sys.executable, str(script_dir / "main.py"), command]

        # 使用 suspend 暫停 TUI，讓終端機正常顯示
        with self.suspend():
            print(f"\n--- Executing: {command} ---\n")
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
            enabled = is_resource_enabled(
                self.toggle_config,
                self.current_target,
                self.current_type,
                name,
            )
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

    def action_toggle_selected(self) -> None:
        """切換選中項目的啟用狀態。"""
        focused = self.focused
        if isinstance(focused, Checkbox):
            focused.toggle()

    def action_select_all(self) -> None:
        """選取所有項目。"""
        for checkbox in self.query(Checkbox):
            checkbox.value = True

    def action_select_none(self) -> None:
        """取消選取所有項目。"""
        for checkbox in self.query(Checkbox):
            checkbox.value = False

    def action_save(self) -> None:
        """儲存目前的設定。"""
        # 收集所有 ResourceItem 的狀態
        disabled_list = []

        for item in self.query(ResourceItem):
            checkbox = item.query_one(Checkbox)
            if not checkbox.value:
                disabled_list.append(item.resource_name)

        # 更新 toggle_config
        if self.current_target not in self.toggle_config:
            self.toggle_config[self.current_target] = {}
        if self.current_type not in self.toggle_config[self.current_target]:
            self.toggle_config[self.current_target][self.current_type] = {
                "enabled": True,
                "disabled": [],
            }

        self.toggle_config[self.current_target][self.current_type]["disabled"] = disabled_list
        save_toggle_config(self.toggle_config)

        # 執行同步
        self.notify("Syncing resources...")
        copy_skills()
        self.notify("Settings saved and synced!", severity="information")

    def action_add_package(self) -> None:
        """開啟新增套件對話框。"""
        self.push_screen(AddSkillsModal())


def main() -> None:
    """TUI 主程式入口。"""
    app = SkillManagerApp()
    app.run()


if __name__ == "__main__":
    main()
