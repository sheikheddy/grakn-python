"""Grakn python client."""
import json
from queue import Queue
from typing import Any, Optional, Iterator, Union, TypeVar, Generic

import grpc

from grakn import grakn_pb2_grpc
from grakn.grakn_pb2 import TxRequest, Keyspace, Query, TxResponse

_TIMEOUT = 60

T = TypeVar('T')


class BlockingIter(Generic[T]):
    def __init__(self):
        self._queue = Queue()

    def __iter__(self) -> Iterator[T]:
        return self

    def __next__(self) -> T:
        elem = self._queue.get(block=True)
        if elem is None:
            raise StopIteration()
        else:
            return elem

    def add(self, elem: T):
        if elem is None:
            raise ValueError()
        else:
            self._queue.put(elem)

    def close(self):
        self._queue.put(None)


def _next_response(responses: Iterator[TxResponse], default: Optional[TxResponse] = None) -> TxResponse:
    try:
        return next(responses, default)
    except grpc.RpcError as e:
        raise _convert_grpc_error(e)


class GraknTx:
    """A transaction against a knowledge graph. The transaction ends when its surrounding context closes."""

    def __init__(self, requests: BlockingIter[TxRequest], responses: Iterator[TxResponse]):
        self._requests = requests
        self._responses = responses

    def _next_response(self) -> TxResponse:
        return _next_response(self._responses)

    def execute(self, query: str, *, infer: Optional[bool] = None) -> Any:
        """Execute a Graql query against the knowledge base

        :param query: the Graql query string to execute against the knowledge base
        :param infer: enable inference
        :return: a list of query results

        :raises: GraknError, GraknConnectionError
        """
        set_infer = infer is not None
        exec_query = TxRequest(execQuery=TxRequest.ExecQuery(query=Query(value=query), setInfer=set_infer, infer=infer))
        self._requests.add(exec_query)
        response = self._next_response()
        return json.loads(response.queryResult.value)

    def commit(self):
        """Commit the transaction."""
        self._requests.add(TxRequest(commit=TxRequest.Commit()))


class GraknTxContext:
    """Contains a GraknTx. This should be used in a `with` statement in order to retrieve the GraknTx"""
    def __init__(self, keyspace: str, stub: grakn_pb2_grpc.GraknStub):
        self._requests = BlockingIter()

        self._requests.add(TxRequest(open=TxRequest.Open(keyspace=Keyspace(value=keyspace))))

        try:
            self._responses: Iterator[TxResponse] = stub.Tx(self._requests, timeout=_TIMEOUT)

        except grpc.RpcError as e:
            raise _convert_grpc_error(e)

        self._tx = GraknTx(self._requests, self._responses)

    def __enter__(self) -> GraknTx:
        return self._tx

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._requests.close()
        # we ask for another response. This tells gRPC we are done
        _next_response(self._responses, None)


class Client:
    """Client to a Grakn knowledge base, identified by a uri and a keyspace."""

    DEFAULT_URI: str = 'localhost:48555'
    DEFAULT_KEYSPACE: str = 'grakn'

    def __init__(self, uri: str = DEFAULT_URI, keyspace: str = DEFAULT_KEYSPACE):
        channel = grpc.insecure_channel(uri)
        self._stub = grakn_pb2_grpc.GraknStub(channel)
        self.uri = uri
        self.keyspace = keyspace

    def execute(self, query: str, *, infer: Optional[bool] = None) -> Any:
        """Execute and commit a Graql query against the knowledge base

        :param query: the Graql query string to execute against the knowledge base
        :param infer: enable inference
        :return: a list of query results

        :raises: GraknError, GraknConnectionError
        """
        with self.open() as tx:
            result = tx.execute(query, infer=infer)
            tx.commit()
        return result

    def open(self) -> GraknTxContext:
        """Open a transaction

        :return: a GraknTxContext that can be opened using a `with` statement
        """
        return GraknTxContext(self.keyspace, self._stub)


class GraknError(Exception):
    """An exception when executing an operation on a Grakn knowledge base"""
    pass


def _convert_grpc_error(error: grpc.RpcError) -> Union[GraknError, ConnectionError]:
    """Convert an error message from gRPC into a GraknError or a ConnectionError"""
    assert isinstance(error, grpc.Call)
    message = next((value for (key, value) in error.trailing_metadata() if key == 'message'), None)
    if message is not None:
        return GraknError(message)
    else:
        return ConnectionError(error)
