import json
import random
import subprocess

import appdirs

from behave.runner import Context
from requests import ConnectionError

from grakn.client import GraknError

cache_dir: str = appdirs.user_cache_dir('grakn-spec')

env: str = './features/grakn-spec/env.sh'

match_query_with_results: str = 'match $x isa person; limit 5;'
match_query_without_results: str = 'match $x has name "Not in graph";'
invalid_query: str = 'select $x where $x isa person;'

broken_connection: str = 'http://0.1.2.3:4567'


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


def existing_type(context: Context) -> str:
    query = 'match $x isa $X; $X sub entity; $X != entity; limit 1;'
    result = graql_shell(context, '-o', 'json', '-e', query)
    return json.loads(result)['X']['name']


def non_existent_type(context: Context) -> str:
    the_type = 'teapot-in-space'
    prefixes = ['invisible-', 'pink-', 'java-one-liner-']

    def type_is_in_graph() -> bool:
        args = ['-o', 'json', '-e', f'match label {the_type}; ask;']
        result = graql_shell(context, *args)
        return result == b'true\n'

    while type_is_in_graph():
        the_type += random.choice(prefixes)

    return the_type


def new_keyspace(context: Context) -> str:
    keyspace = 'k' + str(context.keyspace_counter)
    context.keyspace_counter += 1
    return keyspace


def before_all(context: Context):
    subprocess.run([env, 'start'])
    context.grakn_dir = f'{cache_dir}/grakn'
    context.keyspace_counter = 0


def after_all(context: Context):
    subprocess.run([f'./features/grakn-spec/env.sh', 'stop'])

