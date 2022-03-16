RealCruddyBench: Realistic benchmarks for ORMs
==============================================

``Rev. 1.0.0``

A benchmark intended to compare various Python and JavaScript 
ORMs against EdgeDB and other databases, using realistic queries. 

Why is this needed?
-------------------

The question of ORM performance is more complex than simply "they generate slow queries".

**Query splitting**

It's common for ORMs to perform non-trivial operations (deep fetching, 
nested mutation, inline aggregation, etc) by opaquely executing several 
queries under the hood. This may not be obvious to the end user. The 
incurred latency is rarely reflected in `more <https://github.com/tortoise/orm-benchmarks>`_ `simplistic <https://github.com/emanuelcasco/typescript-orm-benchmark>`_ ORM benchmarks.

**Aggregation (or lack thereof)**

Less mature ORMs often don't support functionality like aggregations 
(counts, statistics, averages, etc), forcing users to overfetch and perform 
these calculations server-side. Some ORMs provide no aggregation functionality 
at all; even advanced ORMs rarely support relational aggregations, such as 
``Find the movie where id=X, returning its title and the number of reviews 
about it.``
   
**Transactional queries**

Since ORM users must often run several correlated queries in series to 
obtain the full set of data they need, the possibility for 
hard-to-reproduce data integrity bugs is introduced. Transactions can 
alleviate these bugs but can rapidly place unacceptable limits on read 
capacity. 

Methodology
-----------

This benchmark is called RealCruddyBench, as it attempts to quantify the **throughput** (iterations/second) and **latency** (milliseconds) of a set of **realistic** CRUD queries. These queries are not arcane or complex, nor are they unreasonably simplistic (as benchmarking queries tend to be). Queries of comparable complexity will be necessary in any non-trivial web application. 

Simulated server-database latency
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The execution environment simulates a *1 millisecond* latency between the server and database. This is the `typical latency <https://aws.amazon.com/blogs/architecture/improving-performance-and-reducing-cost-using-availability-zone-affinity/>`_ between zones in a single AWS region. The vast majority of applications do not have the resources to support per-availability-zone replication, so this assumption is reasonable. 

In the "serverless age" it is common for server code to run in Lambda-style function that is executed in a different availability zone from the underlying database, which would incur latencies far greater than 1ms.

Schema
^^^^^^

We are simulating a `Letterboxd <https://letterboxd.com/>`_-style movie review website. 

.. image:: report/schema.png

The schema consists of four main types.

- ``Person`` (used to represent the cast and crew) 
- ``Movie``
  - ``directors -> Person`` (to many, orderable with ``list_order``)
  - ``cast -> Person`` (to many, orderable with ``list_order``)
- ``User``
- ``Review``
  - ``author -> User`` (to one)
  - ``movie -> Movie`` (to one)

Queries
^^^^^^^

The following queries have been implemented for each target.

- ``insert_movie`` Evaluates *nested mutations* and *the ability to insert and 
  select in a single step*.

  Insert a ``Movie``, setting its ``cast`` and ``directors`` 
  with pre-existing ``Person`` objects. Return the new ``Movie``, including 
  all its properties, its ``cast``, and its ``directors``. 

  .. raw:: html

    <details>
      <summary>View query</summary>
      <pre>
    with 
      new_movie := (
        insert Movie {
          title := &lt;str&gt;$title,
          image := &lt;str&gt;$image,
          description := &lt;str&gt;$description,
          year := &lt;int64&gt;$year,
          directors := (
            select Person
            filter .id = (&lt;uuid&gt;$d_id)
          ),
          cast := (
            select Person
            filter .id in array_unpack(&lt;array&lt;uuid&gt;&gt;$cast)
          ),
        }
      )
    select new_movie {
      id,
      title,
      image,
      description,
      year,
      directors: { id, full_name, image } order by .last_name,
      cast: { id, full_name, image } order by .last_name,
    };
      </pre>
    </details>

- ``get_movie`` Evaluates *deep (3-level) fetches* and *ordered 
  relation fetching*.

  Fetch a ``Movie`` by ID, including all its properties, its 
  ``cast`` (in ``list_order``), its ``directors`` (in ``list_order``), and its 
  associated ``Reviews`` (including basic information about the review 
  ``author``).

  .. raw:: html

    <details>
      <summary>View query</summary>
      <pre>
    with m := Movie
    select m {
      id,
      image,
      title,
      year,
      description,
      avg_rating,
      directors: { 
        id, 
        full_name, 
        image 
      } order by @list_order empty last
        then m.directors.last_name,
      cast: {
        id,
        full_name,
        image,
      } order by @list_order empty last
        then m.cast.last_name,
      reviews := (
        select m.&lt;movie[is Review] {
          id,
          body,
          rating,
          author: {
            id,
            name,
            image,
          }
        } order by .creation_time desc
      )
    }
    filter .id = &lt;uuid&gt;$id;
    </pre>
    </details>
  
