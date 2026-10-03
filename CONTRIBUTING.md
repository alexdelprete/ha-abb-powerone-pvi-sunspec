# Contributing to ABB/Power-One/FIMER PVI SunSpec

Thanks for wanting to contribute. This document covers the development environment and the
pull request flow. For anything beyond a small fix, open an issue first so we can agree on the
approach before you spend time on it.

## Development environment: use the devcontainer

The repository ships a devcontainer, and it is **the supported way to develop and run the tests**
on every platform.

Open the repository in VS Code with the [Dev Containers][devcontainers] extension and choose
*Reopen in Container*. Docker Desktop is enough on Windows and macOS. The container gives you,
with no further setup:

- the exact **Python** version pinned in `.python-version`, in a virtualenv that is already on
  `PATH`;
- all development dependencies, installed with `uv pip install -e '.[dev]'` from `pyproject.toml`.
  That includes `pytest-homeassistant-custom-component`, which pins the exact Home Assistant
  release the tests run against;
- `pre-commit` installed and wired to the git hooks, so every commit is linted;
- a live Home Assistant instance you can start on port **8123** (see below).

### Running the tests

```bash
pytest tests/                    # the whole suite, without coverage
pytest tests/test_init.py        # one module
pytest tests/ --cov=custom_components/abb_powerone_pvi_sunspec --cov-report=term-missing
```

The last form is what CI runs. Coverage is collected only in CI so local runs stay fast, and the
VS Code test explorer is configured the same way.

### Linting and type checking

`pre-commit run --all-files` runs everything CI runs: ruff (lint and format), ty, yamllint,
jsonlint and pymarkdown. The same hooks run automatically on `git commit`. The individual tools:

```bash
ruff check custom_components/ tests/
ruff format custom_components/ tests/
ty check custom_components/abb_powerone_pvi_sunspec
```

### Running a live Home Assistant

```bash
scripts/develop
```

or the *Run Home Assistant* task in VS Code. It starts Home Assistant with `config/` as its
configuration directory and this integration loaded from `custom_components/`, then serves the
UI on <http://localhost:8123>.
`config/configuration.yaml` is versioned; the runtime state Home Assistant writes under `config/`
is ignored by git.

## ⚠️ The test suite cannot run natively on Windows

This is not a matter of missing packages: `homeassistant/runner.py` imports **`fcntl`**, which is
a Unix-only module, so the import fails before the first test is collected. No amount of
installing fixes it.

Windows contributors have three options, in order of preference: the **devcontainer** (above),
**WSL**, or any Linux container.

A few further obstacles are worth knowing about, because each one produces an error message that
points somewhere else. They are all handled by the devcontainer, and are listed here only to
explain why it is the supported path rather than a convenience:

| Symptom | Cause |
|---|---|
| `No matching distribution found for homeassistant>=2026.8.0` | Python older than **3.14.2** — pip does not say so. |

## Installing dependencies by hand

If you are not using the devcontainer (Linux or WSL), install the `dev` extra from
`pyproject.toml` in one step, with Python 3.14.2 or newer:

```bash
uv venv && source .venv/bin/activate
uv pip install -e '.[dev]'
pre-commit install
```

`pyproject.toml` is the single source of truth for development dependencies: there is no
`requirements-dev.txt`. `pytest-homeassistant-custom-component` is pinned there to an exact version,
and it in turn pins the exact `homeassistant` release, which is what makes the test environment
reproducible.

## Making changes

- Branch from `main` and keep each pull request to one change.
- Write commit messages as [Conventional Commits][conventional]: `feat:`, `fix:`, `docs:`,
  `refactor:`, `test:`, `chore:`, with an optional scope such as `feat(sensor):`.
- Reference issues neutrally (`Refs #12`), never with closing keywords such as `fixes #12`:
  issues are closed by the maintainer, not by automation.
- Add or update tests for behaviour you change; CI runs the full suite with coverage.
- Do not edit files marked as managed by `repo-sync` (the `BEGIN SHARED` / `END SHARED` blocks
  and the workflow, lint and devcontainer files). They are overwritten from a shared template.
- Make sure `pre-commit run --all-files` and `pytest tests/` pass before opening the pull
  request, and that all CI checks are green before requesting a review.

[devcontainers]: https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers
[conventional]: https://www.conventionalcommits.org/
