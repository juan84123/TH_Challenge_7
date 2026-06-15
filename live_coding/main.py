from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

productos = [
    {"id": 1, "nombre": "Laptop", "precio": 800},
    {"id": 2, "nombre": "Mouse", "precio": 20}
]

class ProductoEntrada(BaseModel):
    nombre: str
    precio: float

# escribí los endpoints acá
@app.get("/productos")
def listar_productos():
    return productos

@app.get("/productos/{id}")
def listar_producto_id(id: int):
    for p in productos:
        if["id"]== id:
            return p
    return {"error": "Producto no encontrado"}

@app.post("/productos", status_code=201)
def crear_producto(producto: ProductoEntrada):
    id_nuevo = productos[-1]["id"] + 1
    nuevo = {"id": id_nuevo, "nombre": producto.nombre, "precio": producto.precio}
    productos.append(nuevo)
    return nuevo

@app.put("/productos/{id}")
def actualizar_producto(id: int, producto: ProductoEntrada):
    for p in productos:
        if p["id"] == id:
            p["nombre"] = producto.nombre
            p["precio"] = producto.precio
            return p
    return {"error": "Producto no encontrado"}

@app.delete("/productos/{id}")
def eliminar_producto(id: int):
    for p in productos:
        if p["id"] == id:
            productos.remove(p)
            return {"mensaje": "Producto eliminado", "producto": p}
    return {"error": "Producto no encontrado"}