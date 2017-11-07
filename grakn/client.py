"""Grakn python client."""

from typing import Dict, Any

import requests

_HEADERS: Dict[str, str] = {'Accept': 'application/graql+json'}


class Graph:
    """Represents a Grakn graph, identified by a uri and a keyspace."""

    DEFAULT_URI: str = 'http://localhost:4567'

    def __init__(self, uri: str = DEFAULT_URI, keyspace: str = 'grakn'):
        self.uri = uri
        self.keyspace = keyspace

    def execute(self, query: str) -> Any:
        """Execute a Graql query against the graph

        :param query: the Graql query string to execute against the graph
        :return: a list of query results

        :raises: GraknError, requests.exceptions.ConnectionError
        """
        response = self._post(query)

        if response.ok:
            return response.json()
        else:
            raise GraknError(response.json()['exception'])

    def _post(self, query: str) -> requests.Response:
        params = self._params()
        url = self._url()
        return requests.post(url, data=query, params=params, headers=_HEADERS)

    def _url(self) -> str:
        return f'{self.uri}/kb/graql/execute'

    def _params(self) -> Dict[str, Any]:
        return {
            'keyspace': self.keyspace, 'infer': False, 'materialise': False
        }


class GraknError(Exception):
    """An exception when executing an operation on a Grakn graph"""
    pass
