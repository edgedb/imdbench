"use strict";

const { Pool } = require("pg");

class App {
  constructor(options) {
    options = {
      user: "postgres_bench",
      host: "localhost",
      database: "postgres_bench",
      password: "edgedbbenchmark",
      port: 15432,
      ...(options || {})
    };
    this.pool = new Pool(options);
    this.concurrency = options.max;
    this.INSERT_PREFIX = 'insert_test__'
  }

  async userDetails(id) {
    const res = await this.pool.query(
      `
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
      `,
      [id]
    );

    const rows = res.rows;

    const user = {
      id: rows[0].id,
      name: rows[0].name,
      image: rows[0].image,
      latest_reviews: rows.map((r) => ({
        id: r.review_id,
        body: r.review_body,
        rating: r.review_rating,
        movie: {
          id: r.movie_id,
          image: r.movie_image,
          title: r.movie_title,
          avg_rating: parseFloat(r.movie_avg_rating)
        }
      }))
    };

    return JSON.stringify(user);
  }

  async personDetails(id) {
    const res = (await this.pool.query(
      `
      SELECT
          p.id,
          p.full_name,
          p.image,
          p.bio,
          (
            SELECT COALESCE(json_agg(t.v), '[]'::json)
            FROM (
              SELECT ROW(
                  movie.id,
                  movie.image,
                  movie.title,
                  movie.year,
                  movie.avg_rating
              ) as v
              FROM
                  actors
                  INNER JOIN movies AS movie
                      ON (actors.movie_id = movie.id)
              WHERE
                  actors.person_id = p.id
              ORDER BY
                  movie.year ASC, movie.title ASC
            ) t
          ) as acted_in,
          (
            SELECT COALESCE(json_agg(t.v), '[]'::json)
            FROM (
              SELECT ROW(
                  movie.id,
                  movie.image,
                  movie.title,
                  movie.year,
                  movie.avg_rating
                ) as v
              FROM
                  directors
                  INNER JOIN movies AS movie
                      ON (directors.movie_id = movie.id)
              WHERE
                  directors.person_id = p.id
              ORDER BY
                  movie.year ASC, movie.title ASC
            ) t
          ) as directed
      FROM
          persons p
      WHERE
          p.id = $1
      `,
      [id]
    ))

    const row = res.rows[0];

    const person = {
      id: row.id,
      full_name: row.full_name,
      image: row.image,
      bio: row.bio,
      acted_in: row.acted_in.map((m) => ({
        id: m.f1,
        image: m.f2,
        title: m.f3,
        year: m.f4,
        avg_rating: parseInt(m.f5)
      })),
      directed: row.directed.map((m) => ({
        id: m.f1,
        image: m.f2,
        title: m.f3,
        year: m.f4,
        avg_rating: parseInt(m.f5)
      }))
    };

    return JSON.stringify(person);
  }

  async movieDetails(id) {
    const res = await this.pool.query(
      `
        SELECT
            movie.id,
            movie.image,
            movie.title,
            movie.year,
            movie.description,
            movie.avg_rating,
            (
              SELECT json_agg(t.v)
              FROM (
                SELECT ROW(
                    person.id,
                    person.full_name,
                    person.image
                ) as v
                FROM
                    directors
                    INNER JOIN persons AS person
                        ON (directors.person_id = person.id)
                WHERE
                    directors.movie_id = movie.id
                ORDER BY
                    directors.list_order NULLS LAST,
                    person.last_name
              ) t
            ) as directors,
            (
              SELECT json_agg(t.v)
              FROM (
                SELECT ROW(
                    person.id,
                    person.full_name,
                    person.image
                ) as v
                FROM
                    actors
                    INNER JOIN persons AS person
                        ON (actors.person_id = person.id)
                WHERE
                    actors.movie_id = movie.id
                ORDER BY
                    actors.list_order NULLS LAST,
                    person.last_name
              ) t
            ) as cast,
            (
              SELECT json_agg(t.v)
              FROM (
                SELECT ROW(
                    review.id,
                    review.body,
                    review.rating,
                    author.id,
                    author.name,
                    author.image
                ) as v
                FROM
                    reviews AS review
                    INNER JOIN users AS author
                        ON (review.author_id = author.id)
                WHERE
                    review.movie_id = movie.id
                ORDER BY
                    review.creation_time DESC
              ) t
            ) as reviews
        FROM
            movies AS movie
        WHERE
            movie.id = $1
        `,
      [id]
    );

    const row = res.rows[0];

    const movie = {
      id: row.id,
      image: row.image,
      title: row.title,
      year: row.year,
      description: row.description,
      avg_rating: parseFloat(row.avg_rating),
      directors: row.directors.map((d) => ({
        id: d.f1,
        full_name: d.f2,
        image:d.f3
      })),
      cast: row.cast.map((c) => ({
        id: c.f1,
        full_name: c.f2,
        image:c.f3
      })),
      reviews: row.reviews.map((r) => ({
        id: r.f1,
        body: r.f2,
        rating: r.f3,
        author: {
          id: r.f4,
          name: r.f5,
          image: r.f6
        }
      }))
    };

    return JSON.stringify(movie);
  }

