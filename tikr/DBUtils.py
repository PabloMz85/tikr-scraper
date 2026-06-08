"""DB Utils - Adaptado para MariaDB 12"""
import os
import datetime
import mariadb
import sys
from typing import List, Optional
import logging

# Extraemos el valor del entorno como string
raw_port = os.environ.get("MYSQL_PORT", "3306")

# Limpieza defensiva (Elimina espacios ocultos o comillas que Docker pueda arrastrar)
clean_port = str(raw_port).strip().replace("'", "").replace('"', "")

# Parámetros de conexión al contenedor MariaDB
# Se recomienda extraer estos valores hacia variables de entorno (os.getenv) en entornos de producción.
DB_CONFIG = {
    "user": os.environ.get("MYSQL_USER"),
    "password": os.environ.get("MYSQL_PASSWORD"),
    "host": os.environ.get("MYSQL_HOST"),
    # Convertimos a entero de forma segura. Si el string está vacío por error, cae a 3306
    "port": int(clean_port) if clean_port.isdigit() else 3306,
    "database": os.environ.get("MYSQL_DATABASE"),
    "autocommit": False
}


def get_connection() -> mariadb.Connection:
    """
    Establece y retorna una conexión a la base de datos MariaDB.
    """
    try:
        conn = mariadb.connect(**DB_CONFIG)
        return conn
    except mariadb.Error as e:
        # Registramos el error en los logs del contenedor para poder auditarlo
        logging.error(f"Error crítico de conexión a MariaDB: {e}")
        # Lanzamos una excepción controlada para que Flask la maneje
        raise ConnectionError(f"No se pudo conectar a la base de datos: {e}") from e


def record_exists_and_unchanged(table: str, record: dict) -> bool:
    """
    Verifica si el registro ya existe en la tabla con los mismos valores.
    Retorna True si existe y todos los campos coinciden, False en caso contrario.
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            f"SELECT * FROM {table} WHERE company = ? AND year = ?",
            (record.get("company"), record.get("year"))
        )
        existing = cursor.fetchone()
        if not existing:
            return False
        existing.pop("updated_at", None)
        for key, value in record.items():
            if key not in existing:
                return False
            ev = existing[key]
            if ev is None and value == '':
                continue
            if ev is None and value != '':
                return False
            if ev is not None and value == '':
                return False
            if ev != value:
                return False
        return True
    except mariadb.Error as e:
        print(f"Error verificando existencia de registro en {table}: {e}", file=sys.stderr)
        return False
    finally:
        cursor.close()
        conn.close()


def get_financials_from_db(company: str) -> dict:
    """
    Consulta todas las tablas financieras en busca de datos existentes para una compañía.
    Retorna un dict con la estructura:
    {
        'income_statement': [{'company': ..., 'year': ..., ...}, ...],
        'cashflow_statement': [...],
        'balancesheet_statement': [...],
        'multiples_statement': [...]
    }
    Las tablas sin datos retornan listas vacias.
    """
    tables = ['income_statement', 'cashflow_statement', 'balancesheet_statement', 'multiples_statement']
    result = {table: [] for table in tables}

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        for table in tables:
            cursor.execute(
                f"SELECT * FROM {table} WHERE company = ? ORDER BY year",
                (company,)
            )
            rows = cursor.fetchall()
            if rows:
                for row in rows:
                    row.pop("updated_at", None)
                result[table] = rows
        return result
    except mariadb.Error as e:
        print(f"Error consultando datos financieros desde DB: {e}", file=sys.stderr)
        return result
    finally:
        cursor.close()
        conn.close()


def get_last_update_time(company: str, table: str = 'income_statement') -> Optional[datetime.datetime]:
    """
    Retorna el timestamp del ultimo update de una compañia en la tabla especificada.
    Si no hay registros, retorna None.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            f"SELECT MAX(updated_at) FROM {table} WHERE company = ?",
            (company,)
        )
        row = cursor.fetchone()
        return row[0] if row and row[0] else None
    except mariadb.Error as e:
        print(f"Error consultando ultimo update en {table}: {e}", file=sys.stderr)
        return None
    finally:
        cursor.close()
        conn.close()


