FROM python:3.12-slim

LABEL maintainer="PRSensei"

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY prompts/ ./prompts/

ENTRYPOINT ["python", "/app/src/main.py"]
