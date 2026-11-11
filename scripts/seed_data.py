from app.core.database_connection import session_local
from app.core.reference_data import BASE_CATEGORIES
from app.core.security import get_password_hash
from app.models import CategoryModel, DishModel, UserModel

INITIAL_USERS = [
    {"name": "Administrador", "email": "admin@restaurante.com", "password": "admin123", "role": "admin", "is_active": True},
    {"name": "Mesero", "email": "mesero@restaurante.com", "password": "mesero123", "role": "mesero", "is_active": True},
    {"name": "Mesero Inactivo", "email": "inactivo@restaurante.com", "password": "inactivo123", "role": "mesero", "is_active": False},
]

def run_seed():
    db = session_local()
    try:
        for user_item in INITIAL_USERS:
            user_exists = db.query(UserModel).filter(UserModel.email == user_item["email"]).first()
            if not user_exists:
                db.add(
                    UserModel(
                        name=user_item["name"],
                        email=user_item["email"],
                        password_hash=get_password_hash(user_item["password"]),
                        role=user_item["role"],
                        is_active=user_item["is_active"],
                    )
                )

        categories_map = {}

        for category_name in BASE_CATEGORIES:
            category_db = db.query(CategoryModel).filter(CategoryModel.name == category_name).first()
            if not category_db:
                raise RuntimeError(
                    f"Base category '{category_name}' is missing, run 'alembic upgrade head' first"
                )
            categories_map[category_name] = category_db.id

        initial_dishes = [
            # Entrantes (3)
            {
                "name": "Nachos con Queso",
                "description": "Nachos con queso derregado y guacamole",
                "price": 5.50,
                "category_id": categories_map["Entrantes"]
            },
            {
                "name": "Alitas de Pollo",
                "description": "Alitas de pollo fritas con salsa BBQ",
                "price": 6.00,
                "category_id": categories_map["Entrantes"]
            },
            {
                "name": "Calamares Fritos",
                "description": "Calamares empanados con salsa tártara",
                "price": 7.00,
                "category_id": categories_map["Entrantes"]
            },
            # Primeros (3)
            {
                "name": "Ensalada César",
                "description": "Lechuga romana, pollo y aderezo césar",
                "price": 6.50,
                "category_id": categories_map["Primeros"]
            },
            {
                "name": "Sopa de Tomate",
                "description": "Sopa cremosa de tomate con albahaca",
                "price": 5.00,
                "category_id": categories_map["Primeros"]
            },
            {
                "name": "Bruschetta",
                "description": "Pan tostado con tomate, ajo y albahaca",
                "price": 4.50,
                "category_id": categories_map["Primeros"]
            },
            # Segundos (3)
            {
                "name": "Pollo a la Plancha",
                "description": "Pechuga de pollo con verduras salteadas",
                "price": 8.75,
                "category_id": categories_map["Segundos"]
            },
            {
                "name": "Lomo de Res",
                "description": "Lomo sellado con papas rústicas y salsa",
                "price": 12.00,
                "category_id": categories_map["Segundos"]
            },
            {
                "name": "Salmón al Horno",
                "description": "Salmón con limón, eneldo y espárragos",
                "price": 13.50,
                "category_id": categories_map["Segundos"]
            },
            # Postres (3)
            {
                "name": "Tarta de Queso",
                "description": "Postre de la casa con mermelada",
                "price": 4.50,
                "category_id": categories_map["Postres"]
            },
            {
                "name": "Flan Casero",
                "description": "Flan de caramelo receta familiar",
                "price": 3.75,
                "category_id": categories_map["Postres"]
            },
            {
                "name": "Helado de Vainilla",
                "description": "Dos bolas de helado de vainilla",
                "price": 3.00,
                "category_id": categories_map["Postres"]
            },
            # Bebidas (3)
            {
                "name": "Limonada Cítrica",
                "description": "Bebida refrescante con toque de menta",
                "price": 3.00,
                "category_id": categories_map["Bebidas"]
            },
            {
                "name": "Café Americano",
                "description": "Café negro de taza mediana",
                "price": 2.50,
                "category_id": categories_map["Bebidas"]
            },
            {
                "name": "Agua Mineral",
                "description": "Agua mineral natural 500 ml",
                "price": 1.50,
                "category_id": categories_map["Bebidas"]
            }
        ]

        for dish_item in initial_dishes:
            dish_exists = db.query(DishModel).filter(
                DishModel.name == dish_item["name"],
                DishModel.category_id == dish_item["category_id"]
            ).first()
            if not dish_exists:
                db.add(DishModel(**dish_item))

        db.commit()
        print("Carga inicial de datos completada con éxito.")

    except Exception as error:
        db.rollback()
        print(f"Error durante el seed de datos: {error}")
    finally:
        db.close()

if __name__ == "__main__":
    run_seed()
