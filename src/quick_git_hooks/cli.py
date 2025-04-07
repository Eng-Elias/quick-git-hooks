"""Command-line interface for quick-git-hooks."""

import glob
import os
import shutil
import sys
from pathlib import Path

import click

try:
    import importlib.resources as pkg_resources
except ImportError:
    import importlib_resources as pkg_resources  # type: ignore

from .utils import (
    HOOK_TYPES,
    JS_TOOLS,
    PYTHON_TOOLS,
    TARGET_CONFIG_FILE,
    check_hook_installed,
    command_exists,
    get_template_path,
    is_git_repo,
    run_command,
)

# --- Helper for Setup ---


def _copy_template_files(overwrite: bool) -> tuple[bool, bool]:
    """Copies template files to the target directory.

    Returns:
        Tuple of (config_copied, guide_copied)
    """
    config_copied = False
    guide_copied = False

    try:
        files = pkg_resources.files("quick_git_hooks.templates")

        # Copy config file
        config_template = files / ".pre-commit-config.yaml"
        if not TARGET_CONFIG_FILE.exists() or overwrite:
            config_text = config_template.read_text()
            TARGET_CONFIG_FILE.write_text(config_text)
            click.secho("✅ Created .pre-commit-config.yaml", fg="green")
            config_copied = True
        else:
            click.secho("⚠️ '.pre-commit-config.yaml' already exists. Use --overwrite to replace it.", fg="yellow")
            click.echo("Skipping config file creation.")

        # Copy guide file
        guide_template = files / "GIT_HOOKS_GUIDE.md"
        guide_target = Path("GIT_HOOKS_GUIDE.md")
        if not guide_target.exists() or overwrite:
            guide_text = guide_template.read_text()
            guide_target.write_text(guide_text)
            click.secho("✅ Created GIT_HOOKS_GUIDE.md", fg="green")
            guide_copied = True
        else:
            click.secho("⚠️ 'GIT_HOOKS_GUIDE.md' already exists. Use --overwrite to replace it.", fg="yellow")
            click.echo("Skipping guide file creation.")

    except Exception as e:
        click.secho(f"Error copying template files: {str(e)}", fg="red")
        return False, False

    return config_copied, guide_copied


def _install_python_tools() -> bool:
    """Install required Python tools if missing. Returns True if all installations were successful."""
    success = True

    for tool, info in PYTHON_TOOLS.items():
        if not command_exists(info["command"]):
            click.echo(f"   Installing {tool}...")
            ok, _, err = run_command(["pip", "install", *info["packages"]])
            if not ok:
                click.secho(f"   ⚠️ Failed to install {tool}: {err}", fg="yellow")
                success = False
            else:
                click.secho(f"   ✅ Installed {tool}", fg="green")

    return success


def _install_hooks() -> bool:
    """Install pre-commit hooks. Returns True if successful."""
    success = True
    click.echo("\n🔧 Installing pre-commit hooks...")

    # First ensure pre-commit is installed
    if not command_exists("pre-commit"):
        click.secho(
            "Error: 'pre-commit' command not found. Please install it ('pip install pre-commit')"
            "and ensure it's in your PATH.",
            fg="red",
        )
        return False

    # Install hooks for each type
    for hook_type in HOOK_TYPES:
        click.echo(f"   - Installing {hook_type} hooks...")
        cmd = ["pre-commit", "install", "--hook-type", hook_type]
        ok, _, err_out = run_command(cmd)
        if not ok:
            success = False
            click.secho(f"   ⚠️ Failed to install {hook_type} hook: {err_out}", fg="yellow")

    return success


def _has_js_or_ts_files():
    """Check if the current directory has JavaScript or TypeScript files."""
    js_patterns = ["**/*.js", "**/*.jsx", "**/*.ts", "**/*.tsx", "**/*.mjs", "**/*.cjs", "**/*.mts"]
    for pattern in js_patterns:
        if glob.glob(pattern, recursive=True):
            return True
    return False


