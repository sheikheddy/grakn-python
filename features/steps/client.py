from behave import *
from behave.runner import Context

import features.environment as env
from grakn.client import Graph, GraknError
from requests.exceptions import ConnectionError

use_step_matcher("re")


@given("A graph containing types and instances")
def step_impl(context: Context):
    env.start_grakn()
    env.graql_shell('-f', env.graql_file_of_types_and_instances)
    context.graph = Graph()


@given("A broken connection to the database")
def step_impl(context: Context):
    context.graph = Graph(env.broken_connection)


@when("The user issues (a|a valid|an invalid)? query")
def step_impl(context: Context, query_type: str):
    query = {
        'a': env.valid_query, 'a valid': env.valid_query,
        'an invalid': env.invalid_query
    }[query_type]

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


@then("Return an error")
def step_impl(context: Context):
    assert context.error is not None

