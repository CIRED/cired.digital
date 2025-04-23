## 🧑‍💻 CIRED Chatbot — Python Code Style Guide

### 👣 Philosophy
Write clear, maintainable Python code that reads like prose. Prioritize readability, simplicity, and correctness. This project follows modern best practices, automated by [Ruff](https://docs.astral.sh/ruff/).

---

### 🧱 Structure & Style

| Aspect            | Rule                                                                 |
|-------------------|----------------------------------------------------------------------|
| **Python version**| Use features from Python 3.11 only.                                   |
| **Indentation**   | 4 spaces, no tabs.                                                   |
| **Line length**   | Soft limit at 88 characters (auto-enforced).                         |
| **Quotes**        | Prefer double quotes (`"`), unless single quotes make it clearer.   |
| **Imports**       | Absolute imports only. Order: stdlib, third-party, local. Sorted by Ruff. |
| **Whitespace**    | Let Ruff handle formatting and spacing.                              |
| **Complexity**    | Keep functions under complexity 10. Refactor early.                  |

---

### 🧪 Testing

- Write **unit tests** using `pytest`. Place them in a `tests/` directory.
- Name test files `test_*.py`, and test functions `test_*`.
- Use fixtures for repeated setups.
- Use `assert` statements directly.
- Run tests with `pytest .` before committing.

---

### 📚 Docstrings

- All **public functions**, **classes**, and **modules** should have docstrings.
- Use this format:

```python
  def foo(bar: int) -> str:
      """Return a greeting using the input number.

      Args:
          bar: The number to greet with.

      Returns:
          A greeting string.
      """
```
- Multiline docstrings: one-line summary, then a blank line.
- Class docstrings go directly under the definition (Ruff enforces `D211`).

---

### ⚙️ Tooling

| Tool     | Command                      | Purpose                         |
|----------|------------------------------|---------------------------------|
| Ruff     | `ruff check .`               | Lint for errors & style issues  |
| Ruff     | `ruff format .`              | Format code                     |
| Pytest   | `pytest`                     | Run all tests                   |
| Pre-commit (opt.) | `pre-commit run --all-files` | Auto-check before commit   |

---

### ✅ Good Practices

- Commit only clean code: no lint warnings, tests passing.
- Comment *why*, not what — code should explain the *what*.
- Keep functions small and focused.
- Avoid global state unless necessary.
- Use type hints consistently.
- Raise specific exceptions, not generic ones.

---

> Maintainer: Minh Ha-Duong (<minh.ha-duong@cnrs.fr>)
> Last updated: April 2025
