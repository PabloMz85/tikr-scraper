"""DB Utils - Adaptado para MariaDB 12"""
import os
import datetime
import mariadb
import sys
from typing import List
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

def create_database() -> None:
    """
    La creación de las tablas y bases de datos está delegada idealmente 
    a un script DDL (.sql) inicial. Sin embargo, si se requiere asegurar 
    la existencia de la estructura desde el código, se ejecuta aquí.
    Se omite el DDL repetitivo en esta función para mantener el código limpio, 
    ya que se asume la ejecución previa del script SQL proporcionado.
    """
    pass

def insert_or_update_data(table: str, data: List[dict]) -> None:
    """
    Inserta o actualiza registros en la tabla especificada.
    Utiliza la directiva 'ON DUPLICATE KEY UPDATE' propia de MariaDB.
    """
    if not data:
        return

    conn = get_connection()
    cursor = conn.cursor()

    for record in data:
        company = record.get("company")
        year = record.get("year")

        if not company or not year:
            print(f"Registro descartado. Faltan claves primarias (company o year): {record}")
            continue

        # Generar dinámicamente los nombres de columnas y placeholders
        columns = ', '.join(record.keys())
        placeholders = ', '.join(['?'] * len(record))

        # Construir la cláusula de actualización para MariaDB: columna = VALUES(columna)
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
        except mariadb.Error as e:
            print(f"Error ejecutando UPSERT en {table}: {e}", file=sys.stderr)

    conn.commit()
    cursor.close()
    conn.close()

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