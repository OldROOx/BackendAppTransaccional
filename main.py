from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uuid
from typing import List, Optional

# Inicializamos la app
app = FastAPI(title="OptiScale API - Transaccional", version="1.0")

# Configuración de CORS (Crucial para probar Flutter Web)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- MODELO DE DATOS ---
class OpticProduct(BaseModel):
    id: Optional[str] = None
    name: str
    category: str
    price: float

# --- BASE DE DATOS SIMULADA (En memoria) ---
# Empezamos con un par de productos de prueba para que tu Flutter ya muestre algo
db = {
    "1": {"id": "1", "name": "Armazón Ray-Ban Aviator", "category": "Armazones", "price": 1250.00},
    "2": {"id": "2", "name": "Lente de Contacto Acuvue", "category": "Lentes de Contacto", "price": 450.00}
}

# --- ENDPOINTS (CRUD) ---

@app.get("/api/optics", response_model=List[OpticProduct])
def get_products():
    """Obtiene todos los productos ópticos (GET)"""
    return list(db.values())

@app.post("/api/optics", response_model=OpticProduct, status_code=201)
def create_product(product: OpticProduct):
    """Crea un nuevo producto óptico (POST)"""
    new_id = str(uuid.uuid4())
    new_product = product.dict()
    new_product["id"] = new_id
    db[new_id] = new_product
    return new_product

@app.put("/api/optics/{product_id}", response_model=OpticProduct)
def update_product(product_id: str, product: OpticProduct):
    """Actualiza un producto existente (PUT)"""
    if product_id not in db:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    updated_product = product.dict()
    updated_product["id"] = product_id # Aseguramos que el ID no cambie
    db[product_id] = updated_product
    return updated_product

@app.delete("/api/optics/{product_id}")
def delete_product(product_id: str):
    """Elimina un producto (DELETE)"""
    if product_id not in db:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    del db[product_id]
    return {"message": "Producto eliminado exitosamente"}