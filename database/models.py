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
            
        # Viajes pendientes (Lista)
        cursor.execute("SELECT id, origen, destino, cliente, created_at FROM viajes WHERE chofer_id = ? AND estado = 'Pendiente' ORDER BY orden ASC, created_at ASC", (c["id"],))
        pendientes = cursor.fetchall()
        c["viajes_pendientes"] = [dict(p) for p in pendientes]
            
    conn.close()
    return choferes


def create_viaje(operador_id: int, chofer_id: int, origen: str, destino: str, cliente: str):
    """
    Crea un viaje nuevo. Destino puede ser vacío.
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


def finalizar_viaje(viaje_id: int, monto: float, metodo_pago: str, cliente_nombre: str = None, observaciones: str = None):
    """Marca un viaje como finalizado y le asigna el monto, método de pago, cliente y observaciones."""
    conn = get_connection()
    cursor = conn.cursor()
    
    if cliente_nombre is not None:
        cursor.execute("UPDATE viajes SET estado = 'Finalizado', monto = ?, metodo_pago = ?, cliente = ?, observaciones = ?, updated_at = datetime('now', 'localtime') WHERE id = ?", (monto, metodo_pago, cliente_nombre, observaciones, viaje_id))
    else:
        cursor.execute("UPDATE viajes SET estado = 'Finalizado', monto = ?, metodo_pago = ?, observaciones = ?, updated_at = datetime('now', 'localtime') WHERE id = ?", (monto, metodo_pago, observaciones, viaje_id))
        
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
    cursor.execute("UPDATE viajes SET estado = 'Cancelado', updated_at = datetime('now', 'localtime') WHERE id = ?", (viaje_id,))
    conn.commit()
    conn.close()

def edit_destino(viaje_id: int, destino: str):
    """Permite editar el destino de un viaje activo o pendiente."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE viajes SET destino = ? WHERE id = ?", (destino, viaje_id))
    conn.commit()
    conn.close()

def priorizar_viaje(viaje_id: int):
    """Pone un viaje pendiente como el primero en la cola (orden = -1, o se resta 1 al menor)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE viajes SET orden = orden - 1 WHERE id = ?", (viaje_id,))
    conn.commit()
    conn.close()

def get_historial():
    """Devuelve los viajes finalizados y cancelados, ordenados por los más recientes."""
    conn = get_connection()
    cursor = conn.cursor()
    query = """
        SELECT v.id, v.origen, v.destino, v.cliente, v.monto, v.metodo_pago, v.estado, v.updated_at, v.observaciones,
               c.nombre as chofer_nombre, c.movil as chofer_movil,
               o.nombre as operador_nombre
        FROM viajes v
        JOIN choferes c ON v.chofer_id = c.id
        JOIN operadores o ON v.operador_id = o.id
        WHERE v.estado IN ('Finalizado', 'Cancelado')
        ORDER BY v.updated_at DESC
        LIMIT 100
    """
    cursor.execute(query)
    historial = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return historial

def delete_viaje_historial(viaje_id: int):
    """Elimina permanentemente un viaje de la base de datos (usado para limpiar pruebas)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM viajes WHERE id = ?", (viaje_id,))
    conn.commit()
    conn.close()

def get_daily_stats():
    """Calcula las estadísticas del turno/día actual."""
    conn = get_connection()
    cursor = conn.cursor()
    # Solo viajes finalizados hoy
    query = """
        SELECT metodo_pago, sum(monto) as total_monto, count(id) as total_viajes 
        FROM viajes 
        WHERE estado = 'Finalizado' 
          AND date(updated_at) = date('now', 'localtime')
        GROUP BY metodo_pago
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    
    stats = {
        "viajes_hechos": 0,
        "efectivo": 0.0,
        "transferencia": 0.0,
        "fiados": 0.0,
        "neto": 0.0
    }
    
    for r in rows:
        metodo = r["metodo_pago"]
        monto = r["total_monto"] or 0.0
        cantidad = r["total_viajes"] or 0
        
        stats["viajes_hechos"] += cantidad
        
        if metodo == "Efectivo":
            stats["efectivo"] += monto
            stats["neto"] += monto
        elif metodo == "Transferencia":
            stats["transferencia"] += monto
            stats["neto"] += monto
        elif metodo == "Cuenta Corriente":
            stats["fiados"] += monto
            
    conn.close()
    return stats
