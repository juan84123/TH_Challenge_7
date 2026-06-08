import logging
import os
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from dotenv import load_dotenv
import database
from auth import verificar_token

load_dotenv()

# configuracion de logs
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Products Service",
    description="Microservicio de productos de la tienda pinguina"
)

# crea la tabla al arrancar el servidor
database.crear_tabla()
logger.info("Products Service iniciado correctamente")

# modelo de datos para crear o actualizar un producto
class ProductoEntrada(BaseModel):
    nombre: str
    precio: float
    stock: int

@app.post("/productos", status_code=201, summary="Crear un producto")
def crear_producto(producto: ProductoEntrada, authorization: str = Header(...)):
    verificar_token(authorization)
    logger.info(f"Creando producto: {producto.nombre}")
    id_nuevo = database.insertar_producto(producto.nombre, producto.precio, producto.stock)
    logger.info(f"Producto creado con id: {id_nuevo}")
    return {"id": id_nuevo, "mensaje": "Producto creado"}

@app.get("/productos", summary="Listar todos los productos")
def listar_productos(authorization: str = Header(...)):
    verificar_token(authorization)
    logger.info("Listando todos los productos")
    return database.obtener_productos()

@app.get("/productos/{id}", summary="Obtener un producto por id")
def obtener_producto(id: int, authorization: str = Header(...)):
    verificar_token(authorization)
    logger.info(f"Buscando producto con id: {id}")
    producto = database.obtener_producto_por_id(id)
    if not producto:
        logger.warning(f"Producto con id {id} no encontrado")
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return producto

@app.put("/productos/{id}", summary="Actualizar un producto")
def actualizar_producto(id: int, producto: ProductoEntrada, authorization: str = Header(...)):
    verificar_token(authorization)
    logger.info(f"Actualizando producto con id: {id}")
    actualizado = database.actualizar_producto(id, producto.nombre, producto.precio, producto.stock)
    if not actualizado:
        logger.warning(f"Producto con id {id} no encontrado para actualizar")
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    logger.info(f"Producto con id {id} actualizado correctamente")
    return {"mensaje": "Producto actualizado"}

@app.delete("/productos/{id}", summary="Eliminar un producto")
def eliminar_producto(id: int, authorization: str = Header(...)):
    verificar_token(authorization)
    logger.info(f"Eliminando producto con id: {id}")
    eliminado = database.eliminar_producto(id)
    if not eliminado:
        logger.warning(f"Producto con id {id} no encontrado para eliminar")
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    logger.info(f"Producto con id {id} eliminado correctamente")
    return {"mensaje": "Producto eliminado"}

@app.put("/productos/{id}/stock", summary="Descontar stock de un producto")
def descontar_stock(id: int, cantidad: int, authorization: str = Header(...)):
    verificar_token(authorization)
    logger.info(f"Descontando {cantidad} unidades del producto {id}")
    resultado = database.descontar_stock(id, cantidad)
    if not resultado:
        logger.warning(f"Stock insuficiente para producto {id}")
        raise HTTPException(status_code=400, detail="Stock insuficiente o producto no encontrado")
    logger.info(f"Stock del producto {id} actualizado correctamente")
    return {"mensaje": "Stock actualizado"}