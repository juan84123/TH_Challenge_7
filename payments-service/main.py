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
    title="Payments Service",
    description="Microservicio de pagos de la tienda pinguina"
)

# crea la tabla al arrancar el servidor
database.crear_tabla()
logger.info("Payments Service iniciado correctamente")

ORDERS_SERVICE_URL = os.getenv("ORDERS_SERVICE_URL")
ORDERS_SERVICE_TOKEN = os.getenv("ORDERS_SERVICE_TOKEN")

# modelo de datos para procesar un pago
class PagoEntrada(BaseModel):
    pedido_id: int

# consulta el pedido al orders service con retry
def obtener_pedido(pedido_id):
    headers = {"Authorization": f"Bearer {ORDERS_SERVICE_TOKEN}"}
    intentos = 3

    for intento in range(intentos):
        try:
            logger.info(f"Consultando pedido {pedido_id} al Orders Service (intento {intento + 1})")
            response = requests.get(
                f"{ORDERS_SERVICE_URL}/pedidos/{pedido_id}",
                headers=headers,
                timeout=5
            )
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()
        except requests.exceptions.ConnectionError:
            logger.warning(f"Orders Service no disponible (intento {intento + 1} de {intentos})")
        except requests.exceptions.Timeout:
            logger.warning(f"Orders Service no respondio a tiempo (intento {intento + 1} de {intentos})")

    # si llega aca, todos los intentos fallaron
    logger.error("Orders Service no disponible despues de 3 intentos")
    raise HTTPException(status_code=503, detail="Orders Service no disponible")

# actualiza el estado del pedido a pagado con retry
def marcar_pedido_pagado(pedido_id):
    headers = {"Authorization": f"Bearer {ORDERS_SERVICE_TOKEN}"}
    intentos = 3

    for intento in range(intentos):
        try:
            logger.info(f"Actualizando estado del pedido {pedido_id} a pagado (intento {intento + 1})")
            response = requests.put(
                f"{ORDERS_SERVICE_URL}/pedidos/{pedido_id}",
                json={"estado": "pagado"},
                headers=headers,
                timeout=5
            )
            response.raise_for_status()
            return True
        except requests.exceptions.ConnectionError:
            logger.warning(f"Orders Service no disponible (intento {intento + 1} de {intentos})")
        except requests.exceptions.Timeout:
            logger.warning(f"Orders Service no respondio a tiempo (intento {intento + 1} de {intentos})")

    logger.error("No se pudo actualizar el estado del pedido despues de 3 intentos")
    raise HTTPException(status_code=503, detail="Orders Service no disponible")

@app.post("/pagos", status_code=201, summary="Procesar un pago")
def procesar_pago(pago: PagoEntrada, authorization: str = Header(...)):
    verificar_token(authorization)
    logger.info(f"Procesando pago para pedido_id: {pago.pedido_id}")

    # consulta el pedido al orders service
    pedido = obtener_pedido(pago.pedido_id)
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")

    # verifica que el pedido no este ya pagado
    if pedido["estado"] == "pagado":
        raise HTTPException(status_code=400, detail="El pedido ya fue pagado")

    # guarda el pago en la base de datos
    id_nuevo = database.insertar_pago(pago.pedido_id, pedido["total"])
    logger.info(f"Pago registrado con id: {id_nuevo}")

    # actualiza el estado del pedido a pagado
    marcar_pedido_pagado(pago.pedido_id)
    logger.info(f"Pedido {pago.pedido_id} marcado como pagado")

    return {"id": id_nuevo, "pedido_id": pago.pedido_id, "total": pedido["total"], "mensaje": "Pago procesado"}

@app.get("/pagos", summary="Listar todos los pagos")
def listar_pagos(authorization: str = Header(...)):
    verificar_token(authorization)
    logger.info("Listando todos los pagos")
    return database.obtener_pagos()

@app.get("/pagos/{id}", summary="Obtener un pago por id")
def obtener_pago(id: int, authorization: str = Header(...)):
    verificar_token(authorization)
    logger.info(f"Buscando pago con id: {id}")
    pago = database.obtener_pago_por_id(id)
    if not pago:
        logger.warning(f"Pago con id {id} no encontrado")
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    return pago