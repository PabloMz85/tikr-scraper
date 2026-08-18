"""Gestor independiente del access token de TIKR.

Proceso aparte que se inicia junto con el contenedor:
- Al arrancar verifica la existencia y validez del token en token.tmp.
  Si no existe o no es valido, genera uno nuevo y lo guarda.
- Si el token existe, lo renueva cada 24 horas.

Tambien expone funciones reutilizables: server.py usa ensure_valid_token()
para devolver un token valido sin regenerarlo innecesariamente.
"""
import os
import sys
import time

from tikr.utils import scraper_utils

TOKEN_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'token.tmp')
REFRESH_INTERVAL_SECONDS = 24 * 60 * 60
RETRY_INTERVAL_SECONDS = 10 * 60
RETRY_ATTEMPTS = 5

# Compania de prueba (Apple) para validar el token contra la API
VALIDATION_TID = 2590360
VALIDATION_CID = 24937


def get_headers() -> dict:
    return {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Content-Type': 'application/json',
        'Origin': 'https://app.tikr.com',
        'Referer': 'https://app.tikr.com/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'cross-site',
    }


def read_token() -> str:
    """Lee el token de token.tmp. Retorna '' si el archivo no existe."""
    if os.path.isfile(TOKEN_FILE):
        with open(TOKEN_FILE, 'r') as f:
            return f.read().strip()
    return ''


def write_token(token: str) -> None:
    """Escribe el token de forma atomica para evitar lecturas parciales."""
    tmp_file = TOKEN_FILE + '.tmp'
    with open(tmp_file, 'w') as f:
        f.write(token)
    os.replace(tmp_file, TOKEN_FILE)


def is_token_valid(token: str) -> bool:
    """Verifica el token contra la API de TIKR usando una compania de prueba."""
    if not token:
        return False
    try:
        response = scraper_utils.get_last_quote_data(token, get_headers(), VALIDATION_TID, VALIDATION_CID, 0)
        return 'dates' in response and 'financials' in response
    except Exception as e:
        print(f'[ - ] Error validando token: {e}', file=sys.stderr)
        return False


def generate_token() -> str:
    """Genera un nuevo token, lo guarda en token.tmp y lo retorna."""
    token = scraper_utils.get_access_token()
    if not token:
        raise RuntimeError('No se pudo obtener un access token de TIKR')
    write_token(token)
    return token


def ensure_valid_token() -> str:
    """Retorna el token existente si es valido; si no, genera uno nuevo."""
    token = read_token()
    if is_token_valid(token):
        print('[ + ] Token existente y valido')
        return token
    print('[ + ] Generando nuevo access token...')
    return generate_token()


def main():
    ensure_valid_token()
    while True:
        time.sleep(REFRESH_INTERVAL_SECONDS)
        print('[ + ] Renovando access token (24h)')
        for attempt in range(RETRY_ATTEMPTS):
            try:
                generate_token()
                print('[ + ] Token renovado correctamente')
                break
            except Exception as e:
                print(f'[ - ] Error renovando token (intento {attempt + 1}): {e}', file=sys.stderr)
                time.sleep(RETRY_INTERVAL_SECONDS)


if __name__ == '__main__':
    main()