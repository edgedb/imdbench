import psycopg2


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
        get_user=[str(u[0]) for u in users],
        get_movie=[str(m[0]) for m in movies],
        get_person=[str(p[0]) for p in people],
        # re-use user IDs for update tests
        update_movie=[str(m[0]) for m in movies],
        # generate as many insert stubs as "concurrency" to
        # accommodate concurrent inserts
        insert_user=[INSERT_PREFIX] * ctx.concurrency,
    )


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


def cleanup(ctx, conn, queryname):
    if queryname in {'update_movie', 'insert_user'}:
        # The clean up is the same as setup for mutation benchmarks
        setup(ctx, conn, queryname)


def get_port(ctx):
    return ctx.pg_port


def get_queries(ctx):
    conn = connect(ctx)

    try:
        ids = load_ids(ctx, conn)
    finally:
        close(ctx, conn)

    return {
        'get_user': {
            'query': POSTGRES_GET_USER,
            'ids': ids['get_user'],
        },
        'get_movie': {
            'query': POSTGRES_GET_MOVIE,
            'ids': ids['get_movie'],
        },
        'get_person': {
            'query': POSTGRES_GET_PERSON,
            'ids': ids['get_person'],
        },
        'update_movie': {
            'query': POSTGRES_UPDATE_MOVIE,
            'ids': ids['update_movie'],
        },
        'insert_user': {
            'query': POSTGRES_INSERT_USER,
            'text': ids['insert_user'],
        },
    }


POSTGRES_GET_USER = '''
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
'''

POSTGRES_GET_MOVIE = '''
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
        id = $1;

    SELECT
        person.id,
        person.full_name,
        person.image
    FROM
        directors
        INNER JOIN persons AS person
            ON (directors.person_id = person.id)
    WHERE
        directors.movie_id = $1
    ORDER BY
        directors.list_order NULLS LAST,
        person.last_name;

    SELECT
        person.id,
        person.full_name,
        person.image
    FROM
        actors
        INNER JOIN persons AS person
            ON (actors.person_id = person.id)
    WHERE
        actors.movie_id = $1
    ORDER BY
        actors.list_order NULLS LAST,
        person.last_name;

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
        review.movie_id = $1
    ORDER BY
        review.creation_time DESC;
'''

POSTGRES_GET_PERSON = '''
    SELECT
        person.id,
        person.full_name,
        person.image,
        person.bio
    FROM
        persons AS person
    WHERE
        id = $1;

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
        actors.person_id = $1
    ORDER BY
        movie.year ASC, movie.title ASC;

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
        directors.person_id = $1
    ORDER BY
        movie.year ASC, movie.title ASC;
'''

POSTGRES_UPDATE_MOVIE = '''
    UPDATE
        movies
    SET
        title = movies.title || $2
    WHERE
        movies.id = $1
    RETURNING
        movies.id, movies.title
'''


POSTGRES_INSERT_USER = '''
    INSERT INTO users (name, image) VALUES
        ($1, $2)
    RETURNING
        users.id, users.name, users.image
'''
