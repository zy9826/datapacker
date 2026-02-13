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
