--
-- Copyright (c) 2019 MagicStack Inc.
-- All rights reserved.
--
-- See LICENSE for details.
--


CREATE TABLE movies (
    id INT AUTO_INCREMENT PRIMARY KEY,
    image varchar(191) NOT NULL,
    title varchar(191) NOT NULL,
    year int NOT NULL,
    description varchar(191) NOT NULL
);


CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name varchar(191) NOT NULL,
    image varchar(191) NOT NULL
);


CREATE TABLE persons (
    id INT AUTO_INCREMENT PRIMARY KEY,
    first_name varchar(191) NOT NULL,
    middle_name varchar(191) NOT NULL DEFAULT '',
    last_name varchar(191) NOT NULL,
    image varchar(191) NOT NULL,
    bio varchar(191) NOT NULL
);


CREATE TABLE directors (
    id INT AUTO_INCREMENT PRIMARY KEY,
    list_order int,
    person_id int NOT NULL REFERENCES persons(id),
    movie_id int NOT NULL REFERENCES movies(id)
);

CREATE INDEX directors_person_index ON directors(person_id);
CREATE INDEX directors_movie_index ON directors(movie_id);


CREATE TABLE actors (
    id INT AUTO_INCREMENT PRIMARY KEY,
    list_order int,
    person_id int NOT NULL REFERENCES persons(id),
    movie_id int NOT NULL REFERENCES movies(id)
);

CREATE INDEX actors_person_index ON actors(person_id);
CREATE INDEX actors_movie_index ON actors(movie_id);


CREATE TABLE reviews (
    id INT AUTO_INCREMENT PRIMARY KEY,
    body varchar(191) NOT NULL,
    rating int NOT NULL,
    creation_time timestamp NOT NULL,
    author_id int NOT NULL REFERENCES users(id),
    movie_id int NOT NULL REFERENCES movies(id)
);

CREATE INDEX review_author_index ON reviews(author_id);
CREATE INDEX review_movie_index ON reviews(movie_id);
CREATE INDEX creation_time_index ON reviews(creation_time);