  async updateMovie(id) {
    const res = await this.pool.query(
      `
      UPDATE
          movies
      SET
          title = movies.title || $2
      WHERE
          movies.id = $1
      RETURNING
          movies.id, movies.title
      `,
      [id, "---" + id]
    );

    const row = res.rows[0];

    const movie = {
      id: row.id,
      title: row.title
    };

    return JSON.stringify(movie);
  }

  async insertUser(id) {
    const num = Math.floor(Math.random() * 1000000);
    const res = await this.pool.query(
      `
      INSERT INTO users (name, image) VALUES
          ($1, $2)
      RETURNING
          users.id, users.name, users.image
      `,
      [id + num, 'image_' + id + num]
    );

    const row = res.rows[0];

    const user = {
      id: row.id,
      name: row.name,
      image: row.image
    };

    return JSON.stringify(user);
  }

  async insertMovie(val) {
    const num = Math.floor(Math.random() * 1000000);
    const res = await this.pool.query(
      `
      WITH movie_insert AS (
          INSERT INTO movies (title, image, description, year)
          VALUES ($1, $2, $3, $4)
          RETURNING id, title, image, description, year
      ),
      director_persons AS (
        SELECT p.id, p.full_name, p.image
        FROM persons p
        WHERE p.id = $5
      ),
      actor_persons AS (
        SELECT p.id, p.full_name, p.image
        FROM persons p
        WHERE p.id = ANY($6)
      ),
      director_insert AS (
        INSERT INTO directors(person_id, movie_id)
        SELECT dp.id, mi.id FROM movie_insert mi, director_persons dp
      ),
      cast_inserts AS (
        INSERT INTO actors(person_id, movie_id)
        SELECT ap.id, mi.id
        FROM actor_persons ap, movie_insert mi
      )
      SELECT
        mi.id,
        mi.title,
        mi.image,
        mi.description,
        mi.year,
        (
          SELECT json_agg(t.v)
          FROM (
            SELECT ROW(
              dp.id,
              dp.full_name,
              dp.image
            ) as v
            FROM director_persons dp
          ) t
        ) as directors,
        (
          SELECT json_agg(t.v)
          FROM (
            SELECT ROW(
              ap.id,
              ap.full_name,
              ap.image
            ) as v
            FROM actor_persons ap
          ) t
        ) as cast
      FROM movie_insert mi
      `,
      [
        val.prefix + num,
        val.prefix + "image" + num + ".jpeg",
        val.prefix + "description" + num,
        num,
        val.people[0],
        val.people.slice(1)
      ],
    );

    const row = res.rows[0];

    const movie = {
      id: row.id,
      title: row.title,
      image: row.image,
      description: row.description,
      year: row.year,
      directors: row.directors.map((d) => ({
        id: d.f1,
        full_name: d.f2,
        image: d.f3
      })),
      cast: row.cast.map((c) => ({
        id: c.f1,
        full_name: c.f2,
        image: c.f3
      }))
    };

    return JSON.stringify(movie);
  }

