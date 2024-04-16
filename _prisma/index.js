'use strict';

const {PrismaClient} = require('@prisma/client');

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
    const result = await this.$transaction(async (prisma) => {
      let result = await prisma.users.findUnique({
        where: {
          id: id,
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

      let avgRatings = await prisma.reviews.groupBy({
        by: ['movie_id'],
        where: {
          movie_id: {
            in: result.reviews.map((r) => r.movie.id),
          },
        },
        _avg: {
          rating: true,
        },
      });

      let avgRatingsMap = {};

      for (let m of avgRatings) {
        avgRatingsMap[m.movie_id] = m._avg.rating;
      }

      for (let r of result.reviews) {
        r.movie.avg_rating = avgRatingsMap[r.movie.id];
      }
      result.latest_reviews = result.reviews;
      delete result.reviews;
      return result;
    });

    return JSON.stringify(result);
  }

  async personDetails(id) {
    const result = await this.$transaction(async (prisma) => {
      let result = await prisma.persons.findUnique({
        where: {
          id: id,
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
                },
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
                },
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

      let avgRatings = await prisma.reviews.groupBy({
        by: ['movie_id'],
        where: {
          movie_id: {
            in: movieIds,
          },
        },
        _avg: {
          rating: true,
        },
      });

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

      return result;
    });

    return JSON.stringify(result);
  }

  async movieDetails(id) {
    const result = await this.$transaction([
      this.movies.findUnique({
        where: {
          id: id,
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
                },
              },
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
                },
              },
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
      }),

      this.reviews.aggregate({
        _avg: {
          rating: true,
        },
        where: {
          movie: {
            id: id,
          },
        },
      }),
    ]);

    result[0].avg_rating = result[1]._avg.rating;
    // move the "person" object one level closer to "directors" and
    // "cast"
    for (let fname of ['directors', 'cast']) {
      result[0][fname] = result[0][fname].map((rel) => {
        return {
          id: rel.person.id,
          full_name: get_full_name(rel.person),
          image: rel.person.image,
        };
      });
    }

    return JSON.stringify(result[0]);
  }

  async updateMovie(val) {
    let result = await this.movies.update({
      where: {
        id: val.id,
      },
      data: {
        title: val.title,
      },
      select: {
        id: true,
        title: true,
      },
    });

    return JSON.stringify(result);
  }

  async insertUser(val) {
    let num = Math.floor(Math.random() * 1000000);
    let result = await this.users.create({
      data: {
        name: val + num,
        image: val + 'image' + num,
      },
      select: {
        id: true,
        name: true,
        image: true,
      },
    });

    return JSON.stringify(result);
  }

  async insertMovie(val) {
    let num = Math.floor(Math.random() * 1000000);
    let movie = await this.movies.create({
      data: {
        title: val.prefix + num,
        image: val.prefix + 'image' + num + '.jpeg',
        description: val.prefix + 'description' + num,
        year: num,

        directors: {
          create: {person_id: val.people[0]},
        },
        cast: {
          createMany: {
            data: val.people.slice(1).map((x) => ({
              person_id: x,
            })),
          },
        },
      },
      select: {
        id: true,
        title: true,
        image: true,
        description: true,
        year: true,

        directors: {
          select: {
            person: {
              select: {
                id: true,
                first_name: true,
                middle_name: true,
                last_name: true,
                image: true,
              },
            },
          },
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
              },
            },
          },
        },
      },
    });

    // move the "person" object one level closer to "directors" and
    // "cast"
    for (let fname of ['directors', 'cast']) {
      movie[fname] = movie[fname].map((rel) => {
        return {
          id: rel.person.id,
          full_name: get_full_name(rel.person),
          image: rel.person.image,
        };
      });
    }

    return JSON.stringify(movie);
  }

  async insertMoviePlus(val) {
    let num = Math.floor(Math.random() * 1000000);
    let data = [
      {
        first_name: val + 'Alice',
        middle_name: '',
        last_name: val + 'Director',
        image: val + 'image' + num + '.jpeg',
        bio: '',
      },
      {
        first_name: val + 'Billie',
        middle_name: '',
        last_name: val + 'Actor',
        image: val + 'image' + (num + 1) + '.jpeg',
        bio: '',
      },
      {
        first_name: val + 'Cameron',
        middle_name: '',
        last_name: val + 'Actor',
        image: val + 'image' + (num + 2) + '.jpeg',
        bio: '',
      },
    ];

    const movie = await this.$transaction(async (prisma) => {
      let people = [];

      for (let p of data) {
        people.push(
          await prisma.persons.create({
            data: p,
            select: {
              id: true,
              first_name: true,
              middle_name: true,
              last_name: true,
              image: true,
            },
          })
        );
      }

      let movie = await prisma.movies.create({
        data: {
          title: val + num,
          image: val + 'image' + num + '.jpeg',
          description: val + 'description' + num,
          year: num,

          directors: {
            create: {person_id: people[0].id},
          },
          cast: {
            createMany: {
              data: people.slice(1).map((x) => ({
                person_id: x.id,
              })),
            },
          },
        },
        select: {
          id: true,
          title: true,
          image: true,
          description: true,
          year: true,

          directors: {
            select: {
              person: {
                select: {
                  id: true,
                  first_name: true,
                  middle_name: true,
                  last_name: true,
                  image: true,
                },
              },
            },
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
                },
              },
            },
          },
        },
      });

      // move the "person" object one level closer to "directors" and
      // "cast"
      for (let fname of ['directors', 'cast']) {
        movie[fname] = movie[fname].map((rel) => {
          return {
            id: rel.person.id,
            full_name: get_full_name(rel.person),
            image: rel.person.image,
          };
        });
      }

      return movie;
    });

    return JSON.stringify(movie);
  }

  async benchQuery(query, id) {
    if (query == 'get_user') {
      return await this.userDetails(id);
    } else if (query == 'get_person') {
      return await this.personDetails(id);
    } else if (query == 'get_movie') {
      return await this.movieDetails(id);
    } else if (query == 'update_movie') {
      return await this.updateMovie(id);
    } else if (query == 'insert_user') {
      return await this.insertUser(id);
    } else if (query == 'insert_movie') {
      return await this.insertMovie(id);
    } else if (query == 'insert_movie_plus') {
      return await this.insertMoviePlus(id);
    }
  }

  async getIDs(number_of_ids) {
    var ids;
    if (process.env.IMDBENCH_MYSQL) {
      ids = await Promise.all([
        this.$queryRaw`SELECT id
                       FROM users
                       ORDER BY RAND() LIMIT ${number_of_ids}`,
        this.$queryRaw`SELECT id
                       FROM persons
                       ORDER BY RAND() LIMIT ${number_of_ids}`,
        this.$queryRaw`SELECT id
                       FROM movies
                       ORDER BY RAND() LIMIT ${number_of_ids}`,
      ]);
    } else {
      ids = await Promise.all([
        this.users.findMany({select: {id: true}}),
        this.persons.findMany({select: {id: true}}),
        this.movies.findMany({select: {id: true, title: true}}),
      ]);
    }
    var people = ids[1].map((x) => x.id);

    return {
      get_user: ids[0].map((x) => x.id),
      get_person: people,
      get_movie: ids[2].map((x) => x.id),
      // re-use user IDs for update tests
      update_movie: ids[2].map((x) => ({
        id: x.id,
        title: x.title + '---' + x.id,
      })),
      // generate a bunch of insert stubs to accommodate concurrent
      // inserts
      insert_user: Array(1000).fill('insert_test__'),
      insert_movie: Array(1000).fill({
        prefix: 'insert_test__',
        people: people.slice(0, 4),
      }),
      insert_movie_plus: Array(1000).fill('insert_test__'),
    };
  }

  async setup(query) {
    if (query == 'update_movie') {
      // don't care about using proper Sequelize machinery for this
      return await this.$executeRaw`
        UPDATE
            movies
        SET
            title = split_part(movies.title, '---', 1)
        WHERE
            movies.title LIKE '%---%';
      `;
    } else if (query == 'insert_user') {
      return await this.$executeRaw`
        DELETE FROM
            users
        WHERE
            users.name LIKE 'insert_test__%';
      `;
    } else if (query == 'insert_movie' || query == 'insert_movie_plus') {
      await this.$executeRaw`
          DELETE D FROM
              directors as D
          JOIN
              movies as M
          ON
              D.movie_id = M.id
          WHERE
              M.image LIKE 'insert_test__%';
      `;
      await this.$executeRaw`
          DELETE A FROM
              actors as A
          JOIN
              movies as M
          ON
              A.movie_id = M.id
          WHERE
              M.image LIKE 'insert_test__%';
      `;
      await this.$executeRaw`
          DELETE FROM
              movies as M
          WHERE
              M.image LIKE 'insert_test__%';
      `;
      return await this.$executeRaw`
          DELETE FROM
              persons as P
          WHERE
              P.image LIKE 'insert_test__%';
      `;
    }
  }

  async cleanup(query) {
    if (
      [
        'update_movie',
        'insert_user',
        'insert_movie',
        'insert_movie_plus',
      ].indexOf(query) >= 0
    ) {
      // The clean up is the same as setup for mutation benchmarks
      return await this.setup(query);
    }
  }

  getConnection(i) {
    return this;
  }
}

class TunedApp extends App {
  async userDetails(id) {
    let result = await this.users.findUnique({
      where: {
        id: id,
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
        id: id,
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
              },
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
              },
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

    for (let fname of ['acted_in', 'directed']) {
      for (let r of result[fname]) {
        r.movie.avg_rating = get_avg_rating(r.movie);
        delete r.movie.reviews;
      }
      // clean up
      result[fname] = result[fname].map((rel) => {
        return rel.movie;
      });
    }

    return JSON.stringify(result);
  }

  // movieDetails don't benefit from computations in the client code
}

module.exports.App = App;
module.exports.TunedApp = TunedApp;
