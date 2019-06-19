"use strict";

const { App } = require("./models.js");
const logging = false;

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
      logging: logging,
      benchmark: true
    });

    return result;
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
      logging: logging,
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

    return result;
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
      logging: logging,
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

    return result;
  }

  async benchQuery(query, id) {
    if (query == "get_user") {
      return await this.userDetails(id);
    } else if (query == "get_person") {
      return await this.personDetails(id);
    } else if (query == "get_movie") {
      return this.movieDetails(id);
    }
  }

  async getIDs() {
    var ids = await Promise.all([
      this.models.User.findAll({ attributes: ["id"] }),
      this.models.Person.findAll({ attributes: ["id"] }),
      this.models.Movie.findAll({ attributes: ["id"] })
    ]);

    return {
      get_user: ids[0].map(x => x.id),
      get_person: ids[1].map(x => x.id),
      get_movie: ids[2].map(x => x.id)
    };
  }

  getConnection(i) {
    return this;
  }
}
module.exports.App = BenchApp;
