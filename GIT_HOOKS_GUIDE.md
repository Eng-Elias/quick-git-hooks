# Git Hooks and Branching Strategy Guide

## Pre-configured Git Hooks

This project comes with several pre-configured git hooks to ensure code quality and consistency:

### 1. pre-commit

Runs before each commit to ensure code quality:

- **trim trailing whitespace**: Removes trailing whitespace
- **fix end of files**: Ensures files end with a newline
- **check yaml/toml/json**: Validates configuration files
- **check for merge conflicts**: Prevents committing merge conflicts
- **detect private key**: Prevents committing private keys
- **black**: Formats Python code (max line length: 120)
- **flake8**: Lints Python code
  - Max line length: 120
  - Ignores E203 (conflicts with black)
  - Max complexity: 10
- **isort**: Sorts Python imports (black-compatible)
- **prettier**: Formats JavaScript/TypeScript files
- **eslint**: Lints JavaScript/TypeScript code

### 2. commit-msg

Validates commit messages:

- Enforces [Conventional Commits](https://www.conventionalcommits.org/) format
- Required format: `type(scope): description`
- Types: feat, fix, docs, style, refactor, test, chore
- Example: `feat(auth): add OAuth2 authentication`

### 3. pre-push

Runs before pushing to remote:

- Runs all pre-commit checks
- Validates branch naming convention
- Additional checks can be added as needed

## Recommended Branching Strategy

We recommend following a modified Git Flow strategy with issue tracking integration:

### Main Branches

- `main` / `master`: Production-ready code
- `develop`: Latest development changes
- `QA`: Quality Assurance branch (Optional)
- always merge `develop` to `QA` branch for testing before prepping for release

### Supporting Branches

1. **Feature Branches**

   - Branch from: `develop`
   - Merge back to: `develop`
   - Naming: `feature/issue#<number>-description-in-kebab-case`
   - Example: `feature/issue#123-add-oauth-login`

2. **Bugfix Branches**

   - Branch from: `develop`
   - Merge back to: `develop`
   - Naming: `bugfix/issue#<number>-description-in-kebab-case`
   - Example: `bugfix/issue#456-fix-login-timeout`

3. **Hotfix Branches**

   - Branch from: `main`
   - Merge back to: `main` and `develop`
   - Naming: `hotfix/issue#<number>-description-in-kebab-case`
   - Example: `hotfix/issue#789-fix-critical-security-issue`

4. **Release Branches**

   - Branch from: `develop` / `QA`
   - Merge back to: `main` and `develop` / `QA`
   - Naming: `release/issue#<number>-version-description`
   - Example: `release/issue#321-v1-2-0-beta`

### Branch Protection Rules

Consider implementing these branch protection rules:

1. Require pull request reviews
2. Require status checks to pass
3. No direct pushes to main/develop/QA
4. Keep commit history linear (rebase preferred)

## Branch Name Validation

The pre-push hook enforces the following branch naming rules:

- Protected branches: `main`, `master`, `develop`, `QA`
- Feature branches: `feature/issue#<number>-description`
- Bugfix branches: `bugfix/issue#<number>-description`
- Hotfix branches: `hotfix/issue#<number>-description`
- Release branches: `release/issue#<number>-description`

Where:

- `<number>` is the issue tracker number
- `description` should be in kebab-case (lowercase with hyphens)

## Customizing Hooks

1. Edit `.pre-commit-config.yaml` to modify hook behavior
2. Run `pre-commit install` after changes
3. Test with `pre-commit run --all-files`

## Common Commands

### Hook Installation

```bash
# Install hooks (done automatically by quick-git-hooks setup)
pre-commit install --hook-type pre-commit
pre-commit install --hook-type commit-msg
pre-commit install --hook-type pre-push
```

or you can rerun `quick-git-hooks setup`

### Running Hooks Manually

Using quick-git-hooks:

```bash
# Run on all files
quick-git-hooks run hooks
```

Using pre-commit directly:

```bash
# Run all hooks on staged files
pre-commit run

# Run all hooks on all files
pre-commit run --all-files

# Skip hooks (use sparingly)
git commit --no-verify
git push --no-verify
```

## Additional Resources

- [Conventional Commits](https://www.conventionalcommits.org/)
- [Git Flow](https://nvie.com/posts/a-successful-git-branching-model/)
- [Pre-commit Documentation](https://pre-commit.com/)
- [Black Documentation](https://black.readthedocs.io/)
- [Flake8 Documentation](https://flake8.pycqa.org/)
