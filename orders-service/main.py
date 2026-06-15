import logging  # para registrar lo que pasa en el servidor
import os  # para leer las variables de entorno
import time  # para hacer pausas entre reintentos de conexion
import requests  # para hacer llamadas HTTP a otros servicios
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
    title="Orders Service",
    description="Microservicio de pedidos de la tienda pinguina"
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

logger.info("Orders Service iniciado correctamente")

# leemos la url y el token de products-service desde las variables de entorno
PRODUCTS_SERVICE_URL = os.getenv("PRODUCTS_SERVICE_URL")
PRODUCTS_SERVICE_TOKEN = os.getenv("PRODUCTS_SERVICE_TOKEN")

# modelo de datos para crear un pedido
# define que campos esperamos recibir en el body del request
class PedidoEntrada(BaseModel):
    producto_id: int  # id del producto que se quiere pedir
    cantidad: int  # cantidad de unidades

# modelo de datos para actualizar el estado de un pedido
class EstadoEntrada(BaseModel):
    estado: str  # nuevo estado del pedido, por ejemplo "pagado"

# funcion auxiliar que consulta un producto al products-service
# tiene retry de 3 intentos por si el servicio no esta disponible
def obtener_producto(producto_id):
    headers = {"Authorization": f"Bearer {PRODUCTS_SERVICE_TOKEN}"}  # token para autenticarse
    intentos = 3

    for intento in range(intentos):  # intentamos hasta 3 veces
        try:
            logger.info(f"Consultando producto {producto_id} al Products Service (intento {intento + 1})")
            response = requests.get(
                f"{PRODUCTS_SERVICE_URL}/productos/{producto_id}",  # llamamos al endpoint de products
                headers=headers,
                timeout=5  # esperamos maximo 5 segundos
            )
            if response.status_code == 404:
                return None  # el producto no existe, no tiene sentido reintentar
            response.raise_for_status()  # si hay otro error HTTP lanza una excepcion
            return response.json()  # si funciono, devolvemos el producto como diccionario
        except requests.exceptions.ConnectionError:
            # el servicio no esta levantado o no es alcanzable
            logger.warning(f"Products Service no disponible (intento {intento + 1} de {intentos})")
        except requests.exceptions.Timeout:
            # el servicio tardo mas de 5 segundos en responder
            logger.warning(f"Products Service no respondio a tiempo (intento {intento + 1} de {intentos})")

    # si llegamos aca, los 3 intentos fallaron
    logger.error("Products Service no disponible despues de 3 intentos")
    raise HTTPException(status_code=503, detail="Products Service no disponible")

# endpoint para crear un pedido
@app.post("/pedidos", status_code=201, summary="Crear un pedido")
def crear_pedido(pedido: PedidoEntrada, credentials: HTTPAuthorizationCredentials = Security(security)):
    verificar_token(credentials)  # verificamos que el token sea valido
    logger.info(f"Creando pedido para producto_id: {pedido.producto_id}")

    # consultamos el producto al products-service para obtener el precio
    producto = obtener_producto(pedido.producto_id)
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    # verificamos que haya stock suficiente antes de crear el pedido
    if producto["stock"] < pedido.cantidad:
        raise HTTPException(status_code=400, detail="Stock insuficiente")

    # calculamos el total multiplicando precio por cantidad
    total = producto["precio"] * pedido.cantidad
    logger.info(f"Total calculado: {total}")

    # guardamos el pedido en nuestra base de datos
    id_nuevo = database.insertar_pedido(pedido.producto_id, pedido.cantidad, total)
    logger.info(f"Pedido creado con id: {id_nuevo}")

    # le avisamos a products-service que descuente el stock
    headers = {"Authorization": f"Bearer {PRODUCTS_SERVICE_TOKEN}"}
    try:
        response = requests.put(
            f"{PRODUCTS_SERVICE_URL}/productos/{pedido.producto_id}/stock",
            params={"cantidad": pedido.cantidad},  # mandamos la cantidad a descontar
            headers=headers,
            timeout=5
        )
        response.raise_for_status()
        logger.info(f"Stock descontado correctamente para producto {pedido.producto_id}")
    except Exception as e:
        # si falla el descuento de stock lo registramos pero no cancelamos el pedido
        logger.error(f"No se pudo descontar el stock: {e}")

    return {"id": id_nuevo, "total": total, "mensaje": "Pedido creado"}

# endpoint para listar todos los pedidos
@app.get("/pedidos", summary="Listar todos los pedidos")
def listar_pedidos(credentials: HTTPAuthorizationCredentials = Security(security)):
    verificar_token(credentials)  # verificamos el token
    logger.info("Listando todos los pedidos")
    return database.obtener_pedidos()  # delegamos la consulta a database.py

# endpoint para obtener un pedido por su id
@app.get("/pedidos/{id}", summary="Obtener un pedido por id")
def obtener_pedido(id: int, credentials: HTTPAuthorizationCredentials = Security(security)):
    verificar_token(credentials)
    logger.info(f"Buscando pedido con id: {id}")
    pedido = database.obtener_pedido_por_id(id)  # buscamos el pedido en la base de datos
    if not pedido:
        logger.warning(f"Pedido con id {id} no encontrado")
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    return pedido

# endpoint para actualizar el estado de un pedido
@app.put("/pedidos/{id}", summary="Actualizar estado de un pedido")
def actualizar_pedido(id: int, estado: EstadoEntrada, credentials: HTTPAuthorizationCredentials = Security(security)):
    verificar_token(credentials)
    logger.info(f"Actualizando estado del pedido {id} a: {estado.estado}")
    actualizado = database.actualizar_estado(id, estado.estado)  # actualizamos en la base de datos
    if not actualizado:
        logger.warning(f"Pedido con id {id} no encontrado para actualizar")
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    logger.info(f"Pedido {id} actualizado correctamente")
    return {"mensaje": "Pedido actualizado"}

# endpoint para eliminar un pedido
@app.delete("/pedidos/{id}", summary="Eliminar un pedido")
def eliminar_pedido(id: int, credentials: HTTPAuthorizationCredentials = Security(security)):
    verificar_token(credentials)
    logger.info(f"Eliminando pedido con id: {id}")
    eliminado = database.eliminar_pedido(id)  # eliminamos de la base de datos
    if not eliminado:
        logger.warning(f"Pedido con id {id} no encontrado para eliminar")
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    logger.info(f"Pedido {id} eliminado correctamente")
    return {"mensaje": "Pedido eliminado"}