import asyncpg
import json


ASYNC = True


async def connect(ctx):
    return await asyncpg.connect(
        user='postgres_bench', database='postgres_bench',
        password='edgedbbenchmark')


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

    rows = await conn.fetch('''
        SELECT
            movie.id,
            movie.image,
            movie.title,
            movie.year,
            movie.description,
            movie.avg_rating,

            (SELECT
                array_agg(q.v)
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
                array_agg(q.v)
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
                array_agg(q.v)
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

    # print(rows)
