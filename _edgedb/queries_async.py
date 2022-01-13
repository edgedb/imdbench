#
# Copyright (c) 2019 MagicStack Inc.
# All rights reserved.
#
# See LICENSE for details.
##


import edgedb
import random
import threading


ASYNC = True
INSERT_PREFIX = 'insert_test__'
thread_data = threading.local()


async def connect(ctx):
    client = getattr(thread_data, 'client', None)
    if client is None:
        client = edgedb.create_async_client(concurrency=ctx.concurrency)

    return client


async def close(ctx, conn):
    # Don't bother closing individual pool connections, they'll be
    # closed automatically.
    pass


async def load_ids(ctx, conn):
    d = await conn.query_single('''
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

    movies = list(d.movies)
    people = list(d.people)

    return dict(
        get_user=list(d.users),
        get_movie=movies,
        get_person=people,
        # re-use user IDs for update tests
        update_movie=movies[:],
        # generate as many insert stubs as "concurrency" to
        # accommodate concurrent inserts
        insert_user=[INSERT_PREFIX] * ctx.concurrency,
        insert_movie=[{
            'prefix': INSERT_PREFIX,
            'people': people[:4],
        }] * ctx.concurrency,
        insert_movie_plus=[INSERT_PREFIX] * ctx.concurrency,
    )


async def get_user(conn, id):
    return await conn.query_single_json('''
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
    ''', id=id)


async def get_movie(conn, id):
    return await conn.query_single_json('''
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
            ORDER BY @list_order EMPTY LAST
                THEN .last_name,

            cast: {
                id,
                full_name,
                image,
            }
            ORDER BY @list_order EMPTY LAST
                THEN .last_name,

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
    ''', id=id)


async def get_person(conn, id):
    return await conn.query_single_json('''
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
    ''', id=id)


async def update_movie(conn, id):
    return await conn.query_single_json('''
        SELECT (
            UPDATE Movie
            FILTER .id = <uuid>$id
            SET {
                title := .title ++ '---' ++ <str>$suffix
            }
        ) {
            id,
            title
        }
    ''', id=id, suffix=str(id)[:8])


async def insert_user(conn, val):
    num = random.randrange(1_000_000)
    return await conn.query_single_json('''
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
    ''', name=f'{val}{num}', image=f'image_{val}{num}')


async def insert_movie(conn, val):
    num = random.randrange(1_000_000)
    return await conn.query_single_json(
        r'''
        SELECT (
            INSERT Movie {
                title := <str>$title,
                image := <str>$image,
                description := <str>$description,
                year := <int64>$year,
                directors := (
                    SELECT Person
                    FILTER .id = (<uuid>$d_ids)
                ),
                cast := (
                    SELECT Person
                    FILTER .id IN array_unpack(<array<uuid>>$cast)
                ),
            }
        ) {
            id,
            title,
            image,
            description,
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
        ''',
        title=f'{val["prefix"]}{num}',
        image=f'{val["prefix"]}image{num}.jpeg',
        description=f'{val["prefix"]}description{num}',
        year=num,
        d_ids=val["people"][0],
        cast=val["people"][1:3],
    )


async def insert_movie_plus(conn, val):
    num = random.randrange(1_000_000)

    return await conn.query_single_json(
        r'''
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
            description,
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
        ''',
        title=f'{val}{num}',
        image=f'{val}image{num}.jpeg',
        description=f'{val}description{num}',
        year=num,
        dfn=f'{val}Alice',
        dln=f'{val}Director',
        dimg=f'{val}image{num}.jpeg',
        cfn0=f'{val}Billie',
        cln0=f'{val}Actor',
        cimg0=f'{val}image{num+1}.jpeg',
        cfn1=f'{val}Cameron',
        cln1=f'{val}Actor',
        cimg1=f'{val}image{num+2}.jpeg',
    )


async def setup(ctx, conn, queryname):
    if queryname == 'update_movie':
        await conn.execute('''
            update Movie
            filter contains(.title, '---')
            set {
                title := str_split(.title, '---')[0]
            }
        ''')
    elif queryname == 'insert_user':
        await conn.query('''
            delete User
            filter .name LIKE <str>$prefix
        ''', prefix=f'{INSERT_PREFIX}%')
    elif queryname == 'insert_movie':
        await conn.query('''
            delete Movie
            filter .image LIKE <str>$prefix
        ''', prefix=f'{INSERT_PREFIX}image%')
    elif queryname == 'insert_movie_plus':
        await conn.query('''
            delete Movie
            filter .image LIKE <str>$prefix
        ''', prefix=f'{INSERT_PREFIX}image%')
        await conn.query('''
            delete Person
            filter .image LIKE <str>$prefix
        ''', prefix=f'{INSERT_PREFIX}image%')


async def cleanup(ctx, conn, queryname):
    if queryname in {'update_movie', 'insert_user', 'insert_movie',
                     'insert_movie_plus'}:
        # The clean up is the same as setup for mutation benchmarks
        await setup(ctx, conn, queryname)
