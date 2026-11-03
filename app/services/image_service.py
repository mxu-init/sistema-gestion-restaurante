import os
import uuid
from urllib.parse import urlparse
from fastapi import UploadFile

UPLOAD_DIR = "static/uploads"
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}

def save_dish_image(file: UploadFile) -> str:
    file_extension = os.path.splitext(file.filename or "")[1].lower()
    if file_extension not in ALLOWED_EXTENSIONS:
        raise ValueError("Tipo de archivo no permitido. Usa JPG, JPEG, PNG, WEBP o GIF")

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    with open(file_path, "wb") as buffer:
        buffer.write(file.file.read())

    return f"/static/uploads/{unique_filename}"

def validate_image_url(url: str) -> str:
    normalized = (url or "").strip()
    parsed = urlparse(normalized)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError("La imagen debe ser una URL válida que empiece por http:// o https://")
    return normalized