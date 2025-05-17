import psycopg2
import psycopg2.extras
import os
from fastapi import FastAPI, HTTPException, status, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import date

app = FastAPI()

DB_HOST = "192.168.1.13"
DB_NAME = "opadi_db"
DB_USER = "opadi_user"
DB_PASS = "abc123.." # ¡TU CONTRASEÑA!

class DocumentoBase(BaseModel):
    titulo: str
    fecha: Optional[date] = None
    contenido: Optional[str] = None

class DocumentoCreate(DocumentoBase):
    pass

class DocumentoUpdate(DocumentoBase):
    titulo: Optional[str] = None

class Documento(DocumentoBase):
    id: int

    class Config:
        from_attributes = True

def get_db_connection():
    print("Intentando conectar a la base de datos...")
    conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS)
    print("Conexión a la base de datos exitosa!")
    return conn

@app.on_event("startup")
async def startup_event():
    print("--- Evento STARTUP iniciado ---")
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        print("Creando/verificando tabla 'documentos'...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS documentos (
                id SERIAL PRIMARY KEY,
                titulo VARCHAR(255) NOT NULL,
                fecha DATE,
                contenido TEXT
            );
        """)
        print("Tabla 'documentos' creada/verificada.")
        
        cur.execute("SELECT COUNT(*) FROM documentos;")
        count = cur.fetchone()[0]
        print(f"Número de documentos existentes: {count}")
        if count == 0:
            print("Insertando datos de ejemplo...")
            cur.execute("""
                INSERT INTO documentos (titulo, fecha, contenido) VALUES
                ('Manuscrito DB 1 (Startup)', '2024-01-01', 'Contenido del manuscrito 1...'),
                ('Pergamino DB 2 (Startup)', '2024-02-15', 'Contenido del pergamino 2...');
            """)
            print("Datos de ejemplo insertados.")
        conn.commit()
        cur.close()
        print("--- Evento STARTUP completado exitosamente ---")
    except psycopg2.OperationalError as db_conn_err:
         print(f"FATAL: No se pudo conectar a la base de datos durante el startup: {db_conn_err}")
    except Exception as e:
        print(f"Error inesperado durante el evento startup: {e}")
    finally:
        if conn:
            conn.close()
        print("--- Evento STARTUP finalizado (con o sin error) ---")

origins = [
    "https://openpadi.local", "http://openpadi.local",
    "http://localhost", "http://localhost:3000", "http://localhost:4173",
    "http://localhost:5173", "http://192.168.1.10",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Bienvenido a OpenPaDi API - Conectado a PostgreSQL"}

@app.get("/api/documentos", response_model=List[Documento])
async def get_documentos_db():
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT id, titulo, fecha, contenido FROM documentos ORDER BY id;")
        documentos_data = cur.fetchall()
        cur.close()
        return documentos_data
    except psycopg2.OperationalError as db_conn_err:
        print(f"Error de conexión al obtener documentos: {db_conn_err}")
        raise HTTPException(status_code=503, detail=f"Servicio de base de datos no disponible: {db_conn_err}")
    except psycopg2.Error as db_query_err:
        print(f"Error de base de datos al obtener documentos: {db_query_err}")
        raise HTTPException(status_code=500, detail=f"Error de base de datos: {db_query_err}")
    except Exception as e:
        print(f"Error inesperado al obtener documentos: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno inesperado del servidor: {e}")
    finally:
        if conn:
            conn.close()

@app.get("/api/documentos/{id_documento}", response_model=Documento)
async def get_documento_por_id(id_documento: int):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT id, titulo, fecha, contenido FROM documentos WHERE id = %s;", (id_documento,))
        documento_data = cur.fetchone()
        cur.close()
        if documento_data is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documento no encontrado")
        return documento_data
    except psycopg2.OperationalError as db_conn_err:
        print(f"Error de conexión al obtener documento por ID: {db_conn_err}")
        raise HTTPException(status_code=503, detail=f"Servicio de base de datos no disponible: {db_conn_err}")
    except psycopg2.Error as db_query_err:
        print(f"Error de base de datos al obtener documento por ID: {db_query_err}")
        raise HTTPException(status_code=500, detail=f"Error de base de datos: {db_query_err}")
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        print(f"Error inesperado al obtener documento por ID: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno inesperado del servidor: {e}")
    finally:
        if conn:
            conn.close()

@app.put("/api/documentos/{id_documento}", response_model=Documento)
async def update_documento_db(id_documento: int, documento_update: DocumentoUpdate):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cur.execute("SELECT id FROM documentos WHERE id = %s;", (id_documento,))
        documento_existente = cur.fetchone()
        if documento_existente is None:
            cur.close()
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documento no encontrado para actualizar")

        update_data = documento_update.model_dump(exclude_unset=True)
        if not update_data:
            cur.close()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se proporcionaron datos para actualizar")

        set_clause = ", ".join([f"{key} = %s" for key in update_data.keys()])
        values = list(update_data.values())
        values.append(id_documento) 

        query = f"UPDATE documentos SET {set_clause} WHERE id = %s RETURNING id, titulo, fecha, contenido;"
        
        cur.execute(query, tuple(values))
        documento_actualizado = cur.fetchone()
        conn.commit()
        cur.close()
        
        if documento_actualizado is None:
            raise HTTPException(status_code=500, detail="Error al actualizar el documento en la base de datos.")
        return documento_actualizado
        
    except psycopg2.OperationalError as db_conn_err:
        print(f"Error de conexión al actualizar documento: {db_conn_err}")
        raise HTTPException(status_code=503, detail=f"Servicio de base de datos no disponible: {db_conn_err}")
    except psycopg2.Error as db_err:
        if conn:
            conn.rollback()
        print(f"Error de base de datos al actualizar documento: {db_err}")
        raise HTTPException(status_code=400, detail=f"Error de base de datos: {db_err}")
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error inesperado al actualizar documento: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno inesperado del servidor: {e}")
    finally:
        if conn:
            conn.close()

@app.post("/api/documentos", response_model=Documento, status_code=status.HTTP_201_CREATED)
async def create_documento_db(documento: DocumentoCreate):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        cur.execute(
            """
            INSERT INTO documentos (titulo, fecha, contenido)
            VALUES (%s, %s, %s)
            RETURNING id, titulo, fecha, contenido; 
            """,
            (documento.titulo, documento.fecha, documento.contenido)
        )
        nuevo_documento = cur.fetchone()
        conn.commit()
        cur.close()
        if nuevo_documento is None:
            raise HTTPException(status_code=500, detail="No se pudo crear el documento en la base de datos.")
        return nuevo_documento
    except psycopg2.OperationalError as db_conn_err:
        print(f"Error de conexión al crear documento: {db_conn_err}")
        raise HTTPException(status_code=503, detail=f"Servicio de base de datos no disponible: {db_conn_err}")
    except psycopg2.Error as db_err:
        if conn:
            conn.rollback()
        print(f"Error de base de datos al crear documento: {db_err}")
        raise HTTPException(status_code=400, detail=f"Error de base de datos: {db_err}")
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error inesperado al crear documento: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno inesperado del servidor: {e}")
    finally:
        if conn:
            conn.close()

@app.delete("/api/documentos/{id_documento}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_documento_db(id_documento: int):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("SELECT id FROM documentos WHERE id = %s;", (id_documento,))
        documento_existente = cur.fetchone()
        if documento_existente is None:
            cur.close()
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documento no encontrado para eliminar")

        cur.execute("DELETE FROM documentos WHERE id = %s;", (id_documento,))
        conn.commit()
        cur.close()
        return Response(status_code=status.HTTP_204_NO_CONTENT) 
        
    except psycopg2.OperationalError as db_conn_err:
        print(f"Error de conexión al eliminar documento: {db_conn_err}")
        raise HTTPException(status_code=503, detail=f"Servicio de base de datos no disponible: {db_conn_err}")
    except psycopg2.Error as db_err:
        if conn:
            conn.rollback()
        print(f"Error de base de datos al eliminar documento: {db_err}")
        raise HTTPException(status_code=500, detail=f"Error de base de datos: {db_err}") # Podría ser 400 si es un error de constraint
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error inesperado al eliminar documento: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno inesperado del servidor: {e}")
    finally:
        if conn:
            conn.close()
