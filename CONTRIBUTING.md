# Contributing to Findura

Thank you for your interest in contributing to **Findura**! We welcome contributions, bug reports, and improvements from the community.

Findura is an open-source (Apache-2.0) common inspection ontology and deterministic agent harness designed to provide reproducible evidence packs for operational building inspections, open findings, deadlines, and completed remediations.

---

## 1. Development Prerequisites

- **Python**: Version `3.12` or `3.13` (tested across both in CI).
- **Package Manager**: [`uv`](https://docs.astral.sh/uv/) is the standard package and environment manager for this project.
- **Docker**: For running the local PostgreSQL service.

---

## 2. Local Setup

### 1. Clone the repository

```bash
git clone https://github.com/edgesentry/findura.git
cd findura
```

### 2. Start PostgreSQL

Start the background PostgreSQL database container (port 5432):

```bash
docker compose up -d
```

### 3. Install dependencies

Use `uv` to create the virtual environment and install all runtime and dev dependencies:

```bash
uv sync
```

---

## 3. Running Checks Locally (CI Parity)

Before submitting a pull request, verify that all static checks, type checks, and tests pass locally.

### Code Formatting

Check formatting compliance:
```bash
uv run ruff format --check .
```
Apply automatic formatting:
```bash
uv run ruff format .
```

### Static Analysis & Linting

Run linter checks:
```bash
uv run ruff check .
```
Apply safe auto-fixes:
```bash
uv run ruff check --fix .
```

### Static Type Checking

Check type annotations with `mypy`:
```bash
uv run mypy
```

### Automated Tests and Coverage Gate

Run the test suite against the local PostgreSQL container. Pytest enforces a minimum test coverage floor (>=80%):
```bash
uv run pytest -v
```

### Wheel Packaging Smoke Check (Optional)

Verify that assets bundle cleanly into wheels and sdists:
```bash
uv build
```

---

## 4. Pull Request Guidelines

1. **Branch Naming**: Create a topic branch from `main` using descriptive prefixes:
   - `feat/description` for new features
   - `fix/description` for bug fixes
   - `docs/description` for documentation
   - `ci/description` for workflow and tooling updates
2. **Issue Linkage**: Link the relevant GitHub issue in the PR description (e.g., `Closes #123` or `Fixes #123`).
3. **Commit Messages**: Write clear, descriptive commit messages adhering to conventional prefixes (`feat:`, `fix:`, `docs:`, `ci:`, `packaging:`).
4. **CI Green**: Pull requests run automated CI workflows on both Python 3.12 and 3.13, including code formatting, static analysis, type checking, test coverage verification, OSV vulnerability scanning, and CodeQL security analysis. All checks must pass.

---

## 5. Code of Conduct

We are committed to providing a welcoming, inclusive, and harassment-free environment for everyone. Please be respectful and constructive in all interactions across issues, discussions, and pull requests. When a formal project-wide Code of Conduct is published, it will be linked here.

---

## 6. Security Vulnerability Reporting

Please do not disclose security vulnerabilities in public GitHub issues. Use GitHub's [Private Vulnerability Reporting](https://github.com/edgesentry/findura/security/advisories/new) under the repository's Security tab to report sensitive security issues privately to the maintainers.
