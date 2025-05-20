import psycopg2
import psycopg2.extras
import os
import uuid
import httpx
import logging
from fastapi import FastAPI, HTTPException, status, Response, File, UploadFile, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import date, timedelta, datetime
from minio import Minio
from minio.error import S3Error
from jose import JWTError, jwt
from jose.exceptions import JOSEError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

DB_HOST = "192.168.1.13"
DB_NAME = "opadi_db"
DB_USER = "opadi_user"
DB_PASS = "abc123.."

MINIO_ENDPOINT = "192.168.1.14:9000"
MINIO_ACCESS_KEY = "openpadiadmin"
MINIO_SECRET_KEY = "abc123.."
MINIO_BUCKET_NAME = "openpadi-documentos"
MINIO_USE_SSL = False

KEYCLOAK_OPENID_CONFIG_URL = "https://auth.openpadi.local/realms/openpadi/.well-known/openid-configuration"
KEYCLOAK_AUDIENCE = "account"
KEYCLOAK_ALGORITHMS = ["RS256"]

keycloak_public_keys = None
jwks_uri = None

async def get_keycloak_public_keys():
    global keycloak_public_keys, jwks_uri

    if not jwks_uri:
        async with httpx.AsyncClient(verify=False) as client:
            try:
                logger.info(f"LOGGING: Obteniendo configuración OpenID de: {KEYCLOAK_OPENID_CONFIG_URL}")
                oidc_response = await client.get(KEYCLOAK_OPENID_CONFIG_URL)
                oidc_response.raise_for_status()
                oidc_config = oidc_response.json()
                jwks_uri_temp = oidc_config.get("jwks_uri")
                if not jwks_uri_temp:
                    logger.error("LOGGING: Error: 'jwks_uri' no encontrado en la configuración OpenID de Keycloak.")
                    raise HTTPException(status_code=500, detail="Configuración de autenticación inválida (sin jwks_uri)")
                if jwks_uri is None:
                    jwks_uri = jwks_uri_temp
                logger.info(f"LOGGING: JWKS URI obtenido: {jwks_uri}")
            except httpx.RequestError as exc:
                logger.error(f"LOGGING: Error de HTTPX al obtener config OpenID: {exc}")
                raise HTTPException(status_code=503, detail=f"No se pudo conectar al servidor de autenticación: {exc}")
            except Exception as e:
                logger.error(f"LOGGING: Error inesperado al obtener config OpenID: {e}")
                raise HTTPException(status_code=500, detail=f"Error al procesar configuración de autenticación: {e}")

    if not jwks_uri:
        raise HTTPException(status_code=500, detail="No se pudo obtener el JWKS URI del servidor de autenticación")

    async with httpx.AsyncClient(verify=False) as client:
        try:
            logger.info(f"LOGGING: Obteniendo claves públicas JWKS de: {jwks_uri}")
            jwks_response = await client.get(jwks_uri)
            jwks_response.raise_for_status()
            keycloak_public_keys = jwks_response.json()
            logger.info("LOGGING: Claves públicas JWKS obtenidas y cacheadas (simplemente).")
            return keycloak_public_keys
        except httpx.RequestError as exc:
            logger.error(f"LOGGING: Error de HTTPX al obtener JWKS: {exc}")
            raise HTTPException(status_code=503, detail=f"No se pudo conectar al servidor de autenticación para obtener claves: {exc}")
        except Exception as e:
            logger.error(f"LOGGING: Error inesperado al obtener JWKS: {e}")
            raise HTTPException(status_code=500, detail=f"Error al procesar claves de autenticación: {e}")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="https://auth.openpadi.local/realms/openpadi/protocol/openid-connect/token")

async def get_current_user_token_payload(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    public_keys_data = await get_keycloak_public_keys()
    if not public_keys_data or "keys" not in public_keys_data:
        logger.error("LOGGING: Error: No se pudieron obtener las claves públicas de Keycloak o el formato es incorrecto.")
        raise credentials_exception

    try:
        unverified_header = jwt.get_unverified_header(token)
        rsa_key = {}
        for key_data in public_keys_data["keys"]:
            if key_data["kid"] == unverified_header["kid"]:
                rsa_key = {
                    "kty": key_data["kty"],
                    "kid": key_data["kid"],
                    "use": key_data["use"],
                    "n": key_data["n"],
                    "e": key_data["e"],
                }
                break
        
        if rsa_key:
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=KEYCLOAK_ALGORITHMS,
                audience=KEYCLOAK_AUDIENCE
            )
            username: str = payload.get("preferred_username")
            if username is None:
                logger.error("LOGGING: Error: preferred_username no encontrado en el payload del token.")
                raise credentials_exception
            logger.info(f"LOGGING: Token validado para el usuario: {username}")
            return payload
        else:
            logger.error("LOGGING: Error: No se encontró la clave pública correspondiente (kid) en JWKS.")
            raise credentials_exception
    except JWTError as e:
        logger.error(f"LOGGING: Error de JWT al decodificar/validar token: {e}")
        raise credentials_exception
    except JOSEError as e:
        logger.error(f"LOGGING: Error de JOSE (posiblemente formato de clave o token inválido): {e}")
        raise credentials_exception
    except Exception as e:
        logger.error(f"LOGGING: Error inesperado durante la validación del token: {e}")
        raise credentials_exception

