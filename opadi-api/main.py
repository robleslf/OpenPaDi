from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Lista de orígenes permitidos.
origins = [
    "https://openpadi.local",
    "http://openpadi.local",
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:4173",
    "http://localhost:5173",
    "http://192.168.1.10",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Bienvenido a OpenPaDi API"}

@app.get("/api/documentos")
async def get_documentos():
    return [
        {"id": 1, "titulo": "Manuscrito Visigótico Ejemplo 1 (desde API)", "fecha": "2025-01-15"},
        {"id": 2, "titulo": "Pergamino Carolingio Ejemplo 2 (desde API)", "fecha": "2025-02-20"},
        {"id": 3, "titulo": "Códice Antiguo Ejemplo 3 (desde API)", "fecha": "2025-03-10"}
    ]

