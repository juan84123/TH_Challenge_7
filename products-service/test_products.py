import requests

BASE_URL = "http://127.0.0.1:8001"
HEADERS = {"Authorization": "Bearer token_secreto_productos"}

# crear un producto
r = requests.post(f"{BASE_URL}/productos",
    json={"nombre": "Pinguino de peluche", "precio": 25.0, "stock": 100},
    headers=HEADERS
)
print("Crear producto:", r.status_code, r.json())

# listar productos
r = requests.get(f"{BASE_URL}/productos", headers=HEADERS)
print("Listar productos:", r.status_code, r.json())

# obtener por id
r = requests.get(f"{BASE_URL}/productos/1", headers=HEADERS)
print("Obtener producto 1:", r.status_code, r.json())

# actualizar producto
r = requests.put(f"{BASE_URL}/productos/1",
    json={"nombre": "Pinguino de peluche XL", "precio": 35.0, "stock": 50},
    headers=HEADERS
)
print("Actualizar producto:", r.status_code, r.json())

# eliminar producto
r = requests.delete(f"{BASE_URL}/productos/1", headers=HEADERS)
print("Eliminar producto:", r.status_code, r.json())

# token invalido
r = requests.get(f"{BASE_URL}/productos",
    headers={"Authorization": "Bearer token_falso"}
)
print("Token invalido:", r.status_code, r.json())