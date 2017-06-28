"""Grakn python client."""

from typing import List, Dict, Any, Union
import requests

Var = str
Concept = Dict[str, Any]
Result = Dict[Var, Concept]

MatchResponse = List[Result]
InsertResponse = List[str]  # TODO: Remove this when endpoint changes response
DeleteResponse = None

GraqlResponse = Union[MatchResponse, InsertResponse, DeleteResponse]

_HEADERS: Dict[str, str] = {'Accept': 'application/graql+json'}


class Graph:
    """Represents a Grakn graph, identified by a uri and a keyspace."""

    DEFAULT_URI: str = 'http://localhost:4567'

    def __init__(self, uri: str = DEFAULT_URI, keyspace: str = 'grakn'):
        self.uri = uri
        self.keyspace = keyspace

    def execute(self, query: str) -> GraqlResponse:
        """Execute a Graql query against the graph

        :param query: the Graql query string to execute against the graph
        :return: a list of query results

        :raises: GraknError, requests.exceptions.ConnectionError
        """
        methods = [self._get, self._post, self._delete]

        response = None

        # TODO: Remove this behaviour when there is one Graql endpoint to query
        for method in methods:
            response = method(query)
            right_endpoint = response.status_code != 405
            if right_endpoint:
                break

        if response.ok:
            return response.json().get('response')
        else:
            raise GraknError(response.json()['exception'])

    def _get(self, query: str) -> requests.Response:
        params = self._params()
        params['query'] = query
        url = self._url()
        return requests.get(url, params=params, headers=_HEADERS)

    def _post(self, query: str) -> requests.Response:
        params = self._params()
        url = self._url()
        return requests.post(url, data=query, params=params, headers=_HEADERS)

    def _delete(self, query: str) -> requests.Response:
        params = self._params()
        url = self._url()
        return requests.delete(url, data=query, params=params, headers=_HEADERS)

    def _url(self) -> str:
        return f'{self.uri}/graph/graql'

    def _params(self) -> Dict[str, Any]:
        return {
            'keyspace': self.keyspace, 'infer': False, 'materialise': False
        }


class GraknError(Exception):
    """An exception when executing an operation on a Grakn graph"""
    pass
