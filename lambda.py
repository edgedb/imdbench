import os
import subprocess


def handler(event, context):
    match event["path"]:
        case "/edgedb":
            return run_edgedb()

        case "/supabase-sql-asyncpg":
            return run_supabase()

        case "/supabase-sql-psycopg":
            return run_supabase(asyncpg=False)


def run_edgedb():
    dbname = os.environ["IMDBENCH_EDGEDB_DATABASE"]
    env = {
        "HOME": "/tmp",
        "EDGEDB_SECRET_KEY": os.environ["IMDBENCH_EDGEDB_SECRET_KEY"],
        "PYTHONPATH": os.getcwd(),
        **os.environ,
    }
    subprocess.call(
        [
            "edgedb",
            "project",
            "init",
            "--link",
            "--non-interactive",
            "--server-instance",
            os.environ["IMDBENCH_EDGEDB_INSTANCE"],
            "--database",
            dbname,
        ],
        env=env,
    )
    subprocess.check_call(
        [
            "edgedb",
            "query",
            "create database temp",
        ],
        env=env,
    )
    subprocess.check_call(
        [
            "edgedb",
            "-d",
            "temp",
            "query",
            f"drop database {dbname}",
        ],
        env=env,
    )
    subprocess.check_call(
        [
            "edgedb",
            "-d",
            "temp",
            "query",
            f"create database {dbname}",
        ],
        env=env,
    )
    subprocess.check_call(
        [
            "edgedb",
            "query",
            "drop database temp",
        ],
        env=env,
    )
    subprocess.check_call(
        [
            "edgedb",
            "migrate",
        ],
        env=env,
    )
    subprocess.check_call(
        [
            "python",
            "-m",
            "_edgedb.loaddata",
            os.getcwd() + "/dataset/build/edbdataset.json",
        ],
        env=env,
    )
    subprocess.check_call(
        [
            "python",
            "bench.py",
            "--query",
            "insert_movie",
            "--query",
            "get_movie",
            "--query",
            "get_user",
            "--concurrency",
            "1",
            "--duration",
            "60",
            "--html",
            "/tmp/edgedb.html",
            "edgedb_py_json_async",
        ],
        env=env,
    )
    with open("/tmp/edgedb.html") as f:
        resp = f.read()
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "text/html",
        },
        "body": resp,
    }


def run_supabase(asyncpg=True, clean=True):
    env = {
        "HOME": "/tmp",
        "PYTHONPATH": os.getcwd(),
        "PGHOST": os.environ["IMDBENCH_SUPABASE_HOST"],
        "PGPORT": os.environ["IMDBENCH_SUPABASE_PORT"],
        "PGDATABASE": os.environ["IMDBENCH_SUPABASE_DATABASE"],
        "PGUSER": os.environ["IMDBENCH_SUPABASE_USER"],
        "PGPASSWORD": os.environ["IMDBENCH_SUPABASE_PASSWORD"],
        **os.environ,
    }
    if clean:
        subprocess.check_call(
            [
                "psql",
                "-tc",
                "DROP DATABASE IF EXISTS postgres_bench;",
            ],
            env=env,
        )
        subprocess.check_call(
            [
                "psql",
                "-tc",
                "CREATE DATABASE postgres_bench;",
            ],
            env=env,
        )
    env["PGDATABASE"] = "postgres_bench"
    if clean:
        subprocess.check_call(
            [
                "psql",
                "--file",
                os.getcwd() + "/_postgres/schema.sql",
            ],
            env=env,
        )
        subprocess.check_call(
            [
                "python",
                "_postgres/loaddata.py",
                os.getcwd() + "/dataset/build/dataset.json",
            ],
            env=env,
        )
        subprocess.check_call(
            [
                "psql",
                "-tc",
                """\
                CREATE OR REPLACE VIEW movie_view AS \
                SELECT \
                    movies.id, \
                    movies.image, \
                    movies.title, \
                    movies.year, \
                    movies.description, \
                    movies.avg_rating AS avg_rating \
                FROM movies; \
                CREATE OR REPLACE VIEW person_view AS \
                SELECT \
                    persons.id, \
                    persons.first_name, \
                    persons.middle_name, \
                    persons.last_name, \
                    persons.image, \
                    persons.bio, \
                    persons.full_name AS full_name \
                FROM persons; \
                """,
            ],
            env=env,
        )
    subprocess.check_call(
        [
            "python",
            "bench.py",
            "--query",
            "insert_movie",
            "--query",
            "get_movie",
            "--query",
            "get_user",
            "--concurrency",
            "1",
            "--duration",
            "60",
            "--db-host",
            os.environ["IMDBENCH_SUPABASE_HOST"],
            "--pg-port",
            os.environ["IMDBENCH_SUPABASE_PORT"],
            "--pg-database",
            "postgres_bench",
            "--pg-user",
            os.environ["IMDBENCH_SUPABASE_USER"],
            "--pg-password",
            os.environ["IMDBENCH_SUPABASE_PASSWORD"],
            "--html",
            "/tmp/supabase.html",
            "postgres_asyncpg" if asyncpg else "postgres_psycopg",
        ],
        env=env,
    )
    with open("/tmp/supabase.html") as f:
        resp = f.read()
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "text/html",
        },
        "body": resp,
    }
