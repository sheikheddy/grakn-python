import subprocess

import appdirs

from behave.runner import Context
from requests import ConnectionError

from grakn.client import GraknError

cache_dir: str = appdirs.user_cache_dir('grakn-spec')

env: str = './features/grakn-spec/env.sh'

broken_connection: str = 'http://0.1.2.3:4567'


class Keyspaces:

    def __init__(self):
        self.count = 0

    def new(self) -> str:
        keyspace = f'k{self.count}'
        self.count += 1
        return keyspace


def execute_query(context: Context, query: str):
    print(f">>> {query}")
    try:
        context.response = context.graph.execute(query)
        context.received_response = True
        context.error = None
        print(context.response)
    except (GraknError, ConnectionError) as e:
        context.response = None
        context.received_response = False
        context.error = e
        print(context.error)


def graql_shell(context: Context, *args: str) -> bytes:
    graql_sh = f'{context.grakn_dir}/bin/graql.sh'
    args = [graql_sh, '-k', context.graph.keyspace] + list(args)
    proc = subprocess.run(args, stdout=subprocess.PIPE)
    return proc.stdout


def before_all(context: Context):
    subprocess.run([env, 'start'])
    context.grakn_dir = f'{cache_dir}/grakn'
    keyspaces = Keyspaces()
    context.new_keyspace = keyspaces.new


def after_all(context: Context):
    subprocess.run([f'./features/grakn-spec/env.sh', 'stop'])

