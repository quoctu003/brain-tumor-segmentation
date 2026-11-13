FROM python:3.12-slim
WORKDIR /project
RUN apt-get update && apt-get install -y --no-install-recommends fonts-dejavu-core && rm -rf /var/lib/apt/lists/*
COPY backend/requirements.txt /project/requirements.txt
RUN pip install --no-cache-dir "torch>=2.6,<3" --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir -r requirements.txt
COPY backend /project/backend
COPY demo /project/demo
WORKDIR /project/backend
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
