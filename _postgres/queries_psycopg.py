#
# Copyright (c) 2019 MagicStack Inc.
# All rights reserved.
#
# See LICENSE for details.
##


import json
import psycopg2
import random


INSERT_PREFIX = 'insert_test__'


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
        # re-use user IDs for update tests
        update_movie=[m[0] for m in movies],
        # generate as many insert stubs as "concurrency" to
        # accommodate concurrent inserts
        insert_user=[INSERT_PREFIX] * ctx.concurrency,
        insert_movie=[{
            'prefix': INSERT_PREFIX,
            'people': [p[0] for p in people[:4]],
        }] * ctx.concurrency,
        insert_movie_plus=[INSERT_PREFIX] * ctx.concurrency,
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


def update_movie(conn, id):
    with conn.cursor() as cur:
        cur.execute('''
            UPDATE
                movies
            SET
                title = movies.title || '---' || %(suffix)s
            WHERE
                movies.id = %(id)s
            RETURNING
                movies.id, movies.title
        ''', dict(id=id, suffix=str(id)[:8]))

        rows = cur.fetchall()
        cur.connection.commit()

    return json.dumps({
        'id': rows[0][0],
        'title': rows[0][1],
    })


def insert_user(conn, val):
    num = random.randrange(1_000_000)
    with conn.cursor() as cur:
        cur.execute('''
            INSERT INTO users (name, image) VALUES
                (%(name)s, %(image)s)
            RETURNING
                users.id, users.name, users.image
        ''', dict(name=f'{val}{num}', image=f'image_{val}{num}'))

        rows = cur.fetchall()
        cur.connection.commit()

    return json.dumps({
        'id': rows[0][0],
        'name': rows[0][1],
        'image': rows[0][2],
    })


def insert_movie(conn, val):
    num = random.randrange(1_000_000)
    with conn.cursor() as cur:
        cur.execute(
            '''
            INSERT INTO movies AS M (title, image, description, year) VALUES
                (%(title)s, %(image)s, %(description)s, %(year)s)
            RETURNING
                M.id, M.title, M.image, M.description, M.year
            ''',
            dict(
                title=f'{val["prefix"]}{num}',
                image=f'{val["prefix"]}image{num}.jpeg',
                description=f'{val["prefix"]}description{num}',
                year=num,
            )
        )
        movie = cur.fetchall()[0]

        # we don't need the full people records to insert things, but
        # we'll need them as return values
        cur.execute(
            '''
            SELECT
                person.id,
                person.full_name,
                person.image
            FROM
                persons AS person
            WHERE
                id IN (%s, %s, %s, %s);
            ''',
            val["people"],
        )
        people = cur.fetchall()

        directors = []
        cast = []

        for p in people:
            if p[0] == val['people'][0]:
                directors.append(p)
            else:
                cast.append(p)

        cur.execute(
            '''
            INSERT INTO directors AS M (person_id, movie_id) VALUES
                (%(d)s, %(m)s);
            ''',
            dict(
                d=directors[0][0],
                m=movie[0],
            )
        )
        cur.execute(
            '''
            INSERT INTO actors AS M (person_id, movie_id) VALUES
                (%(c0)s, %(m)s),
                (%(c1)s, %(m)s),
                (%(c2)s, %(m)s);
            ''',
            dict(
                c0=cast[0][0],
                c1=cast[1][0],
                c2=cast[2][0],
                m=movie[0],
            )
        )
        cur.connection.commit()

    result = {
        'id': movie[0],
        'image': movie[1],
        'title': movie[2],
        'description': movie[3],
        'year': movie[4],
        'directors': [
            {
                'id': p[0],
                'full_name': p[1],
                'image': p[2],
            } for p in directors
        ],
        'cast': [
            {
                'id': p[0],
                'full_name': p[1],
                'image': p[2],
            } for p in cast
        ],
    }
    return json.dumps(result)


def insert_movie_plus(conn, val):
    num = random.randrange(1_000_000)
    with conn.cursor() as cur:
        cur.execute(
            '''
            INSERT INTO movies AS M (title, image, description, year) VALUES
                (%(title)s, %(image)s, %(description)s, %(year)s)
            RETURNING
                M.id, M.title, M.image, M.description, M.year
            ''',
            dict(
                title=f'{val}{num}',
                image=f'{val}image{num}.jpeg',
                description=f'{val}description{num}',
                year=num,
            )
        )
        movie = cur.fetchall()[0]

        # we don't need the full people records to insert things, but
        # we'll need them as return values
        cur.execute(
            '''
            INSERT INTO persons AS P (first_name, last_name, image, bio) VALUES
                (%s, %s, %s, ''),
                (%s, %s, %s, ''),
                (%s, %s, %s, '')
            RETURNING
                P.id, P.full_name, P.image
            ''',
            [
                f'{val}Alice',
                f'{val}Director',
                f'{val}image{num}.jpeg',
                f'{val}Billie',
                f'{val}Actor',
                f'{val}image{num+1}.jpeg',
                f'{val}Cameron',
                f'{val}Actor',
                f'{val}image{num+2}.jpeg',
            ]
        )
        people = cur.fetchall()

        directors = []
        cast = []
        for p in people:
            if 'Director' in p[1]:
                directors.append(p)
            else:
                cast.append(p)

        cur.execute(
            '''
            INSERT INTO directors AS M (person_id, movie_id) VALUES
                (%(d)s, %(m)s);
            ''',
            dict(
                d=directors[0][0],
                m=movie[0],
            )
        )
        cur.execute(
            '''
            INSERT INTO actors AS M (person_id, movie_id) VALUES
                (%(c0)s, %(m)s),
                (%(c1)s, %(m)s);
            ''',
            dict(
                c0=cast[0][0],
                c1=cast[1][0],
                m=movie[0],
            )
        )
        cur.connection.commit()

    result = {
        'id': movie[0],
        'image': movie[1],
        'title': movie[2],
        'description': movie[3],
        'year': movie[4],
        'directors': [
            {
                'id': p[0],
                'full_name': p[1],
                'image': p[2],
            } for p in directors
        ],
        'cast': [
            {
                'id': p[0],
                'full_name': p[1],
                'image': p[2],
            } for p in cast
        ],
    }
    return json.dumps(result)


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
