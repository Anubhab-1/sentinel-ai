# Contributing to Sentinel AI

Thank you for your interest in contributing to **RakshaNetra™ Sentinel AI**! We welcome improvements, bug fixes, and new features.

## 🛠️ Development Setup

1.  **Fork & Clone**:
    ```bash
    git clone https://github.com/Anubhab-1/sentinel-ai.git
    cd sentinel-ai
    ```

2.  **Environment Setup**:
    ```bash
    python -m venv .venv
    # Windows
    .\.venv\Scripts\activate
    # Linux/Mac
    source .venv/bin/activate
    
    pip install -r requirements.txt
    ```

3.  **Install Pre-commit Hooks** (Recommended):
    ```bash
    pre-commit install
    ```

## 🧪 Running Tests

We use `pytest` for testing. Ensure all tests pass before submitting a PR.

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app
```

## 🎨 Coding Standards

We enforce high code quality standards:
- **Formatting**: `black`
- **Linting**: `ruff`
- **Type Checking**: `mypy`

Run the quality suite manually:
```bash
ruff check .
black --check .
mypy .
```

## 📝 Pull Request Process

1.  Create a new branch (`feat/new-feature` or `fix/bug-fix`).
2.  Commit your changes with clear messages.
3.  Ensure CI checks pass.
4.  Open a Pull Request describing your changes.

---
© 2025 RakshaNetra™
