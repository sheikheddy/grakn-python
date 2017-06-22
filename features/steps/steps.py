from behave import *
from behave.runner import Context

import features.environment as env
from grakn.client import Graph

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
    env.start_grakn(context)
    file = env.graql_file_of_types_and_instances(context)
    env.graql_shell(context, '-f', file)
    context.graph = Graph()


@given("A broken connection to the database")
def step_impl(context: Context):
    context.graph = Graph(env.broken_connection)


@given("A type that does not exist")
def step_impl(context: Context):
    context.type = env.non_existent_type


@given("A type that already exists")
def step_impl(context: Context):
    context.type = env.existing_type


@when(f"The user issues ({query_keys})")
def step_impl(context: Context, query_type: str):
    query = query_table[query_type]
    env.execute_query(context, query)


@when("The user inserts the type")
def step_impl(context: Context):
    env.execute_query(context, f'insert $x label {context.type} sub entity;')


@when("The user inserts an instance of the type")
def step_impl(context: Context):
    query = f'insert $x isa {context.type};'
    env.execute_query(context, query)
    if context.response is not None:
        context.instance = context.response[0]


@then("Return a response")
def step_impl(context: Context):
    for result in context.response:
        for concept in result.values():
            assert 'id' in concept, f"Could not find 'id' in {concept}"


# TODO: Re-think if these steps are really the same
@then("Return a response with (matching|new|existing) concepts")
def step_impl(context: Context, concept_kind: str):
    assert len(context.response) > 0, f"Response was empty: {context.response}"


@then("Return an empty response")
def step_impl(context: Context):
    assert context.response == []


@then("The type is in the graph")
def step_impl(context: Context):
    result = context.graph.execute(f'match label {context.type}; ask;')
    assert result, f'The type is not in the graph: {result}'


@then("The instance is in the graph")
def step_impl(context: Context):
    result = context.graph.execute(f'match id "{context.instance}"; ask;')
    assert result, f'The instance is not in the graph: {result}'


@then("Return an error")
def step_impl(context: Context):
    assert context.error is not None