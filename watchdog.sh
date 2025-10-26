#!/bin/bash

SERVER_SCRIPT="server.py"
LOG_FILE="tikr-scraper-server.log"

# Comando para ejecutar el servidor
START_CMD="nohup $(pwd)/.venv/bin/python $SERVER_SCRIPT > $LOG_FILE 2>&1 &"

# Nombre identificador para buscar el proceso
PROCESS_NAME="server.py"

while true; do
    # Comprobar si el proceso está corriendo
    if ! pgrep -f "$PROCESS_NAME" > /dev/null; then
        echo "$(date '+%Y-%m-%d %H:%M:%S') - Servidor no encontrado, iniciando..." >> $LOG_FILE
        eval $START_CMD
    fi
    sleep 120  # Espera 2 minutos
done