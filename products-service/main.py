import logging
import os
import time
from fastapi import FastAPI, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel
from dotenv import load_dotenv
import database
from auth import verificar_token, security

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Products Service",
    description="Microservicio de productos de la tienda pinguina"
)

for intento in range(10):
    try:
        database.crear_tabla()
        break
    except Exception as e:
        logger.warning(f"Base de datos no disponible, reintentando en 2 segundos... (intento {intento + 1})")
        time.sleep(2)
else:
    logger.error("No se pudo conectar a la base de datos despues de 10 intentos")
    exit(1)

logger.info("Products Service iniciado correctamente")

class ProductoEntrada(BaseModel):
    nombre: str
    precio: float
    stock: int

@app.post("/productos", status_code=201, summary="Crear un producto")
def crear_producto(producto: ProductoEntrada, credentials: HTTPAuthorizationCredentials = Security(security)):
    verificar_token(credentials)
    logger.info(f"Creando producto: {producto.nombre}")
    id_nuevo = database.insertar_producto(producto.nombre, producto.precio, producto.stock)
    logger.info(f"Producto creado con id: {id_nuevo}")
    return {"id": id_nuevo, "mensaje": "Producto creado"}

@app.get("/productos", summary="Listar todos los productos")
def listar_productos(credentials: HTTPAuthorizationCredentials = Security(security)):
    verificar_token(credentials)
    logger.info("Listando todos los productos")
    return database.obtener_productos()

@app.get("/productos/{id}", summary="Obtener un producto por id")
def obtener_producto(id: int, credentials: HTTPAuthorizationCredentials = Security(security)):
    verificar_token(credentials)
    logger.info(f"Buscando producto con id: {id}")
    producto = database.obtener_producto_por_id(id)
    if not producto:
        logger.warning(f"Producto con id {id} no encontrado")
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return producto

@app.put("/productos/{id}", summary="Actualizar un producto")
def actualizar_producto(id: int, producto: ProductoEntrada, credentials: HTTPAuthorizationCredentials = Security(security)):
    verificar_token(credentials)
    logger.info(f"Actualizando producto con id: {id}")
    actualizado = database.actualizar_producto(id, producto.nombre, producto.precio, producto.stock)
    if not actualizado:
        logger.warning(f"Producto con id {id} no encontrado para actualizar")
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    logger.info(f"Producto con id {id} actualizado correctamente")
    return {"mensaje": "Producto actualizado"}

@app.delete("/productos/{id}", summary="Eliminar un producto")
def eliminar_producto(id: int, credentials: HTTPAuthorizationCredentials = Security(security)):
    verificar_token(credentials)
    logger.info(f"Eliminando producto con id: {id}")
    eliminado = database.eliminar_producto(id)
    if not eliminado:
        logger.warning(f"Producto con id {id} no encontrado para eliminar")
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    logger.info(f"Producto con id {id} eliminado correctamente")
    return {"mensaje": "Producto eliminado"}

@app.put("/productos/{id}/stock", summary="Descontar stock de un producto")
def descontar_stock(id: int, cantidad: int, credentials: HTTPAuthorizationCredentials = Security(security)):
    verificar_token(credentials)
    logger.info(f"Descontando {cantidad} unidades del producto {id}")
    resultado = database.descontar_stock(id, cantidad)
    if not resultado:
        logger.warning(f"Stock insuficiente para producto {id}")
        raise HTTPException(status_code=400, detail="Stock insuficiente o producto no encontrado")
    logger.info(f"Stock del producto {id} actualizado correctamente")
    return {"mensaje": "Stock actualizado"}