# Agent Guidelines for cc-context

## Build/Test Commands
- Install: `pip install -e .`
- Run tests: `python test_utils.py` (if exists)
- No pytest/unittest framework detected - use manual test functions from test_utils.py

## Code Style
- **Language**: Python 3.8+ (type hints required: `str | None`, not `Optional[str]`)
- **Imports**: stdlib first, then third-party, then local (`from cc_context.module import ...`)
- **Formatting**: 4-space indentation, no trailing whitespace
- **Types**: Always use type hints for function signatures and return types
- **Naming**: snake_case for functions/variables, PascalCase for classes
- **Error handling**: Use try/except with subprocess.CalledProcessError, print errors to stderr
- **Paths**: Use pathlib.Path, not os.path
- **Docstrings**: Google-style docstrings for public functions (see core/git_ops.py:13-16)
- **Abstract classes**: Use ABC with @abstractmethod (see storage/base.py)
- **Git operations**: Always use subprocess.run with capture_output=True, text=True, check=True

## Project Structure
- Entry points defined in setup.py console_scripts (cc-init, cc-capture, etc.)
- CLI commands in cc_context/cli/, core logic in cc_context/core/
- Storage abstraction in cc_context/storage/ with base.py interface
