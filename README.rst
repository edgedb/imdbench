WebAppBench: Realistic benchmarks for ORMs
==========================================

A collection of benchmarks intended to compare various Python and JavaScript 
ORMs against EdgeDB and other databases, using realistic queries. 

Why is this needed?
-------------------

The question of ORM performance is complex.

1. It's common for ORMs to perform non-trivial operations (deep fetching, nested mutation, inline aggregation, etc) by opaquely executing several queries against the underlying database. The incurred latency is rarely reflected in more simplistic ORM benchmarks.

2. Less sophisticated ORMs may not support such functionality at all, forcing users to manually compose several simpler queries themselves. Transactions are required to ensure data consistency among these serially-executed queries, which can place unacceptable limits on request throughput. 

3. Dispensing with transactions may simplify the implementation but can result in hard-to-reproduce data integrity bugs. 

Why "Just use SQL" isn't enough
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The popularity of ORM libraries is driven by their ability to express deep or nested queries in an approachable way, relative to raw SQL. The object-oriented of most ORM schemas allows for more intuitive ways of expressing these operations.

We are sympathetic to this; SQLs lack of composability and `incompatibility <https://en.wikipedia.org/wiki/Object%E2%80%93relational_impedance_mismatch>` with the predominantly object-oriented nature of modern languages is a real usability issue. 

While ORMs are largely incapable of expressing complex queries that include computed fields or aggregation, the common refrain of "Just use SQL" is also too simplistic. SQL queries quickly explode in verbosity when expressing operations like deep fetches, subqueries, and aggregations. T declarative/object-oriented approach to schema modeling, and the desire for idiomatic code-first data fetching APIs in different languages. As statically typed languages like Go and TypeScript gain popularity, the ability of ORMs to return strongly-typed query results in a DRY, non-reduntant way is increasingly desirable.

Targets
-------

The benchmarks target the following set of ORMs and databases.

Python
^^^^^^
- `Django ORM <https://docs.djangoproject.com/en/4.0/topics/db/queries/>`_

Benchmarks are 

Run the benchmarks
------------------

1. Install Python 3.8 and create a virtual environment. We recommend using `pyenv <https://github.com/pyenv/pyenv_>` to avoid conflicts with existing Python versions.

   .. code-block::
   
      pyenv install 3.8.12
      pyenv local 3.8.12
      python -m venv my_venv
   

2. Install dependencies from ``requirements.txt``

   .. code-block::
   
      pip install -r requirements.txt

3. Install `EdgeDB <https://www.edgedb.com/install_>`, `MongoDB <https://docs.mongodb.com/manual/installation/>`_, PostgreSQL 13, and Golang toolchains.

4. Install NodeJS (at least v14.16.0) and TypeScript toolchains.

5. Install docker and docker-compose (needed for Hasura).

6. Install Prisma via ``npm install prisma -D``.

7. Install ``synth``. (https://www.getsynth.com)

     **Note:**
     Synth v0.5.0 replaces python faker with fake-rs, and loses
     support for some generators used by this project.
     The previous supported version, Synth v0.4.7, can be installed
     from https://github.com/getsynth/synth/releases/tag/v0.4.7

8. Create the benchmark data via ``$ make new-dataset``.

9. Load data via ``$ make load``.

10. Compile Go benchmarks: ``$ make go``

11. Compile TypeScript benchmarks: ``$ make ts``

12. Run benchmarks via ``bench.py``, for example:

   .. code-block::

      python bench.py --html out.html --concurrency 10 -D 10 all


Dataset
-------

The default dataset (100000 people, 100000 users, 500000 reviews) is
included in the repository.  A new dataset can be generated via
``$ make new-dataset``.


License
-------

Apache 2.0.
