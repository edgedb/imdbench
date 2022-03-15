WebAppBench: Realistic benchmarks for ORMs
==========================================

``Rev. 1.0.0``

A benchmark intended to compare various Python and JavaScript 
ORMs against EdgeDB and other databases, using realistic queries. 

Why is this needed?
-------------------

The question of ORM performance is more complex than simply "they generate slow queries".

1. It's common for ORMs to perform non-trivial operations (deep fetching, nested mutation, inline aggregation, etc) by opaquely executing several queries against the underlying database. These queries rely on The incurred latency is rarely reflected in more simplistic ORM benchmarks.

2. Less sophisticated ORMs may not support such functionality at all, forcing users to manually compose several simpler queries themselves. Transactions are required to ensure data consistency among these serially-executed queries, which can place unacceptable limits on request throughput. 

3. Dispensing with transactions may simplify the implementation but can result in hard-to-reproduce data integrity bugs. 

Why "Just use SQL" isn't enough
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The popularity of ORM libraries is driven by their ability to express deep or nested queries in an approachable way, relative to raw SQL. Their underlying  object-oriented schema allows for more intuitive ways of expressing these operations.

We are sympathetic to this; SQLs lack of composability and `incompatibility <https://en.wikipedia.org/wiki/Object%E2%80%93relational_impedance_mismatch>`_ with the predominantly object-oriented nature of modern languages is a real usability issue. 

While ORMs are largely incapable of expressing complex queries that include computed fields or aggregation, the common refrain of "Just use SQL" is also too simplistic. SQL queries quickly explode in verbosity when expressing operations like deep fetches, subqueries, and aggregations. T declarative/object-oriented approach to schema modeling, and the desire for idiomatic code-first data fetching APIs in different languages. As statically typed languages like Go and TypeScript gain popularity, the ability of ORMs to return strongly-typed query results in a DRY, non-reduntant way is increasingly desirable.

Targets
-------

The benchmarks target the following set of ORMs and databases.

**Python ORMs**

- `Django ORM v3 <https://docs.djangoproject.com/en/4.0/topics/db/queries/>`_
- `SQLAlchemy 1.4 <https://www.sqlalchemy.org/>`_

**JavaScript ORMs**

- `Prisma v3 <https://www.prisma.io/>`_
- `TypeORM 0.2.41 <https://typeorm.io/#/>`_
- `Sequelize v6 <https://sequelize.org/>`
- `EdgeDB query builder <https://www.edgedb.com/docs/clients/01_js/index>`_

**Databases/CMS**

- `Hasura v2 <https://hasura.io/>`_
- `Postgraphile 4.11 <https://www.graphile.org/postgraphile/>`_
- `MongoDB 5.0 + Python client <https://www.mongodb.com/>`_
- `Postgres 13 <https://www.postgresql.org/docs/13/index.html>`_

   - with ``asyncpg``
   - with ``psycopg2``
   - with ``pq``
   - with ``pgx``
   - with ``pg`` (Node.js)

- `EdgeDB 1.0 <https://edgedb.com>`_ 

   - `Node.js client <https://github.com/edgedb/edgedb-js>`_
   - `Python client <https://github.com/edgedb/edgedb-python>`_
   - `Go client <https://github.com/edgedb/edgedb-go>`_
   - `GraphQL endpoint <https://www.edgedb.com/docs/graphql/index>`_
   - `EdgeQL-over-HTTP <https://www.edgedb.com/docs/clients/90_edgeql/index>`_

Methodology
-----------

This benchmark is called "WebAppBench" to simulate the kinds of queries that are required in a non-trivial web application. In this case, we are simulating a Letterboxd-style movie review application. 

**Schema**

The schema consisting of four main types: ``Movie``, ``Person`` (used to represent the cast and crew), ``Review``, and ``User``. Each type contains a number of properties. Each ``Movie`` contains a "to many" relation to its ``directors`` and ``cast`` (both ``Person``). Each ``Review`` contains "to one" relations to its ``author`` (a ``Person``) and the ``movie`` it is about.

**Queries**

The following queries have been implemented for each target.

Run the benchmarks
------------------

#. Install Python 3.8 and create a virtual environment. We recommend using `pyenv <https://github.com/pyenv/pyenv_>` to avoid conflicts with existing Python versions.

   .. code-block::
   
      pyenv install 3.8.12
      pyenv local 3.8.12
      python -m venv my_venv
   

#. Install dependencies from ``requirements.txt``

   .. code-block::
   
      pip install -r requirements.txt

#. Install the following toolchains:

   - `EdgeDB <https://www.edgedb.com/install_>`
   - `PostgreSQL 13 <https://www.postgresql.org/docs/13/installation.html>`_
   - `Golang <https://go.dev/doc/install>`_
   - (Optional) `MongoDB <https://docs.mongodb.com/manual/installation/>`_

#. Install `Node.js <https://nodejs.org/en/download/>`_ v14.16.0+.

#. Install `Docker <https://docs.docker.com/get-docker/>`_ and `docker-compose <https://docs.docker.com/compose/install/>`_ (needed for Hasura).

.. 6. Install Prisma via ``npm install prisma -D``.

#. Install ``synth``. (https://www.getsynth.com)

     **Note:**
     Synth v0.5.0 replaces python faker with fake-rs, and loses
     support for some generators used by this project.
     The previous supported version, Synth v0.4.7, can be installed
     from https://github.com/getsynth/synth/releases/tag/v0.4.7

#. [Optional] A sample dataset consisting of 100000 people, 100000 users, 
   and 500000 reviews already exists in the ``dataset/build`` directory. Optionally, you can generate a fresh dataset like so: 
   
   .. code-block::

      $ make new-dataset

   You can also customize the number of inserted objects with the arguments ``people``, ``user``, and ``reviews``:

   .. code-block::

      $ make new-dataset people=5000 user=1000 reviews=100

#. Load the data into the test databases via ``$ make load``.

#. Compile Go files: ``$ make go``

#. Compile TypeScript files: ``$ make ts``

#. Run the benchmarks via ``bench.py``.

   To run all benchmarks:

   .. code-block::

      python bench.py --html out.html --concurrency 10 -D 10 all

   To run all JavaScript ORM benchmarks:

   .. code-block::

      python bench.py --html out.html --concurrency 10 --duration 10 typeorm,sequelize,postgres_prisma_js,edgedb_querybuilder

   To run all Python ORM benchmarks:

   .. code-block::

      python bench.py --html out.html --concurrency 10 --duration 10 django,sqlalchemy
   
   To customize the targets, just pass a comma-separated list of the following options.

   - ``edgedb_json_sync``
   - ``edgedb_json_async``
   - ``edgedb_repack_sync``
   - ``edgedb_graphql_go``
   - ``edgedb_http_go``
   - ``edgedb_json_go``
   - ``edgedb_repack_go``
   - ``django``
   - ``django_restfw``
   - ``mongodb``
   - ``sqlalchemy``
   - ``postgres_asyncpg``
   - ``postgres_psycopg``
   - ``postgres_pq``
   - ``postgres_pgx``
   - ``postgres_hasura_go``
   - ``postgres_postgraphile_go``
   - ``edgedb_json_js``
   - ``edgedb_repack_js``
   - ``edgedb_querybuilder_js``
   - ``edgedb_querybuilder_uncached_js``
   - ``typeorm``
   - ``sequelize``
   - ``postgres_js``
   - ``postgres_prisma_js``
   - ``postgres_prisma_tuned_js``

   You can see a full list of command options like so:

   .. code-block::

      python bench.py --help

License
-------

Apache 2.0.
