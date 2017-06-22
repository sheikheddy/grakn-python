Feature: Insert Queries
    As a Grakn Developer I should be able to perform graql insert queries which write new concepts to the graph.

    Background: A graph containing types and instances
        Given A graph containing types and instances

    Scenario: Insert Types
        Given A type that does not exist
        When The user inserts the type
        Then The type is in the graph
        And Return a response with new concepts

    Scenario: Insert Types Which Exist
        Given A type that already exists
        When The user inserts the type
        Then Return a response with existing concepts

    Scenario: Insert Instances
        Given A type that already exists
        When The user inserts an instance of the type
        Then The instance is in the graph
        And Return a response with new concepts

    Scenario: Insert Instances With Missing Type
        Given A type that does not exist
        When The user inserts an instance of the type
        Then Return an error
