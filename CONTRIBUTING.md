# Contributing to AWS Cost Optimizer

Thank you for your interest in contributing to AWS Cost Optimizer! This document provides guidelines for contributing to the project.

## Development Setup

### 1. Fork and Clone
```bash
git clone https://github.com/yourusername/aws-cost-optimizer.git
cd aws-cost-optimizer
```

### 2. Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Development Dependencies
```bash
pip install -r requirements.txt
pip install -e ".[dev]"  # Install in editable mode with dev dependencies
```

### 4. Set Up Pre-commit Hooks (Optional)
```bash
pip install pre-commit
pre-commit install
```

## Development Workflow

### 1. Create a Feature Branch
```bash
git checkout -b feature/your-feature-name
```

### 2. Make Your Changes
- Write clean, documented code
- Follow PEP 8 style guidelines
- Add tests for new functionality
- Update documentation as needed

### 3. Run Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src tests/

# Run specific test file
pytest tests/test_cost_calculator.py
```

### 4. Format Code
```bash
# Format with Black
black src/ tests/

# Check with flake8
flake8 src/ tests/

# Type checking with mypy
mypy src/
```

### 5. Commit Your Changes
```bash
git add .
git commit -m "feat: add support for RDS cost analysis"
```

**Commit Message Format:**
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `test:` Adding tests
- `refactor:` Code refactoring
- `style:` Code style changes
- `chore:` Maintenance tasks

### 6. Push and Create Pull Request
```bash
git push origin feature/your-feature-name
```

Then create a pull request on GitHub.

## Code Style Guidelines

### Python Style
- Follow PEP 8
- Use type hints where appropriate
- Maximum line length: 100 characters
- Use docstrings for all functions and classes

### Example:
```python
def calculate_cost(instance_type: str, region: str) -> float:
    """
    Calculate the monthly cost for an EC2 instance.
    
    Args:
        instance_type (str): EC2 instance type (e.g., 't2.micro')
        region (str): AWS region (e.g., 'us-east-1')
        
    Returns:
        float: Monthly cost in USD
        
    Raises:
        ValueError: If instance_type is not found in pricing data
    """
    # Implementation here
    pass
```

## Testing Guidelines

### Writing Tests
- Place tests in the `tests/` directory
- Name test files as `test_<module_name>.py`
- Use descriptive test names
- Cover edge cases and error conditions

### Test Example:
```python
def test_calculate_ec2_cost_with_invalid_region():
    """Test that invalid region raises appropriate error"""
    calculator = CostCalculator(config)
    with pytest.raises(ValueError):
        calculator.calculate_ec2_cost('t2.micro', 'invalid-region')
```

## Adding New Features

### Adding a New Resource Analyzer

1. Create new file in `src/analyzers/`:
```python
# src/analyzers/rds_analyzer.py
from analyzers.base_analyzer import BaseAnalyzer

class RDSAnalyzer(BaseAnalyzer):
    def analyze(self):
        # Implementation
        pass
```

2. Add tests:
```python
# tests/test_rds_analyzer.py
def test_rds_analyzer():
    # Test implementation
    pass
```

3. Update main.py to include new analyzer
4. Update configuration files
5. Update documentation

### Adding a New Report Format

1. Create reporter in `src/reports/`:
```python
# src/reports/excel_reporter.py
class ExcelReporter:
    def generate(self, results):
        # Implementation
        pass
```

2. Register in main.py
3. Add tests
4. Update documentation

## Documentation

### Updating README
- Keep README.md up to date with new features
- Update usage examples
- Document new configuration options

### Code Documentation
- Use docstrings for all public functions/classes
- Include type hints
- Provide usage examples in docstrings

### Architecture Documentation
- Update `docs/ARCHITECTURE.md` for major changes
- Document design decisions
- Include diagrams where helpful

## Pull Request Process

1. **Before Submitting:**
   - [ ] All tests pass
   - [ ] Code is formatted (black, flake8)
   - [ ] Documentation is updated
   - [ ] CHANGELOG.md is updated
   - [ ] No merge conflicts with main branch

2. **PR Description Should Include:**
   - Clear description of changes
   - Link to related issues
   - Screenshots (if UI changes)
   - Breaking changes (if any)

3. **Review Process:**
   - Maintainers will review your PR
   - Address any feedback
   - Once approved, PR will be merged

## Reporting Issues

### Bug Reports
Include:
- Clear description of the bug
- Steps to reproduce
- Expected vs actual behavior
- Environment details (Python version, OS, AWS region)
- Error messages/logs

### Feature Requests
Include:
- Use case description
- Proposed solution
- Alternative solutions considered
- Impact on existing functionality

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers
- Accept constructive criticism
- Focus on what's best for the project

## Questions?

- Open a GitHub issue
- Check existing issues and PRs
- Review the README and documentation

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to AWS Cost Optimizer! 🚀