def insert_or_update_data(table: str, data: List[dict]) -> dict:
    """
    Inserta o actualiza registros en la tabla especificada.
    Utiliza la directiva 'ON DUPLICATE KEY UPDATE' propia de MariaDB.
    Antes de insertar/actualizar, verifica si el registro ya existe
    con los mismos valores para evitar escrituras innecesarias.
    Retorna un dict con estadisticas: {'inserted': N, 'updated': N, 'unchanged': N, 'skipped': N}
    """
    stats = {'inserted': 0, 'updated': 0, 'unchanged': 0, 'skipped': 0}

    if not data:
        return stats

    conn = get_connection()
    cursor = conn.cursor()

    for record in data:
        company = record.get("company")
        year = record.get("year")

        if not company or not year:
            print(f"Registro descartado. Faltan claves primarias (company o year): {record}")
            stats['skipped'] += 1
            continue

        # Verificar si el registro ya existe y no cambio
        if record_exists_and_unchanged(table, record):
            stats['unchanged'] += 1
            continue

        # Generar dinamicamente los nombres de columnas y placeholders
        columns = ', '.join(record.keys())
        placeholders = ', '.join(['?'] * len(record))

        # Construir la clausula de actualizacion para MariaDB: columna = VALUES(columna)
        update_cols = [col for col in record.keys() if col not in ("company", "year")]
        update_clause = ', '.join([f"{col}=VALUES({col})" for col in update_cols])

        sql = f"""
            INSERT INTO {table} ({columns})
            VALUES ({placeholders})
            ON DUPLICATE KEY UPDATE
            {update_clause};
        """
        print('Consulta a ejecutar: ' + sql)
        try:
            cursor.execute(sql, tuple(record.values()))
            # MariaDB: info() retorna "Records: N Duplicates: M Warnings: N" en INSERT...ON DUPLICATE
            info = conn.info() if hasattr(conn, 'info') else ''
            if info and 'Duplicates' in info and int(info.split('Duplicates: ')[1].split()[0]) > 0:
                stats['updated'] += 1
            else:
                stats['inserted'] += 1
        except mariadb.Error as e:
            print(f"Error ejecutando UPSERT en {table}: {e}", file=sys.stderr)

    conn.commit()
    cursor.close()
    conn.close()
    return stats


def list_users() -> list:
    """
    Retorna todos los usuarios existentes en el sistema en formato de lista de diccionarios.
    """
    conn = get_connection()
    # Retornar los resultados como diccionarios automáticamente
    cursor = conn.cursor(dictionary=True) 
    
    try:
        cursor.execute("SELECT * FROM approved_users")
        rows = cursor.fetchall()
        return rows
    except mariadb.Error as e:
        print(f"Error consultando usuarios: {e}", file=sys.stderr)
        return []
    finally:
        cursor.close()
        conn.close()


def is_user_approved(user_number: str) -> bool:
    """
    Verifica si un user_number existe y posee el estado activo (1).
    """
    if not user_number:
        return False
        
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "SELECT 1 FROM approved_users WHERE user_number = ? AND active = 1", 
            (user_number,)
        )
        row = cursor.fetchone()
        return row is not None
    except mariadb.Error as e:
        print(f"Error verificando aprobación: {e}", file=sys.stderr)
        return False
    finally:
        cursor.close()
        conn.close()


def add_approved_user(user_number: str) -> None:
    """
    Registra un nuevo usuario. Utiliza 'INSERT IGNORE' para garantizar la idempotencia,
    evitando excepciones si la clave primaria ya existe.
    """
    if not user_number:
        return
        
    conn = get_connection()
    cursor = conn.cursor()
    created_at = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    try:
        cursor.execute(
            "INSERT IGNORE INTO approved_users (user_number, active, created_at) VALUES (?, 1, ?)", 
            (user_number, created_at)
        )
        conn.commit()
    except mariadb.Error as e:
        print(f"Error registrando usuario: {e}", file=sys.stderr)
    finally:
        cursor.close()
        conn.close()

def block_user(user_number: str) -> None:
    """
    Bloquea el acceso a un usuario modificando su estado y registrando el instante del bloqueo.
    Corrección aplicada: Sustitución de 'AND' por coma en la cláusula SET.
    """
    if not user_number:
        return
        
    conn = get_connection()
    cursor = conn.cursor()
    blocked_at = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    try:
        cursor.execute(
            "UPDATE approved_users SET active = 0, blocked_at = ? WHERE user_number = ?", 
            (blocked_at, user_number)
        )
        conn.commit()
    except mariadb.Error as e:
        print(f"Error bloqueando usuario: {e}", file=sys.stderr)
    finally:
        cursor.close()
        conn.close()


def unblock_user(user_number: str) -> None:
    """
    Restituye el acceso a un usuario y registra el instante de la liberación.
    Corrección aplicada: Alineación de la columna (released_at en lugar de unblocked_at)
    y reparación de sintaxis SQL en el SET.
    """
    if not user_number:
        return
        
    conn = get_connection()
    cursor = conn.cursor()
    released_at = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    try:
        cursor.execute(
            "UPDATE approved_users SET active = 1, released_at = ? WHERE user_number = ?", 
            (released_at, user_number)
        )
        conn.commit()
    except mariadb.Error as e:
        print(f"Error desbloqueando usuario: {e}", file=sys.stderr)
    finally:
        cursor.close()
        conn.close()


def log_user_activity(user_number: str, ip_address: str, token: str) -> None:
    """
    Registra en la bitácora la actividad del usuario validado en el sistema.
    """
    if not user_number or not ip_address:
        return
        
    conn = get_connection()
    cursor = conn.cursor()
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    try:
        cursor.execute(
            "INSERT INTO users_log (user_number, ip_address, token, logged_at) VALUES (?, ?, ?, ?)", 
            (user_number, ip_address, token, timestamp)
        )
        conn.commit()
    except mariadb.Error as e:
        print(f"Error registrando actividad de usuario: {e}", file=sys.stderr)
    finally:
        cursor.close()
        conn.close()