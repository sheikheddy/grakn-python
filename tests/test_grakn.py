import json
import unittest
from concurrent import futures
from threading import Thread
from typing import Iterator, List, Iterable, Dict, Callable, Optional, Union

import grpc
from collections import defaultdict

import grakn
import grakn_pb2_grpc
from concept_pb2 import Concept, ConceptId, Unit, ConceptMethod, ConceptResponse, Label
from grakn_pb2 import TxRequest, TxResponse, Keyspace, Query, Open, Write, QueryResult, Answer, Done, ExecQuery, Infer, \
    RunConceptMethod, Commit
from grakn_pb2_grpc import GraknServicer
from iterator_pb2 import Next, IteratorId

ITERATOR_ID = iteratorId=IteratorId(id=5)
ITERATOR_RESPONSE = TxResponse(iteratorId=ITERATOR_ID)
DONE = TxResponse(done=Done())
NEXT = TxRequest(next=Next(iteratorId=ITERATOR_ID))

query: str = 'match $x sub concept; limit 3;'

expected_response = [
    {'x': {'id': 'a', 'label': 'concept'}},
    {'x': {'id': 'b', 'label': 'entity'}},
    {'x': {'id': 'c', 'label': 'resource'}}
]

grpc_answers = [
    Answer(answer={'x': Concept(id=ConceptId(value='a'))}),
    Answer(answer={'x': Concept(id=ConceptId(value='b'))}),
    Answer(answer={'x': Concept(id=ConceptId(value='c'))})
]
grpc_responses = [QueryResult(answer=grpc_answer) for grpc_answer in grpc_answers]

error_message: str = 'sorry we changed the syntax again'

mock_uri: str = 'localhost:48556'
mock_uri_to_no_server: str = 'localhost:9999'
keyspace: str = 'somesortofkeyspace'


def eq(tx_request: TxRequest):
    return lambda other: other == tx_request


class MockResponse:
    def __init__(self, request_matcher: Callable[[TxRequest], bool], response: TxResponse):
        self._request_matcher = request_matcher
        self._response = response

    def test(self, request: TxRequest) -> Optional[TxResponse]:
        if self._request_matcher(request):
            return self._response
        else:
            return None


class MockGraknServicer(GraknServicer):

    def __init__(self):
        self.responses = []
        self.error = None
        self.requests = None

    def Tx(self, request_iterator: Iterator[TxRequest], context: grpc.ServicerContext) -> Iterator[TxResponse]:
        if self.error is not None:
            context.set_code(grpc.StatusCode.UNKNOWN)
            context.set_trailing_metadata([("message", self.error)])
            return None

        self.requests = []

        for request in request_iterator:
            print(f"REQUEST: {request}")
            self.requests.append(request)

            for mock_response in self.responses:
                tx_response = mock_response.test(request)
                if tx_response is not None:
                    print(f"RESPONSE: {tx_response}")
                    self.responses.remove(mock_response)
                    yield tx_response
                    break
            else:
                yield DONE

    def Delete(self, request, context):
        raise NotImplementedError


class GrpcServer:
    @property
    def requests(self) -> List[TxRequest]:
        return self._servicer.requests

    @requests.setter
    def requests(self, value: List[TxRequest]):
        self._servicer.requests = value

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

    def verify(self, predicate: Union[TxRequest, Callable[[TxRequest], bool]]):
        assert self._test(predicate), f"Expected {predicate}"

    def _test(self, predicate: Union[TxRequest, Callable[[TxRequest], bool]]) -> bool:
        if predicate in SERVER.requests:
            return True
        else:
            try:
                if any(predicate(r) for r in SERVER.requests):
                    return True
                else:
                    return False
            except TypeError:
                return False

    def __init__(self, *, responses: List[MockResponse] = None, error: str = None):
        self._responses = responses if responses else []
        self._error = error

    def __enter__(self):
        SERVER.requests = None
        SERVER._servicer.responses = self._responses
        SERVER.error = self._error
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


def _mock_label_response(cid: str, label: str) -> MockResponse:
    run_concept_method = RunConceptMethod(id=ConceptId(value=cid), conceptMethod=ConceptMethod(getLabel=Unit()))
    concept_response = ConceptResponse(label=Label(value=label))
    request = TxRequest(runConceptMethod=run_concept_method)
    return MockResponse(eq(request), TxResponse(conceptResponse=concept_response))


def engine_responding_to_query() -> MockEngine:
    mock_responses = [MockResponse(lambda req: req.execQuery.query.value == query, ITERATOR_RESPONSE)]
    mock_responses += [MockResponse(eq(NEXT), TxResponse(queryResult=grpc_response)) for grpc_response in grpc_responses]
    mock_responses.append(MockResponse(eq(NEXT), DONE))

    mock_responses += [
        _mock_label_response('a', 'concept'), _mock_label_response('b', 'entity'), _mock_label_response('c', 'resource')
    ]

    return MockEngine(responses=mock_responses)


