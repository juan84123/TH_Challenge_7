import psycopg2
import psycopg2.extras
import os
from dotenv import load_dotenv

load_dotenv()

# datos de conexion a PostgreSQL
DB_HOST     = os.getenv("DB_HOST", "localhost")
DB_NAME     = os.getenv("DB_NAME", "orders_db")
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
        CREATE TABLE IF NOT EXISTS pedidos (
            id          SERIAL PRIMARY KEY,
            producto_id INTEGER NOT NULL,
            cantidad    INTEGER NOT NULL,
            total       REAL    NOT NULL,
            estado      TEXT    NOT NULL DEFAULT 'pendiente'
        )
    """)
    conn.commit()
    cursor.close()
    conn.close()

# inserta un pedido y devuelve su id
def insertar_pedido(producto_id, cantidad, total):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO pedidos (producto_id, cantidad, total) VALUES (%s, %s, %s) RETURNING id",
        (producto_id, cantidad, total)
    )
    id_nuevo = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    conn.close()
    return id_nuevo

# devuelve todos los pedidos
def obtener_pedidos():
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT * FROM pedidos")
    filas = cursor.fetchall()
    cursor.close()
    conn.close()
    return [dict(fila) for fila in filas]

# devuelve un pedido por id, o None si no existe
def obtener_pedido_por_id(id):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT * FROM pedidos WHERE id = %s", (id,))
    fila = cursor.fetchone()
    cursor.close()
    conn.close()
    return dict(fila) if fila else None

# actualiza el estado de un pedido
def actualizar_estado(id, estado):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE pedidos SET estado=%s WHERE id=%s",
        (estado, id)
    )
    conn.commit()
    filas_afectadas = cursor.rowcount
    cursor.close()
    conn.close()
    return filas_afectadas > 0

# elimina un pedido
def eliminar_pedido(id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM pedidos WHERE id=%s", (id,))
    conn.commit()
    filas_afectadas = cursor.rowcount
    cursor.close()
    conn.close()
    return filas_afectadas > 0