try:
    minio_client = Minio(
        MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=MINIO_USE_SSL
    )
except Exception as e:
    logger.critical(f"LOGGING: FATAL: Error al inicializar el cliente MinIO: {e}")
    minio_client = None

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
    minio_object_key: Optional[str] = None

    class Config:
        from_attributes = True

def get_db_connection():
    logger.info("LOGGING: Intentando conectar a la base de datos PostgreSQL...")
    conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS)
    logger.info("LOGGING: Conexión a PostgreSQL exitosa!")
    return conn

@app.on_event("startup")
async def startup_event():
    logger.warning("LOGGING: --- INICIO DEL EVENTO STARTUP FastAPI ---")
    
    try:
        logger.warning("LOGGING: Intentando llamar a get_keycloak_public_keys desde startup...")
        await get_keycloak_public_keys() 
        logger.warning("LOGGING: Llamada a get_keycloak_public_keys desde startup completada (sin error explicito).")
        logger.warning("LOGGING: Configuración OpenID y JWKS URI verificados/precargados en startup (si la llamada anterior tuvo éxito).")
    except HTTPException as http_exc:
        logger.error(f"LOGGING: HTTPException durante precarga de Keycloak en startup: {http_exc.status_code} - {http_exc.detail}")
    except Exception as e:
        logger.error(f"LOGGING: EXCEPCIÓN GENERAL durante precarga de Keycloak en startup: TIPO={type(e)}, MSG={e}")
    
    logger.info("LOGGING: Continuando con la inicialización de MinIO...")
    if minio_client:
        try:
            logger.info(f"LOGGING: Verificando/creando bucket MinIO: {MINIO_BUCKET_NAME}")
            found = minio_client.bucket_exists(MINIO_BUCKET_NAME)
            if not found:
                minio_client.make_bucket(MINIO_BUCKET_NAME)
                logger.info(f"LOGGING: Bucket MinIO '{MINIO_BUCKET_NAME}' creado.")
            else:
                logger.info(f"LOGGING: Bucket MinIO '{MINIO_BUCKET_NAME}' ya existe.")
        except S3Error as s3_err:
            logger.error(f"LOGGING: Error S3 durante la verificación/creación del bucket MinIO: {s3_err}")
        except Exception as e:
            logger.error(f"LOGGING: Error general durante la configuración de MinIO en startup: {e}")
    else:
        logger.warning("LOGGING: Cliente MinIO no inicializado en startup.")
    
    logger.info("LOGGING: Continuando con la inicialización de PostgreSQL...")
    conn_pg = None
    try:
        conn_pg = get_db_connection()
        cur = conn_pg.cursor()
        logger.info("LOGGING: Creando/verificando tabla 'documentos' en PostgreSQL...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS documentos (
                id SERIAL PRIMARY KEY,
                titulo VARCHAR(255) NOT NULL,
                fecha DATE,
                contenido TEXT,
                minio_object_key VARCHAR(255) NULL
            );
        """)
        logger.info("LOGGING: Tabla 'documentos' en PostgreSQL creada/verificada.")
        cur.execute("SELECT COUNT(*) FROM documentos;")
        count = cur.fetchone()[0]
        logger.info(f"LOGGING: Número de documentos existentes en PostgreSQL: {count}")
        if count == 0:
            logger.info("LOGGING: Insertando datos de ejemplo en PostgreSQL...")
            cur.execute("""
                INSERT INTO documentos (titulo, fecha, contenido) VALUES
                ('Manuscrito DB 1 (Startup)', '2024-01-01', 'Contenido del manuscrito 1...'),
                ('Pergamino DB 2 (Startup)', '2024-02-15', 'Contenido del pergamino 2...');
            """)
            logger.info("LOGGING: Datos de ejemplo insertados en PostgreSQL.")
        conn_pg.commit()
        cur.close()
        logger.info("LOGGING: --- Evento STARTUP FastAPI (PostgreSQL) completado exitosamente ---")
    except psycopg2.OperationalError as db_conn_err:
         logger.critical(f"LOGGING: FATAL: No se pudo conectar a PostgreSQL durante el startup: {db_conn_err}")
    except Exception as e:
        logger.error(f"LOGGING: Error inesperado durante el startup (PostgreSQL): {e}")
    finally:
        if conn_pg:
            conn_pg.close()
        logger.warning("LOGGING: --- FIN DEL EVENTO STARTUP FastAPI ---")

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
    return {"message": "Bienvenido a OpenPaDi API - Conectado a PostgreSQL y MinIO"}

@app.get("/api/documentos", response_model=List[Documento])
async def get_documentos_db():
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT id, titulo, fecha, contenido, minio_object_key FROM documentos ORDER BY id;")
        documentos_data = cur.fetchall()
        cur.close()
        return documentos_data
    except psycopg2.OperationalError as db_conn_err:
        raise HTTPException(status_code=503, detail=f"Servicio de base de datos no disponible: {db_conn_err}")
    except psycopg2.Error as db_query_err:
        raise HTTPException(status_code=500, detail=f"Error de base de datos: {db_query_err}")
    except Exception as e:
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
        cur.execute("SELECT id, titulo, fecha, contenido, minio_object_key FROM documentos WHERE id = %s;", (id_documento,))
        documento_data = cur.fetchone()
        cur.close()
        if documento_data is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documento no encontrado")
        return documento_data
    except psycopg2.OperationalError as db_conn_err:
        raise HTTPException(status_code=503, detail=f"Servicio de base de datos no disponible: {db_conn_err}")
    except psycopg2.Error as db_query_err:
        raise HTTPException(status_code=500, detail=f"Error de base de datos: {db_query_err}")
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno inesperado del servidor: {e}")
    finally:
        if conn:
            conn.close()

@app.put("/api/documentos/{id_documento}", response_model=Documento)
async def update_documento_db(
    id_documento: int, 
    documento_update: DocumentoUpdate,
    current_user_payload: dict = Depends(get_current_user_token_payload)
):
    logger.info(f"LOGGING: Usuario '{current_user_payload.get('preferred_username')}' actualizando documento ID: {id_documento}")
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT id FROM documentos WHERE id = %s;", (id_documento,))
        if cur.fetchone() is None:
            cur.close()
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documento no encontrado para actualizar")
        update_data = documento_update.model_dump(exclude_unset=True)
        if not update_data:
            cur.close()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se proporcionaron datos para actualizar")
        set_clause = ", ".join([f"{key} = %s" for key in update_data.keys()])
        values = list(update_data.values())
        values.append(id_documento) 
        query = f"UPDATE documentos SET {set_clause} WHERE id = %s RETURNING id, titulo, fecha, contenido, minio_object_key;"
        cur.execute(query, tuple(values))
        documento_actualizado = cur.fetchone()
        conn.commit()
        cur.close()
        if documento_actualizado is None:
             raise HTTPException(status_code=500, detail="Error al actualizar el documento.")
        return documento_actualizado
    except psycopg2.OperationalError as db_conn_err:
        raise HTTPException(status_code=503, detail=f"Servicio de base de datos no disponible: {db_conn_err}")
    except psycopg2.Error as db_err:
        if conn: conn.rollback()
        raise HTTPException(status_code=400, detail=f"Error de base de datos: {db_err}")
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        if conn: conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno inesperado del servidor: {e}")
    finally:
        if conn:
            conn.close()

@app.post("/api/documentos", response_model=Documento, status_code=status.HTTP_201_CREATED)
async def create_documento_db(
    titulo: str = File(...),
    fecha: Optional[date] = File(None), 
    contenido: Optional[str] = File(None), 
    archivo: Optional[UploadFile] = File(None),
    current_user_payload: dict = Depends(get_current_user_token_payload)
):
    logger.info(f"LOGGING: Usuario '{current_user_payload.get('preferred_username')}' creando documento.")
    conn = None
    minio_key_guardada = None
    try:
        if archivo and minio_client:
            extension = os.path.splitext(archivo.filename)[1]
            minio_key_guardada = f"{uuid.uuid4()}{extension}"
            try:
                minio_client.put_object(
                    MINIO_BUCKET_NAME,
                    minio_key_guardada,
                    archivo.file,
                    length=-1,
                    part_size=10*1024*1024,
                    content_type=archivo.content_type
                )
            except S3Error as s3_err:
                raise HTTPException(status_code=500, detail=f"Error al subir el archivo: {s3_err}")
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error general al subir el archivo: {e}")
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            """
            INSERT INTO documentos (titulo, fecha, contenido, minio_object_key)
            VALUES (%s, %s, %s, %s)
            RETURNING id, titulo, fecha, contenido, minio_object_key; 
            """,
            (titulo, fecha, contenido, minio_key_guardada)
        )
        nuevo_documento = cur.fetchone()
        conn.commit()
        cur.close()
        if nuevo_documento is None:
            raise HTTPException(status_code=500, detail="No se pudo crear el documento en la base de datos.")
        return nuevo_documento
    except psycopg2.OperationalError as db_conn_err:
        raise HTTPException(status_code=503, detail=f"Servicio de base de datos no disponible: {db_conn_err}")
    except psycopg2.Error as db_err:
        if conn: conn.rollback()
        raise HTTPException(status_code=400, detail=f"Error de base de datos: {db_err}")
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        if conn: conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno inesperado del servidor: {e}")
    finally:
        if conn:
            conn.close()

@app.delete("/api/documentos/{id_documento}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_documento_db(
    id_documento: int,
    current_user_payload: dict = Depends(get_current_user_token_payload)
):
    logger.info(f"LOGGING: Usuario '{current_user_payload.get('preferred_username')}' eliminando documento ID: {id_documento}")
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT minio_object_key FROM documentos WHERE id = %s;", (id_documento,))
        documento_a_borrar = cur.fetchone()
        if documento_a_borrar is None:
            cur.close()
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documento no encontrado para eliminar")
        minio_key_a_borrar = documento_a_borrar.get("minio_object_key")
        cur.execute("DELETE FROM documentos WHERE id = %s;", (id_documento,))
        conn.commit()
        cur.close()
        if minio_key_a_borrar and minio_client:
            try:
                minio_client.remove_object(MINIO_BUCKET_NAME, minio_key_a_borrar)
            except S3Error as s3_err:
                logger.error(f"LOGGING: Error S3 al eliminar archivo '{minio_key_a_borrar}' de MinIO (el registro de la BBDD se eliminó de todas formas): {s3_err}")
            except Exception as e:
                 logger.error(f"LOGGING: Error general al eliminar archivo '{minio_key_a_borrar}' de MinIO: {e}")
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except psycopg2.OperationalError as db_conn_err:
        raise HTTPException(status_code=503, detail=f"Servicio de base de datos no disponible: {db_conn_err}")
    except psycopg2.Error as db_err:
        if conn: conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error de base de datos: {db_err}")
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        if conn: conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno inesperado del servidor: {e}")
    finally:
        if conn:
            conn.close()

@app.get("/api/documentos/{id_documento}/archivo")
async def get_archivo_documento(id_documento: int):
    if not minio_client:
        raise HTTPException(status_code=503, detail="Servicio de almacenamiento MinIO no disponible.")
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT minio_object_key, titulo FROM documentos WHERE id = %s;", (id_documento,))
        documento_data = cur.fetchone()
        cur.close()
        if documento_data is None or documento_data.get("minio_object_key") is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Archivo no encontrado para este documento.")
        object_key = documento_data["minio_object_key"]
        base_titulo = documento_data.get("titulo", "documento")
        nombre_archivo_limpio = "".join(c if c.isalnum() or c in (' ', '.', '-') else '_' for c in base_titulo).rstrip()
        extension_archivo = os.path.splitext(object_key)[1]
        nombre_archivo_sugerido_para_descarga = f"{nombre_archivo_limpio}{extension_archivo}"
        try:
            response_headers = {
                "response-content-disposition": f'attachment; filename="{nombre_archivo_sugerido_para_descarga}"'
            }
            presigned_url = minio_client.presigned_get_object(
                MINIO_BUCKET_NAME,
                object_key,
                expires=timedelta(hours=1),
                response_headers=response_headers
            )
            return {"url_descarga": presigned_url}
        except S3Error as s3_err:
            raise HTTPException(status_code=500, detail=f"Error al obtener URL de descarga: {s3_err}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error general al obtener URL de descarga: {e}")
    except psycopg2.OperationalError as db_conn_err:
        raise HTTPException(status_code=503, detail=f"Servicio de base de datos no disponible: {db_conn_err}")
    except psycopg2.Error as db_query_err:
        raise HTTPException(status_code=500, detail=f"Error de base de datos: {db_query_err}")
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno inesperado del servidor: {e}")
    finally:
        if conn:
            conn.close()
