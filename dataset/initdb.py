import pathlib
import edgedb


if __name__ == '__main__':
    con = edgedb.connect(user='edgedb', database='edgedb')

    # check if the DB exists
    res = con.fetch("""
        SELECT schema::Database.name
        FILTER schema::Database.name = 'edgedb_bench';
    """)

    if res:
        con.execute("""
            DROP DATABASE edgedb_bench;
        """)

    con.execute("""
        CREATE DATABASE edgedb_bench;

        CONFIGURE SYSTEM INSERT Port {
            protocol := "graphql+http",
            database := "edgedb_bench",
            address := "127.0.0.1",
            port := 8888,
            user := "http",
            concurrency := 4,
        };
    """)

    schema = (pathlib.Path(__file__).resolve().parent.parent
              / 'flask_edgedb' / 'default.eschema')

    with open(schema) as f:
        schema = f.read()

    setup = (pathlib.Path(__file__).resolve().parent.parent
             / 'flask_edgedb' / 'default_setup.eql')
    with open(setup) as f:
        setup = f.read()

    con = edgedb.connect(user='edgedb', database='edgedb_bench')
    con.execute(f'''
        START TRANSACTION;
        CREATE MIGRATION default::d0 TO eschema $${schema}$$;
        COMMIT MIGRATION default::d0;
        {setup}
        COMMIT;
    ''')
