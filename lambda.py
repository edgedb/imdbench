import os
import subprocess


def handler(event, context):
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
            "4",
            "--duration",
            "60",
            "--html",
            "/tmp/edgedb.html",
            "edgedb_py_json_async",
        ],
        env=env,
    )
    with open('/tmp/edgedb.html') as f:
        resp = f.read()
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "text/html",
        },
        "body": resp,
    }
