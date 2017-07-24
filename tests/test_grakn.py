from grakn import client as gc
import unittest
import json
from typing import List
from requests import PreparedRequest
from httmock import urlmatch, response, HTTMock
from urllib.parse import parse_qs
from urllib.parse import SplitResult
from requests.exceptions import ConnectionError

query: str = 'match $x sub concept; limit 3;'

expected_response = [
    {'id': 'a', 'label': 'concept'},
    {'id': 'b', 'label': 'entity'},
    {'id': 'c', 'label': 'resource'}
]

error_message: str = 'sorry we changed the syntax again'

mock_uri: str = 'myfavouriteserver.com'
keyspace: str = 'somesortofkeyspace'


class MockEngine:
    def __init__(self):
        self.status_code = None
        self.response = None

        @urlmatch(netloc=mock_uri, path='^/graph/graql/execute$', method='POST')
        def grakn_mock(url: SplitResult, request: PreparedRequest):
            assert self.status_code is not None

            self.request = request
            self.params = parse_qs(url.query)
            return response(self.status_code, json.dumps(self.response))

        self.request: PreparedRequest = None
        self.params: dict = None

        self._httmock: HTTMock = HTTMock(grakn_mock)

    def __enter__(self):
        self._httmock.__enter__()

    def __exit__(self, *args, **kwargs):
        self._httmock.__exit__(*args, **kwargs)

    def config_200(self) -> None:
        self.status_code = 200
        self.response = {'response': expected_response}

    def config_400(self) -> None:
        self.status_code = 400
        self.response = {'exception': error_message}


class TestGraphConstructor(unittest.TestCase):
    def test_open_accepts_no_arguments(self):
        graph = gc.Graph()
        self.assertEqual(graph.keyspace, 'grakn')
        self.assertEqual(graph.uri, 'http://localhost:4567')

    def test_open_accepts_two_arguments(self):
        graph = gc.Graph('http://www.google.com', 'mykeyspace')
        self.assertEqual(graph.uri, 'http://www.google.com')
        self.assertEqual(graph.keyspace, 'mykeyspace')

    def test_open_accepts_keyword_arguments(self):
        graph = gc.Graph(keyspace='mykeyspace', uri='http://www.google.com')
        self.assertEqual(graph.uri, 'http://www.google.com')
        self.assertEqual(graph.keyspace, 'mykeyspace')


class TestExecute(unittest.TestCase):
    def setUp(self):
        self.graph = gc.Graph(uri=f'http://{mock_uri}', keyspace=keyspace)
        self.engine = MockEngine()

    def test_executing_a_valid_query_returns_expected_response(self):
        self.engine.config_200()

        with self.engine:
            self.assertEqual(self.graph.execute(query), expected_response)

    def test_executing_a_query_sends_expected_accept_header(self):
        self.engine.config_200()

        with self.engine:
            self.graph.execute(query)
            headers = self.engine.request.headers
            self.assertEqual(headers['Accept'], 'application/graql+json')

    def test_executing_a_query_sends_query_in_params(self):
        self.engine.config_200()

        with self.engine:
            self.graph.execute(query)
            self.assertEqual(self.engine.params['query'], [query])

    def test_executing_a_query_sends_keyspace_in_params(self):
        self.engine.config_200()

        with self.engine:
            self.graph.execute(query)
            self.assertEqual(self.engine.params['keyspace'], [keyspace])

    def test_executing_a_query_sends_infer_in_params(self):
        self.engine.config_200()

        with self.engine:
            self.graph.execute(query)
            self.assertEqual(self.engine.params['infer'], ['False'])

    def test_executing_a_query_sends_materialise_in_params(self):
        self.engine.config_200()

        with self.engine:
            self.graph.execute(query)
            self.assertEqual(self.engine.params['materialise'], ['False'])

    def test_executing_an_invalid_query_throws_grakn_exception(self):
        self.engine.config_400()

        with self.engine:
            with self.assertRaises(gc.GraknError, msg=error_message):
                self.graph.execute(query)

    def test_executing_an_insert_query_returns_expected_response(self):
        self.engine.config_200()

        with self.engine:
            self.assertEqual(self.graph.execute(query), expected_response)

    def test_executing_a_query_without_a_server_throws_grakn_exception(self):
        self.engine.config_200()

        with self.assertRaises(ConnectionError):
            self.graph.execute(query)
