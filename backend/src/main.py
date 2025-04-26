from fastapi import FastAPI, UploadFile, HTTPException
from minio import Minio
from minio.error import S3Error

app = FastAPI()

# Configuración de MinIO (usar "minio:9000" si está en Docker)
minio_client = Minio(
    "minio:9000",
    access_key="minioadmin",
    secret_key="minioadmin",
    secure=False
)

@app.post("/upload")
async def upload_file(file: UploadFile):
    try:
        # Verificar y crear el bucket si no existe
        if not minio_client.bucket_exists("documentos"):
            minio_client.make_bucket("documentos")
        
        # Subir el archivo
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
