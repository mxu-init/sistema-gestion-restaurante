Feature: Request correlation identifiers

  Scenario: An incoming X-Request-ID is preserved
    Given the SGR-49 application is available
    When the client calls health with correlation id "trace-sgr-49"
    Then the response correlation id is "trace-sgr-49"

  Scenario: A request without an incoming id receives a generated correlation id
    Given the SGR-49 application is available
    When the client calls health without a correlation id
    Then the response includes a generated correlation id
