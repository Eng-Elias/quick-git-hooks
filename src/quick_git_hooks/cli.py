"""Command line interface for quick-git-hooks."""

import sys
from pathlib import Path

import click

try:
    import importlib.resources as pkg_resources
except ImportError:
    import importlib_resources as pkg_resources  # type: ignore

from .utils import (
    ESLINTRC_GLOB,
    HOOK_TYPES,
    JS_TOOLS,
    PACKAGE_JSON,
    PRETTIERRC_GLOB,
    PYTHON_TOOLS,
    TARGET_CONFIG_FILE,
    check_hook_installed,
    command_exists,
    find_config_file,
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

    # Install commitizen if missing
    if not command_exists("cz"):
        click.echo("   Installing commitizen...")
        ok, _, err = run_command(["pip", "install", "commitizen"])
        if not ok:
            click.secho(f"   ⚠️ Failed to install commitizen: {err}", fg="yellow")
            success = False
        else:
            click.secho("   ✅ Installed commitizen", fg="green")

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


def _check_python_tools() -> tuple[list[str], bool]:
    """Check Python tools and return any missing tools and overall status."""
    missing_tools = []
    all_tools_ok = True
    for tool, install_cmd in PYTHON_TOOLS.items():
        check_cmd = "cz" if tool == "commitizen" else tool
        if not command_exists(check_cmd):
            missing_tools.append(f"     - {tool}: `{install_cmd}` (add to dev dependencies)")
            all_tools_ok = False
    return missing_tools, all_tools_ok


def _check_js_tools() -> tuple[list[str], bool]:
    """Check JavaScript/TypeScript tools and return any missing items and overall status."""
    missing_tools = []
    all_tools_ok = True

    # Check Prettier
    if not command_exists("prettier"):
        missing_tools.append(f"     - prettier: `{JS_TOOLS['prettier']}`")
        all_tools_ok = False
    if not find_config_file(PRETTIERRC_GLOB):
        missing_tools.append(f"     - Prettier config: Create a '{PRETTIERRC_GLOB}' file (e.g., .prettierrc.json)")
        all_tools_ok = False

    # Check ESLint
    if not command_exists("eslint"):
        missing_tools.append(f"     - eslint: `{JS_TOOLS['eslint']}`")
        all_tools_ok = False
    if not find_config_file(ESLINTRC_GLOB):
        missing_tools.append(f"     - ESLint config: Create an '{ESLINTRC_GLOB}' file (e.g., .eslintrc.js)")
        all_tools_ok = False

    return missing_tools, all_tools_ok


def _print_dependency_instructions():
    """Checks for common tools and prints installation instructions if missing."""
    click.echo("\n Priting Instructions:")
    click.echo("ℹ️  Checking for required tools and configurations...")

    # Check Python tools
    missing_py_tools, py_tools_ok = _check_python_tools()
    if missing_py_tools:
        click.secho("\n   🐍 Python Tools:", fg="cyan")
        for item in missing_py_tools:
            click.echo(item)
        click.echo("      (Add these to your project's dev dependencies, e.g., in `pyproject.toml`)")

    # Check JS/TS tools if package.json exists
    if PACKAGE_JSON.exists():
        click.secho("\n   📜 JavaScript/TypeScript Tools (package.json detected):", fg="cyan")
        missing_js_tools, js_tools_ok = _check_js_tools()
        if missing_js_tools:
            for item in missing_js_tools:
                click.echo(item)
            click.echo("      (Install via npm/yarn and configure according to your project needs)")
        else:
            click.echo("     ✅ Prettier & ESLint commands and config files seem present.")
            click.echo("        (Ensure they are configured correctly in .prettierrc.* and .eslintrc.*)")
    else:
        click.echo("\n   📜 No package.json detected, skipping JS/TS tool check.")

    click.echo("\n👉 You can verify the setup using: `quick-git-hooks check`")


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

    # Python Tools Check
    for tool in PYTHON_TOOLS:
        check_cmd = "cz" if tool == "commitizen" else tool
        if command_exists(check_cmd):
            success_msgs.append(f"✅ {tool} command found.")
        else:
            warning_msgs.append(f"⚠️ {tool} command not found. Install: `{PYTHON_TOOLS[tool]}`")

    # JS/TS Tools Check
    if PACKAGE_JSON.exists():
        click.echo("   Checking JS/TS tools...")
        missing_js_tools, _ = _check_js_tools()
        if missing_js_tools:
            warning_msgs.extend(missing_js_tools)
    else:
        click.echo("   Skipping JS/TS tool check (no package.json).")

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

    # Print dependency instructions for any remaining tools
    _print_dependency_instructions()

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


if __name__ == "__main__":
    cli()
