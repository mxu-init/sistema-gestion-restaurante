import json
import logging
import os
import sys
import urllib.error
import urllib.request
import uuid

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)
import app.core.database_connection


class OnlyWarnings(logging.Filter):
    def filter(self, record):
        return record.levelno >= logging.WARNING


logging.getLogger("sqlalchemy.engine.Engine").addFilter(OnlyWarnings())

BASE_URL = os.environ.get("E2E_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
TEST_PREFIX = "E2E Smoke Test"

PASSED = 0
FAILED = 0


def check(label, condition, extra=""):
    global PASSED, FAILED
    if condition:
        PASSED += 1
        print(f"  PASS  {label}")
    else:
        FAILED += 1
        print(f"  FAIL  {label} {extra}")


def request(method, path, body=None, headers=None):
    req = urllib.request.Request(
        f"{BASE_URL}{path}", data=body, method=method, headers=headers or {}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            status, data = resp.status, resp.read()
    except urllib.error.HTTPError as exc:
        status, data = exc.code, exc.read()
    text = data.decode("utf-8", "replace")
    try:
        return status, json.loads(text) if text else None
    except json.JSONDecodeError:
        return status, text


def get(path):
    return request("GET", path)


def post_json(path, payload):
    return request(
        "POST", path, json.dumps(payload).encode(),
        {"Content-Type": "application/json"},
    )


def put_json(path, payload):
    return request(
        "PUT", path, json.dumps(payload).encode(),
        {"Content-Type": "application/json"},
    )


def delete(path):
    return request("DELETE", path)


def post_form(fields, files=None):
    body, content_type = multipart(fields, files or {})
    return request("POST", "/dishes/", body, {"Content-Type": content_type})


def multipart(fields, files):
    boundary = f"----e2e{uuid.uuid4().hex}"
    chunks = []
    for key, value in fields.items():
        chunks.append(
            f'--{boundary}\r\nContent-Disposition: form-data; name="{key}"\r\n\r\n{value}\r\n'.encode()
        )
    for key, (filename, content) in files.items():
        chunks.append(
            f'--{boundary}\r\nContent-Disposition: form-data; name="{key}"; filename="{filename}"\r\n'
            f"Content-Type: application/octet-stream\r\n\r\n".encode()
        )
        chunks.append(content)
        chunks.append(b"\r\n")
    chunks.append(f"--{boundary}--\r\n".encode())
    return b"".join(chunks), f"multipart/form-data; boundary={boundary}"


def cleanup_test_rows():
    from sqlalchemy import text
    from app.core.database_connection import session_local

    db = session_local()
    try:
        rows = db.execute(
            text("SELECT id, image FROM dishes WHERE name LIKE :prefix"),
            {"prefix": f"{TEST_PREFIX}%"},
        ).fetchall()
        for _, image in rows:
            if image and image.startswith("/static/uploads/"):
                file_path = os.path.join(ROOT, "static", "uploads", os.path.basename(image))
                if os.path.exists(file_path):
                    os.remove(file_path)
        db.execute(
            text("DELETE FROM dishes WHERE name LIKE :prefix"),
            {"prefix": f"{TEST_PREFIX}%"},
        )
        db.commit()
        return len(rows)
    finally:
        db.close()


def db_dish_state(dish_id):
    from sqlalchemy import text
    from app.core.database_connection import session_local

    db = session_local()
    try:
        return db.execute(
            text("SELECT deleted_at FROM dishes WHERE id = :id"), {"id": dish_id}
        ).first()
    finally:
        db.close()


def main():
    print(f"== E2E CRUD de platos contra {BASE_URL} ==\n")

    removed = cleanup_test_rows()
    if removed:
        print(f"  INFO  limpiados {removed} plato(s) de ejecuciones anteriores\n")

    print("-- Setup --")
    status, categories = get("/categories/")
    check("GET /categories/ responde 200", status == 200, f"(got {status})")
    if status != 200 or not categories:
        print("  No hay categorias, abortando.")
        return 1
    category = next(
        (c for c in categories if c["name"].lower() == "bebidas"), categories[0]
    )
    category_id = category["id"]

    status, dishes = get("/dishes/")
    other = next(
        (d for d in dishes if d["category_id"] == category_id), None
    )

    test_name = f"{TEST_PREFIX} {uuid.uuid4().hex[:8]}"
    image_filename = None

    try:
        print("\n-- CREATE --")
        body, content_type = multipart(
            {"name": test_name, "description": "plato de prueba", "price": "1.99",
             "category_id": str(category_id), "is_available": "true"},
            {"file": ("plato.jpg", b"\xff\xd8\xff\xe0fake-jpeg-bytes")},
        )
        status, created = request(
            "POST", "/dishes/", body, {"Content-Type": content_type}
        )
        check("POST /dishes/ crea el plato -> 201", status == 201, f"(got {status})")
        if status != 201:
            print(f"        respuesta: {created}")
            return 1
        dish_id = created["id"]
        check("la respuesta trae id", isinstance(dish_id, int))
        check("image apunta a /static/uploads/", str(created.get("image", "")).startswith("/static/uploads/"), f"(got {created.get('image')})")
        image_filename = os.path.basename(created.get("image") or "")
        image_path = os.path.join(ROOT, "static", "uploads", image_filename)
        check("el archivo de imagen existe en disco", os.path.exists(image_path))

        print("\n-- READ --")
        status, listed = get("/dishes/")
        check("GET /dishes/ lista el plato nuevo", status == 200 and any(d["id"] == dish_id for d in listed))
        status, fetched = get(f"/dishes/{dish_id}")
        check("GET /dishes/{id} devuelve el plato", status == 200 and fetched.get("name") == test_name)

        print("\n-- UPDATE --")
        status, updated = put_json(f"/dishes/{dish_id}", {"price": 2.49, "description": "actualizado"})
        check("PUT /dishes/{id} responde 200", status == 200, f"(got {status})")
        status, fetched = get(f"/dishes/{dish_id}")
        price_ok = status == 200 and abs(float(fetched.get("price", 0)) - 2.49) < 0.001
        check("el precio quedo en 2.49", price_ok, f"(got {fetched.get('price')})")

        print("\n-- Validaciones --")
        status, _ = post_form(
            {"name": test_name.upper(), "price": "1.0", "category_id": str(category_id)}
        )
        check("POST duplicado (mayusculas) -> 409", status == 409, f"(got {status})")
        status, _ = post_form(
            {"name": "   ", "price": "1.0", "category_id": str(category_id)}
        )
        check("POST nombre vacio -> 400", status == 400, f"(got {status})")
        body, content_type = multipart(
            {"name": f"{test_name} exe", "price": "1.0", "category_id": str(category_id)},
            {"file": ("malware.exe", b"MZ-fake")},
        )
        status, _ = request("POST", "/dishes/", body, {"Content-Type": content_type})
        check("POST imagen .exe -> 400", status == 400, f"(got {status})")
        status, _ = put_json(f"/dishes/{dish_id}", {"category_id": 999999})
        check("PUT categoria inexistente -> 400", status == 400, f"(got {status})")
        status, _ = put_json(f"/dishes/{dish_id}", {"name": None})
        check("PUT name null -> 400", status == 400, f"(got {status})")
        if other:
            status, _ = put_json(f"/dishes/{dish_id}", {"name": other["name"].swapcase()})
            check("PUT renombrado a plato existente -> 409", status == 409, f"(got {status})")
        else:
            print("  SKIP  PUT duplicado (no hay otro plato activo en la categoria)")
        status, _ = get("/dishes/?skip=-1")
        check("GET skip=-1 -> 422", status == 422, f"(got {status})")
        status, _ = get("/dishes/?limit=999")
        check("GET limit=999 -> 422", status == 422, f"(got {status})")
        status, _ = delete("/dishes/999999")
        check("DELETE inexistente -> 404", status == 404, f"(got {status})")

        print("\n-- DELETE --")
        status, _ = delete(f"/dishes/{dish_id}")
        check("DELETE /dishes/{id} -> 204", status == 204, f"(got {status})")
        status, _ = get(f"/dishes/{dish_id}")
        check("GET del plato borrado -> 404", status == 404, f"(got {status})")
        status, listed = get("/dishes/")
        check("ya no aparece en /dishes/", status == 200 and not any(d["id"] == dish_id for d in listed))
        status, category_data = get(f"/categories/{category_id}/dishes")
        check(
            "ya no aparece en /categories/{id}/dishes",
            status == 200 and not any(d["id"] == dish_id for d in category_data.get("dishes", [])),
        )
        row = db_dish_state(dish_id)
        check("deleted_at poblado en la BD", row is not None and row.deleted_at is not None, f"(got {row})")
        status, _ = delete(f"/dishes/{dish_id}")
        check("DELETE repetido -> 410", status == 410, f"(got {status})")

        print("\n-- RESTORE --")
        status, restored = post_json(f"/dishes/{dish_id}/restore", {})
        check("POST restore -> 200", status == 200, f"(got {status})")
        check("restaurado con deleted_at null", status == 200 and restored.get("deleted_at") is None)
        status, listed = get("/dishes/")
        check("vuelve a aparecer en /dishes/", status == 200 and any(d["id"] == dish_id for d in listed))
        status, _ = post_json(f"/dishes/{dish_id}/restore", {})
        check("restore de plato ya activo -> 409", status == 409, f"(got {status})")
        status, _ = post_json("/dishes/999999/restore", {})
        check("restore inexistente -> 404", status == 404, f"(got {status})")

        print("\n-- DELETE final --")
        status, _ = delete(f"/dishes/{dish_id}")
        check("DELETE final -> 204", status == 204, f"(got {status})")
    finally:
        print("\n-- Limpieza --")
        removed = cleanup_test_rows()
        check("datos de prueba eliminados de la BD", removed >= 1, f"(removed={removed})")
        if image_filename:
            image_path = os.path.join(ROOT, "static", "uploads", image_filename)
            leftover = os.path.exists(image_path)
            if leftover:
                os.remove(image_path)
            check("imagen de prueba eliminada de disco", not leftover)

    print(f"\n== Resultado: {PASSED} PASS, {FAILED} FAIL ==")
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
