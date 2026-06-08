import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "payments.db")

# abre una conexion a la base de datos
def get_connection():
    conn = sqlite3.connect(DATABASE_URL)
    conn.row_factory = sqlite3.Row  # devuelve filas como diccionarios
    return conn

# crea la tabla si no existe
def crear_tabla():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS pagos (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            pedido_id INTEGER NOT NULL,
            total     REAL    NOT NULL,
            estado    TEXT    NOT NULL DEFAULT 'completado'
        )
    """)
    conn.commit()
    conn.close()

# inserta un pago y devuelve su id
def insertar_pago(pedido_id, total):
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO pagos (pedido_id, total) VALUES (?, ?)",
        (pedido_id, total)
    )
    conn.commit()
    id_nuevo = cursor.lastrowid
    conn.close()
    return id_nuevo

# devuelve todos los pagos
def obtener_pagos():
    conn = get_connection()
    filas = conn.execute("SELECT * FROM pagos").fetchall()
    conn.close()
    return [dict(fila) for fila in filas]

# devuelve un pago por id, o None si no existe
def obtener_pago_por_id(id):
    conn = get_connection()
    fila = conn.execute(
        "SELECT * FROM pagos WHERE id = ?", (id,)
    ).fetchone()
    conn.close()
    return dict(fila) if fila else None