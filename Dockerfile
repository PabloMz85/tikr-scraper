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
    libgbm1 \
    libmariadb-dev \
    fonts-liberation \
    ca-certificates \
    gcc \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# El paquete chromium-driver instala chromedriver en /usr/bin/chromedriver,
# pero el código también lo busca en /usr/local/bin/chromedriver
RUN ln -sf /usr/bin/chromedriver /usr/local/bin/chromedriver

ENV MARIADB_CONFIG=/usr/bin/mariadb_config
#RUN apt-get update && apt-get install -y \
#    wget \
#    unzip \
#    curl \
#    gnupg \
#    chromium \
#    chromium-driver \
#    libnss3 \
#    libatk-bridge2.0-0 \
#    libgtk-3-0 \
#    libx11-6 \
#    libxrandr2 \
#    libgbm1 \
#    libxss1 \
#    libxcursor1 \
#    libxcomposite1 \
#    libasound2 \
#    libatk1.0-0 \
#    libxdamage1 \
#    fonts-liberation \
#    ca-certificates \
#    gcc \
#    libmariadb-dev \
#    && rm -rf /var/lib/apt/lists/*

# Copiamos solo los archivos necesarios para instalar dependencias
COPY requirements.txt .

# Copiamos solo lo necesario del proyecto
COPY tikr/ tikr/
COPY plantillas/ plantillas/
COPY server.py .
COPY token_manager.py .
COPY keys.py .

# Alembic + migrations (los modelos viven en database/)
COPY alembic.ini .
COPY alembic/ alembic/
COPY database/ database/

# Instalamos las dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Exponemos el puerto 5555
EXPOSE 5050

# Comando para iniciar el gestor de token en background y el servidor Flask en primer plano
CMD ["sh", "-c", "python -u token_manager.py & exec python -u -m server"]
