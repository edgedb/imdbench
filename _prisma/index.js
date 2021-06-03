"use strict";

const { PrismaClient } = require('@prisma/client')


function get_full_name(person) {
  let fn;
  if (!person.middle_name) {
    fn = `${person.first_name} ${person.last_name}`;
  } else {
    fn = `${person.first_name} ${person.middle_name} ${person.last_name}`;
  }

  return fn;
}


function get_avg_rating(movie) {
  return (
    movie.reviews.reduce((total, r) => total + r.rating, 0) /
    movie.reviews.length
  );
}


class App extends PrismaClient {
  async userDetails(id) {
    let result = await this.users.findUnique({
      where: {
        id: id
      },
      select: {
        id: true,
        name: true,
        image: true,
        reviews: {
          take: 10,
          orderBy: {
            creation_time: 'desc',
          },
          select: {
            id: true,
            body: true,
            rating: true,
            movie: {
              select: {
                id: true,
                image: true,
                title: true,
              },
            },
          },
        },
      },
    });

    let avgRatings = await this.reviews.groupBy({
      by: ['movie_id'],
      where: {
        movie_id: {
          in: result.reviews.map((r) => r.movie.id),
        },
      },
      _avg: {
        rating: true,
      }
    })

    let avgRatingsMap = {};

    for (let m of avgRatings) {
      avgRatingsMap[m.movie_id] = m._avg.rating;
    }

    for (let r of result.reviews) {
      r.movie.avg_rating = avgRatingsMap[r.movie.id];
    }
    result.latest_reviews = result.reviews;
    delete result.reviews;

    return JSON.stringify(result);
  }

  async personDetails(id) {
    let result = await this.persons.findUnique({
      where: {
        id: id
      },
      select: {
        id: true,
        first_name: true,
        middle_name: true,
        last_name: true,
        image: true,
        bio: true,
        acted_in: {
          select: {
            movie: {
              select: {
                id: true,
                image: true,
                title: true,
                year: true,
              }
            },
          },
          orderBy: [
            {
              movie: {
                year: 'asc',
              },
            },
            {
              movie: {
                title: 'asc',
              },
            },
          ],
        },
        directed: {
          select: {
            movie: {
              select: {
                id: true,
                image: true,
                title: true,
                year: true,
              }
            },
          },
          orderBy: [
            {
              movie: {
                year: 'asc',
              },
            },
            {
              movie: {
                title: 'asc',
              },
            },
          ],
        },
      },
    });

    // move the "movie" object one level closer to "acted_in" and
    // "directed"
    result.acted_in = result.acted_in.map((m) => m.movie);
    result.directed = result.directed.map((m) => m.movie);

    let movieIds = result.acted_in.map((m) => m.id);
    movieIds.concat(result.directed.map((m) => m.id));

    let avgRatings = await this.reviews.groupBy({
      by: ['movie_id'],
      where: {
        movie_id: {
          in: movieIds,
        },
      },
      _avg: {
        rating: true,
      }
    })

    let avgRatingsMap = {};

    for (let m of avgRatings) {
      avgRatingsMap[m.movie_id] = m._avg.rating;
    }

    for (let m of result.acted_in) {
      m.avg_rating = avgRatingsMap[m.id];
    }
    for (let m of result.directed) {
      m.avg_rating = avgRatingsMap[m.id];
    }

    result.full_name = get_full_name(result);
    delete result.first_name;
    delete result.middle_name;
    delete result.last_name;

    return JSON.stringify(result);
  }

  async movieDetails(id) {
    let movie = this.movies.findUnique({
      where: {
        id: id
      },
      select: {
        id: true,
        image: true,
        title: true,
        year: true,
        description: true,

        directors: {
          select: {
            person: {
              select: {
                id: true,
                first_name: true,
                middle_name: true,
                last_name: true,
                image: true,
              }
            }
          },
          orderBy: [
            {
              list_order: 'asc',
            },
            {
              person: {
                last_name: 'asc',
              },
            },
          ],
        },
        cast: {
          select: {
            person: {
              select: {
                id: true,
                first_name: true,
                middle_name: true,
                last_name: true,
                image: true,
              }
            }
          },
          orderBy: [
            {
              list_order: 'asc',
            },
            {
              person: {
                last_name: 'asc',
              },
            },
          ],
        },

        reviews: {
          orderBy: {
            creation_time: 'desc',
          },
          select: {
            id: true,
            body: true,
            rating: true,
            author: {
              select: {
                id: true,
                name: true,
                image: true,
              },
            },
          },
        },
      },
    });

    let avgRating = this.reviews.aggregate({
      _avg: {
        rating: true,
      },
      where: {
        movie: {
          id: id,
        },
      },
    })

    let result = await Promise.all([
      movie,
      avgRating,
    ])

    result[0].avg_rating = result[1]._avg.rating
    // move the "person" object one level closer to "directors" and
    // "cast"
    for (let fname of ["directors", "cast"]) {
      result[0][fname] = result[0][fname].map(rel => {
        return {
          id: rel.person.id,
          full_name: get_full_name(rel.person),
          image: rel.person.image
        };
      });
    }

    return JSON.stringify(result[0]);
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
      this.users.findMany({select: {id: true}}),
      this.persons.findMany({select: {id: true}}),
      this.movies.findMany({select: {id: true}}),
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


class TunedApp extends App {
  async userDetails(id) {
    let result = await this.users.findUnique({
      where: {
        id: id
      },
      select: {
        id: true,
        name: true,
        image: true,
        reviews: {
          take: 10,
          orderBy: {
            creation_time: 'desc',
          },
          select: {
            id: true,
            body: true,
            rating: true,
            movie: {
              select: {
                id: true,
                image: true,
                title: true,
                reviews: {
                  select: {
                    rating: true,
                  },
                },
              },
            },
          },
        },
      },
    });

    for (let r of result.reviews) {
      r.movie.avg_rating = get_avg_rating(r.movie);
      delete r.movie.reviews;
    }
    result.latest_reviews = result.reviews;
    delete result.reviews;

    return JSON.stringify(result);
  }

  async personDetails(id) {
    let result = await this.persons.findUnique({
      where: {
        id: id
      },
      select: {
        id: true,
        first_name: true,
        middle_name: true,
        last_name: true,
        image: true,
        bio: true,
        acted_in: {
          select: {
            movie: {
              select: {
                id: true,
                image: true,
                title: true,
                year: true,
                reviews: {
                  select: {
                    rating: true,
                  },
                },
              }
            },
          },
          orderBy: [
            {
              movie: {
                year: 'asc',
              },
            },
            {
              movie: {
                title: 'asc',
              },
            },
          ],
        },
        directed: {
          select: {
            movie: {
              select: {
                id: true,
                image: true,
                title: true,
                year: true,
                reviews: {
                  select: {
                    rating: true,
                  },
                },
              }
            },
          },
          orderBy: [
            {
              movie: {
                year: 'asc',
              },
            },
            {
              movie: {
                title: 'asc',
              },
            },
          ],
        },
      },
    });

    result.full_name = get_full_name(result);
    delete result.first_name;
    delete result.middle_name;
    delete result.last_name;

    for (let fname of ["acted_in", "directed"]) {
      for (let r of result[fname]) {
        r.movie.avg_rating = get_avg_rating(r.movie);
        delete r.movie.reviews;
      }
      // clean up
      result[fname] = result[fname].map(rel => {
        return rel.movie;
      });
    }

    return JSON.stringify(result);
  }

  // movieDetails don't benefit from computations in the client code
}



module.exports.App = App;
module.exports.TunedApp = TunedApp;
