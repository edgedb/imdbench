"use strict";

var loopback = require("loopback");
var boot = require("loopback-boot");

var app = (module.exports = loopback());

app.boot = async function(options) {
  options = {
    appRootDir: __dirname,
    dataSources: {
      psqlDs: {
        host: "localhost",
        port: 5432,
        url: "",
        database: "lb_bench",
        password: "edgedbbenchmark",
        name: "psqlDs",
        user: "lb_bench",
        connector: "postgresql",
        min: 1,
        max: 1,
        ...(options || {})
      }
    }
  };
  await boot(this, options);
};

app.benchQuery = async function(query, id) {
  var method;

  if (query == "get_user") {
    method = this.models.User.userDetails;
  } else if (query == "get_person") {
    method = this.models.Person.personDetails;
  } else if (query == "get_movie") {
    method = this.models.Movie.movieDetails;
  }

  return await method(id);
};

app.getIDs = async function() {
  var ids = await Promise.all([
    this.models.User.find({ fields: { id: true } }),
    this.models.Person.find({ fields: { id: true } }),
    this.models.Movie.find({ fields: { id: true } })
  ]);

  return {
    get_user: ids[0].map(x => x.id),
    get_person: ids[1].map(x => x.id),
    get_movie: ids[2].map(x => x.id)
  };
};

app.getConnection = function(i) {
  return this;
};
