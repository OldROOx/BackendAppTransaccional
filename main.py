"""
OptiScale API - Transaccional
=============================
Backend en FastAPI con:
  - CRUD de productos ópticos (/api/optics)
  - Autenticación: registro y login (/api/auth/register, /api/auth/login)
  - Almacenamiento en memoria (sin BD persistente; al reiniciar Render se borra)
  - CORS abierto para Flutter Web/móvil

Estructura monolítica intencional (un solo archivo) para deploy trivial.
"""

import uuid
from typing import Dict, List, Optional

from fastapi import FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# App + CORS
# ---------------------------------------------------------------------------
app = FastAPI(title="OptiScale API - Transaccional", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Modelos (Pydantic)
# ---------------------------------------------------------------------------
class OpticProduct(BaseModel):
    id: Optional[str] = None
    name: str
    category: str
    price: float


class RegisterRequest(BaseModel):
    name: str
    email: str
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class UserPublic(BaseModel):
    """Datos de usuario que sí se devuelven al cliente (sin password)."""
    id: str
    name: str
    email: str
    username: str


class AuthResponse(BaseModel):
    """Respuesta del login y del registro: usuario + token."""
    user: UserPublic
    accessToken: str


# ---------------------------------------------------------------------------
# "Base de datos" en memoria
# ---------------------------------------------------------------------------
products_db: Dict[str, dict] = {
    "1": {"id": "1", "name": "Armazón Ray-Ban Aviator",
          "category": "Armazones", "price": 1250.00},
    "2": {"id": "2", "name": "Lente de Contacto Acuvue",
          "category": "Lentes de Contacto", "price": 450.00},
}

# Usuarios indexados por username. Password en texto plano porque es un
# proyecto académico. En producción se haría hashing (bcrypt/argon2).
users_db: Dict[str, dict] = {
    "admin": {
        "id": "u-admin",
        "name": "Administrador Demo",
        "email": "admin@optiscale.mx",
        "username": "admin",
        "password": "admin123",
    }
}

# Mapa token -> username (sesiones activas en memoria).
tokens_db: Dict[str, str] = {}


def _public_user(user: dict) -> UserPublic:
    """Convierte el usuario interno (con password) en su versión pública."""
    return UserPublic(
        id=user["id"], name=user["name"],
        email=user["email"], username=user["username"],
    )


def _resolve_user(authorization: Optional[str]) -> dict:
    """Valida el header 'Authorization: Bearer <token>' y devuelve el usuario."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Token no proporcionado")
    token = authorization.split(" ", 1)[1].strip()
    username = tokens_db.get(token)
    if not username or username not in users_db:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")
    return users_db[username]


# ---------------------------------------------------------------------------
# AUTH endpoints
# ---------------------------------------------------------------------------
@app.post("/api/auth/register",
          response_model=AuthResponse,
          status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest):
    """Crea un nuevo usuario y devuelve sus datos + token."""
    if body.username in users_db:
        raise HTTPException(status_code=409,
                            detail="El usuario ya está registrado")

    new_user = {
        "id": f"u-{uuid.uuid4().hex[:8]}",
        "name": body.name,
        "email": body.email,
        "username": body.username,
        "password": body.password,
    }
    users_db[body.username] = new_user

    token = uuid.uuid4().hex
    tokens_db[token] = body.username

    return AuthResponse(user=_public_user(new_user), accessToken=token)


@app.post("/api/auth/login", response_model=AuthResponse)
def login(body: LoginRequest):
    """Verifica credenciales y devuelve usuario + token."""
    user = users_db.get(body.username)
    if not user or user["password"] != body.password:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    token = uuid.uuid4().hex
    tokens_db[token] = body.username
    return AuthResponse(user=_public_user(user), accessToken=token)


@app.get("/api/auth/me", response_model=UserPublic)
def me(authorization: Optional[str] = Header(default=None)):
    """Devuelve el usuario asociado al token (sirve para validar sesión)."""
    user = _resolve_user(authorization)
    return _public_user(user)


# ---------------------------------------------------------------------------
# OPTICS endpoints (CRUD)
# ---------------------------------------------------------------------------
@app.get("/api/optics", response_model=List[OpticProduct])
def get_products():
    """Obtiene todos los productos ópticos (GET)."""
    return list(products_db.values())


@app.post("/api/optics",
          response_model=OpticProduct,
          status_code=status.HTTP_201_CREATED)
def create_product(product: OpticProduct):
    """Crea un nuevo producto óptico (POST). El ID lo asigna el servidor."""
    new_id = str(uuid.uuid4())
    new_product = product.dict()
    new_product["id"] = new_id
    products_db[new_id] = new_product
    return new_product


@app.put("/api/optics/{product_id}", response_model=OpticProduct)
def update_product(product_id: str, product: OpticProduct):
    """Actualiza un producto existente (PUT). El ID no cambia."""
    if product_id not in products_db:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    updated = product.dict()
    updated["id"] = product_id
    products_db[product_id] = updated
    return updated


@app.delete("/api/optics/{product_id}")
def delete_product(product_id: str):
    """Elimina un producto (DELETE)."""
    if product_id not in products_db:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    del products_db[product_id]
    return {"message": "Producto eliminado exitosamente"}