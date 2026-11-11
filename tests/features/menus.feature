# language: es
Característica: Gestión de menús del restaurante
  Como manager o super_admin
  Quiero crear, consultar, modificar y dar de baja menús
  Para gestionar la oferta de menús y asegurar que solo se sirven menús con platos disponibles

  Escenario: Crear un menú con platos válidos
    Dado que existen platos disponibles en la carta
    Cuando creo un menú con nombre "Menú Ejecutivo", precio 16.50 y día "Lunes"
    Entonces la respuesta tiene código 201
    Y el menú tiene el nombre "Menú Ejecutivo" y precio 16.50
    Y el menú tiene disponibilidad efectiva true

  Escenario: Intentar crear un menú con un plato inexistente
    Dado que no existe ningún plato con id 999999
    Cuando intento crear un menú con el plato inexistente 999999
    Entonces la respuesta tiene código 404
    Y el mensaje de error indica que no existen los platos

  Escenario: Intentar crear un menú con precio negativo
    Dado que existen platos disponibles en la carta
    Cuando intento crear un menú con precio negativo -10.00
    Entonces la respuesta tiene código 422

  Escenario: Consultar un menú por su identificador
    Dado que existe un menú "Menú Degustación" con precio 30.00
    Cuando consulto el menú por su identificador
    Entonces la respuesta tiene código 200
    Y los datos del menú corresponden a "Menú Degustación"

  Escenario: Consultar un menú inexistente
    Dado que no existe el menú con id 999999
    Cuando consulto el menú con id 999999
    Entonces la respuesta tiene código 404

  Escenario: Modificar el nombre y precio de un menú
    Dado que existe un menú "Menú Especial" con precio 20.00
    Cuando modifico el menú con nuevo nombre "Menú Fin de Semana" y precio 25.00
    Entonces la respuesta tiene código 200
    Y el menú actualizado tiene nombre "Menú Fin de Semana" y precio 25.00

  Escenario: Cambiar manualmente la disponibilidad de un menú
    Dado que existe un menú activo disponible
    Cuando desactivo manualmente la disponibilidad del menú
    Entonces la respuesta tiene código 200
    Y el menú tiene disponibilidad efectiva false

  Escenario: Disponibilidad efectiva automática al desactivar un plato
    Dado que existe un menú compuesto por platos disponibles
    Cuando desactivo uno de los platos que componen el menú
    Entonces la consulta del menú refleja que su disponibilidad efectiva es false
    Y la bandera en base de datos del menú sigue activa

  Escenario: Filtrar menús por disponibilidad efectiva
    Dado que existen menús disponibles y menús no disponibles
    Cuando solicito listar los menús filtrando por disponibles
    Entonces la lista devuelta contiene únicamente menús disponibles

  Escenario: Borrado lógico de un menú
    Dado que existe un menú "Menú a Eliminar"
    Cuando solicito eliminar el menú por su identificador
    Entonces la respuesta tiene código 204
    Y el menú ya no aparece al consultarlo por su identificador

  Escenario: Intentar borrar un menú ya eliminado
    Dado que existe un menú que ya ha sido eliminado
    Cuando solicito eliminar nuevamente ese mismo menú
    Entonces la respuesta tiene código 409
    Y el mensaje de error indica que el menú ya ha sido eliminado

