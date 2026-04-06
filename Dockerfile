FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# system dependences
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# packages install
COPY pyproject.toml .
RUN pip install --upgrade pip && pip install .

COPY . .

# run baseline and lstm train
CMD ["sh", "-c", "python -m src.models.baseline && python -m src.models.train"]