import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "orders.db")

# abre una conexion a la base de datos
def get_connection():
    conn = sqlite3.connect(DATABASE_URL)
    conn.row_factory = sqlite3.Row  # devuelve filas como diccionarios
    return conn

# crea la tabla si no existe
def crear_tabla():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS pedidos (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            producto_id INTEGER NOT NULL,
            cantidad    INTEGER NOT NULL,
            total       REAL    NOT NULL,
            estado      TEXT    NOT NULL DEFAULT 'pendiente'
        )
    """)
    conn.commit()
    conn.close()

# inserta un pedido y devuelve su id
def insertar_pedido(producto_id, cantidad, total):
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO pedidos (producto_id, cantidad, total) VALUES (?, ?, ?)",
        (producto_id, cantidad, total)
    )
    conn.commit()
    id_nuevo = cursor.lastrowid
    conn.close()
    return id_nuevo

# devuelve todos los pedidos
def obtener_pedidos():
    conn = get_connection()
    filas = conn.execute("SELECT * FROM pedidos").fetchall()
    conn.close()
    return [dict(fila) for fila in filas]

# devuelve un pedido por id, o None si no existe
def obtener_pedido_por_id(id):
    conn = get_connection()
    fila = conn.execute(
        "SELECT * FROM pedidos WHERE id = ?", (id,)
    ).fetchone()
    conn.close()
    return dict(fila) if fila else None

# actualiza el estado de un pedido
def actualizar_estado(id, estado):
    conn = get_connection()
    cursor = conn.execute(
        "UPDATE pedidos SET estado = ? WHERE id = ?",
        (estado, id)
    )
    conn.commit()
    filas_afectadas = cursor.rowcount
    conn.close()
    return filas_afectadas > 0

# elimina un pedido
def eliminar_pedido(id):
    conn = get_connection()
    cursor = conn.execute(
        "DELETE FROM pedidos WHERE id = ?", (id,)
    )
    conn.commit()
    filas_afectadas = cursor.rowcount
    conn.close()
    return filas_afectadas > 0