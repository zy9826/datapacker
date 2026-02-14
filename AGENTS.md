# DataPacker Agent Rules

## Python Runtime Policy
- Always use `.env\Scripts\python.exe` for coding tasks, tests, builds, and version checks.
- Do not use bare `python` commands.
- Expected interpreter version: Python 3.13.x.

## Required Command Style
- Version check: `.env\Scripts\python.exe --version`
- Run tests: `.env\Scripts\python.exe -m pytest`
- Build package: `.env\Scripts\python.exe build.py`
- Module execution: `.env\Scripts\python.exe -m <module>`

## Safety Check
- Before running any Python command, verify `.env\Scripts\python.exe` exists.
- If the virtual environment is missing, stop and ask to recreate `.env` first.

## XML Boolean Semantics
- Treat XML boolean-like attributes as raw strings.
- Missing attribute or empty string (`""`) means `False`.
- Any non-empty string means `True` (including `"0"` and `"false"`).
- This behavior is intentional design; do not report it as a bug in reviews.

## Runtime Lifecycle Assumption
- The program is designed to run once per process.
- `DataPacker.load()` / `DataPackage.load()` are expected to be called once in that process.
- Do not add default per-load cleanup/reset for `DataPackage.package_list` and `DataPackage.global_vars`.
