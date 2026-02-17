# Contributing to App Crawler

Thank you for considering contributing to App Crawler! This document provides guidelines and instructions for contributing.

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Setup](#development-setup)
4. [Making Changes](#making-changes)
5. [Testing](#testing)
6. [Submitting Changes](#submitting-changes)
7. [Coding Standards](#coding-standards)
8. [Documentation](#documentation)

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers and help them get started
- Focus on constructive feedback
- Maintain a harassment-free environment

## Getting Started

### Finding Issues to Work On

1. Check the [GitHub Issues](https://github.com/codekaa1ciu1/app-crawler/issues)
2. Look for issues tagged with `good first issue` or `help wanted`
3. Comment on the issue to let others know you're working on it

### Reporting Bugs

When reporting bugs, please include:

- Python version
- Operating system
- Appium version
- Device/emulator details
- Steps to reproduce
- Expected vs actual behavior
- Error messages and stack traces
- Screenshots if applicable

### Suggesting Features

When suggesting features:

- Check if it's already requested
- Explain the use case
- Describe the proposed solution
- Consider backwards compatibility

## Development Setup

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then:
git clone https://github.com/YOUR-USERNAME/app-crawler.git
cd app-crawler
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
pip install -e .  # Install in development mode
```

### 4. Set Up Pre-commit Hooks (Optional)

```bash
pip install pre-commit
pre-commit install
```

### 5. Set Up Environment

```bash
cp .env.example .env
# Edit .env with your API keys
```

### 6. Start Appium

```bash
appium
```

## Making Changes

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

Use prefixes:
- `feature/` for new features
- `fix/` for bug fixes
- `docs/` for documentation
- `test/` for test additions
- `refactor/` for refactoring

### 2. Make Your Changes

- Write clean, readable code
- Follow existing code style
- Add comments for complex logic
- Update documentation as needed

### 3. Test Your Changes

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_database.py

# Run with coverage
pytest --cov=app_crawler
```

### 4. Commit Your Changes

```bash
git add .
git commit -m "Brief description of changes"
```

Commit message format:
```
<type>: <subject>

<body>

<footer>
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Test additions/changes
- `refactor`: Code refactoring
- `style`: Code style changes
- `chore`: Build/config changes

Example:
```
feat: Add support for iOS swipe gestures

- Implemented horizontal and vertical swipes
- Added swipe direction parameter
- Updated documentation with examples

Closes #123
```

## Testing

### Running Tests

```bash
# All tests
pytest

# Specific test
pytest tests/test_database.py::test_create_path

# With verbose output
pytest -v

# With coverage report
pytest --cov=app_crawler --cov-report=html
```

### Writing Tests

Place tests in the `tests/` directory:

```python
import pytest
from app_crawler.database import CrawlerDatabase

def test_your_feature():
    """Test description."""
    # Arrange
    db = CrawlerDatabase(":memory:")
    
    # Act
    result = db.some_method()
    
    # Assert
    assert result == expected_value
```

### Test Guidelines

- Write tests for all new features
- Aim for >80% code coverage
- Use descriptive test names
- Include docstrings
- Test edge cases
- Use fixtures for common setup

## Submitting Changes

### 1. Push to Your Fork

```bash
git push origin feature/your-feature-name
```

### 2. Create Pull Request

1. Go to the original repository
2. Click "New Pull Request"
3. Select your fork and branch
4. Fill in the PR template:
   - Description of changes
   - Related issues
   - Testing performed
   - Screenshots (if UI changes)

### 3. Code Review Process

- Maintainers will review your PR
- Address feedback and make changes
- Push updates to the same branch
- Once approved, your PR will be merged

## Coding Standards

### Python Style

Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/):

- Use 4 spaces for indentation
- Maximum line length: 100 characters
- Use meaningful variable names
- Add docstrings to functions and classes

### Docstring Format

```python
def function_name(param1: str, param2: int) -> bool:
    """Brief description.
    
    Longer description if needed.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: Description of when this is raised
    """
    pass
```

### Type Hints

Use type hints for function parameters and returns:

```python
from typing import List, Dict, Optional

def process_data(items: List[str], config: Dict[str, Any]) -> Optional[int]:
    pass
```

### Import Order

1. Standard library imports
2. Third-party imports
3. Local application imports

```python
import os
import sys

from flask import Flask
from appium import webdriver

from app_crawler.database import CrawlerDatabase
```

### Error Handling

```python
try:
    result = risky_operation()
except SpecificException as e:
    logger.error(f"Operation failed: {e}")
    raise  # or handle appropriately
```

## Documentation

### Update Documentation

When making changes, update:

- **README.md**: User-facing features
- **API.md**: API changes
- **ARCHITECTURE.md**: Architectural changes
- **Docstrings**: Code documentation
- **CHANGELOG.md**: Version changes

### Writing Good Documentation

- Use clear, concise language
- Include code examples
- Add diagrams for complex concepts
- Keep it up-to-date

### Documentation Format

- Use Markdown for all docs
- Use code blocks with language specification
- Include table of contents for long docs
- Add links to related sections

## Project Structure

```
app-crawler/
├── app_crawler/          # Main package
│   ├── crawler.py       # Crawler implementation
│   ├── database.py      # Database layer
│   └── ai_service.py    # AI integration
├── web_portal/          # Web interface
│   ├── app.py          # Flask app
│   ├── templates/      # HTML templates
│   └── static/         # CSS, JS
├── tests/              # Test files
├── docs/               # Additional documentation
├── examples/           # Example scripts
└── README.md          # Main documentation
```

## Questions?

- Open an issue with the `question` label
- Join our discussions
- Contact maintainers

## Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Acknowledged in the project

Thank you for contributing to App Crawler! 🎉
