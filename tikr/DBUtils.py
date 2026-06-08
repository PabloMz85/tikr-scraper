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


def _values_equal(db_val, new_val) -> bool:
    """
    Compara dos valores de forma segura, normalizando:
    - None y '' se consideran iguales (vacio)
    - floats se comparan con tolerancia de 0.01 (por redondeo de punto flotante)
    - ints y strings se comparan directamente
    """
    # Normalizar vacios
    db_empty = db_val is None or db_val == ''
    new_empty = new_val is None or new_val == ''
    if db_empty and new_empty:
        return True
    if db_empty != new_empty:
        return False

    # Ambos no vacios: comparar
    try:
        db_float = float(db_val)
        new_float = float(new_val)
        return abs(db_float - new_float) < 0.005
    except (TypeError, ValueError):
        return db_val == new_val


def record_exists_and_unchanged(table: str, record: dict) -> bool:
    """
    Verifica si un registro (company + year) ya existe en la tabla
    con exactamente los mismos valores. Retorna True si no hace falta
    actualizar (datos identicos).
    """
    company = record.get("company")
    year = record.get("year")

    if not company or not year:
        return False

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Obtener las columnas de la tabla (excluyendo updated_at)
        cursor.execute("""
            SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = ?
            AND COLUMN_NAME NOT IN ('updated_at')
            ORDER BY ORDINAL_POSITION
        """, (table,))
        columns = [row['COLUMN_NAME'] for row in cursor.fetchall()]

        if not columns:
            return False

        # Buscar el registro existente
        cursor.execute(
            f"SELECT * FROM {table} WHERE company = ? AND year = ?",
            (company, year)
        )
        existing = cursor.fetchone()

        if existing is None:
            # No existe -> hay que insertarlo
            return False

        # Comparar cada campo (ignorando company/year que son la PK y updated_at)
        compare_cols = [c for c in columns if c not in ('company', 'year')]
        for col in compare_cols:
            db_val = existing.get(col)
            new_val = record.get(col)

            if not _values_equal(db_val, new_val):
                # Hay al menos un cambio -> hay que actualizar
                return False

        # Todos los campos son identicos
        return True

    except mariadb.Error as e:
        print(f"Error comparando registro en {table}: {e}", file=sys.stderr)
        # En caso de error, mejor actualizar por las dudas
        return False
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