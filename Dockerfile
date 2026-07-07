FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src

WORKDIR /app
COPY . /app

EXPOSE 8080

CMD ["python", "-m", "care_compass.web", "--host", "0.0.0.0"]
