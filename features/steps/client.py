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


@given("A broken connection to the database")
def step_impl(context: Context):
    context.graph = Graph('http://0.1.2.3:4567')


@when("The user issues a query")
@when("The user issues a valid query")
def step_impl(context: Context):
    env.execute_query(context, valid_query)


@when("The user issues an invalid query")
def step_impl(context: Context):
    env.execute_query(context, invalid_query)


@then("Return a response")
def step_impl(context: Context):
    for result in context.response:
        for concept in result.values():
            assert 'id' in concept, f"Could not find 'id' in {concept}"


@then("Return an error")
def step_impl(context: Context):
    assert context.error is not None

