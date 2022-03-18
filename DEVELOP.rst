Run locally
###########


#. Install Python 3.8+, then create and activate a virtual environment.

   .. code-block::
  
      $ python -m venv my_venv
      $ source my_venv/bin/activate
   
   The steps below assume your virtual environment is activated. To deactivate 
   the venv, just run ``deactivate`` at any time. Read the full `Virtual 
   Environment <https://docs.python.org/3/tutorial/venv.html>`_ docs 
   for details.
  
#. Install Python dependencies

   .. code-block::
  
      pip install -r requirements.txt

#. Install Node.js dependencies

   .. code-block::
  
      npm install

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

      $ make new-dataset people=5000 users=1000 reviews=100

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

#. Compile runner files (Go, TypeScript): ``$ make compile`

#. Run the benchmarks via ``bench.py``.

   To run all benchmarks:

   .. code-block::

      python bench.py --html out.html -D 10 all

   To run all JavaScript ORM benchmarks:

   .. code-block::

      python bench.py --html results/js.html --json results/js.json typeorm sequelize prisma edgedb_js_qb

   To run all Python ORM benchmarks:

   .. code-block::

      python bench.py --html results/python.html --json python.html django sqlalchemy
  
   To specify a custom set of targets, pass a space-separated list of the following options:

   - ``typeorm``
   - ``sequelize``
   - ``prisma``
   - ``edgedb_js_qb``
   - ``django``
   - ``django_restfw``
   - ``mongodb``
   - ``sqlalchemy``
   - ``edgedb_py_sync``
   - ``edgedb_py_json``
   - ``edgedb_py_json_async``
   - ``edgedb_go``
   - ``edgedb_go_json``
   - ``edgedb_go_graphql``
   - ``edgedb_go_http``
   - ``edgedb_js``
   - ``edgedb_js_json``
   - ``postgres_asyncpg``
   - ``postgres_psycopg``
   - ``postgres_pq``
   - ``postgres_pgx``
   - ``postgres_pg``
   - ``postgres_hasura_go``
   - ``postgres_postgraphile_go``
  
   To customize the included queries, use the ``--query`` flag to pass a comma-separated list of the following options.

   - ``get_movie``
   - ``get_person``
   - ``get_user``
   - ``update_movie``
   - ``insert_user``
   - ``insert_movie``
   - ``insert_movie_plus``
  
   
   You can see a full list of command options like so:

   .. code-block::

      python bench.py --help
