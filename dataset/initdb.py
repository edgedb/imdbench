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
    """)

    with open('../flask_edgedb/default.eschema') as f:
        schema = f.read()

    con = edgedb.connect(user='edgedb', database='edgedb_bench')
    con.execute(f'''
        START TRANSACTION;
        CREATE MIGRATION default::d0 TO eschema $${schema}$$;
        COMMIT MIGRATION default::d0;
        COMMIT;
    ''')
