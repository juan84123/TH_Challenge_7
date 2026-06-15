import logging  # para registrar lo que pasa en el servidor
import os  # para leer las variables de entorno
import time  # para hacer pausas entre reintentos de conexion
from fastapi import FastAPI, HTTPException, Security  # framework web y manejo de errores
from fastapi.security import HTTPAuthorizationCredentials  # tipo de dato para las credenciales
from pydantic import BaseModel  # para definir los modelos de datos
from dotenv import load_dotenv  # para cargar el archivo .env
import database  # nuestro archivo de base de datos
from auth import verificar_token, security  # nuestra funcion de autenticacion

load_dotenv()  # carga las variables del archivo .env

# configuracion del sistema de logs
# cada mensaje va a mostrar la fecha, el nivel y el texto
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)  # creamos el logger para este archivo

# creamos la aplicacion FastAPI con titulo y descripcion
# esto aparece en la documentacion automatica en /docs
app = FastAPI(
    title="Products Service",
    description="Microservicio de productos de la tienda pinguina"
)

# al arrancar el servidor esperamos que la base de datos este lista
# intentamos conectarnos hasta 10 veces con 2 segundos de espera entre cada intento
for intento in range(10):
    try:
        database.crear_tabla()  # si funciona, salimos del loop
        break
    except Exception as e:
        logger.warning(f"Base de datos no disponible, reintentando en 2 segundos... (intento {intento + 1})")
        time.sleep(2)  # esperamos 2 segundos antes de reintentar
else:
    # si los 10 intentos fallaron, cerramos el servidor
    logger.error("No se pudo conectar a la base de datos despues de 10 intentos")
    exit(1)

logger.info("Products Service iniciado correctamente")

# modelo de datos para crear o actualizar un producto
# define que campos esperamos recibir en el body del request
class ProductoEntrada(BaseModel):
    nombre: str  # nombre del producto
    precio: float  # precio en guaranies
    stock: int  # cantidad disponible

# endpoint para crear un producto nuevo
@app.post("/productos", status_code=201, summary="Crear un producto")
def crear_producto(producto: ProductoEntrada, credentials: HTTPAuthorizationCredentials = Security(security)):
    verificar_token(credentials)  # verificamos que el token sea valido
    logger.info(f"Creando producto: {producto.nombre}")
    id_nuevo = database.insertar_producto(producto.nombre, producto.precio, producto.stock)  # guardamos en la base de datos
    logger.info(f"Producto creado con id: {id_nuevo}")
    return {"id": id_nuevo, "mensaje": "Producto creado"}

# endpoint para listar todos los productos
@app.get("/productos", summary="Listar todos los productos")
def listar_productos(credentials: HTTPAuthorizationCredentials = Security(security)):
    verificar_token(credentials)  # verificamos el token
    logger.info("Listando todos los productos")
    return database.obtener_productos()  # delegamos la consulta a database.py

# endpoint para obtener un producto por su id
@app.get("/productos/{id}", summary="Obtener un producto por id")
def obtener_producto(id: int, credentials: HTTPAuthorizationCredentials = Security(security)):
    verificar_token(credentials)
    logger.info(f"Buscando producto con id: {id}")
    producto = database.obtener_producto_por_id(id)  # buscamos el producto en la base de datos
    if not producto:
        logger.warning(f"Producto con id {id} no encontrado")
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return producto

# endpoint para actualizar un producto existente
@app.put("/productos/{id}", summary="Actualizar un producto")
def actualizar_producto(id: int, producto: ProductoEntrada, credentials: HTTPAuthorizationCredentials = Security(security)):
    verificar_token(credentials)
    logger.info(f"Actualizando producto con id: {id}")
    actualizado = database.actualizar_producto(id, producto.nombre, producto.precio, producto.stock)  # actualizamos en la base de datos
    if not actualizado:
        logger.warning(f"Producto con id {id} no encontrado para actualizar")
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    logger.info(f"Producto con id {id} actualizado correctamente")
    return {"mensaje": "Producto actualizado"}

# endpoint para eliminar un producto
@app.delete("/productos/{id}", summary="Eliminar un producto")
def eliminar_producto(id: int, credentials: HTTPAuthorizationCredentials = Security(security)):
    verificar_token(credentials)
    logger.info(f"Eliminando producto con id: {id}")
    eliminado = database.eliminar_producto(id)  # eliminamos de la base de datos
    if not eliminado:
        logger.warning(f"Producto con id {id} no encontrado para eliminar")
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    logger.info(f"Producto con id {id} eliminado correctamente")
    return {"mensaje": "Producto eliminado"}

# endpoint interno usado por orders-service para descontar stock al crear un pedido
@app.put("/productos/{id}/stock", summary="Descontar stock de un producto")
def descontar_stock(id: int, cantidad: int, credentials: HTTPAuthorizationCredentials = Security(security)):
    verificar_token(credentials)
    logger.info(f"Descontando {cantidad} unidades del producto {id}")
    resultado = database.descontar_stock(id, cantidad)  # descontamos el stock en la base de datos
    if not resultado:
        logger.warning(f"Stock insuficiente para producto {id}")
        raise HTTPException(status_code=400, detail="Stock insuficiente o producto no encontrado")
    logger.info(f"Stock del producto {id} actualizado correctamente")
    return {"mensaje": "Stock actualizado"}