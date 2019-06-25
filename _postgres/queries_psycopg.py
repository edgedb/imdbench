#
# Copyright (c) 2019 MagicStack Inc.
# All rights reserved.
#
# See LICENSE for details.
##


import json

import psycopg2


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

    cur.execute(
        'SELECT u.id FROM users u ORDER BY random() LIMIT %s',
        [ctx.number_of_ids])
    users = cur.fetchall()

    cur.execute(
        'SELECT m.id FROM movies m ORDER BY random() LIMIT %s',
        [ctx.number_of_ids])
    movies = cur.fetchall()

    cur.execute(
        'SELECT p.id FROM persons p ORDER BY random() LIMIT %s',
        [ctx.number_of_ids])
    people = cur.fetchall()

    return dict(
        get_user=[u[0] for u in users],
        get_movie=[m[0] for m in movies],
        get_person=[p[0] for p in people],
    )


def get_user(conn, id):
    with conn.cursor() as cur:
        cur.execute('''
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
                users.id = %s
        ''', [id])

        rows = cur.fetchall()

    return json.dumps({
        'id': rows[0][0],
        'name': rows[0][1],
        'image': rows[0][2],
        'latest_reviews': [
            {
                'id': r[3],
                'body': r[4],
                'rating': r[5],
                'movie': {
                    'id': r[6],
                    'image': r[7],
                    'title': r[8],
                    'avg_rating': float(r[9]),
                }
            } for r in rows
        ]
    })


def get_movie(conn, id):
    with conn.cursor() as cur:
        cur.execute('''
            SELECT
                movie.id,
                movie.image,
                movie.title,
                movie.year,
                movie.description,
                movie.avg_rating
            FROM
                movies AS movie
            WHERE
                movie.id = %s;
        ''', [id])

        movie_rows = cur.fetchall()
        movie = movie_rows[0]

        cur.execute('''
            SELECT
                person.id,
                person.full_name,
                person.image
            FROM
                directors
                INNER JOIN persons AS person
                    ON (directors.person_id = person.id)
            WHERE
                directors.movie_id = %s
            ORDER BY
                directors.list_order NULLS LAST,
                person.last_name
        ''', [id])
        directors_rows = cur.fetchall()

        cur.execute('''
            SELECT
                person.id,
                person.full_name,
                person.image
            FROM
                actors
                INNER JOIN persons AS person
                    ON (actors.person_id = person.id)
            WHERE
                actors.movie_id = %s
            ORDER BY
                actors.list_order NULLS LAST,
                person.last_name
        ''', [id])
        cast_rows = cur.fetchall()

        cur.execute('''
            SELECT
                review.id,
                review.body,
                review.rating,
                author.id AS author_id,
                author.name AS author_name,
                author.image AS author_image
            FROM
                reviews AS review
                INNER JOIN users AS author
                    ON (review.author_id = author.id)
            WHERE
                review.movie_id = %s
            ORDER BY
                review.creation_time DESC
        ''', [id])
        reviews_rows = cur.fetchall()

    return json.dumps({
        'id': movie[0],
        'image': movie[1],
        'title': movie[2],
        'year': movie[3],
        'description': movie[4],
        'avg_rating': str(movie[5]),

        'directors': [
            {
                'id': d[0],
                'full_name': d[1],
                'image': d[2]
            } for d in directors_rows
        ],

        'cast': [
            {
                'id': c[0],
                'full_name': c[1],
                'image': c[2]
            } for c in cast_rows
        ],

        'reviews': [
            {
                'id': r[0],
                'body': r[1],
                'rating': r[2],
                'author': {
                    'id': r[3],
                    'name': r[4],
                    'image': r[5]
                }
            } for r in reviews_rows
        ]
    })


def get_person(conn, id):
    with conn.cursor() as cur:
        cur.execute('''
            SELECT
                p.id,
                p.full_name,
                p.image,
                p.bio
            FROM
                persons p
            WHERE
                p.id = %s;
        ''', [id])
        people_rows = cur.fetchall()
        person = people_rows[0]

        cur.execute('''
            SELECT
                movie.id,
                movie.image,
                movie.title,
                movie.year,
                movie.avg_rating
            FROM
                actors
                INNER JOIN movies AS movie
                    ON (actors.movie_id = movie.id)
            WHERE
                actors.person_id = %s
            ORDER BY
                movie.year ASC, movie.title ASC
        ''', [id])
        acted_in_rows = cur.fetchall()

        cur.execute('''
            SELECT
                movie.id,
                movie.image,
                movie.title,
                movie.year,
                movie.avg_rating
            FROM
                directors
                INNER JOIN movies AS movie
                    ON (directors.movie_id = movie.id)
            WHERE
                directors.person_id = %s
            ORDER BY
                movie.year ASC, movie.title ASC
        ''', [id])
        directed_rows = cur.fetchall()

    return json.dumps({
        'id': person[0],
        'full_name': person[1],
        'image': person[2],
        'bio': person[3],

        'acted_in': [
            {
                'id': mov[0],
                'image': mov[1],
                'title': mov[2],
                'year': mov[3],
                'avg_rating': float(mov[4]),
            } for mov in acted_in_rows
        ],

        'directed': [
            {
                'id': mov[0],
                'image': mov[1],
                'title': mov[2],
                'year': mov[3],
                'avg_rating': float(mov[4]),
            } for mov in directed_rows
        ],
    })
