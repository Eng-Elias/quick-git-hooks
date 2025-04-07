# Quick Git Hooks

A CLI tool to quickly set up and manage pre-commit Git hooks for Python, JavaScript, and TypeScript projects.

## Features

- 🚀 One-command setup of pre-commit hooks
- 🔍 Automatic detection of Python/JS/TS projects
- 📝 Comprehensive documentation and guides
- ✨ Pre-configured hooks for:
  - Code formatting (black, prettier)
  - Linting (flake8, eslint with flat config)
  - Import sorting (isort)
  - Commit message formatting (commitizen)
  - Branch naming conventions
- 🔄 Easy hook management and customization
- 🛠️ Modern tooling support:
  - ESLint flat config (eslint.config.js)
  - Automatic tool installation
  - Smart file ignoring (.prettierignore)

## Installation

```bash
pip install quick-git-hooks
```

## Quick Start

1. Navigate to your Git repository:

   ```bash
   cd your-repository
   ```

2. Run the setup command:

   ```bash
   quick-git-hooks setup
   ```

   This will:

   - Create `.pre-commit-config.yaml` with recommended hooks
   - Create `GIT_HOOKS_GUIDE.md` with detailed documentation
   - For JS/TS projects:
     - Create `eslint.config.js` with modern flat config
     - Install required tools globally (prettier, eslint)
   - Install pre-commit hooks
   - Install required Python tools
   - Provide instructions for any missing dependencies

3. Check the setup status:

   ```bash
   quick-git-hooks check
   ```

4. Review `GIT_HOOKS_GUIDE.md` for:
   - Pre-configured git hooks and their purpose
   - Recommended branching strategy (Git Flow)
   - How to customize hooks
   - Common commands and troubleshooting

## Commands

### Setup

```bash
quick-git-hooks setup [--overwrite]  # Set up hooks (--overwrite to replace existing config)
```

### Check

```bash
quick-git-hooks check  # Verify setup and dependencies
```

### Run Hooks Manually

```bash
quick-git-hooks run hooks  # Run all hooks on all files
```

### Skip Hooks

```bash
git commit --no-verify  # Skip pre-commit and commit-msg hooks
git push --no-verify   # Skip pre-push hooks
```

## Included Hooks

- **Code Quality**

  - black (Python formatting)
  - flake8 (Python linting)
  - isort (Python import sorting)
  - prettier (JS/TS formatting)
  - eslint (JS/TS linting with modern flat config)

- **Commit Quality**

  - commitizen (Conventional Commits)
  - merge conflict detection
  - trailing whitespace fixing
  - end of file fixing

- **Branch Quality**
  - Branch naming convention enforcement
  - Protected branch checks

See `GIT_HOOKS_GUIDE.md` for detailed configuration options.

## Configuration Files

When JS/TS files are detected, the following files are automatically created:

- `eslint.config.js`: Modern ESLint flat configuration with:
  - JavaScript and TypeScript support
  - Recommended rules and best practices
  - Customizable ignore patterns
  - TypeScript-specific rules when needed

## Development

1. Clone the repository:

   ```bash
   git clone https://github.com/Eng-Elias/quick-git-hooks
   cd quick-git-hooks
   ```

2. Create and activate virtual environment:

   ```bash
   python -m venv .venv
   # On Windows:
   .\.venv\Scripts\activate
   # On Unix:
   source .venv/bin/activate
   ```

3. Install development dependencies:

   ```bash
   make install-dev
   ```

4. Available make commands:
   ```bash
   make install       # Install package from local sources
   make install-dev   # Install in editable mode with dev dependencies
   make build         # Build package distribution
   make publish       # Upload to PyPI (requires twine setup)
   make clean         # Clean build artifacts
   ```

## Requirements

- Python ≥ 3.7
- Git
- For Python hooks: black, flake8, isort
- For JS/TS hooks: Node.js, npm (for global installation of prettier and eslint)
- For commit messages: commitizen

## License

MIT License - see LICENSE file for details.
