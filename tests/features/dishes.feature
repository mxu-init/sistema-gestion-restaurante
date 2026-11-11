# language: es
Característica: Gestión de platos
  Como administrador o maître
  Quiero gestionar los platos de la carta
  Para mantener actualizada la oferta gastronómica del restaurante

  Escenario: Listar platos existentes
    Dado que existen platos registrados en el restaurante
    Cuando consulto la lista de platos
    Entonces la respuesta tiene código 200
    Y la lista contiene los platos registrados

  Escenario: Consultar un plato por su identificador
    Dado que existe un plato con nombre "Ensalada César" y precio 9.50
    Cuando consulto el plato por su identificador
    Entonces la respuesta tiene código 200
    Y el detalle del plato muestra el nombre "Ensalada César"

  Escenario: Consultar un plato inexistente
    Dado que no existe ningún plato con id 999999
    Cuando consulto el plato con id 999999
    Entonces la respuesta tiene código 404

  Escenario: Crear un plato correctamente
    Dado que existe una categoría "Entrantes"
    Cuando solicito crear un plato con nombre "Croquetas de Jamón" y precio 8.00 en la categoría "Entrantes"
    Entonces la respuesta tiene código 201
    Y el plato creado tiene el nombre "Croquetas de Jamón"

  Escenario: Intentar crear un plato con precio negativo
    Dado que existe una categoría "Entrantes"
    Cuando solicito crear un plato con nombre "Plato Inválido" y precio -5.00 en la categoría "Entrantes"
    Entonces la respuesta tiene código 400

  Escenario: Borrado lógico de un plato
    Dado que existe un plato con nombre "Plato para Borrar"
    Cuando solicito eliminar el plato
    Entonces la respuesta tiene código 204
    Y el plato no aparece en las consultas posteriores

