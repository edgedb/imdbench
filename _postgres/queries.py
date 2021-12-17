#
# Copyright (c) 2019 MagicStack Inc.
# All rights reserved.
#
# See LICENSE for details.
##


import asyncpg
import json
import random


ASYNC = True
INSERT_PREFIX = 'insert_test__'


async def connect(ctx):
    return await asyncpg.connect(
        user='postgres_bench',
        database='postgres_bench',
        password='edgedbbenchmark',
        host=ctx.db_host,
        port=ctx.pg_port)


async def close(ctx, conn):
    await conn.close()


async def load_ids(ctx, conn):
    users = await conn.fetch(
        'SELECT u.id FROM users u ORDER BY random() LIMIT $1',
        ctx.number_of_ids)

    movies = await conn.fetch(
        'SELECT m.id FROM movies m ORDER BY random() LIMIT $1',
        ctx.number_of_ids)

    people = await conn.fetch(
        'SELECT p.id FROM persons p ORDER BY random() LIMIT $1',
        ctx.number_of_ids)

    return dict(
        get_user=[u['id'] for u in users],
        get_movie=[m['id'] for m in movies],
        get_person=[p['id'] for p in people],
        # re-use user IDs for update tests
        update_movie=[u['id'] for u in movies],
        # generate as many insert stubs as "concurrency" to
        # accommodate concurrent inserts
        insert_user=[INSERT_PREFIX] * ctx.concurrency,
    )


async def get_user(conn, id):
    # This query with a LATERAL join works well because
    # we fetch only 10 latest reviews per user, so the
    # data duplication is relatively low.

    rows = await conn.fetch('''
        SELECT
            users.id,
            users.name,
            users.image,
            q.review_id,
            q.review_body,
            q.review_rating,
            q.movie_id,
            q.movie_image,
            q.movie_title,
            q.movie_avg_rating
        FROM
            users,
            LATERAL (
                SELECT
                    review.id AS review_id,
                    review.body AS review_body,
                    review.rating AS review_rating,
                    movie.id AS movie_id,
                    movie.image AS movie_image,
                    movie.title AS movie_title,
                    movie.avg_rating AS movie_avg_rating
                FROM
                    reviews AS review
                    INNER JOIN movies AS movie
                        ON (review.movie_id = movie.id)
                WHERE
                    review.author_id = users.id
                ORDER BY
                    review.creation_time DESC
                LIMIT 10
            ) AS q
        WHERE
            users.id = $1
    ''', id)

    return json.dumps({
        'id': rows[0]['id'],
        'name': rows[0]['name'],
        'image': rows[0]['image'],
        'latest_reviews': [
            {
                'id': r['review_id'],
                'body': r['review_body'],
                'rating': r['review_rating'],
                'movie': {
                    'id': r['movie_id'],
                    'image': r['movie_image'],
                    'title': r['movie_title'],
                    'avg_rating': float(r['movie_avg_rating']),
                }
            } for r in rows
        ]
    })


async def get_movie(conn, id):
    # This query only works on PostgreSQL 11 and
    # only asyncpg can unpack it.

    movie = await conn.fetch('''
        SELECT
            movie.id,
            movie.image,
            movie.title,
            movie.year,
            movie.description,
            movie.avg_rating,

            (SELECT
                COALESCE(array_agg(q.v), (ARRAY[])::record[])
             FROM
                (SELECT
                    ROW(
                        person.id,
                        person.full_name,
                        person.image
                    ) AS v
                FROM
                    directors
                    INNER JOIN persons AS person
                        ON (directors.person_id = person.id)
                WHERE
                    directors.movie_id = movie.id
                ORDER BY
                    directors.list_order NULLS LAST,
                    person.last_name
                ) AS q
            ) AS directors,

            (SELECT
                COALESCE(array_agg(q.v), (ARRAY[])::record[])
             FROM
                (SELECT
                    ROW(
                        person.id,
                        person.full_name,
                        person.image
                    ) AS v
                FROM
                    actors
                    INNER JOIN persons AS person
                        ON (actors.person_id = person.id)
                WHERE
                    actors.movie_id = movie.id
                ORDER BY
                    actors.list_order NULLS LAST,
                    person.last_name
                ) AS q
            ) AS actors,


            (SELECT
                COALESCE(array_agg(q.v), (ARRAY[])::record[])
             FROM
                (SELECT
                    ROW(
                        review.id,
                        review.body,
                        review.rating,
                        (SELECT
                            ROW(
                                author.id,
                                author.name,
                                author.image
                            )
                            FROM
                                users AS author
                            WHERE
                                review.author_id = author.id
                        )
                    ) AS v
                FROM
                    reviews AS review
                WHERE
                    review.movie_id = movie.id
                ORDER BY
                    review.creation_time DESC
                ) AS q
            ) AS reviews
        FROM
            movies AS movie
        WHERE
            id = $1;
    ''', id)

    movie = movie[0]

    return json.dumps({
        'id': movie['id'],
        'image': movie['image'],
        'title': movie['title'],
        'year': movie['year'],
        'description': movie['description'],
        'avg_rating': float(movie['avg_rating']),

        'directors': [
            {
                'id': d[0],
                'full_name': d[1],
                'image': d[2],
            } for d in movie['directors']
        ],

        'cast': [
            {
                'id': c[0],
                'full_name': c[1],
                'image': c[2],
            } for c in movie['actors']
        ],

        'reviews': [
            {
                'id': r[0],
                'body': r[1],
                'rating': r[2],
                'author': {
                    'id': r[3][0],
                    'name': r[3][1],
                    'image': r[3][2],
                }
            } for r in movie['reviews']
        ]
    })


