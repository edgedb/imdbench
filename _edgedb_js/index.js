'use strict';

const edgedb = require('edgedb');
const queries = require('./queries');
const qbQueries = require('./qb_queries');

const qbQueryUser = qbQueries.user();
const qbQueryPerson = qbQueries.person();
const qbQueryMovie = qbQueries.movie();
const qbUpdateMovie = qbQueries.updateMovie();
const qbInsertUser = qbQueries.insertUser();
const qbInsertMovie = qbQueries.insertMovie();
const qbInsertMoviePlus = qbQueries.insertMoviePlus();

class _BaseConnection {
  constructor(opts) {
    this.client = edgedb
      .createClient({concurrency: opts.pool})
      .withRetryOptions({attempts: 10});
  }

  async connect() {
    await this.client.ensureConnected();
  }

  async benchQuery(query, id) {
    if (query == 'get_user') {
      return this.userDetails(id);
    } else if (query == 'get_person') {
      return this.personDetails(id);
    } else if (query == 'get_movie') {
      return this.movieDetails(id);
    } else if (query == 'update_movie') {
      return this.updateMovie(id);
    } else if (query == 'insert_user') {
      return this.insertUser(id);
    } else if (query == 'insert_movie') {
      return this.insertMovie(id);
    } else if (query == 'insert_movie_plus') {
      return this.insertMoviePlus(id);
    }
  }
}

class ConnectionJSON extends _BaseConnection {
  async userDetails(id) {
    return await this.client.querySingleJSON(queries.user, {id: id});
  }

  async personDetails(id) {
    return await this.client.querySingleJSON(queries.person, {id: id});
  }

  async movieDetails(id) {
    return await this.client.querySingleJSON(queries.movie, {id: id});
  }

  async updateMovie(id) {
    return await this.client.querySingleJSON(queries.updateMovie, {
      id: id,
      suffix: id.slice(0, 8),
    });
  }

  async insertUser(id) {
    let num = Math.floor(Math.random() * 1000000);
    return await this.client.querySingleJSON(queries.insertUser, {
      name: id + num,
      image: 'image_' + id + num,
    });
  }

  async insertMovie(val) {
    let num = Math.floor(Math.random() * 1000000);
    return await this.client.querySingleJSON(queries.insertMovie, {
      title: val.prefix + num,
      image: val.prefix + 'image' + num + '.jpeg',
      description: val.prefix + 'description' + num,
      year: num,
      d_id: val.people[0],
      cast: val.people.slice(1, 3),
    });
  }

  async insertMoviePlus(val) {
    let num = Math.floor(Math.random() * 1000000);
    return await this.client.querySingleJSON(queries.insertMoviePlus, {
      title: val + num,
      image: val + 'image' + num + '.jpeg',
      description: val + 'description' + num,
      year: num,
      dfn: val + 'Alice',
      dln: val + 'Director',
      dimg: val + 'image' + num + '.jpeg',
      cfn0: val + 'Billie',
      cln0: val + 'Actor',
      cimg0: val + 'image' + (num + 1) + '.jpeg',
      cfn1: val + 'Cameron',
      cln1: val + 'Actor',
      cimg1: val + 'image' + (num + 2) + '.jpeg',
    });
  }
}
module.exports.ConnectionJSON = ConnectionJSON;

class ConnectionRepack extends _BaseConnection {
  async userDetails(id) {
    return JSON.stringify(
      await this.client.querySingle(queries.user, {id: id})
    );
  }

  async personDetails(id) {
    return JSON.stringify(
      await this.client.querySingle(queries.person, {id: id})
    );
  }

  async movieDetails(id) {
    return JSON.stringify(
      await this.client.querySingle(queries.movie, {id: id})
    );
  }

  async updateMovie(id) {
    return JSON.stringify(
      await this.client.querySingle(queries.updateMovie, {
        id: id,
        suffix: id.slice(0, 8),
      })
    );
  }

  async insertUser(id) {
    let num = Math.floor(Math.random() * 1000000);
    return JSON.stringify(
      await this.client.querySingle(queries.insertUser, {
        name: id + num,
        image: id + 'image' + num,
      })
    );
  }

