from behave import *
from behave.runner import Context

import features.environment as env
from grakn.client import Graph

use_step_matcher("re")


@given("A graph containing types and instances")
def step_impl(context: Context):
    env.start_grakn()
    env.graql_shell('-f', env.graql_file_of_types_and_instances)
    context.graph = Graph()


@given("A broken connection to the database")
def step_impl(context: Context):
    context.graph = Graph(env.broken_connection)


@when("The user issues a (valid)? query")
def step_impl(context: Context):
    env.execute_query(context, env.valid_query)


@when("The user issues an invalid query")
def step_impl(context: Context):
    env.execute_query(context, env.invalid_query)


@then("Return a response")
def step_impl(context: Context):
    for result in context.response:
        for concept in result.values():
            assert 'id' in concept, f"Could not find 'id' in {concept}"


@then("Return an error")
def step_impl(context: Context):
    assert context.error is not None

