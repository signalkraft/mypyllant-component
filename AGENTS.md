* Use uv for dependency management and executing commands
* Ensure prek is installed for pre-commit hooks and running tests: `uv run prek install`
* After changing files, run `uv run prek --skip pytest --files ...` for linting and code formatting (drop in for pre-commit)