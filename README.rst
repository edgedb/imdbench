EdgeDB Benchmark Toolbench
==========================

This is a collection of benchmarks intended to compare EdgeDB
against different databases and ORMs.


Installation and Use
--------------------

1. Make a Python 3.7 venv.

2. Install dependencies from ``requirements.txt``.

3. Install EdgeDB, MongoDB, PostgreSQL 11, Golang toolchain.

4. Configure PostgreSQL similarly to EdgeDB:

   * ``shared_buffers``: 20% of RAM.
   * ``effective_cache_size``: 50% of RAM.
   * ``query_work_mem``: 6MB.

5. Load data via ``$ make load``.

6. Compile Go benchmarks: ``$ make go``

7. Compile TypeScript benchmarks: ``$ make ts``

8. Run benchmarks via ``bench.py``, for example:

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