  async insertMoviePlus(val) {
    const num = Math.floor(Math.random() * 1000000);
    const res = await this.pool.query(
      `
      WITH movie_insert AS (
          INSERT INTO movies (title, image, description, year)
          VALUES ($1, $2, $3, $4)
          RETURNING id, title, image, description, year
      ),
      director_persons AS (
        INSERT INTO persons AS p (first_name, last_name, image, bio)
        VALUES ($5, $6, $7, '')
        RETURNING p.id, p.full_name, p.image
      ),
      actor_persons AS (
        INSERT INTO persons AS p (first_name, last_name, image, bio)
        VALUES ($8, $9, $10, ''), ($11, $12, $13, '')
        RETURNING p.id, p.full_name, p.image
      ),
      director_insert AS (
        INSERT INTO directors(person_id, movie_id)
        SELECT dp.id, mi.id FROM movie_insert mi, director_persons dp
      ),
      cast_inserts AS (
        INSERT INTO actors(person_id, movie_id)
        SELECT ap.id, mi.id
        FROM actor_persons ap, movie_insert mi
      )
      SELECT
        mi.id,
        mi.title,
        mi.image,
        mi.description,
        mi.year,
        (
          SELECT json_agg(t.v)
          FROM (
            SELECT ROW(
              dp.id,
              dp.full_name,
              dp.image
            ) as v
            FROM director_persons dp
          ) t
        ) as directors,
        (
          SELECT json_agg(t.v)
          FROM (
            SELECT ROW(
              ap.id,
              ap.full_name,
              ap.image
            ) as v
            FROM actor_persons ap
          ) t
        ) as cast
      FROM movie_insert mi
      `,
      [
        val + num,
        val + "image" + num + ".jpeg",
        val + "description" + num,
        num,
        val + "Alice",
        val + "Director",
        val + "image" + num + ".jpeg",
        val + "Billie",
        val + "Actor",
        val + "image" + (num + 1) + ".jpeg",
        val + "Cameron",
        val + "Actor",
        val + "image" + (num + 2) + ".jpeg",
      ],
    );

    const row = res.rows[0];

    const movie = {
      id: row.id,
      title: row.title,
      image: row.image,
      description: row.description,
      year: row.year,
      directors: row.directors.map((d) => ({
        id: d.f1,
        full_name: d.f2,
        image: d.f3
      })),
      cast: row.cast.map((c) => ({
        id: c.f1,
        full_name: c.f2,
        image: c.f3
      }))
    };

    return JSON.stringify(movie);
  }

  async benchQuery(query, id) {
    if (query == "get_user") {
      return await this.userDetails(id);
    } else if (query == "get_person") {
      return await this.personDetails(id);
    } else if (query == "get_movie") {
      return await this.movieDetails(id);
    } else if (query == "update_movie") {
      return await this.updateMovie(id);
    } else if (query == "insert_user") {
      return await this.insertUser(id);
    } else if (query == "insert_movie") {
      return await this.insertMovie(id);
    } else if (query == "insert_movie_plus") {
      return await this.insertMoviePlus(id);
    }
  }

  async getIDs() {
    var ids = await Promise.all([
      await this.pool.query("SELECT u.id FROM users u ORDER BY random();"),
      await this.pool.query("SELECT p.id FROM persons p ORDER BY random();"),
      await this.pool.query("SELECT m.id FROM movies m ORDER BY random();")
    ]);
    var people = ids[1].rows.map(x => x.id);

    return {
      get_user: ids[0].rows.map(x => x.id),
      get_person: people,
      get_movie: ids[2].rows.map(x => x.id),
      // re-use user IDs for update tests
      update_movie: ids[2].rows.map(x => x.id),
      // generate as many insert stubs as "concurrency" to
      // accommodate concurrent inserts
      insert_user: Array(this.concurrency).fill(this.INSERT_PREFIX),
      insert_movie: Array(this.concurrency).fill({
        prefix: this.INSERT_PREFIX,
        people: people.slice(0, 4),
      }),
      insert_movie_plus: Array(this.concurrency).fill(this.INSERT_PREFIX),
    };
  }

  async setup(query) {
    if (query == "update_movie") {
      return await this.pool.query(`
        UPDATE
            movies
        SET
            title = split_part(movies.title, '---', 1)
        WHERE
            movies.title LIKE '%---%';
      `);
    } else if (query == "insert_user") {
      return await this.pool.query(`
        DELETE FROM
            users
        WHERE
            users.name LIKE $1;
      `, [this.INSERT_PREFIX + '%']);
    } else if (query == "insert_movie" || query == "insert_movie_plus") {
      await this.pool.query(`
        DELETE FROM
            "directors" as D
        USING
            "movies" as M
        WHERE
            D.movie_id = M.id AND M.image LIKE $1;
      `, [this.INSERT_PREFIX + '%']);
      await this.pool.query(`
        DELETE FROM
            "actors" as A
        USING
            "movies" as M
        WHERE
            A.movie_id = M.id AND M.image LIKE $1;
      `, [this.INSERT_PREFIX + '%']);
      await this.pool.query(`
        DELETE FROM
            "movies" as M
        WHERE
            M.image LIKE $1;
      `, [this.INSERT_PREFIX + '%']);
      return await this.pool.query(`
        DELETE FROM
            "persons" as P
        WHERE
            P.image LIKE $1;
      `, [this.INSERT_PREFIX + '%']);
    }
  }

  async cleanup(query) {
    if ([
      "update_movie", "insert_user", "insert_movie", "insert_movie_plus"
    ].indexOf(query) >= 0) {
      // The clean up is the same as setup for mutation benchmarks
      return await this.setup(query);
    }
  }

  getConnection(i) {
    return this;
  }
}
module.exports.App = App;
