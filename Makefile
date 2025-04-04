.PHONY: help install install-dev build publish clean clean-unix clean-windows

# Default target
help:
	@echo "Available commands for quick-git-hooks development:"
	@echo "  install       - Install package from local sources"
	@echo "  install-dev   - Install package in editable mode and dev dependencies"
	@echo "  build         - Build the package distribution files"
	@echo "  publish       - Upload the package to PyPI (requires twine)"
	@echo "  clean         - Remove build artifacts, caches, and compiled files"

# Variables
PYTHON = python # Use 'python' - assumes it's in PATH and resolves correctly
PIP = $(PYTHON) -m pip
SRC_DIR = src/quick_git_hooks

install:
	@echo "--- Installing package ---"
	$(PIP) install .

install-dev:
	@echo "--- Installing package in editable mode with dev dependencies ---"
	$(PIP) install -e .
	$(PIP) install -r requirements-dev.txt

build: clean
	@echo "--- Building package ---"
	$(PYTHON) -m build

publish: build
	@echo "--- Publishing to PyPI ---"
	@echo "Ensure you have twine installed ($(PIP) install twine) and configured."
	$(PYTHON) -m twine upload dist/*

# --- Cleaning Logic ---

# Common patterns to remove
CLEAN_PATTERNS_DIRS = build dist *.egg-info .pytest_cache .mypy_cache htmlcov .tox .nox __pycache__ .ipynb_checkpoints
CLEAN_PATTERNS_FILES = *.py[cod] *.so *.coverage .coverage.* *.log MANIFEST *.manifest *.spec *.cover *.log

# Detect OS
ifeq ($(OS),Windows_NT)
	detected_os = windows
else
	detected_os = unix
endif

# Main clean target
clean:
ifeq ($(detected_os),windows)
	@$(MAKE) clean-windows
else
	@$(MAKE) clean-unix
endif

# Clean command for Unix-like systems (Linux, macOS, Git Bash on Windows)
clean-unix:
	@echo "--- Cleaning build artifacts (Unix) ---"
	rm -rf $(CLEAN_PATTERNS_DIRS)
	find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
	find . -type f \( $(foreach ext,$(CLEAN_PATTERNS_FILES), -name "$(ext)" -o) -false \) -delete 2>/dev/null || true
	@echo "Clean complete."

# Clean command for Windows (CMD, PowerShell)
# Uses built-in commands for better compatibility than relying on rm/find potentially not being in PATH
clean-windows:
	@echo "--- Cleaning build artifacts (Windows) ---"
	@for %%d in ($(CLEAN_PATTERNS_DIRS)) do ( if exist "%%d" ( echo Removing directory %%d && rmdir /s /q "%%d" 2>nul || echo Could not remove %%d ) )
	@echo Removing __pycache__ recursively...
	@for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"
	@echo Removing compiled/log files...
	@for %%f in ($(CLEAN_PATTERNS_FILES)) do ( del /s /q /f "%%f" 2>nul )
	@echo Clean complete.
