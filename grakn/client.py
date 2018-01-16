"""Grakn python client."""
import json
from typing import Dict, Any, Optional, Iterator, Union

import grpc

from grakn import grakn_pb2_grpc
from grakn.grakn_pb2 import TxRequest, Keyspace, Query, TxResponse

_HEADERS: Dict[str, str] = {'Accept': 'application/graql+json'}
_QUERY_ENDPOINT: str = '/kb/{}/graql'

_TIMEOUT = 60


class Client:
    """Client to a Grakn knowledge base, identified by a uri and a keyspace."""

    DEFAULT_URI: str = 'localhost:48555'
    DEFAULT_KEYSPACE: str = 'grakn'

    def __init__(self, uri: str = DEFAULT_URI, keyspace: str = DEFAULT_KEYSPACE):
        channel = grpc.insecure_channel(uri)
        self._stub = grakn_pb2_grpc.GraknStub(channel)
        self.uri = uri
        self.keyspace = keyspace

    def execute(self, query: str, *, infer: Optional[bool] = None, multi: bool = False) -> Any:
        """Execute a Graql query against the knowledge base

        :param query: the Graql query string to execute against the knowledge base
        :param infer: enable inference
        :param multi: treat this request as a list of queries
        :return: a list of query results

        :raises: GraknError, GraknConnectionError
        """
        set_infer = infer is not None

        open_tx = TxRequest(open=TxRequest.Open(keyspace=Keyspace(value=self.keyspace)))
        exec_query = TxRequest(execQuery=TxRequest.ExecQuery(query=Query(value=query), setInfer=set_infer, infer=infer))
        commit = TxRequest(commit=TxRequest.Commit())

        requests = iter((open_tx, exec_query, commit))

        try:
            responses: Iterator[TxResponse] = self._stub.Tx(requests, timeout=_TIMEOUT)
            response = next(responses)

            # we ask for another response. This tells gRPC we are done
            next(responses, None)
        except grpc.RpcError as e:
            raise _convert_grpc_error(e)

        return json.loads(response.queryResult.value)


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