def engine_responding_with_nothing() -> MockEngine:
    return MockEngine()


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
        with engine_responding_to_query():
            self.assertEqual(self.client.execute(query), expected_response)

    def test_sends_open_request_with_keyspace(self):
        with engine_responding_to_query() as engine:
            self.client.execute(query)
            expected_request = TxRequest(open=Open(keyspace=Keyspace(value=keyspace), txType=Write))
            engine.verify(expected_request)

    def test_sends_execute_query_request_with_parameters(self):
        with engine_responding_to_query() as engine:
            self.client.execute(query)
            expected = TxRequest(execQuery=ExecQuery(query=Query(value=query), infer=None))
            engine.verify(expected)

    def test_specifies_inference_on_when_requested(self):
        with engine_responding_to_query() as engine:
            self.client.execute(query, infer=True)
            engine.verify(lambda req: req.execQuery.infer.value)

    def test_specifies_inference_off_when_requested(self):
        with engine_responding_to_query() as engine:
            self.client.execute(query, infer=False)
            engine.verify(lambda req: not req.execQuery.infer.value)

    def test_sends_commit_request(self):
        with engine_responding_to_query() as engine:
            self.client.execute(query)
            expected = TxRequest(commit=Commit())
            engine.verify(expected)

    def test_completes_request(self):
        with engine_responding_to_query():
            self.client.execute(query)

    def test_throws_with_invalid_query(self):
        throws_error = self.assertRaises(grakn.GraknError, msg=error_message)
        with engine_responding_bad_request(), throws_error:
            self.client.execute(query)

    def test_throws_without_server(self):
        with self.assertRaises(ConnectionError):
            self.client_to_no_server.execute(query)


class TestOpenTx(unittest.TestCase):

    def setUp(self):
        self._original_timeout = grakn.client._TIMEOUT
        grakn.client._TIMEOUT = 5
        self.client = grakn.Client(uri=mock_uri, keyspace=keyspace)
        self.client_to_no_server = grakn.Client(uri=mock_uri_to_no_server, keyspace=keyspace)

    def tearDown(self):
        grakn.client._TIMEOUT = self._original_timeout

    def test_sends_open_request_with_keyspace(self):
        with engine_responding_with_nothing() as engine, self.client.open():
            pass

        expected_request = TxRequest(open=Open(keyspace=Keyspace(value=keyspace), txType=Write))
        engine.verify(expected_request)

    def test_completes_request(self):
        with engine_responding_to_query(), self.client.open() as tx:
            tx.execute(query)
            tx.commit()


class TestExecuteOnTx(unittest.TestCase):

    def setUp(self):
        self._original_timeout = grakn.client._TIMEOUT
        grakn.client._TIMEOUT = 5
        self.client = grakn.Client(uri=mock_uri, keyspace=keyspace)
        self.client_to_no_server = grakn.Client(uri=mock_uri_to_no_server, keyspace=keyspace)

    def tearDown(self):
        grakn.client._TIMEOUT = self._original_timeout

    def test_valid_query_returns_expected_response(self):
        with engine_responding_to_query() as engine, self.client.open() as tx:
            self.assertEqual(tx.execute(query), expected_response)

    def test_sends_execute_query_request_with_parameters(self):
        with engine_responding_to_query() as engine, self.client.open() as tx:
            tx.execute(query)

        expected = TxRequest(execQuery=ExecQuery(query=Query(value=query), infer=None))
        engine.verify(expected)

    def test_specifies_inference_on_when_requested(self):
        with engine_responding_to_query() as engine, self.client.open() as tx:
            tx.execute(query, infer=True)

        engine.verify(lambda req: req.execQuery.infer.value)

    def test_specifies_inference_off_when_requested(self):
        with engine_responding_to_query() as engine, self.client.open() as tx:
            tx.execute(query, infer=False)

        engine.verify(lambda req: not req.execQuery.infer.value)


class TestCommit(unittest.TestCase):

    def setUp(self):
        self._original_timeout = grakn.client._TIMEOUT
        grakn.client._TIMEOUT = 5
        self.client = grakn.Client(uri=mock_uri, keyspace=keyspace)
        self.client_to_no_server = grakn.Client(uri=mock_uri_to_no_server, keyspace=keyspace)

    def tearDown(self):
        grakn.client._TIMEOUT = self._original_timeout

    def test_sends_commit_request(self):
        with engine_responding_to_query() as engine, self.client.open() as tx:
            tx.execute(query)
            tx.commit()

        expected = TxRequest(commit=Commit())
        engine.verify(expected)
