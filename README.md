# Sayings Image Generator

A FastAPI web application for CRUD management of sayings and generated images from prompt templates.

## Features
- CRUD sayings with `saying`, `prompt`, and `image_path`
- Prompt interpolation with `%1`
- Context-aware prompt construction from `context.md`
- Pluggable image generation service
- Import/export JSON format:

```json
{
  "sayings": [
    { "saying": "...", "prompt": "... %1" }
  ]
}
```

## Local Run
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8080
```

Then open http://localhost:8080

## AI Image Generation Config
Set these environment variables before using `Generate`:

- `OPENAI_API_KEY` (required)
- `OPENAI_BASE_URL` (optional, default `https://api.openai.com/v1`)
- `OPENAI_IMAGE_MODEL` (optional, default `gpt-image-1`)
- `OPENAI_IMAGE_SIZE` (optional, default `1024x1024`)
- `OPENAI_TIMEOUT_SECONDS` (optional, default `120`)

PowerShell example:

```powershell
$env:OPENAI_API_KEY = "your-key"
$env:OPENAI_IMAGE_MODEL = "gpt-image-1"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

## GitHub Actions (Azure Deploy)
The workflow file is:
- `.github/workflows/deploy-azure-webapp.yml`

It deploys to:
- `sayingsweb749787` (Azure App Service)

Setup required in GitHub repository settings:
1. Add secret `AZURE_CREDENTIALS`
2. Set it to Service Principal JSON from Azure CLI.

Create the Service Principal JSON (scoped to this resource group):

```bash
az ad sp create-for-rbac \
  --name "github-sayings-deploy" \
  --role contributor \
  --scopes /subscriptions/b48f9cca-dd2b-472d-8955-a7e6b8e180d2/resourceGroups/rg-sayings-app \
  --sdk-auth
```

Triggering deploy:
- Push to `main`, or
- Run workflow manually via `workflow_dispatch`.

Important:
- The workflow only deploys code.
- Configure Azure App Settings/startup command separately (one-time), to avoid deployment interruption from SCM restarts.

Example one-time Azure setup:

```bash
az webapp config set \
  --resource-group rg-sayings-app \
  --name sayingsweb749787 \
  --startup-file "python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"

az webapp config appsettings set \
  --resource-group rg-sayings-app \
  --name sayingsweb749787 \
  --settings \
    SCM_DO_BUILD_DURING_DEPLOYMENT=true \
    ENABLE_ORYX_BUILD=true \
    WEBSITE_RUN_FROM_PACKAGE=0 \
    OPENAI_API_KEY="<your-key>" \
    OPENAI_BASE_URL="https://api.openai.com/v1" \
    OPENAI_IMAGE_MODEL="gpt-image-1" \
    OPENAI_IMAGE_SIZE="1024x1024" \
    OPENAI_TIMEOUT_SECONDS="120"
```
