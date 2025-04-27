from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware  # <-- Añadido
from minio import Minio
from minio.error import S3Error

app = FastAPI()

# Configuración CORS (Nuevo)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuración de MinIO
minio_client = Minio(
    "minio:9000",
    access_key="minioadmin",
    secret_key="minioadmin",
    secure=False
)

@app.post("/upload")
async def upload_file(file: UploadFile):
    try:
        if not minio_client.bucket_exists("documentos"):
            minio_client.make_bucket("documentos")

        minio_client.put_object(
            "documentos",
            file.filename,
            file.file,
            file.size
        )
        return {"status": "ok"}
    except S3Error as e:
        raise HTTPException(status_code=500, detail=f"Error de MinIO: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
