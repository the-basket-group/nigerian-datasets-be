# GitHub Environment Setup for Deployment

To use the automated deployment with environment variables, you need to set up a GitHub environment called "production".

## Setup Steps

1. Go to your GitHub repository
2. Navigate to **Settings** → **Environments**
3. Click **New environment**
4. Name it `production`
5. Add the following variables and secrets:

### Variables (non-sensitive, visible)
- `DEBUG` → `false`
- `USE_POSTGRES` → `true` or `false`
- `CORS_ALLOWED_ORIGINS` → your frontend URLs (comma-separated)
- `GOOGLE_REDIRECT_URI` → your Google OAuth redirect URI
- `GOOGLE_AUTH_SCOPE` → `email,profile`

### Secrets (sensitive, encrypted)
- `SECRET_KEY` → your Django secret key
- `DB_NAME` → your database name
- `DB_USER` → your database username
- `DB_PASSWORD` → your database password
- `DB_HOST` → your database host
- `DB_PORT` → your database port
- `GOOGLE_CLIENT_ID` → your Google OAuth client ID
- `GOOGLE_CLIENT_SECRET` → your Google OAuth client secret
- `GCP_SERVICE_ACCOUNT_KEY` → your GCP service account JSON key

## Adding New Environment Variables

When you add new environment variables to your project:

1. Add them to the `env:` section in `.github/workflows/deploy.yml`
2. Add the variable name to the `for var in ...` loop
3. Add the corresponding secret/variable in the GitHub environment

The deployment will automatically pick up any new variables you define.