  async insertMovie(val) {
    let num = Math.floor(Math.random() * 1000000);
    return JSON.stringify(
      await this.client.querySingle(queries.insertMovie, {
        title: val.prefix + num,
        image: val.prefix + 'image' + num + '.jpeg',
        description: val.prefix + 'description' + num,
        year: num,
        d_id: val.people[0],
        cast: val.people.slice(1, 3),
      })
    );
  }

  async insertMoviePlus(val) {
    let num = Math.floor(Math.random() * 1000000);
    return JSON.stringify(
      await this.client.querySingle(queries.insertMoviePlus, {
        title: val + num,
        image: val + 'image' + num + '.jpeg',
        description: val + 'description' + num,
        year: num,
        dfn: val + 'Alice',
        dln: val + 'Director',
        dimg: val + 'image' + num + '.jpeg',
        cfn0: val + 'Billie',
        cln0: val + 'Actor',
        cimg0: val + 'image' + (num + 1) + '.jpeg',
        cfn1: val + 'Cameron',
        cln1: val + 'Actor',
        cimg1: val + 'image' + (num + 2) + '.jpeg',
      })
    );
  }
}
module.exports.ConnectionRepack = ConnectionRepack;

class ConnectionQB extends _BaseConnection {
  async userDetails(id) {
    return JSON.stringify(await qbQueryUser.run(this.client, {id}));
  }

  async personDetails(id) {
    return JSON.stringify(await qbQueryPerson.run(this.client, {id}));
  }

  async movieDetails(id) {
    return JSON.stringify(await qbQueryMovie.run(this.client, {id}));
  }

  async updateMovie(id) {
    return JSON.stringify(
      await qbUpdateMovie.run(this.client, {
        id: id,
        suffix: id.slice(0, 8),
      })
    );
  }

  async insertUser(id) {
    let num = Math.floor(Math.random() * 1000000);
    return JSON.stringify(
      await qbInsertUser.run(this.client, {
        name: id + num,
        image: 'image_' + id + num,
      })
    );
  }

  async insertMovie(val) {
    let num = Math.floor(Math.random() * 1000000);
    return JSON.stringify(
      await qbInsertMovie.run(this.client, {
        title: val.prefix + num,
        image: val.prefix + 'image' + num + '.jpeg',
        description: val.prefix + 'description' + num,
        year: num,
        d_id: val.people[0],
        cast: val.people.slice(1, 3),
      })
    );
  }

  async insertMoviePlus(val) {
    let num = Math.floor(Math.random() * 1000000);
    return JSON.stringify(
      await qbInsertMoviePlus.run(this.client, {
        title: val + num,
        image: val + 'image' + num + '.jpeg',
        description: val + 'description' + num,
        year: num,
        dfn: val + 'Alice',
        dln: val + 'Director',
        dimg: val + 'image' + num + '.jpeg',
        cfn0: val + 'Billie',
        cln0: val + 'Actor',
        cimg0: val + 'image' + (num + 1) + '.jpeg',
        cfn1: val + 'Cameron',
        cln1: val + 'Actor',
        cimg1: val + 'image' + (num + 2) + '.jpeg',
      })
    );
  }
}
module.exports.ConnectionQB = ConnectionQB;

class ConnectionQBUncached extends _BaseConnection {
  async userDetails(id) {
    return JSON.stringify(await qbQueries.user().run(this.client, {id}));
  }

  async personDetails(id) {
    return JSON.stringify(await qbQueries.person().run(this.client, {id}));
  }

  async movieDetails(id) {
    return JSON.stringify(await qbQueries.movie().run(this.client, {id}));
  }

  async updateMovie(id) {
    return JSON.stringify(
      await qbQueries.updateMovie().run(this.client, {
        id: id,
        suffix: id.slice(0, 8),
      })
    );
  }

  async insertUser(id) {
    let num = Math.floor(Math.random() * 1000000);
    return JSON.stringify(
      await qbQueries.insertUser().run(this.client, {
        name: id + num,
        image: 'image_' + id + num,
      })
    );
  }

  async insertMovie(val) {
    let num = Math.floor(Math.random() * 1000000);
    return JSON.stringify(
      await qbQueries.insertMovie().run(this.client, {
        title: val.prefix + num,
        image: val.prefix + 'image' + num + '.jpeg',
        description: val.prefix + 'description' + num,
        year: num,
        d_id: val.people[0],
        cast: val.people.slice(1, 3),
      })
    );
  }

