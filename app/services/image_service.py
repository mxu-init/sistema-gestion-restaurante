import os
import uuid
from fastapi import UploadFile

UPLOAD_DIR = "static/uploads"

def save_dish_image(file: UploadFile) -> str:
    try:
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)

        with open(file_path, "wb") as buffer:
            buffer.write(file.file.read())

        return f"/{file_path}"
    except Exception:
        raise Exception("Falla al registrar la imagen")