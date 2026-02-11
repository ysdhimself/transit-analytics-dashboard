# Contributing to Edmonton Transit Analytics Dashboard

Thank you for considering contributing to this project! This document provides guidelines and best practices for contributing.

## Code of Conduct

Be respectful, inclusive, and professional in all interactions.

## How to Contribute

### Reporting Bugs

If you find a bug:

1. Check if the bug has already been reported in Issues
2. If not, create a new issue with:
   - Clear, descriptive title
   - Steps to reproduce
   - Expected vs actual behavior
   - Your environment (Python version, OS, etc.)
   - Relevant logs or screenshots

### Suggesting Features

For feature requests:

1. Check if the feature has been suggested already
2. Create a new issue with:
   - Clear description of the feature
   - Use cases and benefits
   - Possible implementation approach (optional)

### Pull Requests

1. **Fork and Clone**
   ```bash
   git clone https://github.com/yourusername/transit-analytics-dashboard.git
   cd transit-analytics-dashboard
   ```

2. **Create a Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make Changes**
   - Follow the existing code style
   - Add tests for new functionality
   - Update documentation as needed
   - Run linting: `flake8 .`
   - Format code: `black .`

4. **Test Your Changes**
   ```bash
   pytest tests/ -v
   ```

5. **Commit**
   ```bash
   git add .
   git commit -m "feat: add new feature description"
   ```
   
   Use conventional commit messages:
   - `feat:` for new features
   - `fix:` for bug fixes
   - `docs:` for documentation
   - `test:` for tests
   - `refactor:` for code refactoring
   - `chore:` for maintenance tasks

6. **Push and Create PR**
   ```bash
   git push origin feature/your-feature-name
   ```
   Then create a pull request on GitHub.

## Development Setup

```bash
# Install dev dependencies
pip install -r requirements.txt
pip install pytest pytest-cov black flake8

# Run tests with coverage
pytest tests/ --cov=src --cov-report=html

# Format code
black .

# Lint code
flake8 .
```

## Code Style

- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Write docstrings for all functions and classes
- Keep functions focused and under 50 lines when possible
- Use meaningful variable names

### Example Function

```python
def calculate_delay(arrival_time: datetime, scheduled_time: datetime) -> float:
    """
    Calculate delay in minutes between actual and scheduled arrival.
    
    Args:
        arrival_time: Actual arrival datetime
        scheduled_time: Scheduled arrival datetime
        
    Returns:
        Delay in minutes (positive for late, negative for early)
    """
    delay_seconds = (arrival_time - scheduled_time).total_seconds()
    return delay_seconds / 60.0
```

## Project Structure Guidelines

- **src/ingestion/**: Data fetching and parsing
- **src/processing/**: Data transformation and feature engineering
- **src/ml/**: Machine learning models
- **src/utils/**: Shared utilities
- **dashboard/**: Streamlit dashboard components
- **tests/**: Unit tests mirroring src/ structure

## Testing Guidelines

- Write tests for all new functions
- Aim for >80% code coverage
- Use pytest fixtures for common test data
- Mock external services (AWS, APIs) in tests

### Example Test

```python
def test_delay_calculation():
    """Test delay calculation with sample data."""
    scheduled = datetime(2024, 1, 1, 10, 0, 0)
    actual = datetime(2024, 1, 1, 10, 2, 30)
    
    delay = calculate_delay(actual, scheduled)
    
    assert delay == 2.5  # 2.5 minutes late
```

## Documentation

- Update README.md for new features
- Add docstrings to all functions/classes
- Update SETUP_GUIDE.md for setup changes
- Add inline comments for complex logic

## Questions?

- Open a Discussion on GitHub
- Email: your.email@example.com

Thank you for contributing! 🚌
