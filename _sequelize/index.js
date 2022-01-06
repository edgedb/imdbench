"use strict";

const { App } = require("./models.js");

class BenchApp extends App {
  async userDetails(id) {
    const User = this.models.User;
    const Review = this.models.Review;
    const Movie = this.models.Movie;

    var result = await User.findByPk(id, {
      include: [
        {
          model: Review,
          as: "latest_reviews",
          attributes: ["id", "body", "rating"],
          include: [
            {
              model: Movie,
              as: "movie",
              attributes: ["id", "image", "title", Movie.avg_rating("movie")]
            }
          ],
          order: [["creation_time", "DESC"]],
          limit: 10
        }
      ],
      benchmark: true
    });

    return JSON.stringify(result);
  }

  async personDetails(id) {
    const Person = this.models.Person;
    const Movie = this.models.Movie;

    var result = await Person.findByPk(id, {
      attributes: ["id", "full_name", "image", "bio"],
      include: [
        {
          model: Movie,
          as: "acted_in",
          attributes: [
            "id",
            "image",
            "title",
            "year",
            Movie.avg_rating("acted_in")
          ],
          through: { attributes: [] }
        },
        {
          model: Movie,
          as: "directed",
          attributes: [
            "id",
            "image",
            "title",
            "year",
            Movie.avg_rating("directed")
          ],
          through: { attributes: [] }
        }
      ],
      order: [
        [{ model: Movie, as: "acted_in" }, "year", "ASC"],
        [{ model: Movie, as: "acted_in" }, "title", "ASC"],
        [{ model: Movie, as: "directed" }, "year", "ASC"],
        [{ model: Movie, as: "directed" }, "title", "ASC"]
      ],
      benchmark: true
    });

    // still need to repack the top-level person
    result = {
      id: result.id,
      full_name: result.full_name,
      image: result.image,
      bio: result.bio,
      acted_in: result.acted_in,
      directed: result.directed
    };

    return JSON.stringify(result);
  }

  async movieDetails(id) {
    const Movie = this.models.Movie;
    const Person = this.models.Person;
    const Review = this.models.Review;
    const Directors = this.models.Directors;
    const Cast = this.models.Cast;

    var result = await Movie.findByPk(id, {
      include: [
        {
          model: Person,
          as: "directors",
          attributes: [
            "id",
            "first_name",
            "middle_name",
            "last_name",
            "full_name",
            "image"
          ],
          through: { attributes: [] }
        },
        {
          model: Person,
          as: "cast",
          attributes: [
            "id",
            "first_name",
            "middle_name",
            "last_name",
            "full_name",
            "image"
          ],
          through: { attributes: [] }
        },
        {
          separate: true,
          model: Review,
          as: "reviews",
          attributes: ["id", "body", "rating"],
          include: ["author"],
          order: [["creation_time", "DESC"]]
        }
      ],
      order: [
        [{ model: Person, as: "directors" }, Directors, "list_order", "ASC"],
        [{ model: Person, as: "directors" }, "last_name", "ASC"],
        [{ model: Person, as: "cast" }, Cast, "list_order", "ASC"],
        [{ model: Person, as: "cast" }, "last_name", "ASC"]
      ],
      benchmark: true
    });

    result = result.toJSON();
    // compute the average rating from the actual fetched reviews
    result.avg_rating =
      result.reviews.reduce((total, r) => total + r.rating, 0) /
      result.reviews.length;
    // clean up directors and cast attributes
    for (let fname of ["directors", "cast"]) {
      result[fname] = result[fname].map(person => {
        return {
          id: person.id,
          full_name: person.full_name,
          image: person.image
        };
      });
    }

    return JSON.stringify(result);
  }

  async updateMovie(val) {
    const Movie = this.models.Movie;
    var result = await Movie.update({
      title: val.title
    }, {
      where: {id: val.id},
      returning: ["id", "title"],
    });

    return JSON.stringify(result[1][0]);
  }

  async insertUser(val) {
    let num = Math.floor(Math.random() * 1000000);
    const User = this.models.User;
    var result = await User.create({
      // using the automatic id sequence from cast as a matter of convenience
      id: App.literal(`nextval('"Cast_id_seq"'::regclass)`),
      name: val + num,
      image: val + 'image' + num,
    });

    return JSON.stringify(result);
  }

  async _getMovieAfterInsert(id) {
    const Movie = this.models.Movie;
    const Person = this.models.Person;
    const Directors = this.models.Directors;
    const Cast = this.models.Cast;

    // returning is not sufficient to get nested results, so we fetch them
    var result = await Movie.findByPk(id, {
      include: [
        {
          model: Person,
          as: "directors",
          attributes: [
            "id",
            "first_name",
            "middle_name",
            "last_name",
            "full_name",
            "image"
          ],
          through: { attributes: [] }
        },
        {
          model: Person,
          as: "cast",
          attributes: [
            "id",
            "first_name",
            "middle_name",
            "last_name",
            "full_name",
            "image"
          ],
          through: { attributes: [] }
        },
      ],
      benchmark: true
    });

    result = result.toJSON();
    // clean up directors and cast attributes
    for (let fname of ["directors", "cast"]) {
      result[fname] = result[fname].map(person => {
        return {
          id: person.id,
          full_name: person.full_name,
          image: person.image
        };
      });
    }

    return JSON.stringify(result);
  }

