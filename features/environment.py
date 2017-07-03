import subprocess
from sys import stdout

from behave.runner import Context
from requests import ConnectionError

from grakn.client import GraknError

env: str = './features/grakn-spec/env.sh'

broken_connection: str = 'http://0.1.2.3:4567'


def execute_query(self: Context, query: str):
    print(f">>> {query}")
    try:
        self.response = self.graph.execute(query)
        self.received_response = True
        self.error = None
        print(self.response)
    except (GraknError, ConnectionError) as e:
        self.response = None
        self.received_response = False
        self.error = e
        print(f"Error: {self.error}")


Context.execute_query = execute_query


def new_keyspace() -> str:
    process = subprocess.run([env, 'keyspace'], stdout=subprocess.PIPE)
    return process.stdout.strip().decode('utf-8')


def insert(patterns: str):
    subprocess.run([env, 'insert', patterns])


def check_type(label: str) -> bool:
    process = subprocess.run([env, 'check', 'type', label])
    return process.returncode == 0


def check_instance(resource_label: str, value: str) -> bool:
    process = subprocess.run([env, 'check', 'instance', resource_label, value])
    return process.returncode == 0


def before_all(context: Context):
    subprocess.run([env, 'start'])


def after_all(context: Context):
    subprocess.run([env, 'stop'])

