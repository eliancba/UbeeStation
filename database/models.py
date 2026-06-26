"""
Funciones CRUD para las entidades de la base de datos.
"""

from database.connection import get_connection

# --- CHOFERES ---

def get_choferes():
    """
    Obtiene todos los choferes de la base de datos, ordenados por estado 
    (activos primero) y luego por nombre.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # ORDER BY activo DESC pone los 1 (activos) antes que los 0 (inactivos)
    cursor.execute("SELECT * FROM choferes ORDER BY activo DESC, nombre ASC")
    choferes = cursor.fetchall()
    
    conn.close()
    
    # Convertimos los sqlite3.Row a diccionarios estándar de Python
    # para que sea más fácil trabajar con ellos en las vistas.
    return [dict(row) for row in choferes]


def add_chofer(nombre: str, movil: str, telefono: str):
    """
    Agrega un nuevo chofer a la base de datos.
    Por defecto se crea como activo (1).
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "INSERT INTO choferes (nombre, movil, telefono) VALUES (?, ?, ?)",
        (nombre, movil, telefono)
    )
    
    conn.commit()
    conn.close()


def toggle_chofer_status(chofer_id: int, nuevo_estado: int):
    """
    Cambia el estado de un chofer (1 = Activo, 0 = Inactivo).
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "UPDATE choferes SET activo = ? WHERE id = ?",
        (nuevo_estado, chofer_id)
    )
    
    conn.commit()
    conn.close()


def delete_chofer(chofer_id: int):
    """
    Elimina un chofer de forma permanente.
    (A diferencia de los viajes, los choferes mal cargados se pueden borrar).
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM choferes WHERE id = ?", (chofer_id,))
    conn.commit()
    conn.close()


# --- OPERADORES ---

def get_operadores():
    """Obtiene todos los operadores activos."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM operadores WHERE activo = 1 ORDER BY nombre ASC")
    operadores = cursor.fetchall()
    conn.close()
    return [dict(row) for row in operadores]


def add_operador(nombre: str):
    """Agrega un nuevo operador."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO operadores (nombre) VALUES (?)", (nombre,))
    conn.commit()
    conn.close()


# --- VIAJES Y DESPACHO ---

def get_flota_status():
    """
    Devuelve la lista de choferes activos junto con su viaje en curso 
    y su viaje en cola (si lo tienen).
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Obtenemos choferes activos (ordenados por móvil)
    # CAST para que ordene numéricamente el móvil si es posible
    cursor.execute("SELECT id, nombre, movil, telefono FROM choferes WHERE activo = 1 ORDER BY CAST(movil AS INTEGER) ASC, nombre ASC")
    choferes = [dict(row) for row in cursor.fetchall()]
    
    # 2. Para cada chofer, buscamos su estado
    for c in choferes:
        c["viaje_actual"] = None
        c["viaje_pendiente"] = None
        
        # Viaje actual
        cursor.execute("SELECT id, origen, destino, cliente, created_at FROM viajes WHERE chofer_id = ? AND estado = 'En viaje' LIMIT 1", (c["id"],))
        actual = cursor.fetchone()
        if actual:
            c["viaje_actual"] = dict(actual)
            
        # Viaje pendiente
        cursor.execute("SELECT id, origen, destino, cliente, created_at FROM viajes WHERE chofer_id = ? AND estado = 'Pendiente' ORDER BY created_at ASC LIMIT 1", (c["id"],))
        pendiente = cursor.fetchone()
        if pendiente:
            c["viaje_pendiente"] = dict(pendiente)
            
    conn.close()
    return choferes


def create_viaje(operador_id: int, chofer_id: int, origen: str, destino: str, cliente: str):
    """
    Crea un viaje nuevo.
    Si el chofer ya está en viaje, el nuevo pasa a 'Pendiente'.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM viajes WHERE chofer_id = ? AND estado = 'En viaje'", (chofer_id,))
    is_busy = cursor.fetchone() is not None
    
    estado = "Pendiente" if is_busy else "En viaje"
    
    cursor.execute(
        "INSERT INTO viajes (operador_id, chofer_id, origen, destino, cliente, estado) VALUES (?, ?, ?, ?, ?, ?)",
        (operador_id, chofer_id, origen, destino, cliente, estado)
    )
    conn.commit()
    conn.close()


def finalizar_viaje(viaje_id: int, monto: float):
    """Marca un viaje como finalizado y le asigna el monto cobrado."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE viajes SET estado = 'Finalizado', monto = ? WHERE id = ?", (monto, viaje_id))
    conn.commit()
    conn.close()


def iniciar_viaje_pendiente(viaje_id: int):
    """Inicia un viaje que estaba pendiente. Resetea su created_at para el cronómetro."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE viajes SET estado = 'En viaje', created_at = datetime('now', 'localtime') WHERE id = ?", (viaje_id,))
    conn.commit()
    conn.close()

def cancelar_viaje(viaje_id: int):
    """Cancela un viaje (queda en el historial)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE viajes SET estado = 'Cancelado' WHERE id = ?", (viaje_id,))
    conn.commit()
    conn.close()
