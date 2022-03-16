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

Follow the instructions in the `Run Locally <DEVELOP.rst>`_ guide to execute these benchmarks on your local machine.

License
-------

Apache 2.0.
