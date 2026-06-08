import requests

BASE_URL = "http://127.0.0.1:8002"
HEADERS = {"Authorization": "Bearer token_secreto_orders"}

# crear un pedido
r = requests.post(f"{BASE_URL}/pedidos",
    json={"producto_id": 4, "cantidad": 3},
    headers=HEADERS
)
print("Crear pedido:", r.status_code, r.json())

# listar pedidos
r = requests.get(f"{BASE_URL}/pedidos", headers=HEADERS)
print("Listar pedidos:", r.status_code, r.json())

# obtener por id
r = requests.get(f"{BASE_URL}/pedidos/1", headers=HEADERS)
print("Obtener pedido 1:", r.status_code, r.json())

# actualizar estado
r = requests.put(f"{BASE_URL}/pedidos/1",
    json={"estado": "pagado"},
    headers=HEADERS
)
print("Actualizar estado:", r.status_code, r.json())

# eliminar pedido
r = requests.delete(f"{BASE_URL}/pedidos/1", headers=HEADERS)
print("Eliminar pedido:", r.status_code, r.json())

# token invalido
r = requests.get(f"{BASE_URL}/pedidos",
    headers={"Authorization": "Bearer token_falso"}
)
print("Token invalido:", r.status_code, r.json())