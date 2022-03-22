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
        qargs = load_ids(ctx, conn)
    finally:
        close(ctx, conn)

    return {
        'get_user': {
            'query': EDGEQL_GET_USER,
            'QArgs': qargs['get_user'],
        },
        'get_movie': {
            'query': EDGEQL_GET_MOVIE,
            'QArgs': qargs['get_movie'],
        },
        'get_person': {
            'query': EDGEQL_GET_PERSON,
            'QArgs': qargs['get_person'],
        },
        'update_movie': {
            'query': EDGEQL_UPDATE_MOVIE,
            'QArgs': qargs['update_movie'],
        },
        'insert_user': {
            'query': EDGEQL_INSERT_USER,
            'QArgs': qargs['insert_user'],
        },
        'insert_movie': {
            'query': EDGEQL_INSERT_MOVIE,
            'QArgs': qargs['insert_movie'],
        },
        'insert_movie_plus': {
            'query': EDGEQL_INSERT_MOVIE_PLUS,
            'QArgs': qargs['insert_movie_plus'],
        },
    }


def connect(ctx):
    return edgedb.create_client(max_concurrency=1)


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
            movies := array_agg((SELECT M ORDER BY M.r LIMIT <int64>$lim).id),
            people := array_agg((SELECT P ORDER BY P.r LIMIT <int64>$lim).id),
        );
    ''', lim=ctx.number_of_ids)

    people = list(d.people)

    return dict(
        get_user=[[str(v)] for v in d.users],
        get_movie=[[str(v)] for v in d.movies],
        get_person=[[str(v)] for v in people],
        # re-use user IDs for update tests
        update_movie=[[str(v)] for v in d.movies],
        # generate as many insert stubs as "concurrency" to
        # accommodate concurrent inserts
        insert_user=[[INSERT_PREFIX]] * ctx.concurrency,
        insert_movie=[
            [INSERT_PREFIX] + [str(v) for v in people[:4]]
        ] * ctx.concurrency,
        insert_movie_plus=[[INSERT_PREFIX]] * ctx.concurrency,
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
    elif queryname == 'insert_movie':
        conn.query('''
            delete Movie
            filter .image LIKE <str>$prefix
        ''', prefix=f'{INSERT_PREFIX}image%')
    elif queryname == 'insert_movie_plus':
        conn.query('''
            delete Movie
            filter .image LIKE <str>$prefix
        ''', prefix=f'{INSERT_PREFIX}image%')
        conn.query('''
            delete Person
            filter .image LIKE <str>$prefix
        ''', prefix=f'{INSERT_PREFIX}image%')


def cleanup(ctx, conn, queryname):
    if queryname in {'update_movie', 'insert_user', 'insert_movie',
                     'insert_movie_plus'}:
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
    WITH id := <uuid>$id
    SELECT (
        UPDATE Movie
        FILTER .id = id
        SET {
            title := .title ++ '---' ++ (<str>id)[:8]
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


EDGEQL_INSERT_MOVIE = '''
    SELECT (
        INSERT Movie {
            title := <str>$title,
            image := <str>$image,
            description := <str>$description,
            year := <int64>$year,
            directors := (
                SELECT Person
                FILTER .id = (<uuid>$did)
            ),
            cast := (
                SELECT Person
                FILTER .id IN {<uuid>$cid0, <uuid>$cid1, <uuid>$cid2}
            ),
        }
    ) {
        id,
        title,
        image,
        year,
        directors: {
            id,
            full_name,
            image,
        }
        ORDER BY .last_name,

        cast: {
            id,
            full_name,
            image,
        }
        ORDER BY .last_name,
    }
'''


EDGEQL_INSERT_MOVIE_PLUS = '''
    SELECT (
        INSERT Movie {
            title := <str>$title,
            image := <str>$image,
            description := <str>$description,
            year := <int64>$year,
            directors := (
                INSERT Person {
                    first_name := <str>$dfn,
                    last_name := <str>$dln,
                    image := <str>$dimg,
                }
            ),
            cast := {(
                INSERT Person {
                    first_name := <str>$cfn0,
                    last_name := <str>$cln0,
                    image := <str>$cimg0,
                }
            ), (
                INSERT Person {
                    first_name := <str>$cfn1,
                    last_name := <str>$cln1,
                    image := <str>$cimg1,
                }
            )},
        }
    ) {
        id,
        title,
        image,
        year,
        directors: {
            id,
            full_name,
            image,
        }
        ORDER BY .last_name,

        cast: {
            id,
            full_name,
            image,
        }
        ORDER BY .last_name,
    }
'''
