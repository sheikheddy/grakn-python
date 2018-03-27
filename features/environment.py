import subprocess

from behave.runner import Context

import grakn

env: str = './features/grakn-spec/env.sh'

broken_connection: str = 'http://0.1.2.3:4567'


def execute_query(self: Context, query: str):
    print(f">>> {query}")
    try:
        self._response = self.client.execute(query, **self.params)
        self._received_response = True
        self._error = None
        print(self._response)
    except (grakn.GraknError, ConnectionError) as e:
        self._response = None
        self._received_response = False
        self._error = e
        print(f"Error: {self._error}")


def get_response(self: Context):
    assert self._received_response, self._error
    return self._response


def get_error(self: Context):
    assert not self._received_response, self._response
    return self._error


Context.execute_query = execute_query
Context.get_response = get_response
Context.get_error = get_error


def new_keyspace() -> str:
    process = subprocess.run([env, 'keyspace'], stdout=subprocess.PIPE)
    return process.stdout.strip().decode('utf-8')


def define(patterns: str):
    subprocess.run([env, 'define', patterns])


def insert(patterns: str):
    subprocess.run([env, 'insert', patterns])


def check_type(label: str) -> bool:
    process = subprocess.run([env, 'check', 'type', label])
    return process.returncode == 0


def check_instance(resource_label: str, value: str) -> bool:
    process = subprocess.run([env, 'check', 'instance', resource_label, value])
    return process.returncode == 0


def before_all(context: Context):
    context.params = {}
    version = context.config.userdata['graknversion']
    process = subprocess.run([env, 'start', version])
    assert process.returncode == 0, "Failed to start test environment"


def after_all(context: Context):
    subprocess.run([env, 'stop'])

