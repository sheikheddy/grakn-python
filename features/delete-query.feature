@skip
Feature: Delete Queries
    The user should be able to perform deletion queries which delete existing concepts from the graph

	Scenario: Deleting a Type
        Given An empty type
        When The user deletes the type
        Then Write to the graph
        And Return a response

    Scenario: Deleting a Type with instances
        Given A Type With instances
        When The user deletes the type
        Then Return an error

    Scenario: Deleting Non-existant Concept
        Given A graph containing types and instances
        When The user delete a concept
        And The concept does not exist
        Then Return a response
