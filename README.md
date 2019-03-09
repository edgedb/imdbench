Benchmarks
==========

Each of the benchmark apps is setup in its own directory:

- django_rest (Django + REST framework)
- django_custom (Django + customized data retrieval and JSON serialization)
- flask_sqlalchemy (Flask + SQLAlchemy)
- flask_edgedb (Flask + sync EdgeDB)
- sanic_edgedb (Sanic + async EdgeDB)

Setup
-----

There are several steps involved in setting up the benchmarks:

- install required packages

        pip install -r requirements.txt

- generate the Makefile

    This will create the base Makefile that is used for setup:

        python initmake.py

- generate the base dataset

    This process will take awhile and it will produce a pickle file
    that can be used by other utilities that import this data.

        make dataset

    The resulting pickle file will be:

        dataset/build/mdb_100000_100000_500000.pickle

    (The specific numerical values will reflect the dataset settings.
    For more info see the Makefile itself)

    This step also updates the Makefile itself with the settings for
    the dataset (the path to the pickle file and dataset parameters)
    as well as the appropriate targets for the rest of the steps.

- initialize the benchmark databases

    EdgeDB benchmarks all use the same database as their backend. To
    initialize it run:

        make loadedgedb

    SQLAlchemy benchmark DB can be initailized via:

        make loadsqlalchemy

    Django benchmarks share the same Postgres DB and can be initailized via:

        make loaddjango

- initialize the benchmark scripts

    Populate the benchmark scripts with the up-to-date IDs and GraphQL
    queries:

        make initscripts

- start up benchmark apps

    Go to the appropriate directory based on the specific benchmark
    app and start it with:

        ./bench_app_start.sh

Run the benchmarks
------------------

Once all the benchmark DBs are initialized and the necessary apps
are running, the benchmarks can be launched by:

    ./benchmark.sh

For example, to run all of the benchmarks for 1 minute use:

    ./benchmark.sh -d 1m

To run benchmarks for 1 minute only on Sanic + EdgeDB app use:

    ./benchmark.sh -d 1m sanicedb

Refer to the "--help" for more details.
