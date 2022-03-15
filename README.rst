WebAppBench: Realistic benchmarks for ORMs
==========================================

A collection of benchmarks intended to compare various Python and JavaScript 
ORMs against EdgeDB and other databases, using realistic queries. It's common 
for ORMs to perform non-trivial operations by opaquely executing several 
queries against the underlying database. The incurred latency is rarely 
reflect in more simplistic ORM benchmarks.


Run the benchmarks
------------------

1. Install Python 3.8 and create a virtual environment. We recommend using `pyenv <https://github.com/pyenv/pyenv_>` to avoid conflicts with existing Python versions.

   ```
   pyenv install 3.8.12
   pyenv local 3.8.12
   python -m venv my_venv
   ```

2. Install dependencies from ``requirements.txt``

   ```
   pip install -r requirements.txt
   ```

3. Install EdgeDB, MongoDB, PostgreSQL 13, Golang toolchain.

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
