import grakn
import unittest
import json
from typing import Any
from requests import PreparedRequest
import httmock
from httmock import urlmatch, HTTMock
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
    def __init__(self, status_code: int, response: Any):
        self.headers: dict = None
        self.body: str = None
        self.path: str = None
        self.params: dict = None

        @urlmatch(netloc=mock_uri, path='^/kb/.*/graql$', method='POST')
        def grakn_mock(url: SplitResult, request: PreparedRequest):
            self.headers = request.headers
            self.body = request.body
            self.path = url.path
            self.params = parse_qs(url.query)
            return httmock.response(status_code, json.dumps(response))

        self._httmock: HTTMock = HTTMock(grakn_mock)

    def __enter__(self):
        self._httmock.__enter__()
        return self

    def __exit__(self, *args, **kwargs):
        self._httmock.__exit__(*args, **kwargs)


def engine_responding_ok() -> MockEngine:
    return MockEngine(status_code=200, response=expected_response)


def engine_responding_bad_request() -> MockEngine:
    return MockEngine(status_code=400, response={'exception': error_message})


class TestClientConstructor(unittest.TestCase):
    def test_accepts_no_arguments(self):
        client = grakn.Client()
        self.assertEqual(client.keyspace, 'grakn')
        self.assertEqual(client.uri, 'http://localhost:4567')

    def test_accepts_two_arguments(self):
        client = grakn.Client('http://www.google.com', 'mykeyspace')
        self.assertEqual(client.uri, 'http://www.google.com')
        self.assertEqual(client.keyspace, 'mykeyspace')

    def test_accepts_keyword_arguments(self):
        client = grakn.Client(keyspace='mykeyspace', uri='http://www.google.com')
        self.assertEqual(client.uri, 'http://www.google.com')
        self.assertEqual(client.keyspace, 'mykeyspace')


class TestExecute(unittest.TestCase):
    def setUp(self):
        self.client = grakn.Client(uri=f'http://{mock_uri}', keyspace=keyspace)

    def test_valid_query_returns_expected_response(self):
        with engine_responding_ok():
            self.assertEqual(self.client.execute(query), expected_response)

    def test_sends_expected_accept_header(self):
        with engine_responding_ok() as engine:
            self.client.execute(query)
            self.assertEqual(engine.headers['Accept'], 'application/graql+json')

    def test_sends_query_in_body(self):
        with engine_responding_ok() as engine:
            self.client.execute(query)
            self.assertEqual(engine.body, query)

    def test_sends_keyspace_in_path(self):
        with engine_responding_ok() as engine:
            self.client.execute(query)
            self.assertEqual(engine.path, f'/kb/{keyspace}/graql')

    def test_sends_infer_true_in_params(self):
        with engine_responding_ok() as engine:
            self.client.execute(query)
            self.assertEqual(engine.params['infer'], ['True'])

    def test_sends_infer_false_when_specified(self):
        with engine_responding_ok() as engine:
            self.client.execute(query, infer=False)
            self.assertEqual(engine.params['infer'], ['False'])

    def test_sends_materialise_in_params(self):
        with engine_responding_ok() as engine:
            self.client.execute(query)
            self.assertEqual(engine.params['materialise'], ['False'])

    def test_sends_multi_false_when_unspecified(self):
        with engine_responding_ok() as engine:
            self.client.execute(query)
            self.assertEqual(engine.params['multi'], ['False'])

    def test_sends_multi_true_when_specified(self):
        with engine_responding_ok() as engine:
            self.client.execute(query, multi=True)
            self.assertEqual(engine.params['multi'], ['True'])

    def test_throws_with_invalid_query(self):
        throws_error = self.assertRaises(grakn.GraknError, msg=error_message)
        with engine_responding_bad_request(), throws_error:
            self.client.execute(query)

    def test_insert_query_returns_expected_response(self):
        with engine_responding_ok():
            self.assertEqual(self.client.execute(query), expected_response)

    def test_throws_without_server(self):
        with self.assertRaises(ConnectionError):
            self.client.execute(query)
