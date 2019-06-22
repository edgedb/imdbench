EdgeDB Benchmark Toolbench
==========================

This is a collection of benchmarks intended to compare EdgeDB
against different databases and ORMs.


Installation and Use
--------------------

1. Make a Python 3.7 venv.

2. Install dependencies from ``requirements.txt``.

3. Install EdgeDB, MongoDB, PostgreSQL 11, Golang toolchain.

4. Install NodeJS (at least v10.15.3) and TypeScript toolchains.

5. Install docker and docker-compose (needed for Hasura and Prisma benchmarks).

6. Install Prisma 1.26.4 (later versions don't work with timestamptz) via
   ``npm i -g prisma@1.26.4``.

7. Configure PostgreSQL similarly to EdgeDB:

   * ``shared_buffers``: 20% of RAM.
   * ``effective_cache_size``: 50% of RAM.
   * ``query_work_mem``: 6MB.

8. Load data via ``$ make load``.

9. Compile Go benchmarks: ``$ make go``

10. Compile TypeScript benchmarks: ``$ make ts``

11. Run benchmarks via ``bench.py``, for example:

   .. code-block::

      python bench.py --html out.html --concurrency 10 -A 2  -D 10 all


Dataset
-------

The default dataset (100000 people, 100000 users, 500000 reviews) is
included in the repository.  A new dataset can be generated via
``$ make new-dataset``.


License
-------

Apache 2.0.
