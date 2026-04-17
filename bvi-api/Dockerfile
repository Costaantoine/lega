FROM python:3.11-slim
WORKDIR /app
RUN pip install fastapi uvicorn websockets httpx beautifulsoup4 asyncpg python-multipart aiofiles PyJWT==2.8.0 edge-tts
COPY *.py .
RUN mkdir -p /app/uploads
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
