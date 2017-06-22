import subprocess
import shutil
import tempfile
import os
import os.path
import tarfile
import urllib.request
import time

import errno

import appdirs
import socket

import sys
from behave.runner import Context
from behave.model import Scenario
from requests import ConnectionError

from grakn.client import GraknError

cache_dir: str = appdirs.user_cache_dir('grakn', 'graknlabs')

grakn_release: str = 'grakn-dist-0.13.0'
grakn_tar: str = f'{grakn_release}.tar.gz'
grakn_download_url: str = f'https://github.com/graknlabs/grakn/releases/download/v0.13.0/{grakn_tar}'

match_query_with_results: str = 'match $x isa pokemon; limit 5;'
match_query_without_results: str = 'match $x has name "Not in graph";'
invalid_query: str = 'select $x where $x isa pokemon;'

broken_connection: str = 'http://0.1.2.3:4567'

existing_type: str = 'pokemon'
non_existent_type: str = 'teapot-in-space'


def start_grakn(context: Context):
    grakn_cmd(context, 'start')
    time.sleep(5)


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


def graql_shell(context: Context, *args: str):
    subprocess.run([f'{context.grakn_dir}/bin/graql.sh'] + list(args))


def graql_file_of_types_and_instances(context: Context) -> str:
    return f'{context.grakn_dir}/examples/pokemon.gql'


def before_all(context: Context):
    if is_port_in_use(4567):
        msg = "Port 4567 is in use. Maybe a Grakn server is already running?"
        print(msg, file=sys.stderr)
        exit(1)

    grakn_download_path = f'{cache_dir}/{grakn_tar}'

    try:
        os.makedirs(cache_dir)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise

    if not os.path.isfile(grakn_download_path):
        urllib.request.urlretrieve(grakn_download_url, grakn_download_path)

    temp_dir = tempfile.mkdtemp()
    tarfile.open(grakn_download_path).extractall(temp_dir)
    context.grakn_dir = f'{temp_dir}/{grakn_release}'


def after_scenario(context: Context, scenario: Scenario):
    grakn_cmd(context, 'clean', inp=b"Y")


def after_all(context: Context):
    grakn_cmd(context, 'stop')
    shutil.rmtree(context.grakn_dir)


def is_port_in_use(port: int) -> bool:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        s.bind(("127.0.0.1", port))
    except socket.error as e:
        if e.errno in [48, 98]:
            return True
        else:
            # something else raised the socket.error exception
            print(e)

    s.close()

    return False
