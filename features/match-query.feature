@skip
Feature: Match Queries
    As a Grakn Developer I should able to execute graql match queries which find concepts based on the contents of the query. These concepts should be returned to me in a usable format.

    Scenario: Match Non Existant Concept
    	Given A graph containing types and instances
		When The user issues a match query
		And No concept matches
    	Then Return an empty response

    Scenario: Match Existant Concept
        Given A graph containing types and instances
		When The user issues a match query
		And Concepts match
    	Then Return a response with matching concepts