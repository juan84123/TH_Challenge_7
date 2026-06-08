import logging
import os
import requests
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
    title="Orders Service",
    description="Microservicio de pedidos de la tienda pinguina"
)

# crea la tabla al arrancar el servidor
database.crear_tabla()
logger.info("Orders Service iniciado correctamente")

PRODUCTS_SERVICE_URL = os.getenv("PRODUCTS_SERVICE_URL")
PRODUCTS_SERVICE_TOKEN = os.getenv("PRODUCTS_SERVICE_TOKEN")

# modelo de datos para crear un pedido
class PedidoEntrada(BaseModel):
    producto_id: int
    cantidad: int

# modelo de datos para actualizar el estado
class EstadoEntrada(BaseModel):
    estado: str

# funcion que consulta el precio al products service con retry
def obtener_producto(producto_id):
    headers = {"Authorization": f"Bearer {PRODUCTS_SERVICE_TOKEN}"}
    intentos = 3

    for intento in range(intentos):
        try:
            logger.info(f"Consultando producto {producto_id} al Products Service (intento {intento + 1})")
            response = requests.get(
                f"{PRODUCTS_SERVICE_URL}/productos/{producto_id}",
                headers=headers,
                timeout=5
            )
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()
        except requests.exceptions.ConnectionError:
            logger.warning(f"Products Service no disponible (intento {intento + 1} de {intentos})")
        except requests.exceptions.Timeout:
            logger.warning(f"Products Service no respondio a tiempo (intento {intento + 1} de {intentos})")

    # si llega aca, todos los intentos fallaron
    logger.error("Products Service no disponible despues de 3 intentos")
    raise HTTPException(status_code=503, detail="Products Service no disponible")

@app.post("/pedidos", status_code=201, summary="Crear un pedido")
def crear_pedido(pedido: PedidoEntrada, authorization: str = Header(...)):
    verificar_token(authorization)
    logger.info(f"Creando pedido para producto_id: {pedido.producto_id}")

    # consulta el producto al products service
    producto = obtener_producto(pedido.producto_id)
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    # calcula el total
    total = producto["precio"] * pedido.cantidad
    logger.info(f"Total calculado: {total}")

    id_nuevo = database.insertar_pedido(pedido.producto_id, pedido.cantidad, total)
    logger.info(f"Pedido creado con id: {id_nuevo}")
    return {"id": id_nuevo, "total": total, "mensaje": "Pedido creado"}

@app.get("/pedidos", summary="Listar todos los pedidos")
def listar_pedidos(authorization: str = Header(...)):
    verificar_token(authorization)
    logger.info("Listando todos los pedidos")
    return database.obtener_pedidos()

@app.get("/pedidos/{id}", summary="Obtener un pedido por id")
def obtener_pedido(id: int, authorization: str = Header(...)):
    verificar_token(authorization)
    logger.info(f"Buscando pedido con id: {id}")
    pedido = database.obtener_pedido_por_id(id)
    if not pedido:
        logger.warning(f"Pedido con id {id} no encontrado")
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    return pedido

@app.put("/pedidos/{id}", summary="Actualizar estado de un pedido")
def actualizar_pedido(id: int, estado: EstadoEntrada, authorization: str = Header(...)):
    verificar_token(authorization)
    logger.info(f"Actualizando estado del pedido {id} a: {estado.estado}")
    actualizado = database.actualizar_estado(id, estado.estado)
    if not actualizado:
        logger.warning(f"Pedido con id {id} no encontrado para actualizar")
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    logger.info(f"Pedido {id} actualizado correctamente")
    return {"mensaje": "Pedido actualizado"}

@app.delete("/pedidos/{id}", summary="Eliminar un pedido")
def eliminar_pedido(id: int, authorization: str = Header(...)):
    verificar_token(authorization)
    logger.info(f"Eliminando pedido con id: {id}")
    eliminado = database.eliminar_pedido(id)
    if not eliminado:
        logger.warning(f"Pedido con id {id} no encontrado para eliminar")
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    logger.info(f"Pedido {id} eliminado correctamente")
    return {"mensaje": "Pedido eliminado"}