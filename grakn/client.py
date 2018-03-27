"""Grakn python client."""
import json
import time
from queue import Queue
from typing import Any, Optional, Iterator, Union, TypeVar, Generic

import grpc

import grakn_pb2_grpc
from concept_pb2 import Concept, ConceptId, ConceptMethod, Unit, RelationshipType, AttributeType, EntityType, Role, Rule
from grakn_pb2 import TxRequest, Keyspace, Query, TxResponse, Open, TxType, Write, ExecQuery, Infer, QueryResult, \
    Commit, RunConceptMethod
from iterator_pb2 import Next

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
        grpc_infer = Infer(value=infer) if infer is not None else None
        request = TxRequest(execQuery=ExecQuery(query=Query(value=query), infer=grpc_infer))
        self._requests.add(request)

        iterator_id = self._next_response().iteratorId

        query_results = []

        while True:
            next_request = TxRequest(next=Next(iteratorId=iterator_id))
            self._requests.add(next_request)
            response = self._next_response()

            if response.HasField('done'):
                break
            else:
                query_results.append(response.queryResult)

        return [self._parse_result(query_result) for query_result in query_results]

    def _parse_result(self, result: QueryResult):
        if result.HasField('otherResult'):
            return json.loads(result.otherResult)
        else:
            answer = result.answer.answer
            return {var: self._parse_concept(answer[var]) for var in answer}

    def _parse_concept(self, concept: Concept):
        concept_dict = {'id': concept.id.value}

        if concept.baseType in {RelationshipType, AttributeType, EntityType, Role, Rule}:
            concept_dict['label'] = self._get_label(concept.id)

        return concept_dict

    def _get_label(self, cid: ConceptId):
        request = TxRequest(runConceptMethod=RunConceptMethod(id=cid, conceptMethod=ConceptMethod(getLabel=Unit())))
        self._requests.add(request)
        response = self._next_response()
        return response.conceptResponse.label.value

    def commit(self):
        """Commit the transaction."""
        self._requests.add(TxRequest(commit=Commit()))


class GraknTxContext:
    """Contains a GraknTx. This should be used in a `with` statement in order to retrieve the GraknTx"""
    def __init__(self, keyspace: str, stub: grakn_pb2_grpc.GraknStub):
        self._requests = BlockingIter()

        try:
            self._responses: Iterator[TxResponse] = stub.Tx(self._requests, timeout=_TIMEOUT)
        except grpc.RpcError as e:
            raise _convert_grpc_error(e)

        request = TxRequest(open=Open(keyspace=Keyspace(value=keyspace), txType=Write))
        self._requests.add(request)

        # wait for response from "open"
        _next_response(self._responses)

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

        # wait for channel to be ready before continuing
        grpc.channel_ready_future(channel).result(timeout=_TIMEOUT)

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
    error_type = next((value for (key, value) in error.trailing_metadata() if key == 'ErrorType'), None)
    if error_type is not None:
        return GraknError(error)
    else:
        return ConnectionError(error)
