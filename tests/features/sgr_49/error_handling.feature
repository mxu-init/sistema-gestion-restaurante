Feature: Centralized application exception handling

  Scenario: A domain NotFoundError returns a standardized HTTP 404
    Given the SGR-49 application is available
    When the client requests the missing demo resource 41
    Then the response status is 404
    And the response detail is "El recurso con identificador 41 no fue encontrado"

  Scenario: Invalid request data returns a standardized HTTP 422
    Given the SGR-49 application is available
    When the client submits a demo reservation without a name
    Then the response status is 422
    And the response detail is "Error en el campo 'nombre': El campo es obligatorio"

  Scenario: An unexpected exception returns a safe HTTP 500
    Given a test-only crash route is registered
    When the client requests the test-only crash route
    Then the response status is 500
    And the response detail is "Error interno del servidor"
    And the response body hides internal exception details
