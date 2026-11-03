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
            # Comida (10)
            {
                "name": "Hamburguesa Clásica",
                "description": "Carne de res con queso cheddar y lechuga",
                "price": 9.50,
                "category_id": categories_map["Comida"]
            },
            {
                "name": "Pollo a la Plancha",
                "description": "Pechuga de pollo con verduras salteadas",
                "price": 8.75,
                "category_id": categories_map["Comida"]
            },
            {
                "name": "Lomo de Res",
                "description": "Lomo sellado con papas rústicas y salsa",
                "price": 12.00,
                "category_id": categories_map["Comida"]
            },
            {
                "name": "Pasta Alfredo",
                "description": "Pasta con salsa cremosa de queso parmesano",
                "price": 7.90,
                "category_id": categories_map["Comida"]
            },
            {
                "name": "Ensalada César",
                "description": "Lechuga romana, pollo y aderezo césar",
                "price": 6.50,
                "category_id": categories_map["Comida"]
            },
            {
                "name": "Tacos de Pollo",
                "description": "Tortillas de maíz con pollo y pico de gallo",
                "price": 7.25,
                "category_id": categories_map["Comida"]
            },
            {
                "name": "Salmón al Horno",
                "description": "Salmón con limón, eneldo y espárragos",
                "price": 13.50,
                "category_id": categories_map["Comida"]
            },
            {
                "name": "Pizza Margarita",
                "description": "Masa fina con tomate, albahaca y mozzarella",
                "price": 9.00,
                "category_id": categories_map["Comida"]
            },
            {
                "name": "Arroz con Pollo",
                "description": "Arroz marinado con pollo y vegetales",
                "price": 8.25,
                "category_id": categories_map["Comida"]
            },
            {
                "name": "Estofado de Res",
                "description": "Res guisada con papas y zanahorias",
                "price": 10.75,
                "category_id": categories_map["Comida"]
            },
            # Bebidas (10)
            {
                "name": "Limonada Cítrica",
                "description": "Bebida refrescante con toque de menta",
                "price": 3.00,
                "category_id": categories_map["Bebidas"]
            },
            {
                "name": "Jugo de Naranja",
                "description": "Jugo natural recién exprimido",
                "price": 3.50,
                "category_id": categories_map["Bebidas"]
            },
            {
                "name": "Café Americano",
                "description": "Café negro de taza mediana",
                "price": 2.50,
                "category_id": categories_map["Bebidas"]
            },
            {
                "name": "Té Verde",
                "description": "Infusión de té verde con miel opcional",
                "price": 2.00,
                "category_id": categories_map["Bebidas"]
            },
            {
                "name": "Agua Mineral",
                "description": "Agua mineral natural 500 ml",
                "price": 1.50,
                "category_id": categories_map["Bebidas"]
            },
            {
                "name": "Soda de Limón",
                "description": "Gaseosa de limón con hielo y rodajas",
                "price": 2.75,
                "category_id": categories_map["Bebidas"]
            },
            {
                "name": "Batido de Fresa",
                "description": "Batido de fresa con leche y vainilla",
                "price": 4.25,
                "category_id": categories_map["Bebidas"]
            },
            {
                "name": "Chocolate Caliente",
                "description": "Chocolate con leche y canela",
                "price": 3.25,
                "category_id": categories_map["Bebidas"]
            },
            {
                "name": "Smoothie de Mango",
                "description": "Batido de mango y piña sin azúcar añadida",
                "price": 4.50,
                "category_id": categories_map["Bebidas"]
            },
            {
                "name": "Cerveza Artesanal",
                "description": "Cerveza rubia artesanal 350 ml",
                "price": 5.00,
                "category_id": categories_map["Bebidas"]
            },
            # Postres (10)
            {
                "name": "Tarta de Queso",
                "description": "Postre de la casa con mermelada",
                "price": 4.50,
                "category_id": categories_map["Postres"]
            },
            {
                "name": "Brownie con Helado",
                "description": "Brownie tibio con bola de helado de vainilla",
                "price": 5.25,
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
            {
                "name": "Pudín de Pan",
                "description": "Pudín con canela y pasas",
                "price": 4.00,
                "category_id": categories_map["Postres"]
            },
            {
                "name": "Pay de Manzana",
                "description": "Pay tibio de manzana con canela",
                "price": 4.75,
                "category_id": categories_map["Postres"]
            },
            {
                "name": "Mousse de Chocolate",
                "description": "Mousse ligero de chocolate oscuro",
                "price": 4.25,
                "category_id": categories_map["Postres"]
            },
            {
                "name": "Frutas con Crema",
                "description": "Frutas frescas con crema batida",
                "price": 3.90,
                "category_id": categories_map["Postres"]
            },
            {
                "name": "Churros con Chocolate",
                "description": "Churros crujientes con salsa de chocolate",
                "price": 4.60,
                "category_id": categories_map["Postres"]
            },
            {
                "name": "Tres Leches",
                "description": "Bizcocho bañado en tres leches",
                "price": 4.85,
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