async def get_person(conn, id):
    # This query only works on PostgreSQL 11 and
    # only asyncpg can unpack it.

    person = await conn.fetch('''
        SELECT
            person.id,
            person.full_name,
            person.image,
            person.bio,

            (SELECT
                COALESCE(array_agg(q.v), (ARRAY[])::record[])
             FROM
                (SELECT
                    ROW(
                        movie.id,
                        movie.image,
                        movie.title,
                        movie.year,
                        movie.avg_rating
                    ) AS v
                FROM
                    actors
                    INNER JOIN movies AS movie
                        ON (actors.movie_id = movie.id)
                WHERE
                    actors.person_id = person.id
                ORDER BY
                    movie.year ASC, movie.title ASC
                ) AS q
            ) AS acted_in,

            (SELECT
                COALESCE(array_agg(q.v), (ARRAY[])::record[])
             FROM
                (SELECT
                    ROW(
                        movie.id,
                        movie.image,
                        movie.title,
                        movie.year,
                        movie.avg_rating
                    ) AS v
                FROM
                    directors
                    INNER JOIN movies AS movie
                        ON (directors.movie_id = movie.id)
                WHERE
                    directors.person_id = person.id
                ORDER BY
                    movie.year ASC, movie.title ASC
                ) AS q
            ) AS directed

        FROM
            persons AS person
        WHERE
            id = $1;
    ''', id)

    person = person[0]

    return json.dumps({
        'id': person['id'],
        'full_name': person['full_name'],
        'image': person['image'],
        'bio': person['bio'],

        'acted_in': [
            {
                'id': mov[0],
                'image': mov[1],
                'title': mov[2],
                'year': mov[3],
                'avg_rating': float(mov[4]),
            } for mov in person['acted_in']
        ],

        'directed': [
            {
                'id': mov[0],
                'image': mov[1],
                'title': mov[2],
                'year': mov[3],
                'avg_rating': float(mov[4]),
            } for mov in person['directed']
        ]
    })


async def update_movie(conn, id):
    rows = await conn.fetch('''
        UPDATE
            movies
        SET
            title = movies.title || $2
        WHERE
            movies.id = $1
        RETURNING
            movies.id, movies.title
    ''', id, f'---{str(id)[:8]}')

    return json.dumps({
        'id': rows[0]['id'],
        'title': rows[0]['title'],
    })


async def insert_user(conn, val):
    num = random.randrange(1_000_000)
    rows = await conn.fetch('''
        INSERT INTO users (name, image) VALUES
            ($1, $2)
        RETURNING
            users.id, users.name, users.image
    ''', f'{val}{num}', f'image_{val}{num}')

    return json.dumps({
        'id': rows[0]['id'],
        'name': rows[0]['name'],
        'image': rows[0]['image'],
    })


async def setup(ctx, conn, queryname):
    if queryname == 'update_movie':
        await conn.execute('''
            UPDATE
                movies
            SET
                title = split_part(movies.title, '---', 1)
            WHERE
                movies.title LIKE '%---%'
        ''')
    elif queryname == 'insert_user':
        await conn.fetch('''
            DELETE FROM
                users
            WHERE
                users.name LIKE $1
        ''', f'{INSERT_PREFIX}%')


async def cleanup(ctx, conn, queryname):
    if queryname in {'update_movie', 'insert_user'}:
        # The clean up is the same as setup for mutation benchmarks
        await setup(ctx, conn, queryname)