def _copy_eslint_config():
    """Copy ESLint config file if it doesn't exist and JS/TS files are present."""
    if not _has_js_or_ts_files():
        return

    eslint_config = "eslint.config.js"
    if os.path.exists(eslint_config):
        click.echo(f"Found existing {eslint_config}, skipping...")
        return

    try:
        shutil.copy(str(get_template_path() / eslint_config), eslint_config)
        click.echo(f"Created {eslint_config} with default configuration")
    except Exception as e:
        click.echo(f"Warning: Could not create {eslint_config}: {e}", err=True)


def _install_js_tools():
    """Install JavaScript/TypeScript tools globally if needed."""
    if not _has_js_or_ts_files():
        return

    if not command_exists("npm"):
        click.echo("\n⚠️  npm not found. Please install Node.js to use JavaScript/TypeScript features.")
        return

    click.echo("\n📦 Installing JavaScript/TypeScript tools globally...")
    missing_tools = []

    for tool, info in JS_TOOLS.items():
        if not command_exists(info["command"]):
            missing_tools.append(tool)
            try:
                click.echo(f"\n🔧 Installing {tool}...")
                success, stdout, stderr = run_command(["npm", "install", "-g", *info["packages"]])
                if not success:
                    click.echo(f"⚠️  Failed to install {tool}. Error: {stderr}", err=True)
            except Exception as e:
                click.echo(f"⚠️  Error installing {tool}: {e}", err=True)

    if not missing_tools:
        click.echo("✅ All JavaScript/TypeScript tools are already installed.")
    else:
        click.echo("\n✅ Finished installing JavaScript/TypeScript tools.")


def _check_python_tools() -> tuple[list[str], list[str], list[str], bool]:
    """Check Python tools and return messages and status."""
    success_msgs = []
    warning_msgs = []
    error_msgs = []
    issues_found = False

    click.echo("\n   🐍 Python tools:")
    missing_tools = []

    for tool, info in PYTHON_TOOLS.items():
        check_cmd = info["command"]
        if command_exists(check_cmd):
            success_msgs.append(f"✅ {tool} command found.")
        else:
            missing_tools.append(f"   - {tool}: {info['install']}")
            warning_msgs.append(f"⚠️ {tool} command not found. Install: `{info['install']}`")
            issues_found = True

    if missing_tools:
        click.echo("\n   ⚠️ Missing tools:")
        for tool in missing_tools:
            click.echo(tool)
    else:
        click.echo("   ✅ All required Python tools are installed.")

    return success_msgs, warning_msgs, error_msgs, issues_found


def _check_js_ts_tools() -> tuple[list[str], list[str], list[str], bool]:
    success_msgs = []
    warning_msgs = []
    error_msgs = []
    issues_found = False

    if not _has_js_or_ts_files():
        return success_msgs, warning_msgs, error_msgs, issues_found

    click.echo("\n   📝 JavaScript/TypeScript tools:")
    missing_tools = []

    # Check for required JS/TS tools
    for tool, info in JS_TOOLS.items():
        if not command_exists(info["command"]):
            missing_tools.append(f"   - {tool}: {info['install']}")

    if missing_tools:
        click.echo("   ⚠️  Missing tools:")
        for tool in missing_tools:
            click.echo(tool)
    else:
        click.echo("   ✅ All required JS/TS tools are installed.")

    return success_msgs, warning_msgs, error_msgs, issues_found


def _check_git_repo() -> tuple[list[str], list[str], list[str], bool]:
    """Check git repository status and return messages and status."""
    success_msgs = []
    warning_msgs = []
    error_msgs = []
    issues_found = False

    if not is_git_repo():
        error_msgs.append("❌ Not a git repository.")
        issues_found = True
        return success_msgs, warning_msgs, error_msgs, issues_found

    success_msgs.append("✅ Git repository detected.")
    return success_msgs, warning_msgs, error_msgs, issues_found


