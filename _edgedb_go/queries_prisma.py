#
# Copyright (c) 2019 MagicStack Inc.
# All rights reserved.
#
# See LICENSE for details.
##


import psycopg2


def get_port(ctx):
    return 4466


def get_queries(ctx):
    conn = connect(ctx)
    try:
        ids = load_ids(ctx, conn)
    finally:
        close(ctx, conn)

    return {
        'get_user': {
            'query': GRAPHQL_GET_USER,
            'ids': ids['get_user'],
        },
        'get_movie': {
            'query': GRAPHQL_GET_MOVIE,
            'ids': ids['get_movie'],
        },
        'get_person': {
            'query': GRAPHQL_GET_PERSON,
            'ids': ids['get_person'],
        },
    }


def connect(ctx):
    return psycopg2.connect(
        user='postgres_bench',
        dbname='postgres_bench',
        password='edgedbbenchmark',
        host=ctx.db_host,
        port=ctx.pg_port)


def close(ctx, conn):
    conn.close()


def load_ids(ctx, conn):
    cur = conn.cursor()

    # read IDs as strings to be converted later into ints
    cur.execute(
        'SELECT u.id::text FROM users u ORDER BY random() LIMIT %s',
        [ctx.number_of_ids])
    users = cur.fetchall()

    cur.execute(
        'SELECT m.id::text FROM movies m ORDER BY random() LIMIT %s',
        [ctx.number_of_ids])
    movies = cur.fetchall()

    cur.execute(
        'SELECT p.id::text FROM persons p ORDER BY random() LIMIT %s',
        [ctx.number_of_ids])
    people = cur.fetchall()

    return dict(
        get_user=[u[0] for u in users],
        get_movie=[m[0] for m in movies],
        get_person=[p[0] for p in people],
    )


GRAPHQL_GET_USER = '''
    query users($id: Int!) {
      user: users(where: { id: $id }) {
        id
        name
        image
        latest_reviews: reviews(orderBy: creation_time_DESC, first: 10) {
          id
          body
          rating
          movie {
            id
            image
            title
            avg_rating
          }
        }
      }
    }
'''

GRAPHQL_GET_MOVIE = '''
    query movies($id: Int!) {
      movie: movies(where: { id: $id }) {
        id
        title
        image
        year
        description
        directors {
          person {
            id
            full_name
            image
          }
        }
        cast: actors {
          person {
            id
            full_name
            image
          }
        }
        avg_rating
        reviews(orderBy: creation_time_DESC) {
          id
          body
          rating
          author {
            id
            name
            image
          }
        }
      }
    }
'''


GRAPHQL_GET_PERSON = '''
    query persons($id: Int!) {
      person: persons(where: { id: $id }) {
        id
        full_name
        image
        bio
        acted_in: actors {
          movie {
            id
            image
            title
            year
            avg_rating
          }
        }
        directed: directors {
          movie {
            id
            image
            title
            year
            avg_rating
          }
        }
      }
    }
'''
