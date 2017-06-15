Feature: Match Queries
    As a Grakn Developer I should able to execute graql match queries which find concepts based on the contents of the query. These concepts should be returned to me in a usable format.

    Scenario: Match Non Existent Concept
    	Given A graph containing types and instances
		When The user issues a match query which should not have results
    	Then Return an empty response

    @skip
    Scenario: Match Existent Concept
        Given A graph containing types and instances
		When The user issues a match query which should have results
    	Then Return a response with matching concepts