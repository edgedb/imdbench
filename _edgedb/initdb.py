#
# Copyright (c) 2019 MagicStack Inc.
# All rights reserved.
#
# See LICENSE for details.
##


import pathlib
import edgedb


if __name__ == '__main__':
    con = edgedb.connect(user='edgedb', database='edgedb')

    # check if the DB exists
    res = con.fetchall("""
        SELECT sys::Database.name
        FILTER sys::Database.name = 'edgedb_bench';
    """)

    if res:
        con.execute("""
            CONFIGURE SYSTEM RESET Port FILTER .port=8888;
        """)

        con.execute("""
            DROP DATABASE edgedb_bench;
        """)

    con.execute("""
        CREATE DATABASE edgedb_bench;
    """)

    con.execute("""
        CONFIGURE SYSTEM INSERT Port {
            protocol := "graphql+http",
            database := "edgedb_bench",
            address := "127.0.0.1",
            port := 8888,
            user := "http",
            concurrency := 4,
        };
    """)

    base_path = pathlib.Path(__file__).resolve().parent

    with open(base_path / 'default.esdl') as f:
        schema = f.read()

    with open(base_path / 'default_setup.edgeql') as f:
        setup = f.read()

    con = edgedb.connect(user='edgedb', database='edgedb_bench')
    con.execute(f'''
        START TRANSACTION;
        CREATE MIGRATION default::d0 TO {{ {schema} }};
        COMMIT MIGRATION default::d0;
        {setup}
        COMMIT;
    ''')
