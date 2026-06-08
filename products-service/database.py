import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "products.db")

# abre una conexion a la base de datos
def get_connection():
    conn = sqlite3.connect(DATABASE_URL)
    conn.row_factory = sqlite3.Row  # devuelve filas como diccionarios
    return conn

# crea la tabla si no existe
def crear_tabla():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS productos (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre  TEXT    NOT NULL,
            precio  REAL    NOT NULL,
            stock   INTEGER NOT NULL
        )
    """)
    conn.commit()
    conn.close()

# inserta un producto y devuelve su id
def insertar_producto(nombre, precio, stock):
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO productos (nombre, precio, stock) VALUES (?, ?, ?)",
        (nombre, precio, stock)
    )
    conn.commit()
    id_nuevo = cursor.lastrowid
    conn.close()
    return id_nuevo

# devuelve todos los productos
def obtener_productos():
    conn = get_connection()
    filas = conn.execute("SELECT * FROM productos").fetchall()
    conn.close()
    return [dict(fila) for fila in filas]

# devuelve un producto por id, o None si no existe
def obtener_producto_por_id(id):
    conn = get_connection()
    fila = conn.execute(
        "SELECT * FROM productos WHERE id = ?", (id,)
    ).fetchone()
    conn.close()
    return dict(fila) if fila else None

# actualiza un producto y devuelve True si existia, False si no
def actualizar_producto(id, nombre, precio, stock):
    conn = get_connection()
    cursor = conn.execute(
        "UPDATE productos SET nombre = ?, precio = ?, stock = ? WHERE id = ?",
        (nombre, precio, stock, id)
    )
    conn.commit()
    filas_afectadas = cursor.rowcount
    conn.close()
    return filas_afectadas > 0

# elimina un producto y devuelve True si existia, False si no
def eliminar_producto(id):
    conn = get_connection()
    cursor = conn.execute(
        "DELETE FROM productos WHERE id = ?", (id,)
    )
    conn.commit()
    filas_afectadas = cursor.rowcount
    conn.close()
    return filas_afectadas > 0

# descuenta stock de un producto y devuelve True si habia suficiente, False si no
def descontar_stock(id, cantidad):
    conn = get_connection()
    # primero verifica que haya suficiente stock
    fila = conn.execute(
        "SELECT stock FROM productos WHERE id = ?", (id,)
    ).fetchone()
    if not fila or fila["stock"] < cantidad:
        conn.close()
        return False
    # si hay suficiente, descuenta
    conn.execute(
        "UPDATE productos SET stock = stock - ? WHERE id = ?",
        (cantidad, id)
    )
    conn.commit()
    conn.close()
    return True