#
# Copyright (c) 2019 MagicStack Inc.
# All rights reserved.
#
# See LICENSE for details.
##


import edgedb


def get_port(ctx):
    return 8889


def get_queries(ctx):
    conn = connect(ctx)
    try:
        ids = load_ids(ctx, conn)
    finally:
        close(ctx, conn)

    return {
        'get_user': {
            'query': EDGEQL_GET_USER,
            'ids': ids['get_user'],
        },
        'get_movie': {
            'query': EDGEQL_GET_MOVIE,
            'ids': ids['get_movie'],
        },
        'get_person': {
            'query': EDGEQL_GET_PERSON,
            'ids': ids['get_person'],
        },
    }


def connect(ctx):
    return edgedb.connect(
        user=ctx.edgedb_user, database='edgedb_bench',
        host=ctx.db_host, port=ctx.edgedb_port)


def close(ctx, conn):
    conn.close()


def load_ids(ctx, conn):
    d = conn.fetchone('''
        WITH
            U := User {id, r := random()},
            M := Movie {id, r := random()},
            P := Person {id, r := random()}
        SELECT (
            users := array_agg((SELECT U ORDER BY U.r LIMIT <int64>$lim).id),
            movies := array_agg((SELECT M ORDER BY M.r LIMIT <int64>$lim).id),
            people := array_agg((SELECT P ORDER BY P.r LIMIT <int64>$lim).id),
        );
    ''', lim=ctx.number_of_ids)

    return dict(
        get_user=[str(v) for v in d.users],
        get_movie=[str(v) for v in d.movies],
        get_person=[str(v) for v in d.people],
    )


EDGEQL_GET_USER = '''
    SELECT User {
        id,
        name,
        image,
        latest_reviews := (
            WITH UserReviews := User.<author
            SELECT UserReviews {
                id,
                body,
                rating,
                movie: {
                    id,
                    image,
                    title,
                    avg_rating
                }
            }
            ORDER BY .creation_time DESC
            LIMIT 10
        )
    }
    FILTER .id = <uuid>$id
'''

EDGEQL_GET_MOVIE = '''
    SELECT Movie {
        id,
        image,
        title,
        year,
        description,
        avg_rating,

        directors: {
            id,
            full_name,
            image,
        }
        ORDER BY Movie.directors@list_order EMPTY LAST
            THEN Movie.directors.last_name,

        cast: {
            id,
            full_name,
            image,
        }
        ORDER BY Movie.cast@list_order EMPTY LAST
            THEN Movie.cast.last_name,

        reviews := (
            SELECT Movie.<movie {
                id,
                body,
                rating,
                author: {
                    id,
                    name,
                    image,
                }
            }
            ORDER BY .creation_time DESC
        ),
    }
    FILTER .id = <uuid>$id
'''


EDGEQL_GET_PERSON = '''
    SELECT Person {
        id,
        full_name,
        image,
        bio,

        acted_in := (
            WITH M := Person.<cast
            SELECT M {
                id,
                image,
                title,
                year,
                avg_rating
            }
            ORDER BY .year ASC THEN .title ASC
        ),

        directed := (
            WITH M := Person.<directors
            SELECT M {
                id,
                image,
                title,
                year,
                avg_rating
            }
            ORDER BY .year ASC THEN .title ASC
        ),
    }
    FILTER .id = <uuid>$id
'''
