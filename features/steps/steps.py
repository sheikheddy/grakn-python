from behave import *
from behave.runner import Context

import features.environment as env
from grakn.client import Graph, GraknError
from requests.exceptions import ConnectionError

query_table = {
    'a query': env.match_query_with_results,
    'a valid query': env.match_query_with_results,
    'an invalid query': env.invalid_query,
    'a match query which should have results': env.match_query_with_results,
    'a match query which should not have results': env.match_query_without_results
}

query_keys = '|'.join(query_table.keys())

use_step_matcher("re")


@given("A graph containing types and instances")
def step_impl(context: Context):
    env.start_grakn()
    env.graql_shell('-f', env.graql_file_of_types_and_instances)
    context.graph = Graph()


@given("A broken connection to the database")
def step_impl(context: Context):
    context.graph = Graph(env.broken_connection)


@when(f"The user issues ({query_keys})")
def step_impl(context: Context, query_type: str):
    query = query_table[query_type]

    try:
        context.response = context.graph.execute(query)
        context.error = None
    except (GraknError, ConnectionError) as e:
        context.response = None
        context.error = e


@then("Return a response")
def step_impl(context: Context):
    for result in context.response:
        for concept in result.values():
            assert 'id' in concept, f"Could not find 'id' in {concept}"


@then("Return a response with matching concepts")
def step_impl(context: Context):
    assert len(context.response) > 0


@then("Return an empty response")
def step_impl(context: Context):
    assert context.response == []


@then("Return an error")
def step_impl(context: Context):
    assert context.error is not None
