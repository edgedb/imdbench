--
-- Copyright (c) 2019 MagicStack Inc.
-- All rights reserved.
--
-- See LICENSE for details.
--


CREATE TABLE movies (
    id serial PRIMARY KEY,
    image text NOT NULL,
    title text NOT NULL,
    year int NOT NULL,
    description text NOT NULL
);


CREATE TABLE users (
    id serial PRIMARY KEY,
    name text NOT NULL,
    image text NOT NULL
);


CREATE TABLE persons (
    id serial PRIMARY KEY,
    first_name text NOT NULL,
    middle_name text NOT NULL DEFAULT '',
    last_name text NOT NULL,
    image text NOT NULL,
    bio text NOT NULL
);


CREATE OR REPLACE FUNCTION full_name(p persons) RETURNS text AS $$
    SELECT
        (CASE WHEN p.middle_name != '' THEN
            p.first_name || ' ' || p.middle_name || ' ' || p.last_name
         ELSE
            p.first_name || ' ' || p.last_name
         END);
$$ LANGUAGE SQL STABLE;


CREATE TABLE directors (
    id serial PRIMARY KEY,
    list_order int,
    person_id int NOT NULL REFERENCES persons(id),
    movie_id int NOT NULL REFERENCES movies(id)
);

CREATE INDEX directors_person_index ON directors(person_id);
CREATE INDEX directors_movie_index ON directors(movie_id);


CREATE TABLE actors (
    id serial PRIMARY KEY,
    list_order int,
    person_id int NOT NULL REFERENCES persons(id),
    movie_id int NOT NULL REFERENCES movies(id)
);

CREATE INDEX actors_person_index ON actors(person_id);
CREATE INDEX actors_movie_index ON actors(movie_id);


CREATE TABLE reviews (
    id serial PRIMARY KEY,
    body text NOT NULL,
    rating int NOT NULL,
    creation_time timestamptz NOT NULL,
    author_id int NOT NULL REFERENCES users(id),
    movie_id int NOT NULL REFERENCES movies(id)
);

CREATE INDEX review_author_index ON reviews(author_id);
CREATE INDEX review_movie_index ON reviews(movie_id);
CREATE INDEX creation_time_index ON reviews(creation_time);


CREATE OR REPLACE FUNCTION avg_rating(m movies) RETURNS numeric AS $$
    SELECT avg(rating)
    FROM reviews
    WHERE movie_id = m.id;
$$ LANGUAGE SQL STABLE;
