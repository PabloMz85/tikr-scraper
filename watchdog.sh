#!/bin/bash

cd /home/pablomz/tikr-scraper || {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - ❌ No se pudo hacer cd al directorio del proyecto" >> /home/pablomz/tikr-scraper/watchdog.log
    exit 1
}

# Rutas absolutas
SERVER_SCRIPT="/home/pablomz/tikr-scraper/server.py"
LOG_FILE="/home/pablomz/tikr-scraper/tikr-scraper-server.log"
PYTHON_BIN="/home/pablomz/tikr-scraper/.venv/bin/python"

# Comando de arranque
START_CMD="nohup $PYTHON_BIN $SERVER_SCRIPT >> $LOG_FILE 2>&1 &"

PROCESS_NAME=".venv/bin/python.*server.py"

echo "$(date '+%Y-%m-%d %H:%M:%S') - ✅ Watchdog iniciado" >> /home/pablomz/tikr-scraper/watchdog.log

while true; do
    # Comprobar si el proceso está corriendo
    if ! pgrep -f "$PROCESS_NAME" > /dev/null; then
        echo "$(date '+%Y-%m-%d %H:%M:%S') - ⚠️ Servidor no encontrado, iniciando..." >> $LOG_FILE
        eval $START_CMD
    fi
    sleep 120  # Espera 2 minutos
done
