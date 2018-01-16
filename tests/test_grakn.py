import json
import unittest
from concurrent import futures
from typing import Iterator, List, Iterable

import grpc

import grakn
from grakn import grakn_pb2_grpc
from grakn.grakn_pb2 import TxRequest, TxResponse, Keyspace, Query
from grakn.grakn_pb2_grpc import GraknServicer

query: str = 'match $x sub concept; limit 3;'

expected_response = [
    {'id': 'a', 'label': 'concept'},
    {'id': 'b', 'label': 'entity'},
    {'id': 'c', 'label': 'resource'}
]

error_message: str = 'sorry we changed the syntax again'

mock_uri: str = 'localhost:48556'
mock_uri_to_no_server: str = 'localhost:9999'
keyspace: str = 'somesortofkeyspace'


class MockGraknServicer(GraknServicer):
    def __init__(self):
        self.responses = None
        self.error = None
        self.requests = None

    def Tx(self, request_iterator: Iterator[TxRequest], context: grpc.ServicerContext) -> Iterator[TxResponse]:
        if self.error is not None:
            context.set_code(grpc.StatusCode.UNKNOWN)
            context.set_trailing_metadata([("message", self.error)])
            return None

        for response in self.responses:
            print(f"RESPONSE: {response}")
            yield response

        self.requests = list(request_iterator)
        print(f"REQUESTS: {self.requests}")


class GrpcServer:
    @property
    def requests(self) -> List[TxRequest]:
        return self._servicer.requests

    @requests.setter
    def requests(self, value: List[TxRequest]):
        self._servicer.requests = value

    @property
    def responses(self) -> List[TxResponse]:
        return self._servicer.responses

    @responses.setter
    def responses(self, value: List[TxResponse]):
        self._servicer.responses = value

    @property
    def error(self) -> str:
        return self._servicer.error

    @error.setter
    def error(self, value: str):
        self._servicer.error = value

    def __init__(self):
        servicer = MockGraknServicer()

        thread_pool = futures.ThreadPoolExecutor()
        server = grpc.server(thread_pool)
        grakn_pb2_grpc.add_GraknServicer_to_server(servicer, server)
        server.add_insecure_port('[::]:48556')
        server.start()

        self._servicer = servicer
        self._server = server


SERVER = GrpcServer()


class MockEngine:
    @property
    def requests(self) -> List[TxRequest]:
        return SERVER.requests

    def __init__(self, *, responses: Iterable[TxResponse] = None, error: str = None):
        self._responses = responses
        self._error = error

    def __enter__(self):
        SERVER.requests = None
        SERVER.responses = self._responses
        SERVER.error = self._error
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


def engine_responding_ok() -> MockEngine:
    return MockEngine(responses=[TxResponse(queryResult=TxResponse.QueryResult(value=json.dumps(expected_response)))])


def engine_responding_bad_request() -> MockEngine:
    return MockEngine(error=error_message)


class TestClientConstructor(unittest.TestCase):
    def test_accepts_no_arguments(self):
        client = grakn.Client()
        self.assertEqual(client.keyspace, 'grakn')
        self.assertEqual(client.uri, 'localhost:48555')

    def test_accepts_two_arguments(self):
        client = grakn.Client('www.google.com', 'mykeyspace')
        self.assertEqual(client.uri, 'www.google.com')
        self.assertEqual(client.keyspace, 'mykeyspace')

    def test_accepts_keyword_arguments(self):
        client = grakn.Client(keyspace='mykeyspace', uri='www.google.com')
        self.assertEqual(client.uri, 'www.google.com')
        self.assertEqual(client.keyspace, 'mykeyspace')


class TestExecute(unittest.TestCase):
    def setUp(self):
        self._original_timeout = grakn.client._TIMEOUT
        grakn.client._TIMEOUT = 5
        self.client = grakn.Client(uri=mock_uri, keyspace=keyspace)
        self.client_to_no_server = grakn.Client(uri=mock_uri_to_no_server, keyspace=keyspace)

    def tearDown(self):
        grakn.client._TIMEOUT = self._original_timeout

    def test_valid_query_returns_expected_response(self):
        with engine_responding_ok():
            self.assertEqual(self.client.execute(query), expected_response)

    def test_sends_open_request_with_keyspace(self):
        with engine_responding_ok() as engine:
            self.client.execute(query)
            expected_request = TxRequest(open=TxRequest.Open(keyspace=Keyspace(value=keyspace)))
            self.assertEqual(engine.requests[0], expected_request)

    def test_sends_execute_query_request_with_parameters(self):
        with engine_responding_ok() as engine:
            self.client.execute(query)
            expected = TxRequest(execQuery=TxRequest.ExecQuery(query=Query(value=query), setInfer=False))
            self.assertEqual(engine.requests[1], expected)

    def test_specifies_inference_on_when_requested(self):
        with engine_responding_ok() as engine:
            self.client.execute(query, infer=True)
            self.assertEqual(engine.requests[1].execQuery.setInfer, True)
            self.assertEqual(engine.requests[1].execQuery.infer, True)

    def test_specifies_inference_off_when_requested(self):
        with engine_responding_ok() as engine:
            self.client.execute(query, infer=False)
            self.assertEqual(engine.requests[1].execQuery.setInfer, True)
            self.assertEqual(engine.requests[1].execQuery.infer, False)

    def test_sends_commit_request(self):
        with engine_responding_ok() as engine:
            self.client.execute(query)
            expected = TxRequest(commit=TxRequest.Commit())
            self.assertEqual(engine.requests[2], expected)

    def test_completes_request(self):
        with engine_responding_ok() as engine:
            self.client.execute(query)
            self.assertEqual(len(engine.requests), 3)

    def test_throws_with_invalid_query(self):
        throws_error = self.assertRaises(grakn.GraknError, msg=error_message)
        with engine_responding_bad_request(), throws_error:
            self.client.execute(query)

    def test_throws_without_server(self):
        with self.assertRaises(ConnectionError):
            self.client_to_no_server.execute(query)
