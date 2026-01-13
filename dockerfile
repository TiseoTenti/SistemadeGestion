# Imagen base de Python
FROM python:3.11-slim

# Crear carpeta de la app
WORKDIR /app

# Copiar requirements y luego instalar
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar toda la app
COPY . .

# Exponer puerto
EXPOSE 5000

# Comando para correr la app
CMD ["python", "app.py"]
