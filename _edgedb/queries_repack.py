#
# Copyright (c) 2019 MagicStack Inc.
# All rights reserved.
#
# See LICENSE for details.
##


import edgedb
import json
import random

from . import queries

INSERT_PREFIX = 'insert_test__'


def connect(ctx):
    return edgedb.create_client().with_retry_options(
        edgedb.RetryOptions(attempts=10),
    )


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
    u = conn.query_single(queries.GET_USER, id=id)
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
    m = conn.query_single(queries.GET_MOVIE, id=id)
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
    p = conn.query_single(queries.GET_PERSON, id=id)
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
    u = conn.query_single(queries.UPDATE_MOVIE, id=id, suffix=str(id)[:8])
    return json.dumps({
        'id': str(u.id),
        'title': u.title,
    })


def insert_user(conn, val):
    num = random.randrange(1_000_000)
    u = conn.query_single(
        queries.INSERT_USER, name=f'{val}{num}', image=f'image_{val}{num}')
    return json.dumps({
        'id': str(u.id),
        'name': u.name,
        'image': u.image,
    })


def insert_movie(conn, val):
    num = random.randrange(1_000_000)
    m = conn.query_single(
        queries.INSERT_MOVIE,
        title=f'{val["prefix"]}{num}',
        image=f'{val["prefix"]}image{num}.jpeg',
        description=f'{val["prefix"]}description{num}',
        year=num,
        d_id=val["people"][0],
        cast=val["people"][1:4],
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
        queries.INSERT_MOVIE_PLUS,
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
