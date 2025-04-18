import os
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple

import click

try:
    from importlib.resources import files
except ImportError:
    # For Python < 3.9
    from importlib_resources import files

# --- Constants ---
TARGET_CONFIG_FILE = Path(".pre-commit-config.yaml")
GIT_DIR = Path(".git")
PACKAGE_JSON = Path("package.json")
PRETTIERRC_GLOB = ".prettierrc.*"  # Glob pattern for prettier config
ESLINTRC_GLOB = ".eslintrc.*"  # Glob pattern for eslint config

HOOK_TYPES = ["pre-commit", "commit-msg", "pre-push"]

PYTHON_TOOLS = {
    "black": {"command": "black", "install": "pip install black", "packages": ["black"]},
    "flake8": {"command": "flake8", "install": "pip install flake8", "packages": ["flake8"]},
    "isort": {"command": "isort", "install": "pip install isort", "packages": ["isort"]},
    "commitizen": {"command": "cz", "install": "pip install commitizen", "packages": ["commitizen"]},
}

JS_TOOLS = {
    "prettier": {"command": "prettier", "install": "npm install -g prettier", "packages": ["prettier"]},
    "eslint": {
        "command": "eslint",
        "install": "npm install -g eslint @typescript-eslint/parser @typescript-eslint/eslint-plugin",
        "packages": ["eslint", "@typescript-eslint/parser", "@typescript-eslint/eslint-plugin"],
    },
}


# --- Helper Functions ---


def get_template_path() -> Path:
    """Get the path to the templates directory."""
    return files("quick_git_hooks.templates")


def is_git_repo() -> bool:
    """Check if the current directory is a Git repository."""
    return GIT_DIR.is_dir()


def command_exists(command: str) -> bool:
    """Check if a command exists in the system's PATH."""
    try:
        # Use 'where' on Windows, which is equivalent to 'which' on Unix
        cmd = ["where" if os.name == "nt" else "which", command]
        result = subprocess.run(
            " ".join(cmd), shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8"
        )
        return bool(result.stdout.strip())
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def run_command(command: List[str], cwd: Optional[Path] = None, suppress_output: bool = False) -> Tuple[bool, str, str]:
    """
    Runs a shell command and returns success status, stdout, and stderr.
    """
    try:
        # Convert command list to string for Windows shell compatibility
        cmd_str = " ".join(command)
        result = subprocess.run(
            cmd_str,
            check=True,
            capture_output=True,
            text=True,
            cwd=cwd,
            encoding="utf-8",
            shell=True,  # Use shell=True for Windows compatibility
        )
        if not suppress_output:
            if result.stdout:
                click.echo(result.stdout.strip())
            if result.stderr:
                # Don't treat all stderr as errors, pre-commit uses it for info
                click.echo(result.stderr.strip(), err=True)  # Echo to stderr stream
        return True, result.stdout, result.stderr
    except FileNotFoundError:
        click.secho(f"Error: Command '{command[0]}' not found. Is it installed and in your PATH?", fg="red", err=True)
        return False, "", f"Command not found: {command[0]}"
    except subprocess.CalledProcessError as e:
        # Log full error only if output isn't suppressed (e.g., during setup)
        # For checks, we often only care about the success/failure.
        if not suppress_output:
            click.secho(f"Error running command: {' '.join(command)}", fg="red", err=True)
            click.secho(f"Output:\n{e.stdout}", fg="yellow", err=True)
            click.secho(f"Error Output:\n{e.stderr}", fg="red", err=True)
        return False, e.stdout, e.stderr
    except Exception as e:
        if not suppress_output:
            click.secho(f"An unexpected error occurred while running {' '.join(command)}: {e}", fg="red", err=True)
        return False, "", str(e)


def check_hook_installed(hook_type: str) -> bool:
    """Check if a specific pre-commit hook script exists and seems valid."""
    hook_file = GIT_DIR / "hooks" / hook_type
    if not hook_file.is_file():
        return False
    try:
        content = hook_file.read_text(encoding="utf-8")
        # Check for pre-commit script markers
        return "pre-commit" in content and "File generated by pre-commit:" in content and "INSTALL_PYTHON" in content
    except Exception:
        return False  # Error reading file or non-text file


def find_config_file(glob_pattern: str) -> bool:
    """Check if any file matching the glob pattern exists in the current directory."""
    return bool(list(Path(".").glob(glob_pattern)))
