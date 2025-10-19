
FROM python:3.11-slim

WORKDIR /app

# —— Runtime env ————————————————————————————————————————————————
ENV PYTHONDONTWRITEBYTECODE=1         PYTHONUNBUFFERED=1         PIP_DISABLE_PIP_VERSION_CHECK=1

# —— Deps ————————————————————————————————————————————————————————
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# —— App —————————————————————————————————————————————————————————
COPY app ./app
COPY scripts ./scripts

EXPOSE 8000

# —— User setup ————————————————————————————————————————————————
RUN useradd nonroot

RUN chown -R nonroot . 

USER nonroot

# Инициализация БД на старте контейнера (простая семинарская логика)
RUN python scripts/init_db.py
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
