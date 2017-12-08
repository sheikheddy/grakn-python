Grakn Python Client
===================

A Python client for `Grakn <http://grakn.ai>`_.

Requires Python 3.6 and Grakn 0.18.

Installation
------------

To install the Grakn client, simply run:

.. code-block:: bash

    $ pip install grakn

You will also need access to a Grakn database.
Head `here <https://grakn.ai/pages/documentation/get-started/setup-guide.html>`_ to get started with Grakn.

Quickstart
----------

Begin by importing the client:

.. code-block:: python

    >>> from grakn.client import Graph

Now you can connect to a graph:

.. code-block:: python

    >>> graph = Graph(uri='http://localhost:4567', keyspace='mygraph')

You can write to the graph:

.. code-block:: python

    >>> graph.execute('insert person sub entity;')
    []
    >>> graph.execute('insert name sub resource, datatype string;')
    []
    >>> graph.execute('insert person has name;')
    []
    >>> graph.execute('insert $bob isa person, has name "Bob";')
    ['1234']

.. TODO: update this output when insert query output changes

Or read from it:

.. code-block:: python

    >>> graph.execute('match $bob isa person, has name $name; select $name;')
    [{'name': {'isa': 'name', 'id': '3141816', 'value': 'Bob'}}]

.. TODO: reference docs

