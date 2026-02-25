# fit-scraper

Base module for **scraper modules** within the [**FIT Project**], built using [PySide6](https://doc.qt.io/qtforpython/).
Provides the entrypoint, shared utilities, and PySide6 UI components used to launch and orchestrate acquisition modules.

---


## Dependencies

Main dependencies:

- **Python** >=3.11,<3.14
- **Poetry** (recommended for development)
- [PySide6](https://pypi.org/project/PySide6/)  
- [`fit-acquisition`](https://github.com/fit-project/fit-acquisition) – Base utilities and classes for acquisition

See `pyproject.toml` for the full list and version details.

---

## Local checks (same as CI)

Run these commands before opening a PR, so failures are caught locally first.

### What each tool does
- `pytest`: runs automated tests (`unit`, `contract`, `integration` and `e2e` suites).
- `ruff`: checks code style and common static issues (lint).
- `mypy`: performs static type checking on annotated Python code.
- `bandit`: scans source code for common security anti-patterns.
- `pip-audit`: checks installed dependencies for known CVEs.

### 1) Base setup
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
pip install . pytest ruff mypy "bandit[toml]" pip-audit
python -m pip install --upgrade "setuptools>=78.1.1"
```

### 2) Test suite
```bash
export QT_QPA_PLATFORM=offscreen

# unit tests
pytest -m unit -q tests

# contract tests
pytest -m contract -q tests

# integration tests
pytest -m integration -q tests

# end-to-end smoke tests
pytest -m e2e -q tests
```

### 3) Quality and security checks
```bash
ruff check fit_acquisition tests
mypy fit_acquisition
bandit -c pyproject.toml -r fit_acquisition -q -ll -ii
PIPAPI_PYTHON_LOCATION="$(python -c 'import sys; print(sys.executable)')" \
  python -m pip_audit --progress-spinner off
```

Note: `pip-audit` may print a skip message for `fit-acquisition`, `fit-assets`, `fit-cases`, `fit-common` and `fit-configurations` because they are a local packages and not published on PyPI.

---

## Installation

``` bash
    python3 -m venv .venv
    source .venv/bin/activate
    pip install --upgrade pip
    pip install poetry
    poetry lock
    poetry install
    poetry run python main.py
```

---

## Contributing
1. Fork this repository.  
2. Create a new branch (`git checkout -b feat/my-feature`).  
3. Commit your changes using [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/).  
4. Submit a Pull Request describing your modification.
