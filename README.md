# TH_Challenge_7


    🧊 Los monolitos están cayendo. Solo un equipo de pingüinos con arquitectura distribuida puede evitar el colapso global del backend.

🐧 1. Escenario y Desafío

El cuartel general de Penguin Academy está al borde del colapso. Un antiguo servidor monolítico, apodado "EL MAMUT", ha alcanzado temperaturas internas similares a las del sol, y cada vez que un participante intenta hacer login, el sistema entero se reinicia en slow motion.

El caos es real: los pedidos se mezclan con los pagos, los productos aparecen en idiomas que no existen, y un pingüino dice haber visto a una factura hablarle. Necesitamos una solución. Rápido. Elegante. Modular.

Tu misión (y sí, ya sabés que no podés negarte): dividir al Mamut en partes pequeñas, autónomas y funcionales. En otras palabras: MICROSERVICIOS.
🧠 2. ¿Qué tenés que construir?
✨ Paso 1: Dividir para vencer

Elegí un sistema sencillo pero funcional (ej: tienda online, gestor de tareas, app de delivery de hielo, etc.) y:

    Listá todas las funcionalidades principales
    Agrupalas en microservicios lógicamente separados
    Asegurate que cada microservicio tenga una única responsabilidad

Ejemplos:
Microservicio 	Responsabilidad
Servicio de Productos 	Agregar, actualizar productos
Servicio de Inventario 	Verificar stock
Servicio de Pedidos 	Crear, modificar pedidos
Servicio de Pagos 	Procesar transacciones falsas con éxito emocional
🕸️ Paso 2: APIs RESTful

Cada microservicio debe exponer endpoints REST.

    Usá métodos HTTP correctos (GET, POST, PUT, DELETE)
    Que todo esté claramente documentado (como si lo fueran a leer tus enemigos)

📨 Simulá que se hablan entre ellos como si fueran ex compañeros de trabajo que solo se saludan por mail. Ejemplo:

POST /pedido HTTP/1.1
Authorization: Bearer token123
Content-Type: application/json

{
  "producto_id": 7,
  "cantidad": 3
}

🛡️ Paso 3: Seguridad Pingüina

Cada microservicio debe autenticarse con JWT o tokens secretos.

    Incluí el token en el header de las solicitudes:

    Authorization: Bearer tu_token

    Rechazá a los que no tengan permiso. Sin piedad.

💽 Paso 4: Base de datos privada, como el corazón de un pingüino

    Cada microservicio con su propia base de datos
    ¡Nada de compartir tablas! Este no es un asado.
    Si necesitan hablar, que lo hagan por eventos o APIs.

✅ 3. Requisitos Obligatorios

    Crear al menos 3 microservicios con responsabilidades distintas
    Cada uno con su propia API REST
    Implementar autenticación entre servicios
    Usar bases de datos independientes
    Gestionar errores con gracia y resiliencia (Circuit Breaker, retry, logs, llorar)
    Docker obligatorio para cada microservicio
        Cada servicio debe tener su propio Dockerfile
        El sistema completo debe levantarse con docker compose up
        Bases de datos también deben correr en contenedores
    Configuración mediante variables de entorno (no hardcodear)

🎁 4. Bonus Jugosos (pero opcionales)

    Que sean fácilmente escalables
    Diagramas de arquitectura como si fueras ingeniero de la NASA
    Logs centralizados, por si se prende fuego todo

📜 5. Consideraciones

    Aplicá principios SOLID y Clean Code
    Usá nombres descriptivos. No más funciones que se llaman doStuff()
    Diseñá para fallar elegantemente, como un pingüino resbalando con estilo
    Documentá bien. Que lo pueda leer tu "yo" del futuro sin odiarte
    Dividí el sistema en microservicios basados en dominios de negocio claros

🌊 Final Words

Los sistemas monolíticos tuvieron su época. Como los CD-ROM.

Ahora, el futuro es modular, distribuido, escalable y lleno de pingüinos con laptops.

    Dividí el Mamut. Salvá el sistema. Convertite en leyenda.


CLIENTE
  │
  ├── POST /productos  ──────────────► PRODUCTS SERVICE (puerto 8001)
  │                                         │
  │                                         ▼
  │                                    products-db (PostgreSQL)
  │
  ├── POST /pedidos  ───────────────► ORDERS SERVICE (puerto 8002)
  │                                         │
  │                                    consulta precio y descuenta stock
  │                                         │
  │                                         ▼
  │                                    PRODUCTS SERVICE
  │                                         │
  │                                         ▼
  │                                    orders-db (PostgreSQL)
  │
  └── POST /pagos  ────────────────► PAYMENTS SERVICE (puerto 8003)
                                           │
                                      consulta pedido y marca como pagado
                                           │
                                           ▼
                                      ORDERS SERVICE
                                           │
                                           ▼
                                      payments-db (PostgreSQL)

📡 Endpoints
Products Service — http://host.docker.internal:8001/docs

MétodoEndpointAcciónPOST/productosCrear productoGET/productosListar todosGET/productos/{id}Obtener unoPUT/productos/{id}ActualizarDELETE/productos/{id}Eliminar

Orders Service — http://host.docker.internal:8002/docs

MétodoEndpointAcciónPOST/pedidosCrear pedidoGET/pedidosListar todosGET/pedidos/{id}Obtener unoPUT/pedidos/{id}Actualizar estadoDELETE/pedidos/{id}Eliminar

Payments Service — http://host.docker.internal:8003/docs

MétodoEndpointAcciónPOST/pagosProcesar pagoGET/pagosListar todosGET/pagos/{id}Obtener uno

🛡️ Resiliencia
Retry — cada servicio reintenta 3 veces antes de rendirse cuando no puede contactar a otro servicio
Circuit Breaker — después de 3 intentos fallidos devuelve error 503 en vez de colgar
Logs — cada servicio registra INFO, WARNING y ERROR en cada operación