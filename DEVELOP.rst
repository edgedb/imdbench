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

#. Install `Node.js <https://nodejs.org/en/download/>`_ v14.16.0+.

#. Install Node.js dependencies

   .. code-block::
  
      npm install

#. Install the following toolchains:

   - `EdgeDB <https://www.edgedb.com/install>`_
   - `PostgreSQL 13 <https://www.postgresql.org/docs/13/installation.html>`_
   - `Golang <https://go.dev/doc/install>`_
   - (Optional) `MongoDB <https://docs.mongodb.com/manual/installation/>`_

#. Install `Docker <https://docs.docker.com/get-docker/>`_ and `docker-compose 
   <https://docs.docker.com/compose/install/>`_

   **Note:** On macOS, Docker containers are run inside a virtual machine. 
   This incurs significant overhead and can skew results unpredictably.

#. Install `Synth <https://www.getsynth.com>`_

#. Configure simulated latency. The instructions for this vary by operating 
   system. On Linux, this can be achieved with ``tc``:

   .. code-block::

     sudo tc qdisc add dev br-webapp-bench root netem delay 1ms
     
#. Generate the dataset.
  
   .. code-block::

      $ make new-dataset

#. Load the data into the test databases via ``$ make load``. Alternatively, 
   you can run only the loaders you care about:

   .. $ make load-postgraphile

   .. code-block::

      $ make load-django 
      $ make load-edgedb 
      $ make load-hasura
      $ make load-mongodb 
      $ make load-postgres
      $ make load-prisma 
      $ make load-sequelize 
      $ make load-sqlalchemy  
      $ make load-typeorm 

#. Compile runner files (Go, TypeScript): ``$ make compile`

#. Run the JavaScript benchmarks

   First, run the following loaders:
   
   .. code-block::
      
      $ make load-typeorm 
      $ make load-sequelize 
      $ make load-postgres
      $ make load-prisma 
      $ make load-edgedb       

   Then run the benchmarks:

   .. code-block::
      
      $ make run-js
   
   The results will be generated into ``docs/js.html``.

#. Run the Python benchmarks

   First, run the following loaders:
   
   .. code-block::

      $ make load-postgres
      $ make load-django 
      $ make load-sqlalchemy 
      $ make load-edgedb     

   Then run the benchmarks:

   .. code-block::
      
      $ make run-py
   
   The results will be generated into ``docs/py.html``.
   
#. Run the SQL benchmarks

   First, run the following loaders:
   
   .. code-block::

      $ make load-postgres
      $ make load-edgedb

   Then run the benchmarks:

   .. code-block::
      
      $ make run-sql
   
   The results will be generated into ``docs/sql.html``.

#. [Optional] Run a custom benchmark

   The benchmarking system can be customized by directly running ``python 
   bench.py``.

   .. code-block::

      python bench.py 
        --html <path/to/file> 
        --json <path/to/file> 
        --concurrency <seconds>
        --query <query_name>
        [targets]
      
   The ``query_name`` must be one of the folowing options. To pick multiple 
   queries, you can use the ``--query`` flag multiple times.

   - ``get_movie``
   - ``get_person``
   - ``get_user``
   - ``update_movie``
   - ``insert_user``
   - ``insert_movie``
   - ``insert_movie_plus``

   Specify a custom set of ``targets`` with a space-separated list of the 
   following options:

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
   .. - ``postgres_postgraphile_go``
  
   You can see a full list of options like so:

   .. code-block::

      python bench.py --help
