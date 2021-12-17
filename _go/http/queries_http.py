#
# Copyright (c) 2019 MagicStack Inc.
# All rights reserved.
#
# See LICENSE for details.
##


import edgedb


INSERT_PREFIX = 'insert_test__'


def get_port(ctx):
    return ctx.edgedb_port


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
        'update_movie': {
            'query': EDGEQL_UPDATE_MOVIE,
            'ids': [v['id'] for v in ids['update_movie']],
            'text': [v['text'] for v in ids['update_movie']],
        },
        'insert_user': {
            'query': EDGEQL_INSERT_USER,
            'text': ids['insert_user'],
        },
    }


def connect(ctx):
    return edgedb.connect()


def close(ctx, conn):
    conn.close()


def load_ids(ctx, conn):
    d = conn.query_single('''
        WITH
            U := User {id, r := random()},
            M := Movie {id, r := random()},
            P := Person {id, r := random()}
        SELECT (
            users := array_agg((SELECT U ORDER BY U.r LIMIT <int64>$lim).id),
            movies := array_agg((SELECT M ORDER BY M.r LIMIT <int64>$lim){
                id,
                title := '---' ++ (<str>.id)[:8],
            }),
            people := array_agg((SELECT P ORDER BY P.r LIMIT <int64>$lim).id),
        );
    ''', lim=ctx.number_of_ids)

    return dict(
        get_user=[str(v) for v in d.users],
        get_movie=[str(v.id) for v in d.movies],
        get_person=[str(v) for v in d.people],
        # re-use user IDs for update tests
        update_movie=[{'id': str(v.id), 'text': v.title} for v in d.movies],
        # generate as many insert stubs as "concurrency" to
        # accommodate concurrent inserts
        insert_user=[INSERT_PREFIX] * ctx.concurrency,
    )


def setup(ctx, conn, queryname):
    if queryname == 'update_movie':
        conn.execute('''
            update Movie
            filter contains(.title, '---')
            set {
                title := str_split(.title, '---')[0]
            };
        ''')
    elif queryname == 'insert_user':
        conn.query('''
            delete User
            filter .name LIKE <str>$prefix
        ''', prefix=f'{INSERT_PREFIX}%')


def cleanup(ctx, conn, queryname):
    if queryname in {'update_movie', 'insert_user'}:
        # The clean up is the same as setup for mutation benchmarks
        setup(ctx, conn, queryname)


EDGEQL_GET_USER = '''
    SELECT User {
        id,
        name,
        image,
        latest_reviews := (
            WITH UserReviews := User.<author[IS Review]
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
            SELECT Movie.<movie[IS Review] {
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
            WITH M := Person.<cast[IS Movie]
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
            WITH M := Person.<directors[IS Movie]
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


EDGEQL_UPDATE_MOVIE = '''
    SELECT (
        UPDATE Movie
        FILTER .id = <uuid>$id
        SET {
            title := .title ++ <str>$title
        }
    ) {
        id,
        title
    }
'''


EDGEQL_INSERT_USER = '''
    SELECT (
        INSERT User {
            name := <str>$name,
            image := <str>$image,
        }
    ) {
        id,
        name,
        image,
    }
'''
