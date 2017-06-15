from grakn.client import Graph, GraknError

from behave import *
from behave.runner import Context

import features.environment as env

use_step_matcher("re")

valid_query = 'match $x isa pokemon; limit 5;'
invalid_query = 'select $x where $x isa pokemon;'


@given("A graph containing types and instances")
def step_impl(context: Context):
    env.start_grakn()
    env.graql_shell('-f', f'{env.grakn_dir}/examples/pokemon.gql')
    context.graph = Graph()


@when("The user issues a valid query")
def step_impl(context: Context):
    context.response = context.graph.execute(valid_query)


@when("The user issues an invalid query")
def step_impl(context: Context):
    try:
        context.response = context.graph.execute(invalid_query)
    except GraknError as e:
        context.error = e


@then("Return a response")
def step_impl(context: Context):
    for result in context.response:
        for concept in result.values():
            assert 'id' in concept, f"Could not find 'id' in {concept}"


@then("Return an error")
def step_impl(context: Context):
    assert context.error is not None
