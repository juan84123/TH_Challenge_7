# imagen base de Python
FROM python:3.11-slim

# carpeta de trabajo dentro del contenedor
WORKDIR /app

# copia el archivo de dependencias
COPY requirements.txt .

# instala las dependencias
RUN pip install -r requirements.txt

# copia todo el código
COPY . .

# comando para arrancar el servidor
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]