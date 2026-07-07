# Deployment Notes

The app runs without third-party Python dependencies. It reads the platform `PORT` environment variable and defaults to port 8080 locally. The default production workflow uses Gemini Review Agent, so the public demo should set `GEMINI_API_KEY`.

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

Configure `GEMINI_API_KEY` through Cloud Run environment variables or Secret Manager. The app also accepts `GOOGLE_API_KEY` if your platform already uses that name. Set `GEMINI_MODEL=gemini-3.5-flash` unless you intentionally choose another supported Gemini model. Do not commit API keys or passwords to the repository.

## Render

The repository includes `render.yaml` for a Docker-based Render web service.

Recommended UI path:

1. Go to Render and create a new Blueprint or Web Service.
2. Connect the GitHub repository.
3. Select the Docker environment.
4. Add environment variables:
   - `GEMINI_API_KEY`: your Google AI Studio API key.
   - `GEMINI_MODEL`: `gemini-3.5-flash`.
5. Deploy the service.
6. Use the generated `https://...onrender.com` URL as the Kaggle live demo link.

The free plan may sleep after inactivity, so the first request can take a short time to wake up.

## Railway

Railway can also deploy this repository from GitHub using the Dockerfile. Create a new project from the GitHub repository, deploy it, and use the generated public domain as the Kaggle live demo link.

## Production Data

The included catalog uses public support resources. Before real deployment:

- Add an owner and review date for every catalog entry.
- Add human approval before publishing catalog updates.
- Add observability for safety flags and tool failures without logging raw PII.
