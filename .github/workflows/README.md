# GitHub Actions Workflows

This directory contains automated workflows for the Barebones RPG project.

## Workflows

### `deploy-docs.yml`
Automatically builds and deploys Sphinx documentation to GitHub Pages when changes are pushed to the `main` branch.

### `publish-pypi.yml`
Automates testing, building, and publishing the package to PyPI.

**Triggers:**
- **Automatic:** When a GitHub release is published → publishes to PyPI
- **Manual:** Workflow dispatch allows manual testing on Test PyPI or PyPI

**What it does:**
1. Runs full test suite on Python 3.11 and 3.12
2. Checks code formatting with Black
3. Builds wheel and source distributions
4. Validates the package
5. Publishes to PyPI (production) or Test PyPI (testing)

**Setup required:**
See [PUBLISHING.md](../../PUBLISHING.md) for complete setup instructions, including:
- Configuring PyPI trusted publishing
- How to create releases
- How to manually trigger test publishes

## Security

All workflows use **trusted publishing** (OIDC) instead of API tokens, which is more secure. No secrets need to be stored in the repository for PyPI publishing.


