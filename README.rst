Grakn Python Client
===================

A Python client for `Grakn <http://grakn.ai>`_.

Requires Python 3.6 and Grakn 0.17-0.18.

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

Now you can connect to a knowledge base:

.. code-block:: python

    >>> client = Graph(uri='http://localhost:4567', keyspace='mygraph')

You can write to the knowledge base:

.. code-block:: python

    >>> client.execute('define person sub entity;')
    []
    >>> client.execute('define name sub resource, datatype string;')
    []
    >>> client.execute('define person has name;')
    []
    >>> client.execute('insert $bob isa person, has name "Bob";')
    ['1234']

.. TODO: update this output when insert query output changes

Or read from it:

.. code-block:: python

    >>> graph.execute('match $bob isa person, has name $name; get $name;')
    [{'name': {'isa': 'name', 'id': '3141816', 'value': 'Bob'}}]

.. TODO: reference docs

