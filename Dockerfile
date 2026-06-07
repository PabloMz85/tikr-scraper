# Imagen base liviana de Python
FROM python:3.14.5-slim

# Directorio de trabajo dentro del contenedor
WORKDIR /app

# Instalar dependencias del sistema necesarias para Chrome/Chromium y Selenium
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    curl \
    gnupg \
    chromium \
    chromium-driver \
    libnss3 \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    libx11-6 \
    libxrandr2 \
    libgbm1 \
    libxss1 \
    libxcursor1 \
    libxcomposite1 \
    libasound2 \
    libatk1.0-0 \
    libxdamage1 \
    fonts-liberation \
    ca-certificates \
    gcc \
    libmariadb-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiamos solo los archivos necesarios para instalar dependencias
COPY requirements.txt .

# Copiamos solo lo necesario del proyecto
COPY tikr/ tikr/
COPY plantillas/ plantillas/
COPY server.py .
COPY keys.py .

# Instalamos las dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Exponemos el puerto 5555
EXPOSE 5050

# Comando para iniciar el servidor Flask
CMD ["python", "-u", "-m", "server"]
