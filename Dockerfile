FROM python:3.12-slim

WORKDIR /app
COPY . .
RUN pip install --no-cache-dir ".[app]"
RUN coding-review

EXPOSE 8000
HEALTHCHECK CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"
CMD ["uvicorn", "app.api:app", "--host=0.0.0.0", "--port=8000"]