def _check_pre_commit() -> tuple[list[str], list[str], list[str], bool]:
    """Check pre-commit installation and return messages and status."""
    success_msgs = []
    warning_msgs = []
    error_msgs = []
    issues_found = False

    if not command_exists("pre-commit"):
        error_msgs.append("❌ 'pre-commit' command not found. Please install it: pip install pre-commit")
        issues_found = True
    else:
        success_msgs.append("✅ 'pre-commit' command found.")

    if not TARGET_CONFIG_FILE.exists():
        error_msgs.append(f"❌ '{TARGET_CONFIG_FILE}' not found. Run setup first.")
        issues_found = True
    else:
        success_msgs.append(f"✅ '{TARGET_CONFIG_FILE}' found.")

    return success_msgs, warning_msgs, error_msgs, issues_found


def _check_hooks() -> tuple[list[str], list[str], list[str], bool]:
    """Check hook installation status and return messages and status."""
    success_msgs = []
    warning_msgs = []
    error_msgs = []
    issues_found = False
    hooks_ok = True

    for hook_type in HOOK_TYPES:
        if check_hook_installed(hook_type):
            success_msgs.append(f"✅ {hook_type} hook script found in .git/hooks/.")
        else:
            warning_msgs.append(
                f"⚠️ {hook_type} hook script not found or not managed by pre-commit in .git/hooks/. "
                f"Try running `pre-commit install --hook-type {hook_type}`."
            )
            hooks_ok = False
            issues_found = True

    if hooks_ok:
        success_msgs.append("✅ All expected hook types seem installed.")

    return success_msgs, warning_msgs, error_msgs, issues_found


def _check_tools() -> tuple[list[str], list[str], list[str], bool]:
    """Check development tools and return messages and status."""
    success_msgs = []
    warning_msgs = []
    error_msgs = []
    issues_found = False

    # Check Python tools
    py_success_msgs, py_warning_msgs, py_error_msgs, py_issues_found = _check_python_tools()
    success_msgs.extend(py_success_msgs)
    warning_msgs.extend(py_warning_msgs)
    error_msgs.extend(py_error_msgs)
    issues_found = issues_found or py_issues_found

    # Check JS/TS tools
    js_success_msgs, js_warning_msgs, js_error_msgs, js_issues_found = _check_js_ts_tools()
    success_msgs.extend(js_success_msgs)
    warning_msgs.extend(js_warning_msgs)
    error_msgs.extend(js_error_msgs)
    issues_found = issues_found or js_issues_found

    return success_msgs, warning_msgs, error_msgs, issues_found


def _check_files() -> tuple[list[str], list[str], list[str], bool]:
    """Check required files and return messages and status."""
    success_msgs = []
    warning_msgs = []
    error_msgs = []
    issues_found = False

    # Check config file
    if not TARGET_CONFIG_FILE.exists():
        error_msgs.append(f"❌ '{TARGET_CONFIG_FILE}' not found. Run setup first.")
        issues_found = True
    else:
        success_msgs.append(f"✅ '{TARGET_CONFIG_FILE}' found.")

    # Check guide file
    guide_file = Path("GIT_HOOKS_GUIDE.md")
    if not guide_file.exists():
        warning_msgs.append("⚠️ 'GIT_HOOKS_GUIDE.md' not found. Run setup to get the documentation.")
    else:
        success_msgs.append("✅ 'GIT_HOOKS_GUIDE.md' found.")

    return success_msgs, warning_msgs, error_msgs, issues_found


def _run_hooks() -> bool:
    """
    Runs all git hooks.

    Returns:
        bool: True if hooks passed, False if any failed.
    """
    if not command_exists("pre-commit"):
        click.secho("❌ pre-commit not found. Please run setup first.", fg="red")
        return False

    if not TARGET_CONFIG_FILE.exists():
        click.secho("❌ .pre-commit-config.yaml not found. Please run setup first.", fg="red")
        return False

    # Build command
    cmd = ["pre-commit", "run", "--all-files"]

    # Run hooks
    ok, _, err = run_command(cmd)
    if not ok:
        click.secho(f"❌ Hooks failed: {err}", fg="red")
        return False
    return True


