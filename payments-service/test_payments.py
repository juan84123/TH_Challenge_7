import requests

BASE_URL = "http://127.0.0.1:8003"
HEADERS = {"Authorization": "Bearer token_secreto_payments"}

# procesar un pago
r = requests.post(f"{BASE_URL}/pagos",
    json={"pedido_id": 3},
    headers=HEADERS
)
print("Procesar pago:", r.status_code, r.json())

# intentar pagar el mismo pedido de nuevo
r = requests.post(f"{BASE_URL}/pagos",
    json={"pedido_id": 3},
    headers=HEADERS
)
print("Pagar dos veces:", r.status_code, r.json())

# listar pagos
r = requests.get(f"{BASE_URL}/pagos", headers=HEADERS)
print("Listar pagos:", r.status_code, r.json())

# obtener por id
r = requests.get(f"{BASE_URL}/pagos/1", headers=HEADERS)
print("Obtener pago 1:", r.status_code, r.json())

# token invalido
r = requests.get(f"{BASE_URL}/pagos",
    headers={"Authorization": "Bearer token_falso"}
)
print("Token invalido:", r.status_code, r.json())