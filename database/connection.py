"""
Conexión a la base de datos SQLite.

Este módulo maneja la conexión y la creación de tablas.
Cuando migremos a Supabase, este es el archivo principal que se reemplaza.
"""

import sqlite3
from config.settings import DB_PATH


def get_connection():
    """Crea y retorna una conexión a la base de datos SQLite."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Crea las tablas y actualiza esquemas si es necesario."""
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # 1. Tabla de choferes (original)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS choferes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                telefono TEXT,
                activo INTEGER DEFAULT 1,
                created_at TEXT DEFAULT (datetime('now', 'localtime'))
            )
        """)

        # 1.b Actualización de esquema: agregar columna 'movil' de forma segura
        try:
            cursor.execute("ALTER TABLE choferes ADD COLUMN movil TEXT")
        except sqlite3.OperationalError:
            # Si lanza error es porque la columna ya existe, lo cual está bien.
            pass

        # 2. Tabla de operadores
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS operadores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                activo INTEGER DEFAULT 1,
                created_at TEXT DEFAULT (datetime('now', 'localtime'))
            )
        """)

        # 3. Tabla de viajes (con los estados definidos en el manifiesto)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS viajes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                operador_id INTEGER,
                chofer_id INTEGER,
                estado TEXT DEFAULT 'Pendiente', 
                origen TEXT NOT NULL,
                destino TEXT NOT NULL,
                cliente TEXT,
                monto REAL,
                created_at TEXT DEFAULT (datetime('now', 'localtime')),
                FOREIGN KEY(operador_id) REFERENCES operadores(id),
                FOREIGN KEY(chofer_id) REFERENCES choferes(id)
            )
        """)

        conn.commit()
        conn.close()
        return True

    except sqlite3.Error as e:
        print(f"Error al inicializar la base de datos: {e}")
        return False
