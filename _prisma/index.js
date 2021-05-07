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
      // sort by year and title
      result[fname].sort((a, b) => {
        if (a.year < b.year) {
          return -1;
        } else if (a.year > b.year) {
          return 1;
        } else if (a.title < b.title) {
          return -1;
        } else if (a.title > b.title) {
          return 1;
        } else {
          return 0;
        }
      });
    }

    return JSON.stringify(result);
  }

  async movieDetails(id) {
    let result = await this.movies.findUnique({
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
            list_order: true,
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
        },
        cast: {
          select: {
            list_order: true,
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

    result.avg_rating = get_avg_rating(result);

    for (let fname of ["directors", "cast"]) {
      // sort by list_order and last_name
      result[fname].sort((a, b) => {
        if (a.list_order < b.list_order) {
          return -1;
        } else if (a.list_order > b.list_order) {
          return 1;
        } else if (a.person.last_name < b.person.last_name) {
          return -1;
        } else if (a.person.last_name > b.person.last_name) {
          return 1;
        } else {
          return 0;
        }
      });
      // clean up
      result[fname] = result[fname].map(rel => {
        return {
          id: rel.person.id,
          full_name: get_full_name(rel.person),
          image: rel.person.image
        };
      });
    }

    return JSON.stringify(result);
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


module.exports.App = App;
