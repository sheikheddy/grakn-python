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


@given("a graph")
def step_impl(context: Context):
    context.graph = Graph(keyspace=context.new_keyspace())


@given("(ontology|data) `(.*)`")
def step_impl(context: Context, ont_or_data: str, patterns: str):
    env.graql_shell(context, '-e', f'insert {patterns}')


@given("A broken connection to the database")
def step_impl(context: Context):
    context.graph = Graph(env.broken_connection)


@given("A concept that does not exist")
def step_impl(context: Context):
    context.concept = env.non_existent_type(context)


@given("A type that does not exist")
def step_impl(context: Context):
    context.type = env.non_existent_type(context)


@given("A type (that already exists|with instances)")
def step_impl(context: Context, type_kind: str):
    context.type = env.existing_type(context)


@given("An empty type")
def step_impl(context: Context):
    context.type = env.non_existent_type(context)
    env.graql_shell(context, '-e', f'insert {context.type} sub entity;')


@when('The user issues `(.*)`')
def step_impl(context: Context, query: str):
    env.execute_query(context, query)


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


@when("The user deletes the type")
def step_impl(context: Context):
    env.execute_query(context, f'match $x label {context.type}; delete $x;')


@when("The user deletes the concept")
def step_impl(context: Context):
    env.execute_query(context, f'match $x label {context.concept}; delete $x;')


@then("The response is `(.*)`")
def step_impl(context: Context, response: str):
    assert context.response == eval(response)


@then("Return a response")
def step_impl(context: Context):
    assert context.received_response


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
