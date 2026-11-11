Feature: PostgreSQL error translation and rollback

  Scenario: A unique violation is translated and the session remains usable
    Given a PostgreSQL integration route is available
    When the client creates the same category twice
    Then the duplicate response status is 409
    And the duplicate detail is the Spanish uniqueness message without SQL leakage
    And the same database session can still execute a query
