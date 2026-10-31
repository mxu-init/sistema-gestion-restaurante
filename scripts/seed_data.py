from app.core.database_connection import session_local
from app.models.dish_model import CategoryModel, DishModel

def run_seed():
    db = session_local()
    try:
        categories_list = ["Comida", "Bebidas", "Postres"]
        categories_map = {}

        for category_name in categories_list:
            category_db = db.query(CategoryModel).filter(CategoryModel.name == category_name).first()
            if not category_db:
                category_db = CategoryModel(name=category_name)
                db.add(category_db)
                db.commit()
                db.refresh(category_db)
            categories_map[category_name] = category_db.id

        initial_dishes = [
            {
                "name": "Hamburguesa Clásica",
                "description": "Carne de res con queso cheddar y lechuga",
                "price": 9.50,
                "category_id": categories_map["Comida"]
            },
            {
                "name": "Limonada Cítrica",
                "description": "Bebida refrescante con toque de menta",
                "price": 3.00,
                "category_id": categories_map["Bebidas"]
            },
            {
                "name": "Tarta de Queso",
                "description": "Postre de la casa con mermelada",
                "price": 4.50,
                "category_id": categories_map["Postres"]
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