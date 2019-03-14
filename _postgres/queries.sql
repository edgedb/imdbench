PREPARE get_user2 AS
SELECT
    jsonb_build_object(
        'id',
        users.id,
        'name',
        users.name,
        'image',
        users.image,
        'latest_reviews',
        (SELECT
            jsonb_agg(q.v)
         FROM
            (SELECT
                 jsonb_build_object(
                     'id',
                     review.id,
                     'body',
                     review.body,
                     'rating',
                     review.rating,
                     'movie',
                     jsonb_build_object(
                        'id',
                        movie.id,
                        'image',
                        movie.image,
                        'title',
                        movie.title,
                        'avg_rating',
                        movie.avg_rating
                     )
                 ) AS v
             FROM
                 reviews AS review
                 INNER JOIN movies AS movie
                     ON (review.movie_id = movie.id)
             WHERE
                 review.author_id = users.id
             ORDER BY
                 review.creation_time DESC
             LIMIT 3
            ) AS q)
        )
FROM
    users
WHERE
    users.id = $1;



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
            (
                SELECT avg(rating)
                FROM reviews
                WHERE movie_id = movie.id
            ) AS movie_avg_rating
        FROM
            reviews AS review
            INNER JOIN movies AS movie
                ON (review.movie_id = movie.id)
        WHERE
            review.author_id = users.id
        ORDER BY
            review.creation_time DESC
        LIMIT 3
    ) AS q
WHERE
    users.id = 1;


PREPARE get_movie AS
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
                author.id,
                author.name,
                author.image
            ) AS v
        FROM
            reviews AS review
            INNER JOIN users AS author
                ON (review.author_id = author.id)
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


PREPARE get_person AS
SELECT
    person.id,
    person.full_name,
    person.image,
    person.bio,

    (SELECT
        array_agg(q.v)
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
        array_agg(q.v)
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
