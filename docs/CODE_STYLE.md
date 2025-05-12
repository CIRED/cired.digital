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

### 📝 Type Annotations

Type hint everything that crosses a function boundary. Since we're using Python >=3.11, use native type annotations:

```python
# ✅ DO:
def process_data(items: list[str]) -> dict[str, int]:
    ...

# ❌ DON'T:
from typing import List, Dict
def process_data(items: List[str]) -> Dict[str, int]:
    ...

# ❌ ALSO DON'T:
from __future__ import annotations
```

#### Union Types
Use the pipe (`|`) operator for union types:

```python
# ✅ DO:
def get_value() -> int | float | None:
    ...

# ❌ DON'T:
from typing import Union, Optional
def get_value() -> Union[int, Union[float, None]]:
    ...
```

#### Optional Values
Use `| None` instead of `Optional`:

```python
# ✅ DO:
def find_user(user_id: str) -> User | None:
    ...

# ❌ DON'T:
from typing import Optional
def find_user(user_id: str) -> Optional[User]:
    ...
```

#### Type Aliases and TypedDict
Import special types that are not built-in:

```python
from typing import TypedDict, Callable, TypeVar

T = TypeVar('T')

class UserData(TypedDict):
    name: str
    age: int

def transform(func: Callable[[T], T], value: T) -> T:
    ...
```

---

### 🧪 Testing

- Write **unit tests** using `pytest`. Place them in a `tests/` directory.
- Name test files `test_*.py`, and test functions `test_*`.
- Use fixtures for repeated setups.
- Use `assert` statements directly.
- Run tests with `pytest .` before committing.

- Reflect any folder renames in `tests/` immediately, so other developers always find tests next to the code they test. 
- If you move a module, update its test path in the same commit to avoid CI failures.



---

### 📚 Docstrings

- In English
- All **public functions**, **classes**, and **modules** should have docstrings.
- Multiline docstrings: one-line summary, then a blank line.
- Class docstrings go directly under the definition (Ruff enforces `D211`).
- Main() docstring in imperative mode:  ✅ DO write "Upload PDFs..." ❌ DON'T write 
"Entry point to upload PDFs..."

- Use this format:

```python
def foo(bar: int) -> str:
    """Return a greeting using the input number.

    Args:
    ----
        bar: The number to greet with.

    Returns:
    -------
        A greeting string.
        
    Raises:
    ------
        ValueError: If input is negative
    """
    ...
```

---

### ⚙️ Tooling

Ruff handles both linting and formatting for this project. It’s configured in `cired.digital/code/pyproject.toml`. Use the latest `ruff` pulled with `pipx`, not the old version shipped by Ubuntu.


| Tool        | Command                      | Purpose                         |
|-------------|------------------------------|---------------------------------|
| Ruff        | `ruff check .`               | Lint and fix errors & style  |
| Ruff        | `ruff format .`              | Format code  (in lieu of `black`)                    |
| Pytest      | `pytest`                     | Run all tests                   |
| Mypy        | `mypy --strict .`            | Type checking                   |
| Pre-commit  | `pre-commit run --all-files` | Auto-check before commit        |

---

### ✅ Good Practices

- Commit only clean code: no lint warnings, tests passing.
- Comment *why*, not what — code should explain the *what*.
- Keep functions small and focused.
- Avoid global state unless necessary.
- Use type hints consistently.
- Raise specific exceptions, not generic ones.

Naming follows the conventions defined in [PEP 8 – Style Guide for Python Code](https://peps.python.org/pep-0008/#naming-conventions).  Choose English, meaningful, descriptive names that reflect the purpose of the item. No abbreviations.

- snake_case for functions and variables
- PascalCase for classes
- UPPER_CASE for constants.
- Modules and packages: short_snake_case
- Private/internal names: Prefix with a single underscore (_)

---

### 🔄 Version Control

#### Commit Messages

- Use the format <type>: <description>. 
- The type can be **fix:**, **feat:**, **build:**, **chore:**, **ci:**, **docs:**, **style:**, **refactor:**, **perf:**, **test:**...
- Use clear, descriptive commits messages -- refer to [Conventional commits](https://www.conventionalcommits.org/en/v1.0.0/).
- Start the description with a verb in the present tense (e.g., "Add user authentication", "Fix login bug")
- Keep the first line under 50 characters if possible
- For complex changes, add details after a blank line

#### Branch Naming

- Always work on a branch -- never commit to main.
- Use descriptive branch names with hyphens (e.g., `feature/chatbot-api`, `chore/fix-memory-leak`)
- Include issue numbers when applicable (e.g., `issue-42-login-timeout`)

#### Pull Requests

- PR are mandatory. Never push to `main` - it is protected anyway.
- Include a clear description of changes
- Reference related issues using keywords (e.g., "Fixes #123")
- Ensure all CI checks pass before merging. GitHub will run `ruff check .` automatically.
- Request review from appropriate team members

---

### Placeholder
#### async
#### CI/CD
---

> Maintainer: Minh Ha-Duong (<minh.ha-duong@cnrs.fr>)  
> Last updated: April 2025