  async insertMovie(val) {
    let num = Math.floor(Math.random() * 1000000);
    const Movie = this.models.Movie;
    const Directors = this.models.Directors;
    const Cast = this.models.Cast;

    var movie = await Movie.create({
      // using the automatic id sequence from cast as a matter of convenience
      id: App.literal(`nextval('"Cast_id_seq"'::regclass)`),
      title: val.prefix + num,
      image: val.prefix + "image" + num + ".jpeg",
      description: val.prefix + "description" + num,
      year: num,
    });
    // adding directors and cast only seems to be possible as a separate step
    await Directors.create({
      movie_id: movie.id,
      person_id: val.people[0],
    });
    await Cast.bulkCreate(val.people.slice(1).map(x => ({
      movie_id: movie.id,
      person_id: x,
    })));

    // returning is not sufficient to get nested results, so we fetch them
    return await this._getMovieAfterInsert(movie.id);
  }

  async insertMoviePlus(val) {
    let num = Math.floor(Math.random() * 1000000);
    const Movie = this.models.Movie;
    const Person = this.models.Person;
    const Directors = this.models.Directors;
    const Cast = this.models.Cast;

    var people = await Person.bulkCreate([{
        id: App.literal(`nextval('"Cast_id_seq"'::regclass)`),
        first_name: val + "Alice",
        middle_name: "",
        last_name: val + "Director",
        image: val + "image" + num + ".jpeg",
        bio: "",
    }, {
        id: App.literal(`nextval('"Cast_id_seq"'::regclass)`),
        first_name: val + "Billie",
        middle_name: "",
        last_name: val + "Actor",
        image: val + "image" + (num + 1) + ".jpeg",
        bio: "",
    }, {
        id: App.literal(`nextval('"Cast_id_seq"'::regclass)`),
        first_name: val + "Cameron",
        middle_name: "",
        last_name: val + "Actor",
        image: val + "image" + (num + 2) + ".jpeg",
        bio: "",
    }]);

    var movie = await Movie.create({
      // using the automatic id sequence from cast as a matter of convenience
      id: App.literal(`nextval('"Cast_id_seq"'::regclass)`),
      title: val + num,
      image: val + "image" + num + ".jpeg",
      description: val + "description" + num,
      year: num,
    });
    // adding directors and cast only seems to be possible as a separate step
    await Directors.create({
      movie_id: movie.id,
      person_id: people[0].id,
    });
    await Cast.bulkCreate(people.slice(1).map(x => ({
      movie_id: movie.id,
      person_id: x.id,
    })));

    // returning is not sufficient to get nested results, so we fetch them
    return await this._getMovieAfterInsert(movie.id);
  }

  async benchQuery(query, id) {
    if (query == "get_user") {
      return await this.userDetails(id);
    } else if (query == "get_person") {
      return await this.personDetails(id);
    } else if (query == "get_movie") {
      return this.movieDetails(id);
    } else if (query == "update_movie") {
      return this.updateMovie(id);
    } else if (query == "insert_user") {
      return this.insertUser(id);
    } else if (query == "insert_movie") {
      return this.insertMovie(id);
    } else if (query == "insert_movie_plus") {
      return this.insertMoviePlus(id);
    }
  }

  async getIDs() {
    var ids = await Promise.all([
      this.models.User.findAll({ attributes: ["id"] }),
      this.models.Person.findAll({ attributes: ["id"] }),
      this.models.Movie.findAll({ attributes: ["id", "title"] })
    ]);
    var people = ids[1].map(x => x.id);

    return {
      get_user: ids[0].map(x => x.id),
      get_person: people,
      get_movie: ids[2].map(x => x.id),
      // re-use user IDs for update tests
      update_movie: ids[2].map(
        x => ({id: x.id, title: x.title + '---' + x.id})),
      // generate as many insert stubs as "concurrency" to accommodate
      // concurrent inserts, but use 1000 since the actual concurrency
      // parameter is hard to get here
      insert_user: Array(1000).fill('insert_test__'),
      insert_movie: Array(1000).fill({
        prefix: 'insert_test__',
        people: people.slice(0, 4),
      }),
      insert_movie_plus: Array(1000).fill('insert_test__'),
    };
  }

  async setup(query) {
    if (query == "update_movie") {
      // don't care about using proper Sequelize machinery for this
      return await this.query(`
        UPDATE
            "Movie"
        SET
            "title" = split_part("Movie"."title", '---', 1)
        WHERE
            "Movie"."title" LIKE '%---%';
      `);
    } else if (query == "insert_user") {
      return await this.query(`
        DELETE FROM
            "User"
        WHERE
            "User"."name" LIKE 'insert_test__%';
      `);
    } else if (query == 'insert_movie' || query == 'insert_movie_plus') {
      await this.query(`
          DELETE FROM
              "Directors" as D
          USING
              "Movie" as M
          WHERE
              D.movie_id = M.id AND M.image LIKE 'insert_test__%';
      `);
      await this.query(`
          DELETE FROM
              "Cast" as A
          USING
              "Movie" as M
          WHERE
              A.movie_id = M.id AND M.image LIKE 'insert_test__%';
      `);
      await this.query(`
          DELETE FROM
              "Movie" as M
          WHERE
              M.image LIKE 'insert_test__%';
      `);
      return await this.query(`
          DELETE FROM
              "Person" as P
          WHERE
              P.image LIKE 'insert_test__%';
      `);
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
module.exports.App = BenchApp;
