# CLI Development Reference

Guide for developing the ai-dev CLI tool.

## Table of Contents

- [Project Setup](#project-setup)
- [Directory Structure](#directory-structure)
- [Adding Commands](#adding-commands)
- [Adding TUI Features](#adding-tui-features)
- [Testing](#testing)
- [Common Patterns](#common-patterns)

---

## Project Setup

### Prerequisites

- Python 3.11+
- uv (Python package manager)

### Local Development

```bash
# Clone repository
git clone https://github.com/ValorVie/custom-skills.git
cd custom-skills

# Install dependencies
uv sync

# Install locally for testing
uv tool install . --force

# Verify
ai-dev --version
```

### Version Bump Note

`uv` caches based on version number. If modifying code without version change:
1. Update `version` in `pyproject.toml`
2. Run `uv tool install . --force`

---

## Directory Structure

```
script/
├── __init__.py          # Package init
├── main.py              # CLI entry point (Click app)
├── commands/            # CLI command implementations
│   ├── __init__.py
│   ├── install.py       # ai-dev install
│   ├── update.py        # ai-dev update
│   ├── status.py        # ai-dev status
│   ├── list_cmd.py      # ai-dev list
│   ├── toggle.py        # ai-dev toggle
│   ├── clone.py         # ai-dev clone
│   ├── project.py       # ai-dev project init/update
│   ├── standards.py     # ai-dev standards
│   └── hooks.py         # ai-dev hooks
├── tui/                 # Terminal UI (Textual)
│   ├── __init__.py
│   ├── app.py           # Main TUI application
│   └── styles.tcss      # TUI styles
└── utils/               # Shared utilities
    ├── __init__.py
    ├── paths.py         # Path resolution
    └── shared.py        # Copy logic, configurations
```

---

## Adding Commands

### Step 1: Create Command File

`script/commands/mycommand.py`:

```python
"""My command description."""
import click
from rich.console import Console

console = Console()

@click.command()
@click.option("--flag", "-f", is_flag=True, help="Flag description")
@click.argument("name", required=False)
def mycommand(flag: bool, name: str | None):
    """Command help text shown in --help."""
    console.print(f"[green]Running mycommand[/green]")
    if flag:
        console.print("Flag is set")
    if name:
        console.print(f"Name: {name}")
```

### Step 2: Register in main.py

`script/main.py`:

```python
from .commands.mycommand import mycommand

# Add to CLI group
cli.add_command(mycommand)
```

### Step 3: Update Documentation

1. Update `README.md` command table
2. Add to CHANGELOG.md

---

## Adding TUI Features

TUI uses [Textual](https://textual.textualize.io/) framework.

### File Structure

- `script/tui/app.py` - Main application class
- `script/tui/styles.tcss` - CSS-like styling

### Adding a Button

```python
# In app.py
from textual.widgets import Button

def compose(self) -> ComposeResult:
    yield Button("My Button", id="my-button")

@on(Button.Pressed, "#my-button")
def handle_my_button(self) -> None:
    self.notify("Button pressed!")
```

### Adding a Screen

```python
from textual.screen import Screen

class MyScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Static("My Screen Content")

# Push screen
self.push_screen(MyScreen())
```

---

## Testing

### Manual Testing

```bash
# Install and test
uv tool install . --force
ai-dev status
ai-dev list --target claude --type skills

# TUI testing
ai-dev tui
```

### Testing Specific Features

```bash
# Test install (skip slow operations)
ai-dev install --skip-npm --skip-repos

# Test copy logic only
ai-dev clone

# Test status
ai-dev status
```

---

## Common Patterns

### Console Output

```python
from rich.console import Console
from rich.table import Table

console = Console()

# Simple output
console.print("[green]Success[/green]")
console.print("[red]Error[/red]")
console.print("[yellow]Warning[/yellow]")

# Table output
table = Table(title="Resources")
table.add_column("Name")
table.add_column("Status")
table.add_row("skill-1", "[green]enabled[/green]")
console.print(table)
```

### Path Handling

```python
from ..utils.paths import (
    get_config_dir,
    get_claude_skills_dir,
    get_custom_skills_dir,
)

# Get paths
config = get_config_dir()  # ~/.config/
claude_skills = get_claude_skills_dir()  # ~/.claude/skills/
custom = get_custom_skills_dir()  # ~/.config/custom-skills/
```

### Error Handling

```python
import sys

try:
    do_something()
except Exception as e:
    console.print(f"[red]Error: {e}[/red]")
    sys.exit(1)
```

### Running External Commands

```python
import subprocess

result = subprocess.run(
    ["git", "status"],
    capture_output=True,
    text=True,
    cwd=repo_path,
)
if result.returncode != 0:
    console.print(f"[red]Git error: {result.stderr}[/red]")
```

---

## Dependencies

Key dependencies in `pyproject.toml`:

| Package | Purpose |
|---------|---------|
| click | CLI framework |
| rich | Terminal formatting |
| textual | TUI framework |
| pyyaml | YAML parsing |

### Adding Dependencies

```bash
uv add <package>
uv sync
```