def _setup_hooks(overwrite=False):
    """Set up pre-commit hooks in the current Git repository."""
    click.echo("🚀 Starting Git hooks setup...")

    # Check if we're in a git repo
    if not is_git_repo():
        click.secho("❌ Not a git repository. Please run 'git init' first.", fg="red")
        sys.exit(1)
    click.secho("✅ Git repository detected.", fg="green")

    # Copy template files
    config_copied, guide_copied = _copy_template_files(overwrite)
    if not config_copied and not TARGET_CONFIG_FILE.exists():
        click.secho("❌ Failed to create config file. Aborting.", fg="red")
        sys.exit(1)

    # Install required Python tools
    _install_python_tools()

    # Install hooks
    hooks_installed = _install_hooks()
    if not hooks_installed:
        click.secho("❌ Failed to install some hooks. Please check the errors above.", fg="red")
        sys.exit(1)

    # Copy ESLint config if needed (after pre-commit config)
    _copy_eslint_config()

    # Install JS/TS tools if needed
    _install_js_tools()

    # Final success message
    click.secho("\n🎉 Setup process complete!", fg="green")
    if hooks_installed:
        click.echo("   Hooks are installed. Please review any instructions above for missing tools.")
        if guide_copied:
            click.echo("\n📖 Check out GIT_HOOKS_GUIDE.md for detailed information about:")
            click.echo("   - Pre-configured git hooks")
            click.echo("   - Recommended branching strategy")
            click.echo("   - How to customize hooks")

    click.echo("\n💡 Tip: You can customize the hooks by editing .pre-commit-config.yaml")
    click.echo("   After customizing, run 'pre-commit install' to apply your changes.")


# --- CLI Command Group ---
@click.group()
@click.version_option(package_name="quick_git_hooks")
def cli():
    """Quick Git Hooks - Easily set up and manage git hooks."""
    pass


# --- Setup Command ---


@cli.command()
@click.option("--overwrite", is_flag=True, help="Overwrite existing config and guide files if they exist.")
def setup(overwrite: bool):
    """Sets up pre-commit hooks for Python, JS, and TS projects."""
    _setup_hooks(overwrite)


# --- Check Command ---


@cli.command()
def check():
    """
    Verifies the pre-commit setup status and checks for dependencies.
    """
    click.echo("🔍 Checking Git hooks setup status...")

    all_success = []
    all_warnings = []
    all_errors = []
    has_issues = False

    # Run all checks
    for check_func in [_check_git_repo, _check_files, _check_pre_commit, _check_hooks, _check_tools]:
        success, warnings, errors, issues = check_func()
        all_success.extend(success)
        all_warnings.extend(warnings)
        all_errors.extend(errors)
        has_issues = has_issues or issues

    # Print Summary
    click.echo("\n--- Check Summary ---")
    for msg in all_success:
        click.secho(msg, fg="green")
    for msg in all_warnings:
        click.secho(msg, fg="yellow")
    for msg in all_errors:
        click.secho(msg, fg="red")

    if not has_issues and not all_warnings:
        click.secho("\n✅ Setup looks good! Hooks should run.", fg="green")
    elif not has_issues and all_warnings:
        click.secho("\n⚠️ Setup seems okay, but some tools or configs are missing.", fg="yellow")
        click.echo("   Please review the warnings above and install/configure as needed.")
    else:
        click.secho("\n❌ Issues found with the setup. Please fix the errors listed above.", fg="red")


# --- Run Command Group ---


@cli.group()
def run():
    """Run git hooks manually without committing or pushing."""
    pass


@run.command()
def hooks():
    """Run pre-commit hooks manually."""
    click.echo("🔍 Running all git hooks hooks...")
    if _run_hooks():
        click.secho("✅ Pre-commit hooks passed!", fg="green")


if __name__ == "__main__":
    cli()
