# Contributing to Project Tacitus

Thank you for your interest in contributing to Project Tacitus! This document provides guidelines and instructions for contributing to the project.

## Table of Contents
- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Contributions](#making-contributions)
- [Coding Standards](#coding-standards)
- [Pull Request Process](#pull-request-process)
- [Documentation](#documentation)

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment. We expect all contributors to:
- Use welcoming and inclusive language
- Be respectful of differing viewpoints and experiences
- Gracefully accept constructive criticism
- Focus on what is best for the community
- Show empathy towards other community members

## Getting Started

1. Fork the repository
2. Clone your fork locally
3. Set up the development environment as described in the README.md
4. Create a new branch for your feature or bug fix

## Development Setup

Ensure you have the following prerequisites installed:
- Python 3.8 or higher
- PostgreSQL
- Node.js and npm
- Git

Follow the setup instructions in the README.md for:
1. Database setup
2. Environment configuration
3. Backend setup
4. Frontend setup

## Making Contributions

### Types of Contributions
We welcome various types of contributions:
- Bug fixes
- Feature implementations
- Documentation improvements
- Performance optimizations
- Test coverage improvements

### Current Focus Areas
- Tag system enhancements
- Bill analysis improvements
- Data visualization components
- Search functionality optimization
- Documentation updates

## Coding Standards

### Python (Backend)
- Follow PEP 8 style guide
- Use type hints for function parameters and return values
- Write docstrings for functions and classes
- Maintain test coverage for new code
- Use meaningful variable and function names

Example:
```python
def fetch_bill_data(bill_id: str) -> Dict[str, Any]:
    """
    Retrieve detailed information for a specific bill.

    Args:
        bill_id: The unique identifier of the bill

    Returns:
        Dict containing bill information
    """
    # Implementation
```

### JavaScript/React (Frontend)
- Use ESLint and Prettier for code formatting
- Follow React Hooks best practices
- Implement proper error handling
- Write functional components
- Maintain component modularity

Example:
```javascript
const BillDetails = ({ billId }) => {
  const [billData, setBillData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Implementation
};
```

### SQL (Database)
- Use clear, descriptive table and column names
- Follow consistent naming conventions
- Include appropriate indexes
- Write clear comments for complex queries
- Consider query performance

## Pull Request Process

1. Create a new branch for your feature:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes:
   - Write clear, concise commit messages
   - Keep commits focused and atomic
   - Include tests where applicable
   - Update documentation as needed

3. Before submitting:
   - Ensure all tests pass
   - Update relevant documentation
   - Check code formatting
   - Verify the application runs locally

4. Submit a pull request:
   - Provide a clear description of the changes
   - Link to any relevant issues
   - Include screenshots for UI changes
   - List any new dependencies

5. Review process:
   - Address review comments
   - Make requested changes
   - Maintain a constructive dialogue

## Documentation

When contributing documentation:
- Place technical documentation in the appropriate subdirectory under `Docs/`
- Update API documentation for any endpoint changes
- Include code examples where helpful
- Keep documentation clear and concise
- Update the README.md if necessary

### Documentation Structure
```
Docs/
├── 1_Project_Overview/         # Project vision and goals
├── 2_Technical_Documentation/  # Implementation details
├── 3_API_Documentation/        # API endpoints and usage
└── 4_Deployment_Guides/        # Setup and deployment guides
```

## Questions or Need Help?

If you have questions or need help with your contribution:
1. Check existing documentation
2. Review open and closed issues
3. Create a new issue with a clear description
4. Tag appropriate maintainers

Thank you for contributing to Project Tacitus! Your efforts help make legislative information more accessible and understandable to citizens.
