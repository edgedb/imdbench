"use strict";

const connect = require("edgedb").default;
const queries = require("./queries");

class ConnectionJSON {
  constructor(opts) {
    this.connection = connect({
      host: "localhost",
      port: 5656,
      user: "edgedb",
      database: "edgedb_bench",
      ...(opts || {})
    });
  }

  async connect() {
    if (this.connection instanceof Promise) {
      this.connection = await this.connection;
    }
  }

  async userDetails(id) {
    return await this.connection.fetchOneJSON(queries.user, { id: id });
  }

  async personDetails(id) {
    return await this.connection.fetchOneJSON(queries.person, { id: id });
  }

  async movieDetails(id) {
    return await this.connection.fetchOneJSON(queries.movie, { id: id });
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
    this.connection = connect({
      host: "localhost",
      port: 5656,
      user: "edgedb",
      database: "edgedb_bench",
      ...(opts || {})
    });
  }

  async connect() {
    if (this.connection instanceof Promise) {
      this.connection = await this.connection;
    }
  }

  async userDetails(id) {
    return JSON.stringify(
      await this.connection.fetchOne(queries.user, { id: id })
    );
  }

  async personDetails(id) {
    return JSON.stringify(
      await this.connection.fetchOne(queries.person, { id: id })
    );
  }

  async movieDetails(id) {
    return JSON.stringify(
      await this.connection.fetchOne(queries.movie, { id: id })
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
    this.pool = [];

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

    for (let i = 0; i < pool; i++) {
      this.pool.push(
        new Connection({
          host: host,
          port: port,
          username: "edgedb",
          database: "edgedb_bench"
        })
      );
    }
  }

  async initPool() {
    await Promise.all(
      this.pool.map(C => {
        return C.connect();
      })
    );
  }

  async getIDs() {
    var ids = await this.pool[0].connection.fetchOne(`
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
    return this.pool[i];
  }
}
module.exports.App = App;
