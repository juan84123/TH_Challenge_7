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
    title="Payments Service",
    description="Microservicio de pagos de la tienda pinguina"
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

logger.info("Payments Service iniciado correctamente")

# leemos la url y el token de orders-service desde las variables de entorno
ORDERS_SERVICE_URL = os.getenv("ORDERS_SERVICE_URL")
ORDERS_SERVICE_TOKEN = os.getenv("ORDERS_SERVICE_TOKEN")

# modelo de datos para procesar un pago
# define que campos esperamos recibir en el body del request
class PagoEntrada(BaseModel):
    pedido_id: int  # id del pedido que se quiere pagar

# funcion auxiliar que consulta un pedido al orders-service
# tiene retry de 3 intentos por si el servicio no esta disponible
def obtener_pedido(pedido_id):
    headers = {"Authorization": f"Bearer {ORDERS_SERVICE_TOKEN}"}  # token para autenticarse
    intentos = 3

    for intento in range(intentos):  # intentamos hasta 3 veces
        try:
            logger.info(f"Consultando pedido {pedido_id} al Orders Service (intento {intento + 1})")
            response = requests.get(
                f"{ORDERS_SERVICE_URL}/pedidos/{pedido_id}",  # llamamos al endpoint de orders
                headers=headers,
                timeout=5  # esperamos maximo 5 segundos
            )
            if response.status_code == 404:
                return None  # el pedido no existe, no tiene sentido reintentar
            response.raise_for_status()  # si hay otro error HTTP lanza una excepcion
            return response.json()  # si funciono, devolvemos el pedido como diccionario
        except requests.exceptions.ConnectionError:
            # el servicio no esta levantado o no es alcanzable
            logger.warning(f"Orders Service no disponible (intento {intento + 1} de {intentos})")
        except requests.exceptions.Timeout:
            # el servicio tardo mas de 5 segundos en responder
            logger.warning(f"Orders Service no respondio a tiempo (intento {intento + 1} de {intentos})")

    # si llegamos aca, los 3 intentos fallaron
    logger.error("Orders Service no disponible despues de 3 intentos")
    raise HTTPException(status_code=503, detail="Orders Service no disponible")

# funcion auxiliar que marca un pedido como pagado en orders-service
# tiene retry de 3 intentos por si el servicio no esta disponible
def marcar_pedido_pagado(pedido_id):
    headers = {"Authorization": f"Bearer {ORDERS_SERVICE_TOKEN}"}  # token para autenticarse
    intentos = 3

    for intento in range(intentos):  # intentamos hasta 3 veces
        try:
            logger.info(f"Actualizando estado del pedido {pedido_id} a pagado (intento {intento + 1})")
            response = requests.put(
                f"{ORDERS_SERVICE_URL}/pedidos/{pedido_id}",  # llamamos al endpoint de orders
                json={"estado": "pagado"},  # mandamos el nuevo estado
                headers=headers,
                timeout=5
            )
            response.raise_for_status()
            return True  # si funciono devolvemos True
        except requests.exceptions.ConnectionError:
            logger.warning(f"Orders Service no disponible (intento {intento + 1} de {intentos})")
        except requests.exceptions.Timeout:
            logger.warning(f"Orders Service no respondio a tiempo (intento {intento + 1} de {intentos})")

    # si llegamos aca, los 3 intentos fallaron
    logger.error("No se pudo actualizar el estado del pedido despues de 3 intentos")
    raise HTTPException(status_code=503, detail="Orders Service no disponible")

# endpoint para procesar un pago
@app.post("/pagos", status_code=201, summary="Procesar un pago")
def procesar_pago(pago: PagoEntrada, credentials: HTTPAuthorizationCredentials = Security(security)):
    verificar_token(credentials)  # verificamos que el token sea valido
    logger.info(f"Procesando pago para pedido_id: {pago.pedido_id}")

    # consultamos el pedido al orders-service
    pedido = obtener_pedido(pago.pedido_id)
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")

    # verificamos que el pedido no este ya pagado
    if pedido["estado"] == "pagado":
        raise HTTPException(status_code=400, detail="El pedido ya fue pagado")

    # guardamos el pago en nuestra base de datos
    id_nuevo = database.insertar_pago(pago.pedido_id, pedido["total"])
    logger.info(f"Pago registrado con id: {id_nuevo}")

    # le avisamos a orders-service que marque el pedido como pagado
    marcar_pedido_pagado(pago.pedido_id)
    logger.info(f"Pedido {pago.pedido_id} marcado como pagado")

    return {"id": id_nuevo, "pedido_id": pago.pedido_id, "total": pedido["total"], "mensaje": "Pago procesado"}

# endpoint para listar todos los pagos
@app.get("/pagos", summary="Listar todos los pagos")
def listar_pagos(credentials: HTTPAuthorizationCredentials = Security(security)):
    verificar_token(credentials)  # verificamos el token
    logger.info("Listando todos los pagos")
    return database.obtener_pagos()  # delegamos la consulta a database.py

# endpoint para obtener un pago por su id
@app.get("/pagos/{id}", summary="Obtener un pago por id")
def obtener_pago(id: int, credentials: HTTPAuthorizationCredentials = Security(security)):
    verificar_token(credentials)
    logger.info(f"Buscando pago con id: {id}")
    pago = database.obtener_pago_por_id(id)  # buscamos el pago en la base de datos
    if not pago:
        logger.warning(f"Pago con id {id} no encontrado")
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    return pago