Grakn Python Client
===================

A Python client for `Grakn <http://grakn.ai>`_.

Requires Python 3.6 and Grakn 1.0.

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

    >>> import grakn

Now you can connect to a knowledge base:

.. code-block:: python

    >>> client = grakn.Client(uri='localhost:48555', keyspace='mykb')

You can write to the knowledge base:

.. code-block:: python

    
    >>> client.execute('define person sub entity;')
    {}
    >>> client.execute('define name sub attribute, datatype string;')
    {}
    >>> client.execute('define person has name;')
    {}
    >>> client.execute('insert $bob isa person, has name "Bob";')
    [{'bob': {'id': ...}}]
    >>>

.. TODO: update this output when insert query output changes

Or read from it:

.. code-block:: python

    >>> tx.execute('match $bob isa person, has name $name; get $name;')
    [{'name': {'value': 'Bob', 'id': ...}}]
    ...
    >>>

.. TODO: reference docs

