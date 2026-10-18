# Runs Billsight in one container (used by Hugging Face Spaces; works on any Docker host).
FROM python:3.12-slim

RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PORT=7860
WORKDIR /home/user/app

COPY --chown=user backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir --user -r backend/requirements.txt

COPY --chown=user . .

EXPOSE 7860
CMD ["sh", "-c", "cd backend && uvicorn app.api:app --host 0.0.0.0 --port ${PORT}"]
