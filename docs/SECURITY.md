# Security Policy

## Reporting Security Vulnerabilities

We take security seriously. If you discover a security vulnerability, please follow these steps:

### Do NOT:

- Open a public GitHub issue
- Discuss the vulnerability publicly
- Share details on social media

### DO:

1. **Email us directly** at: [victoriaolusheye@gmail.com](mailto:victoriaolusheye@gmail.com)
2. **Include details**:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

## Response Timeline

- **24 hours**: Initial response confirming receipt
- **72 hours**: Initial assessment and severity classification
- **7 days**: Detailed response with fix timeline

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Security Best Practices

### For Contributors:

- Never commit API keys, passwords, or secrets
- Use environment variables for sensitive data
- Follow Django security best practices
- Keep dependencies updated
- Run security checks before committing

### Code Review Requirements:

- All PRs require security review
- Automated security scanning via GitHub Actions
- No hardcoded credentials allowed
- Input validation required for all endpoints

## Security Features

- CSRF protection enabled
- SQL injection protection via Django ORM
- XSS protection with proper template escaping
- Rate limiting (when implemented)
- Authentication required for sensitive endpoints
