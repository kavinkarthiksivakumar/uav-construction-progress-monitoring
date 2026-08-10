"""
pytest configuration for the test suite.

Modules 1–5 test files are standalone scripts (not pytest-compatible).
Only test_module6.py uses the standard pytest format.

Run standalone tests with:
    python tests/test_module1.py
    python tests/test_module2.py
    ...

Run pytest tests with:
    python -m pytest tests/test_module6.py -v
    python -m pytest tests/ -v
"""

collect_ignore = [
    "test_module1.py",
    "test_module2.py",
    "test_module3.py",
    "test_module4.py",
    "test_module5.py",
]
