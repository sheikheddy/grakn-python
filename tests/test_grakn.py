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

expected_response: List[gc.Result] = [
    {'id': 'a', 'label': 'concept'},
    {'id': 'b', 'label': 'entity'},
    {'id': 'c', 'label': 'resource'}
]

error_message: str = 'sorry we changed the syntax again'

mock_uri: str = 'myfavouriteserver.com'
keyspace: str = 'somesortofkeyspace'


class MockEndpoint:
    def __init__(self, method: str):
        self.status_code = 200
        self.response = {'response': expected_response}

        @urlmatch(netloc=mock_uri, path='^/graph/graql$', method=method)
        def grakn_mock(url: SplitResult, request: PreparedRequest):
            self.request = request
            self.params = parse_qs(url.query)
            return response(self.status_code, json.dumps(self.response))

        self.handler = grakn_mock
        self.request: PreparedRequest = None
        self.params: dict = None


class MockEngine:
    def __init__(self):
        self.get: MockEndpoint = MockEndpoint('GET')
        self.post: MockEndpoint = MockEndpoint('POST')
        self.httmock: HTTMock = HTTMock(self.get.handler, self.post.handler)

    def __enter__(self):
        self.httmock.__enter__()

    def __exit__(self, *args, **kwargs):
        self.httmock.__exit__(*args, **kwargs)


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

    def is_insert_query(self):
        self.engine.get.status_code = 405
        self.engine.get.response = {'exception': '🚫'}

    def is_invalid_query(self, endpoint: MockEndpoint):
        endpoint.status_code = 400
        endpoint.response = {'exception': error_message}

    def test_executing_a_valid_match_query_returns_expected_response(self):
        with self.engine:
            self.assertEqual(self.graph.execute(query), expected_response)

    def test_executing_a_match_query_sends_expected_accept_header(self):
        with self.engine:
            self.graph.execute(query)
            headers = self.engine.get.request.headers
            self.assertEqual(headers['Accept'], 'application/graql+json')

    def test_executing_a_match_query_sends_query_in_params(self):
        with self.engine:
            self.graph.execute(query)
            self.assertEqual(self.engine.get.params['query'], [query])

    def test_executing_a_match_query_sends_keyspace_in_params(self):
        with self.engine:
            self.graph.execute(query)
            self.assertEqual(self.engine.get.params['keyspace'], [keyspace])

    def test_executing_a_match_query_sends_infer_in_params(self):
        with self.engine:
            self.graph.execute(query)
            self.assertEqual(self.engine.get.params['infer'], ['False'])

    def test_executing_a_match_query_sends_materialise_in_params(self):
        with self.engine:
            self.graph.execute(query)
            self.assertEqual(self.engine.get.params['materialise'], ['False'])

    def test_executing_a_match_query_does_not_contact_post_endpoint(self):
        with self.engine:
            self.graph.execute(query)
            self.assertIsNone(self.engine.post.request)

    def test_executing_an_invalid_match_query_throws_grakn_exception(self):
        self.is_invalid_query(self.engine.get)

        with self.engine:
            with self.assertRaises(gc.GraknError, msg=error_message):
                self.graph.execute(query)

    def test_executing_an_insert_query_returns_expected_response(self):
        self.is_insert_query()

        with self.engine:
            self.assertEqual(self.graph.execute(query), expected_response)

    def test_executing_an_insert_query_sends_expected_accept_header(self):
        self.is_insert_query()

        with self.engine:
            self.graph.execute(query)
            headers = self.engine.post.request.headers
            self.assertEqual(headers['Accept'], 'application/graql+json')

    def test_executing_an_insert_query_sends_query_in_body(self):
        self.is_insert_query()

        with self.engine:
            self.graph.execute(query)
            self.assertEqual(self.engine.post.request.body, query)

    def test_executing_an_insert_query_sends_keyspace_in_params(self):
        self.is_insert_query()

        with self.engine:
            self.graph.execute(query)
            self.assertEqual(self.engine.post.params['keyspace'], [keyspace])

    def test_executing_an_insert_query_sends_infer_in_params(self):
        self.is_insert_query()

        with self.engine:
            self.graph.execute(query)
            self.assertEqual(self.engine.post.params['infer'], ['False'])

    def test_executing_an_insert_query_sends_materialise_in_params(self):
        self.is_insert_query()

        with self.engine:
            self.graph.execute(query)
            self.assertEqual(self.engine.post.params['materialise'], ['False'])

    def test_executing_an_invalid_insert_query_throws_grakn_exception(self):
        self.is_insert_query()
        self.is_invalid_query(self.engine.post)

        with self.engine:
            with self.assertRaises(gc.GraknError, msg=error_message):
                self.graph.execute(query)

    def test_executing_a_query_without_a_server_throws_grakn_exception(self):
        with self.assertRaises(ConnectionError):
            self.graph.execute(query)
