Feature: Graql Queries
  As a Grakn Developer, I should be able to interact with a Grakn Graph unsing Graql queries

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


  @skip
    Scenario: Match Non Existent Concept
		When The user issues a match query which should not have results
    	Then Return an empty response


  @skip
    Scenario: Match Existent Concept
		When The user issues a match query which should have results
    	Then Return a response with matching concepts


  @skip
    Scenario: Deleting a Type
        Given An empty type
        When The user deletes the type
        Then Write to the graph
        And Return a response


  @skip
    Scenario: Deleting a Type with instances
        Given A Type With instances
        When The user deletes the type
        Then Return an error


  @skip
    Scenario: Deleting Non-existant Concept
        When The user delete a concept
        And The concept does not exist
        Then Return a response