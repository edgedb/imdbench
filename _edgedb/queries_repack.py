#
# Copyright (c) 2019 MagicStack Inc.
# All rights reserved.
#
# See LICENSE for details.
##


import edgedb
import json
import random


INSERT_PREFIX = 'insert_test__'


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


def get_user(conn, id):
    u = conn.query_single('''
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

    return json.dumps({
        'id': str(u.id),
        'name': u.name,
        'image': u.image,
        'latest_reviews': [
            {
                'id': str(r.id),
                'body': r.body,
                'rating': r.rating,
                'movie': {
                    'id': str(r.movie.id),
                    'image': r.movie.image,
                    'title': r.movie.title,
                    'avg_rating': r.movie.avg_rating
                }
            } for r in u.latest_reviews
        ]
    })


def get_movie(conn, id):
    m = conn.query_single('''
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
    ''', id=id)

    return json.dumps({
        'id': str(m.id),
        'image': m.image,
        'title': m.title,
        'year': m.year,
        'description': m.description,
        'avg_rating': m.avg_rating,

        'directors': [
            {
                'id': str(d.id),
                'full_name': d.full_name,
                'image': d.image,
            } for d in m.directors
        ],

        'cast': [
            {
                'id': str(c.id),
                'full_name': c.full_name,
                'image': c.image,
            } for c in m.cast
        ],

        'reviews': [
            {
                'id': str(r.id),
                'body': r.body,
                'rating': r.rating,
                'author': {
                    'id': str(r.author.id),
                    'name': r.author.name,
                    'image': r.author.image,
                }
            } for r in m.reviews
        ]
    })


def get_person(conn, id):
    p = conn.query_single('''
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

    return json.dumps({
        'id': str(p.id),
        'full_name': p.full_name,
        'image': p.image,
        'bio': p.bio,

        'acted_in': [
            {
                'id': str(m.id),
                'image': m.image,
                'title': m.title,
                'year': m.year,
                'avg_rating': m.avg_rating,
            } for m in p.acted_in
        ],

        'directed': [
            {
                'id': str(m.id),
                'image': m.image,
                'title': m.title,
                'year': m.year,
                'avg_rating': m.avg_rating,
            } for m in p.directed
        ],
    })


def update_movie(conn, id):
    u = conn.query_single('''
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

    return json.dumps({
        'id': str(u.id),
        'title': u.title,
    })


def insert_user(conn, val):
    num = random.randrange(1_000_000)
    u = conn.query_single('''
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

    return json.dumps({
        'id': str(u.id),
        'name': u.name,
        'image': u.image,
    })


def insert_movie(conn, val):
    num = random.randrange(1_000_000)
    m = conn.query_single(
        r'''
        SELECT (
            INSERT Movie {
                title := <str>$title,
                image := <str>$image,
                description := <str>$description,
                year := <int64>$year,
                directors := (
                    SELECT Person
                    FILTER .id = (<uuid>$d_id)
                ),
                cast := (
                    SELECT Person
                    FILTER .id IN {<uuid>$c_id0, <uuid>$c_id1, <uuid>$c_id2}
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
        d_id=val["people"][0],
        c_id0=val["people"][1],
        c_id1=val["people"][2],
        c_id2=val["people"][3],
    )

    return json.dumps({
        'id': str(m.id),
        'image': m.image,
        'title': m.title,
        'year': m.year,
        'description': m.description,

        'directors': [
            {
                'id': str(d.id),
                'full_name': d.full_name,
                'image': d.image,
            } for d in m.directors
        ],

        'cast': [
            {
                'id': str(c.id),
                'full_name': c.full_name,
                'image': c.image,
            } for c in m.cast
        ],
    })


def insert_movie_plus(conn, val):
    num = random.randrange(1_000_000)
    m = conn.query_single(
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

    return json.dumps({
        'id': str(m.id),
        'image': m.image,
        'title': m.title,
        'year': m.year,
        'description': m.description,

        'directors': [
            {
                'id': str(d.id),
                'full_name': d.full_name,
                'image': d.image,
            } for d in m.directors
        ],

        'cast': [
            {
                'id': str(c.id),
                'full_name': c.full_name,
                'image': c.image,
            } for c in m.cast
        ],
    })


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
