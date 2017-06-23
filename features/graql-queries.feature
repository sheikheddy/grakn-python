Feature: Graql Queries
  As a Grakn Developer, I should be able to interact with a Grakn Graph using Graql queries

    Background: A graph containing types and instances
        Given A graph containing types and instances

    Scenario: Valid Insert Query for Types
        Given A type that does not exist
        When The user inserts the type
        Then The type is in the graph
        And Return a response with new concepts

    Scenario: Redundant Insert Query
        Given A type that already exists
        When The user inserts the type
        Then Return a response with existing concepts

    Scenario: Valid Insert Query for Instances
        Given A type that already exists
        When The user inserts an instance of the type
        Then The instance is in the graph
        And Return a response with new concepts

    Scenario: Invalid Insert Query
        Given A type that does not exist
        When The user inserts an instance of the type
        Then Return an error


  @skip
    Scenario: Match Query With Empty Response
		When The user issues a match query which should not have results
    	Then Return an empty response


  @skip
    Scenario: Match Query With Non-Empty Response
		When The user issues a match query which should have results
    	Then Return a response with matching concepts


  @skip
    Scenario: Successful Delete Query
        Given An empty type
        When The user deletes the type
        Then Return a response


  @skip
    Scenario: Unsuccessful Delete Query
        Given A Type With instances
        When The user deletes the type
        Then Return an error


  @skip
    Scenario: Delete Query for non Existant Concept
        When The user delete a concept
        And The concept does not exist
        Then Return a response