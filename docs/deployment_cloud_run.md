# Deployment Notes

The app runs without third-party dependencies and listens on port 8080 in the Dockerfile.

## Local Container

```bash
docker build -t care-compass-agent .
docker run --rm -p 8080:8080 care-compass-agent
```

Open:

```text
http://127.0.0.1:8080
```

## Google Cloud Run

From the repository root:

```bash
gcloud run deploy care-compass-agent \
  --source . \
  --region us-central1 \
  --allow-unauthenticated
```

If you use the optional ADK/Gemini path, configure secrets through Cloud Run environment variables or Secret Manager. Do not commit API keys or passwords to the repository.

## Production Data

The included catalog uses public support resources. Before real deployment:

- Add an owner and review date for every catalog entry.
- Add human approval before publishing catalog updates.
- Add observability for safety flags and tool failures without logging raw PII.