- ``get_user`` Evaluates *reverse relation fetching* and *relation 
  aggregation*.

  Fetch a ``User`` by ID, including all its properties and 10 most recently written ``Reviews``. For each review, fetch all its properties, the properties of the ``Movie`` it is about, and the *average rating* of that movie (averaged across all reviews in the database). 

  .. raw:: html

    <details><summary>View query</summary><pre>
    select User {
      id,
      name,
      image,
      latest_reviews := (
        select .&lt;author[is Review] {
          id,
          body,
          rating,
          movie: {
            id,
            image,
            title,
            avg_rating := math::mean(.&lt;movie[is Review].rating)
          }
        }
        order by .creation_time desc
        limit 10
      )
    }
    filter .id = &lt;uuid&gt;$id;
    </pre></details>
      

Results
-------

Below are the results for 

.. image:: result/test.svg

Analysis
^^^^^^^^

The goal of this benchmark is not to attack ORM libraries; they provide a 
partial solution to some of SQL's major usability issues. 

1. They can express deep or nested queries in a compact and intuitive way. 
   Queries return objects, instead of a flat list of rows that must be 
   manually denormalized.
2. They allow schema to be modeled a declarative, object-oriented way.
3. They provide idiomatic, code-first data fetching APIs for different 
   languages. This is particularly important as statically typed languages like Go and TypeScript gain popularity; the ability of ORMs to return strongly-typed query results in a DRY, non-reduntant way is increasingly desirable.

However, the limitations of ORMs can be crippling as an application scales in complexity and traffic. Our goal in designing EdgeDB is to provide a third option with the best of all worlds.

.. list-table::

  * - 
    - ORMs
    - SQL
    - EdgeDB
  * - Intuitive nested fetching
    - 🟢
    - 🔴
    - 🟢
  * - Declarative schema
    - 🟢
    - 🔴
    - 🟢
  * - Structured query results
    - 🟢
    - 🔴
    - 🟢
  * - Idiomatic APIs for different languages
    - 🟢
    - 🔴
    - 🟢
  * - Comprehensive standard library
    - 🔴
    - 🟢
    - 🟢
  * - Computed properties
    - 🔴
    - 🟢
    - 🟢
  * - Aggregates
    - 🟡
    - 🟢
    - 🟢
  * - Computed properties
    - 🔴
    - 🟢
    - 🟢
  * - Composable subquerying
    - 🔴
    - 🔴
    - 🟢

Running locally
---------------


.. collapse:: Local setup instructions

  #. Install Python 3.8+ and create a virtual environment.

    .. code-block::
    
        python -m venv my_venv
    
  #. Install dependencies from ``requirements.txt``

    .. code-block::
    
        pip install -r requirements.txt

  #. Install the following toolchains:

    - `EdgeDB <https://www.edgedb.com/install>`_
    - `PostgreSQL 13 <https://www.postgresql.org/docs/13/installation.html>`_
    - `Golang <https://go.dev/doc/install>`_
    - (Optional) `MongoDB <https://docs.mongodb.com/manual/installation/>`_

  #. Install `Node.js <https://nodejs.org/en/download/>`_ v14.16.0+.

  #. Install `Docker <https://docs.docker.com/get-docker/>`_ and `docker-compose <https://docs.docker.com/compose/install/>`_ (needed for Hasura).

  #. Install ``synth``. (https://www.getsynth.com)

  #. [Optional] A sample dataset consisting of 25k movies, 100k people, 100k 
    users, and 500k reviews already exists in the ``dataset/build`` 
    directory. If you wish, you can generate a fresh dataset like so: 
    
    .. code-block::

        $ make new-dataset

    You can also customize the number of inserted objects with the arguments ``people``, ``user``, and ``reviews``.

    .. code-block::

        $ make new-dataset people=5000 user=1000 reviews=100

  #. Load the data into the test databases via ``$ make load``. Alternatively, 
    you can run the loaders one at a time with the following commands:

    .. code-block::

        $ make load-edgedb 
        $ make load-postgres
        $ make load-mongodb 
        $ make load-django 
        $ make load-sqlalchemy  
        $ make load-typeorm 
        $ make load-sequelize 
        $ make load-prisma 
        $ make load-hasura 
        $ make load-postgraphile

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
