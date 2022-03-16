Run locally
###########


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

#. Install `Docker <https://docs.docker.com/get-docker/>`_ and `docker-compose 
   <https://docs.docker.com/compose/install/>`_ (needed for Hasura).

#. Install ``synth``. (https://www.getsynth.com)

#. [Optional] A sample dataset consisting of 25k movies, 100k people, 100k 
   users, and 500k reviews already exists in the ``dataset/build`` 
   directory. If you wish, you can generate a fresh dataset like so: 
  
   .. code-block::

      $ make new-dataset

   You can also customize the number of inserted objects with the arguments 
   ``people``, ``user``, and ``reviews``.

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
