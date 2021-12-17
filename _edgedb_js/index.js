"use strict";

const edgedb = require("edgedb");
const queries = require("./queries");

class ConnectionJSON {
  constructor(opts) {
    this.client = edgedb.createClient({
      dsn: "edgedb_bench",
      concurrency: opts.pool,
    });
  }

  async connect() {
    await this.client.ensureConnected();
  }

  async userDetails(id) {
    return await this.client.querySingleJSON(queries.user, { id: id });
  }

  async personDetails(id) {
    return await this.client.querySingleJSON(queries.person, { id: id });
  }

  async movieDetails(id) {
    return await this.client.querySingleJSON(queries.movie, { id: id });
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
    }
  }
}
module.exports.ConnectionJSON = ConnectionJSON;

class ConnectionRepack {
  constructor(opts) {
    this.client = edgedb.createClient({
      dsn: "edgedb_bench",
      concurrency: opts.pool,
    });
  }

  async connect() {
    await this.client.ensureConnected();
  }

  async userDetails(id) {
    return JSON.stringify(
      await this.client.querySingle(queries.user, { id: id })
    );
  }

  async personDetails(id) {
    return JSON.stringify(
      await this.client.querySingle(queries.person, { id: id })
    );
  }

  async movieDetails(id) {
    return JSON.stringify(
      await this.client.querySingle(queries.movie, { id: id })
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
        image: 'image_' + id + num,
      })
    );
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
    }
  }
}
module.exports.ConnectionRepack = ConnectionRepack;

class App {
  constructor({ host = "localhost", port = 5656, pool = 1, style = "json" }) {
    this.conn = null;
    this.concurrency = pool;
    this.INSERT_PREFIX = 'insert_test__'

    let Connection;
    if (style === "json") {
      Connection = ConnectionJSON;
    } else if (style === "repack") {
      Connection = ConnectionRepack;
    } else {
      throw new Error(
        "unrecognized 'style': valid values are 'json' and 'repack'"
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
    }
  }

  async setup(query) {
    if (query == "update_movie") {
      return await this.conn.client.execute(`
        update Movie
        filter contains(.title, '---')
        set {
            title := str_split(.title, '---')[0]
        };
      `);
    } else if (query == "insert_user") {
      return await this.conn.client.query(`
        delete User
        filter .name LIKE <str>$0;
      `, [this.INSERT_PREFIX + '%']);
    }
  }

  async cleanup(query) {
    if (query == "update_movie" || query == "insert_user") {
      // The clean up is the same as setup for mutation benchmarks
      return await this.setup(query);
    }
  }

  getConnection(i) {
    return this.conn;
  }
}
module.exports.App = App;