  async insertMoviePlus(val) {
    let num = Math.floor(Math.random() * 1000000);
    return JSON.stringify(
      await qbQueries.insertMoviePlus().run(this.client, {
        title: val + num,
        image: val + 'image' + num + '.jpeg',
        description: val + 'description' + num,
        year: num,
        dfn: val + 'Alice',
        dln: val + 'Director',
        dimg: val + 'image' + num + '.jpeg',
        cfn0: val + 'Billie',
        cln0: val + 'Actor',
        cimg0: val + 'image' + (num + 1) + '.jpeg',
        cfn1: val + 'Cameron',
        cln1: val + 'Actor',
        cimg1: val + 'image' + (num + 2) + '.jpeg',
      })
    );
  }
}
module.exports.ConnectionQBUncached = ConnectionQBUncached;

class App {
  constructor({pool = 1, style = 'json'}) {
    this.conn = null;
    this.concurrency = pool;
    this.INSERT_PREFIX = 'insert_test__';

    let Connection;
    if (style === 'json') {
      Connection = ConnectionJSON;
    } else if (style === 'repack') {
      Connection = ConnectionRepack;
    } else if (style === 'querybuilder') {
      Connection = ConnectionQB;
    } else if (style === 'querybuilder_uncached') {
      Connection = ConnectionQBUncached;
    } else {
      throw new Error(
        "unrecognized 'style': valid values are 'json', 'repack', " +
          "'querybuilder' and 'querybuilder_uncached'"
      );
    }

    this.conn = new Connection({pool: pool});
  }

  async initPool() {
    await this.conn.connect();
  }

  async getIDs() {
    var ids = await this.conn.client.querySingle(`
      WITH
          U := User {id, r := random()},
          M := Movie {id, r := random()},
          P := Person {id, r := random()}
      SELECT (
          users := array_agg((SELECT U ORDER BY U.r).id),
          movies := array_agg((SELECT M ORDER BY M.r).id),
          people := array_agg((SELECT P ORDER BY P.r).id),
      );
    `);

    return {
      get_user: ids.users,
      get_person: ids.people,
      get_movie: ids.movies,
      // re-use user IDs for update tests
      update_movie: [...ids.movies],
      // generate as many insert stubs as "concurrency" to
      // accommodate concurrent inserts
      insert_user: Array(this.concurrency).fill(this.INSERT_PREFIX),
      insert_movie: Array(this.concurrency).fill({
        prefix: this.INSERT_PREFIX,
        people: ids.people.slice(0, 4),
      }),
      insert_movie_plus: Array(this.concurrency).fill(this.INSERT_PREFIX),
    };
  }

  async setup(query) {
    if (query == 'update_movie') {
      return await this.conn.client.execute(`
        update Movie
        filter contains(.title, '---')
        set {
            title := str_split(.title, '---')[0]
        };
      `);
    } else if (query == 'insert_user') {
      return await this.conn.client.query(
        `
        delete User
        filter .name LIKE <str>$0;
      `,
        [this.INSERT_PREFIX + 'image%']
      );
    } else if (query == 'insert_movie') {
      return await this.conn.client.query(
        `
        delete Movie
        filter .image LIKE <str>$0;
      `,
        [this.INSERT_PREFIX + 'image%']
      );
    } else if (query == 'insert_movie_plus') {
      await this.conn.client.query(
        `
        delete Movie
        filter .image LIKE <str>$0;
      `,
        [this.INSERT_PREFIX + 'image%']
      );
      return await this.conn.client.query(
        `
        delete Person
        filter .image LIKE <str>$0;
      `,
        [this.INSERT_PREFIX + 'image%']
      );
    }
  }

  async cleanup(query) {
    if (
      [
        'update_movie',
        'insert_user',
        'insert_movie',
        'insert_movie_plus',
      ].includes(query)
    ) {
      // The clean up is the same as setup for mutation benchmarks
      return await this.setup(query);
    }
  }

  getConnection(i) {
    return this.conn;
  }
}
module.exports.App = App;
