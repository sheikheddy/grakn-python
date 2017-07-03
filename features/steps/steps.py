from behave import *
from behave.runner import Context

import features.environment as env
from grakn.client import Graph


use_step_matcher("re")


@given("a graph")
def step_impl(context: Context):
    context.graph = Graph(keyspace=env.new_keyspace())


@given("(ontology|data) `(.*)`")
def step_impl(context: Context, ont_or_data: str, patterns: str):
    env.insert(patterns)


@given("a broken connection to the database")
def step_impl(context: Context):
    context.graph = Graph(env.broken_connection)


@when('the user issues `(.*)`')
def step_impl(context: Context, query: str):
    context.execute_query(query)


@then("the response is `(.*)`")
def step_impl(context: Context, response: str):
    assert context.response == eval(response)


@then("return a response")
def step_impl(context: Context):
    assert context.received_response


# TODO: Re-think if these steps are really the same
@then("return a response with (matching|new|existing) concepts")
def step_impl(context: Context, concept_kind: str):
    assert len(context.response) > 0, f"Response was empty: {context.response}"


@then("return an empty response")
def step_impl(context: Context):
    assert context.response == []


@then('the type "(.*)" is in the graph')
def step_impl(context: Context, label: str):
    assert env.check_type(label)


@then('the instance with (.*) "(.*)" is in the graph')
def step_impl(context: Context, resource_label: str, value: str):
    assert env.check_instance(resource_label, value)


@then("return an error")
def step_impl(context: Context):
    assert context.error is not None
