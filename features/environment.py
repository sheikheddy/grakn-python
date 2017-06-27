import random
import subprocess

import appdirs

from behave.runner import Context
from requests import ConnectionError

from grakn.client import GraknError

cache_dir: str = appdirs.user_cache_dir('grakn-spec')

env: str = './features/grakn-spec/env.sh'

match_query_with_results: str = 'match $x isa pokemon; limit 5;'
match_query_without_results: str = 'match $x has name "Not in graph";'
invalid_query: str = 'select $x where $x isa pokemon;'

broken_connection: str = 'http://0.1.2.3:4567'

existing_type: str = 'pokemon'


def execute_query(context: Context, query: str):
    print(f">>> {query}")
    try:
        context.response = context.graph.execute(query)
        context.error = None
        print(context.response)
    except (GraknError, ConnectionError) as e:
        context.response = None
        context.error = e
        print(context.error)


def grakn_cmd(context: Context, arg: str, inp=None):
    subprocess.run([f'{context.grakn_dir}/bin/grakn.sh', arg], input=inp)


def graql_shell(context: Context, *args: str) -> bytes:
    args = [f'{context.grakn_dir}/bin/graql.sh'] + list(args)
    proc = subprocess.run(args, stdout=subprocess.PIPE)
    return proc.stdout


def graql_file_of_types_and_instances(context: Context) -> str:
    return f'{context.grakn_dir}/examples/pokemon.gql'


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


def before_all(context: Context):
    subprocess.run([env, 'start'])
    context.grakn_dir = f'{cache_dir}/grakn'


def after_all(context: Context):
    subprocess.run([f'./features/grakn-spec/env.sh', 'stop'])

