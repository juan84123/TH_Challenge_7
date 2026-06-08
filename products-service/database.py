import psycopg2
import psycopg2.extras
import os
from dotenv import load_dotenv

load_dotenv()

# datos de conexion a PostgreSQL
DB_HOST     = os.getenv("DB_HOST", "localhost")
DB_NAME     = os.getenv("DB_NAME", "products_db")
DB_USER     = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

# abre una conexion a la base de datos
def get_connection():
    conn = psycopg2.connect(
        host=DB_HOST,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    return conn

# crea la tabla si no existe
def crear_tabla():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS productos (
            id      SERIAL PRIMARY KEY,
            nombre  TEXT    NOT NULL,
            precio  REAL    NOT NULL,
            stock   INTEGER NOT NULL
        )
    """)
    conn.commit()
    cursor.close()
    conn.close()

# inserta un producto y devuelve su id
def insertar_producto(nombre, precio, stock):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO productos (nombre, precio, stock) VALUES (%s, %s, %s) RETURNING id",
        (nombre, precio, stock)
    )
    id_nuevo = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    conn.close()
    return id_nuevo

# devuelve todos los productos
def obtener_productos():
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT * FROM productos")
    filas = cursor.fetchall()
    cursor.close()
    conn.close()
    return [dict(fila) for fila in filas]

# devuelve un producto por id, o None si no existe
def obtener_producto_por_id(id):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT * FROM productos WHERE id = %s", (id,))
    fila = cursor.fetchone()
    cursor.close()
    conn.close()
    return dict(fila) if fila else None

# actualiza un producto y devuelve True si existia, False si no
def actualizar_producto(id, nombre, precio, stock):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE productos SET nombre=%s, precio=%s, stock=%s WHERE id=%s",
        (nombre, precio, stock, id)
    )
    conn.commit()
    filas_afectadas = cursor.rowcount
    cursor.close()
    conn.close()
    return filas_afectadas > 0

# elimina un producto y devuelve True si existia, False si no
def eliminar_producto(id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM productos WHERE id=%s", (id,))
    conn.commit()
    filas_afectadas = cursor.rowcount
    cursor.close()
    conn.close()
    return filas_afectadas > 0

# descuenta stock de un producto
def descontar_stock(id, cantidad):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT stock FROM productos WHERE id=%s", (id,))
    fila = cursor.fetchone()
    if not fila or fila["stock"] < cantidad:
        cursor.close()
        conn.close()
        return False
    cursor.execute(
        "UPDATE productos SET stock = stock - %s WHERE id=%s",
        (cantidad, id)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return True