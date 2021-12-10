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

  async benchQuery(query, id) {
    if (query == "get_user") {
      return await this.userDetails(id);
    } else if (query == "get_person") {
      return await this.personDetails(id);
    } else if (query == "get_movie") {
      return this.movieDetails(id);
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

  async benchQuery(query, id) {
    if (query == "get_user") {
      return await this.userDetails(id);
    } else if (query == "get_person") {
      return await this.personDetails(id);
    } else if (query == "get_movie") {
      return this.movieDetails(id);
    }
  }
}
module.exports.ConnectionRepack = ConnectionRepack;

class App {
  constructor({ host = "localhost", port = 5656, pool = 1, style = "json" }) {
    this.conn = null;

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
      get_movie: ids.movies
    };
  }

  getConnection(i) {
    return this.conn;
  }
}
module.exports.App = App;
