# Contributing to Ethiopia Capital Market Platform

## Development Setup

1. Fork the repository
2. Clone your fork locally
3. Install dependencies: `pip install -e .`
4. Set up PostgreSQL database
5. Configure environment variables
6. Run data loading script: `python Data/load_data.py`

## Code Style

- Follow PEP 8 for Python code
- Use meaningful variable and function names
- Add docstrings for all functions and classes
- Include type hints where appropriate
- Keep functions focused and single-purpose

## Database Changes

- Never modify data directly in production
- Use proper migrations for schema changes
- Test all database changes locally
- Maintain referential integrity
- Document all schema modifications

## API Guidelines

- Follow RESTful conventions
- Include proper error handling
- Add rate limiting for new endpoints
- Use consistent response formats
- Document all API changes

## Frontend Development

- Maintain responsive design
- Follow Bootstrap conventions
- Use semantic HTML
- Optimize for accessibility
- Test across different browsers

## Testing

- Test all new features thoroughly
- Verify database integrity
- Check API endpoints with curl
- Validate download functionality
- Test responsive design

## Pull Request Process

1. Create a feature branch
2. Make your changes
3. Test thoroughly
4. Update documentation
5. Submit pull request with clear description
6. Address review feedback promptly

## Color Palette

Always use the official color scheme:
- Midnight Green: #075056 (primary)
- Ivory Cream: #FDF6E3 (background)
- Gunmetal: #233038 (text)
- Orange Pantone: #FF5B04 (highlights)
- Sand Yellow: #F4D47C (accents)
- Light Silver: #D3DBDD (secondary)

## Reporting Issues

- Use clear, descriptive titles
- Include steps to reproduce
- Provide error messages
- Specify browser/environment
- Include relevant screenshots