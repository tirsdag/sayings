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

## GitHub Actions (Azure Deploy)
The workflow file is:
- `.github/workflows/deploy-azure-webapp.yml`

It deploys to:
- `sayingsweb749787` (Azure App Service)

Setup required in GitHub repository settings:
1. Add secret `AZURE_WEBAPP_PUBLISH_PROFILE`
2. Put the Azure publish profile XML as the secret value.

You can fetch the publish profile from Azure CLI:

```bash
az webapp deployment list-publishing-profiles \
  --name sayingsweb749787 \
  --resource-group rg-sayings-app \
  --xml
```

Triggering deploy:
- Push to `main`, or
- Run workflow manually via `workflow_dispatch`.
