# Contributing to OCR Vendor Bill Ingestion

Thank you for your interest in contributing! This document provides guidelines for contributing to this project.

## Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd OCR
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -e .  # Install in editable mode
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your ERPNext credentials
   ```

## Code Style

- Follow PEP 8 style guidelines
- Use type hints for function parameters and return values
- Write docstrings for all functions and classes
- Maximum line length: 100 characters

### Formatting

We recommend using these tools:

```bash
# Install formatting tools
pip install black isort flake8 mypy

# Format code
black .
isort .

# Check style
flake8 .

# Check types
mypy .
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_utils.py

# Run specific test
pytest tests/test_utils.py::TestNormalizeAmount::test_simple_amount
```

### Writing Tests

- Place tests in the `tests/` directory
- Name test files as `test_<module>.py`
- Name test functions as `test_<description>`
- Use fixtures for common setup
- Mock external dependencies (ERPNext API, OCR engines)

Example:

```python
import pytest
from unittest.mock import Mock, patch

def test_example():
    """Test description."""
    # Arrange
    expected = "result"

    # Act
    result = function_to_test()

    # Assert
    assert result == expected
```

## Adding New Features

### Adding a New OCR Provider

1. Create a new file in `ocr_parsers/` (e.g., `azure_parser.py`)
2. Inherit from `OCRParser` base class
3. Implement required methods:
   - `extract_text(image: Image.Image) -> OCRResult`
   - `is_available() -> bool`
4. Add configuration options to `config.py`
5. Register in `ocr_parsers/__init__.py`
6. Update `ocr_ingest.py` to support the new provider
7. Add tests in `tests/test_ocr_parsers.py`
8. Update documentation

### Adding New Field Extractors

1. Add extraction logic to `FieldExtractor` class
2. Add regex patterns to `config.py` if needed
3. Update `InvoiceData` dataclass if new fields added
4. Add tests for the new extraction logic
5. Update output format documentation

## Commit Messages

Use clear, descriptive commit messages:

```
feat: Add support for Azure Computer Vision API
fix: Correct date parsing for DD/MM/YYYY format
docs: Update README with installation instructions
test: Add tests for vendor fuzzy matching
refactor: Simplify image preprocessing pipeline
```

Prefixes:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Test additions or changes
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `chore`: Build process or auxiliary tool changes

## Pull Request Process

1. **Fork the repository** and create a new branch
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write code following the style guide
   - Add tests for new functionality
   - Update documentation as needed

3. **Test your changes**
   ```bash
   pytest
   black .
   flake8 .
   ```

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: Your descriptive message"
   ```

5. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create a Pull Request**
   - Provide a clear description of the changes
   - Reference any related issues
   - Ensure CI tests pass

## Code Review

- All submissions require review before merging
- Address review comments promptly
- Keep pull requests focused and reasonably sized

## Reporting Issues

When reporting issues, please include:

1. **Description**: Clear description of the issue
2. **Steps to Reproduce**: Detailed steps to reproduce the problem
3. **Expected Behavior**: What you expected to happen
4. **Actual Behavior**: What actually happened
5. **Environment**:
   - Python version
   - Operating system
   - ERPNext version
   - OCR provider being used
6. **Logs**: Relevant log output (set `LOG_LEVEL=DEBUG`)
7. **Sample Invoice**: If possible, a sample invoice that demonstrates the issue (redact sensitive data)

## Feature Requests

We welcome feature requests! Please:

1. Check existing issues to avoid duplicates
2. Clearly describe the feature and use case
3. Explain why this feature would be valuable
4. Provide examples if applicable

## Documentation

- Update README.md for user-facing changes
- Update docstrings for code changes
- Add examples for new features
- Keep CHANGELOG.md updated

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

## Questions?

Feel free to open an issue for any questions about contributing!
