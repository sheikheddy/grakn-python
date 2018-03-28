import unittest

import grakn
from grakn_pb2 import TxRequest, Keyspace, Query, Open, Write, ExecQuery, \
    Commit
from tests.mock_engine import query, engine_responding_to_query, \
    engine_responding_with_nothing, engine_responding_bad_request, error_message

expected_response = [
    {'x': {'id': 'a', 'label': 'concept'}},
    {'x': {'id': 'b', 'label': 'entity'}},
    {'x': {'id': 'c', 'label': 'resource'}}
]

mock_uri: str = 'localhost:48556'
mock_uri_to_no_server: str = 'localhost:9999'
keyspace: str = 'somesortofkeyspace'


class TestClientConstructor(unittest.TestCase):
    def test_accepts_no_arguments(self) -> None:
        client = grakn.Client()
        self.assertEqual(client.keyspace, 'grakn')
        self.assertEqual(client.uri, 'localhost:48555')

    def test_accepts_two_arguments(self) -> None:
        client = grakn.Client('www.google.com', 'mykeyspace')
        self.assertEqual(client.uri, 'www.google.com')
        self.assertEqual(client.keyspace, 'mykeyspace')

    def test_accepts_keyword_arguments(self) -> None:
        client = grakn.Client(keyspace='mykeyspace', uri='www.google.com')
        self.assertEqual(client.uri, 'www.google.com')
        self.assertEqual(client.keyspace, 'mykeyspace')


class TestExecute(unittest.TestCase):
    def test_valid_query_returns_expected_response(self) -> None:
        with engine_responding_to_query():
            self.assertEqual(client().execute(query), expected_response)

    def test_sends_open_request_with_keyspace(self) -> None:
        with engine_responding_to_query() as engine:
            client().execute(query)
            expected_request = TxRequest(open=Open(keyspace=Keyspace(value=keyspace), txType=Write))
            engine.verify(expected_request)

    def test_sends_execute_query_request_with_parameters(self) -> None:
        with engine_responding_to_query() as engine:
            client().execute(query)
            expected = TxRequest(execQuery=ExecQuery(query=Query(value=query), infer=None))
            engine.verify(expected)

    def test_specifies_inference_on_when_requested(self) -> None:
        with engine_responding_to_query() as engine:
            client().execute(query, infer=True)
            engine.verify(lambda req: req.execQuery.infer.value)

    def test_specifies_inference_off_when_requested(self) -> None:
        with engine_responding_to_query() as engine:
            client().execute(query, infer=False)
            engine.verify(lambda req: not req.execQuery.infer.value)

    def test_sends_commit_request(self) -> None:
        with engine_responding_to_query() as engine:
            client().execute(query)
            expected = TxRequest(commit=Commit())
            engine.verify(expected)

    def test_completes_request(self) -> None:
        with engine_responding_to_query():
            client().execute(query)

    def test_throws_with_invalid_query(self) -> None:
        throws_error = self.assertRaises(grakn.GraknError, msg=error_message)
        with engine_responding_bad_request(), throws_error:
            client().execute(query)

    def test_throws_without_server(self) -> None:
        with self.assertRaises(ConnectionError):
            client_to_no_server = grakn.Client(uri=mock_uri_to_no_server, keyspace=keyspace, timeout=5)
            client_to_no_server.execute(query)


class TestOpenTx(unittest.TestCase):
    def test_sends_open_request_with_keyspace(self) -> None:
        with engine_responding_with_nothing() as engine, client().open():
            pass

        expected_request = TxRequest(open=Open(keyspace=Keyspace(value=keyspace), txType=Write))
        engine.verify(expected_request)

    def test_completes_request(self) -> None:
        with engine_responding_to_query(), client().open() as tx:
            tx.execute(query)
            tx.commit()


class TestExecuteOnTx(unittest.TestCase):
    def test_valid_query_returns_expected_response(self) -> None:
        with engine_responding_to_query(), client().open() as tx:
            self.assertEqual(tx.execute(query), expected_response)

    def test_sends_execute_query_request_with_parameters(self) -> None:
        with engine_responding_to_query() as engine, client().open() as tx:
            tx.execute(query)

        expected = TxRequest(execQuery=ExecQuery(query=Query(value=query), infer=None))
        engine.verify(expected)

    def test_specifies_inference_on_when_requested(self) -> None:
        with engine_responding_to_query() as engine, client().open() as tx:
            tx.execute(query, infer=True)

        engine.verify(lambda req: req.execQuery.infer.value)

    def test_specifies_inference_off_when_requested(self) -> None:
        with engine_responding_to_query() as engine, client().open() as tx:
            tx.execute(query, infer=False)

        engine.verify(lambda req: not req.execQuery.infer.value)


class TestCommit(unittest.TestCase):
    def test_sends_commit_request(self) -> None:
        with engine_responding_to_query() as engine, client().open() as tx:
            tx.execute(query)
            tx.commit()

        expected = TxRequest(commit=Commit())
        engine.verify(expected)


def client() -> grakn.Client:
    return grakn.Client(uri=mock_uri, keyspace=keyspace, timeout=5)
