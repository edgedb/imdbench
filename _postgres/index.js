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

  async fetchUser(conn, id) {
    // single query, no need for a transaction
    const res = await conn.query(
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

    return [res];
  }

  async userDetails(id) {
    const [res] = await this.fetchUser(this.pool, id);

    var user = {
      id: res.rows[0].id,
      name: res.rows[0].name,
      image: res.rows[0].image,
      latest_reviews: res.rows.map(r => {
        return {
          id: r.review_id,
          body: r.review_body,
          rating: r.review_rating,
          movie: {
            id: r.movie_id,
            image: r.movie_image,
            title: r.movie_title,
            avg_rating: parseFloat(r.movie_avg_rating)
          }
        };
      })
    };

    return JSON.stringify(user);
  }

  async fetchPerson(conn, id) {
    var person = (await conn.query(
      `
      SELECT
          p.id,
          p.full_name,
          p.image,
          p.bio
      FROM
          persons p
      WHERE
          p.id = $1
      `,
      [id]
    )).rows[0];

    const actedInRows = (await conn.query(
      `
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
          movie.year ASC, movie.title ASC
      `,
      [id]
    )).rows;

    const directedRows = (await conn.query(
      `
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
          movie.year ASC, movie.title ASC
      `,
      [id]
    )).rows;

    return [person, actedInRows, directedRows];
  }

  async personDetails(id) {
    // multiple queries need to be wrapped in a transaction so that the data is
    // guaranteed to be consistent
    const client = await this.pool.connect();

    try {
      await client.query("BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ");

      var [person, actedInRows, directedRows] = await this.fetchPerson(
        client,
        id
      );
      await client.query("COMMIT");
    } catch (e) {
      await client.query("ROLLBACK");
      throw e;
    } finally {
      client.release();
    }

    person.acted_in = actedInRows.map(mov => {
      mov.avg_rating = parseFloat(mov.avg_rating);
      return mov;
    });
    person.directed = directedRows.map(mov => {
      mov.avg_rating = parseFloat(mov.avg_rating);
      return mov;
    });

    return JSON.stringify(person);
  }

  async fetchMovie(conn, id) {
    var movie = (await conn.query(
      `
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
            movie.id = $1
        `,
      [id]
    )).rows[0];

    const directorsRows = (await conn.query(
      `
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
            person.last_name
        `,
      [id]
    )).rows;

    const castRows = (await conn.query(
      `
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
            person.last_name
        `,
      [id]
    )).rows;

    const reviewsRows = (await conn.query(
      `
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
            review.creation_time DESC
        `,
      [id]
    )).rows;

    return [movie, directorsRows, castRows, reviewsRows];
  }

  async movieDetails(id) {
    // multiple queries need to be wrapped in a transaction so that the data is
    // guaranteed to be consistent
    const client = await this.pool.connect();

    try {
      await client.query("BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ");

      var [movie, directorsRows, castRows, reviewsRows] = await this.fetchMovie(
        client,
        id
      );

      await client.query("COMMIT");
    } catch (e) {
      await client.query("ROLLBACK");
      throw e;
    } finally {
      client.release();
    }

    movie.directors = directorsRows;
    movie.cast = castRows;
    movie.reviews = reviewsRows.map(r => {
      return {
        id: r.id,
        body: r.body,
        rating: r.rating,
        author: {
          id: r.author_id,
          name: r.author_name,
          image: r.author_image
        }
      };
    });

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

    var movie = {
      id: res.rows[0].id,
      title: res.rows[0].title,
    };

    return JSON.stringify(movie);
  }

  async insertUser(id) {
    let num = Math.floor(Math.random() * 1000000);
    const res = await this.pool.query(
      `
      INSERT INTO users (name, image) VALUES
          ($1, $2)
      RETURNING
          users.id, users.name, users.image
      `,
      [id + num, 'image_' + id + num]
    );

    var user = {
      id: res.rows[0].id,
      name: res.rows[0].name,
      image: res.rows[0].image,
    };

    return JSON.stringify(user);
  }

  async insertMovie(val) {
    let num = Math.floor(Math.random() * 1000000);
    const movie = (await this.pool.query(
      `
      INSERT INTO movies AS M (title, image, description, year) VALUES
          ($1, $2, $3, $4)
      RETURNING
          M.id, M.title, M.image, M.description, M.year
      `,
      [
        val.prefix + num,
        val.prefix + "image" + num + ".jpeg",
        val.prefix + "description" + num,
        num,
      ],
    )).rows[0];

    const people = await this.pool.query(
      `
      SELECT
          P.id,
          P.full_name,
          P.image
      FROM
          persons AS P
      WHERE
          P.id IN ($1, $2, $3, $4);
      `,
      val.people,
    );

    var directors = [],
        cast = [];

    for (let p of people.rows) {
      if (p.id == val.people[0]) {
        directors.push(p)
      } else {
        cast.push(p)
      }
    }

    await this.pool.query(
      `
      INSERT INTO directors AS M (person_id, movie_id) VALUES
          ($1, $2);
      `,
      [directors[0].id, movie.id],
    );
    await this.pool.query(
      `
      INSERT INTO actors AS M (person_id, movie_id) VALUES
          ($1, $4),
          ($2, $4),
          ($3, $4);
      `,
      [cast[0].id, cast[1].id, cast[2].id, movie.id],
    );

    movie.directors = directors;
    movie.cast = cast;
    return JSON.stringify(movie);
  }

  async insertMoviePlus(val) {
    let num = Math.floor(Math.random() * 1000000);
    const movie = (await this.pool.query(
      `
      INSERT INTO movies AS M (title, image, description, year) VALUES
          ($1, $2, $3, $4)
      RETURNING
          M.id, M.title, M.image, M.description, M.year
      `,
      [
        val + num,
        val + "image" + num + ".jpeg",
        val + "description" + num,
        num,
      ]
    )).rows[0];

    const people = await this.pool.query(
      `
      INSERT INTO persons AS P (first_name, last_name, image, bio) VALUES
          ($1, $2, $3, ''),
          ($4, $5, $6, ''),
          ($7, $8, $9, '')
      RETURNING
          P.id, P.full_name, P.image
      `,
      [
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

    var directors = [],
        cast = [];

    for (let p of people.rows) {
      if (p.full_name.indexOf("Director") >= 0) {
        directors.push(p)
      } else {
        cast.push(p)
      }
    }

    await this.pool.query(
      `
      INSERT INTO directors AS M (person_id, movie_id) VALUES
          ($1, $2);
      `,
      [directors[0].id, movie.id],
    );
    await this.pool.query(
      `
      INSERT INTO actors AS M (person_id, movie_id) VALUES
          ($1, $3),
          ($2, $3);
      `,
      [cast[0].id, cast[1].id, movie.id],
    );

    movie.directors = directors;
    movie.cast = cast;
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
