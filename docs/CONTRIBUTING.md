# Contributing Guidelines

Thank you for contributing to the Nigerian Datasets Backend project!

## Getting Started

1. **Pull latest changes** before starting work:
   ```bash
   git pull origin main
   ```

2. **Create a new branch** for your changes:
   ```bash
   git checkout -b {initials}/{feature-description}
   ```

3. **Install dependencies**:
   ```bash
   make install
   make dev-install
   ```

4. **Run tests** to ensure everything works:
   ```bash
   make test
   make lint
   make typecheck
   ```

## Branch Naming Convention

Use the following format: `{initials}/{feature-description}`

**Examples:**
- `jo/add-user-authentication`
- `as/fix-dataset-upload-bug`
- `mk/update-api-documentation`

## Commit Message Format

Follow conventional commit format: `type(scope): description`

**Types:**
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation changes
- `style` - Code style changes (formatting, etc.)
- `refactor` - Code refactoring
- `test` - Adding or updating tests
- `chore` - Maintenance tasks

**Examples:**
- `feat(api): add dataset filtering endpoint`
- `fix(auth): resolve token validation issue`
- `docs(readme): update installation instructions`

## Pull Request Guidelines

1. **PR Title Format**: Use same convention as commits
   - `feat: add user authentication system`
   - `fix: resolve database connection timeout`

2. **Before submitting**:
   - Run `make format` to format code
   - Run `make lint` to check code quality
   - Run `make typecheck` for type validation
   - Run `make test` to ensure all tests pass

3. **PR Description**: Fill out the template completely
   - Describe what was changed and why
   - Include testing steps
   - Link related issues

## Development Workflow

1. Create branch: `git checkout -b {initials}/{feature-description}`
2. Make changes and commit frequently
3. Push branch: `git push origin {branch-name}`
4. Create pull request using the template
5. Address review feedback
6. Squash and merge when approved

## Code Standards

- All code must be typed (mypy enforced)
- Follow PEP 8 style guidelines
- **Use class-based views** for all API endpoints
- **Use explicit imports** instead of relative imports (e.g., `from core.views import HealthCheckView` not `from . import views`)
- Write tests for new functionality
- Keep functions small and focused
- Use descriptive variable names
