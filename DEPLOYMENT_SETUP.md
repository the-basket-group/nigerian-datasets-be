# GitHub Environment Setup for Deployment

To use the automated deployment with environment variables, you need to set up GitHub environments for both production and development.

## Setup Steps

1. Go to your GitHub repository
2. Navigate to **Settings** → **Environments**
3. Create two environments:
   - Click **New environment** → name it `production`
   - Click **New environment** → name it `dev`

## Environment Variables for Both Environments

### Variables (non-sensitive, visible)
- `DEBUG` → `false` (production) / `true` (dev)
- `USE_POSTGRES` → `true` or `false`
- `DB_NAME` → your database name
- `DB_USER` → your database username
- `DB_HOST` → your database host
- `DB_PORT` → your database port
- `CORS_ALLOWED_ORIGINS` → your frontend URLs (comma-separated)
- `GOOGLE_REDIRECT_URI` → your Google OAuth redirect URI
- `GOOGLE_AUTH_SCOPE` → `email,profile`
- `BUCKET_NAME` → your Google Cloud Storage bucket name

### Secrets (sensitive, encrypted)
- `SECRET_KEY` → your Django secret key
- `DB_PASSWORD` → your database password
- `GOOGLE_CLIENT_ID` → your Google OAuth client ID
- `GOOGLE_CLIENT_SECRET` → your Google OAuth client secret
- `GCP_SERVICE_ACCOUNT_KEY` → your GCP service account JSON key

## Environment Differences

**Production Environment:**
- Used by main branch deployments
- `DEBUG=false`
- Production database credentials

**Dev Environment:**
- Used by PR preview deployments
- `DEBUG=true`
- Development/staging database credentials

## Adding New Environment Variables

When you add new environment variables to your project:

1. Add them to the `env:` section in `.github/workflows/deploy.yml`
2. Add the variable name to the `for var in ...` loop
3. Add the corresponding secret/variable in the GitHub environment

The deployment will automatically pick up any new variables you define.
