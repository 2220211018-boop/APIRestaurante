FROM python:3.11-slim

WORKDIR /app

COPY servicio_inventario/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY servicio_inventario/ .
COPY shared/ ./shared/

CMD ["uvicorn", "principal:app", "--host", "0.0.0.0", "--port", "8000"]
