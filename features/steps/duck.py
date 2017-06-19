from behave import *
from grakn import duck
from nose.tools import eq_


@given(u'I have a Duck called "{duck_name}"')
def step_impl(context, duck_name):
    context.duck = duck.Duck(duck_name)


@when(u'I squeeze the duck')
def step_impl(context):
    context.response = context.duck.squeeze()


@then(u'the response should be "{expected}"')
def step_impl(context, expected):
    eq_(context.response, expected)
