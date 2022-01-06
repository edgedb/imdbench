#
# Copyright (c) 2019 MagicStack Inc.
# All rights reserved.
#
# See LICENSE for details.
##


import psycopg2


INSERT_PREFIX = 'insert_test__'


def get_port(ctx):
    return 8890


def get_queries(ctx):
    conn = connect(ctx)
    try:
        qargs = load_ids(ctx, conn)
    finally:
        close(ctx, conn)

    return {
        'get_user': {
            'query': GRAPHQL_GET_USER,
            'QArgs': qargs['get_user'],
        },
        'get_movie': {
            'query': GRAPHQL_GET_MOVIE,
            'QArgs': qargs['get_movie'],
        },
        'get_person': {
            'query': GRAPHQL_GET_PERSON,
            'QArgs': qargs['get_person'],
        },
        'update_movie': {
            'query': GRAPHQL_UPDATE_MOVIE,
            'QArgs': qargs['update_movie'],
        },
        'insert_user': {
            'query': GRAPHQL_INSERT_USER,
            'QArgs': qargs['insert_user'],
        },
        'insert_movie': {
            'query': GRAPHQL_INSERT_MOVIE,
            'QArgs': qargs['insert_movie'],
        },
        'insert_movie_plus': {
            'query': GRAPHQL_INSERT_MOVIE_PLUS,
            'QArgs': qargs['insert_movie_plus'],
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
        '''
        SELECT
            m.id::text, m.title || '---' || m.id::text
        FROM
            movies m ORDER BY random() LIMIT %s
        ''',
        [ctx.number_of_ids]
    )
    movies = cur.fetchall()

    cur.execute(
        'SELECT p.id::text FROM persons p ORDER BY random() LIMIT %s',
        [ctx.number_of_ids])
    people = cur.fetchall()

    return dict(
        get_user=[[u[0]] for u in users],
        get_movie=[[m[0]] for m in movies],
        get_person=[[p[0]] for p in people],
        # re-use user IDs for update tests
        update_movie=[[m[0], m[1]] for m in movies],
        # generate as many insert stubs as "concurrency" to
        # accommodate concurrent inserts
        insert_user=[[INSERT_PREFIX]] * ctx.concurrency,
        insert_movie=[
            [INSERT_PREFIX] + [v[0] for v in people[:4]]
        ] * ctx.concurrency,
        insert_movie_plus=[[INSERT_PREFIX]] * ctx.concurrency,
    )


def setup(ctx, conn, queryname):
    if queryname == 'update_movie':
        cur = conn.cursor()
        cur.execute('''
            UPDATE
                movies
            SET
                title = split_part(movies.title, '---', 1)
            WHERE
                movies.title LIKE '%---%';
        ''')
        conn.commit()
    elif queryname == 'insert_user':
        cur = conn.cursor()
        cur.execute('''
            DELETE FROM
                users
            WHERE
                users.name LIKE %s
        ''', [f'{INSERT_PREFIX}%'])
        conn.commit()
    elif queryname in {'insert_movie', 'insert_movie_plus'}:
        cur = conn.cursor()
        cur.execute('''
            DELETE FROM
                "directors" as D
            USING
                "movies" as M
            WHERE
                D.movie_id = M.id AND M.image LIKE %s;
        ''', [f'{INSERT_PREFIX}%'])
        cur.execute('''
            DELETE FROM
                "actors" as A
            USING
                "movies" as M
            WHERE
                A.movie_id = M.id AND M.image LIKE %s;
        ''', [f'{INSERT_PREFIX}%'])
        cur.execute('''
            DELETE FROM
                "movies" as M
            WHERE
                M.image LIKE %s;
        ''', [f'{INSERT_PREFIX}%'])
        cur.execute('''
            DELETE FROM
                "persons" as P
            WHERE
                P.image LIKE %s;
        ''', [f'{INSERT_PREFIX}%'])
        conn.commit()


def cleanup(ctx, conn, queryname):
    if queryname in {'update_movie', 'insert_user', 'insert_movie',
                     'insert_movie_plus'}:
        # The clean up is the same as setup for mutation benchmarks
        setup(ctx, conn, queryname)


GRAPHQL_GET_USER = '''
    query users($id: Int!) {
      user: userById(id: $id) {
        id
        name
        image
        latest_reviews: reviewsByAuthorId(
            orderBy: CREATION_TIME_DESC, first: 10
        ) {
          nodes {
            id
            body
            rating
            movieByMovieId {
              id
              image
              title
              avg_rating: avgRating
            }
          }
        }
      }
    }
'''

GRAPHQL_GET_MOVIE = '''
    query movies($id: Int!) {
      movie: movieById(id: $id) {
        id
        title
        image
        year
        description
        directors: peopleByDirectorMovieIdAndPersonId {
          nodes {
            id
            full_name: fullName
            image
          }
        }
        cast: peopleByActorMovieIdAndPersonId {
          nodes {
            id
            full_name: fullName
            image
          }
        }
        avg_rating: avgRating
        reviews: reviewsByMovieId(orderBy: CREATION_TIME_DESC) {
          nodes {
            id
            body
            rating
            author: userByAuthorId {
              id
              name
              image
            }
          }
        }
      }
    }
'''


GRAPHQL_GET_PERSON = '''
    query persons($id: Int!) {
      person: personById(id: $id) {
        id
        full_name: fullName
        image
        bio
        acted_in: moviesByActorPersonIdAndMovieId(
            orderBy: [YEAR_ASC, TITLE_ASC]
        ) {
          nodes {
            id
            image
            title
            year
            avg_rating: avgRating
          }
        }
        directed: moviesByDirectorPersonIdAndMovieId(
            orderBy: [YEAR_ASC, TITLE_ASC]
        ) {
          nodes {
            id
            image
            title
            year
            avg_rating: avgRating
          }
        }
      }
    }
'''


GRAPHQL_UPDATE_MOVIE = '''
    mutation update_movie($id: Int!, $title: String!) {
        movie: updateMovieById(
            input: {
                id: $id,
                moviePatch: {
                    title: $title
                }
            }
        ) {
            movie {
                id
                title
            }
        }
    }
'''


GRAPHQL_INSERT_USER = '''
    mutation insert_user($name: String!, $image: String!) {
        user: createUser(
            input: {
                user: {
                    name: $name,
                    image: $image,
                }
            }
        ) {
            user {
                id
                name
                image
            }
        }
    }
'''


GRAPHQL_INSERT_MOVIE = '''
'''


GRAPHQL_INSERT_MOVIE_PLUS = '''
'''
