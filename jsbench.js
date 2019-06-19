#!/usr/bin/env node
//
// Copyright (c) 2019 MagicStack Inc.
// All rights reserved.
//
// See LICENSE for details.
//

"use strict";

const argparse = require("argparse");
const _ = require("lodash");
const process = require("process");
const loopbackapp = require("./_loopback/server/bench");
const typeormapp = require("./_typeorm/build/index");
const sequelizeapp = require("./_sequelize/index");
const pgapp = require("./_postgres/index");

async function getApp(args) {
  var app;
  var ncon = args.concurrency;

  if (args.orm == "loopback") {
    app = loopbackapp;
    await app.boot({
      host: args.host,
      port: args.port,
      min: ncon,
      max: ncon
    });
  } else if (args.orm == "typeorm") {
    app = new typeormapp.App({
      host: args.host,
      port: args.port,
      extra: { max: ncon }
    });
    await app.connect();
  } else if (args.orm == "sequelize") {
    app = new sequelizeapp.App({
      host: args.host,
      port: args.port,
      pool: {
        min: ncon,
        max: ncon
      }
    });
  } else if (args.orm == "postgres_js") {
    app = new pgapp.App({
      host: args.host,
      port: args.port,
      max: ncon
    });
  } else {
    throw new Error("unexected orm: " + orm);
  }

  return app;
}

// Return the current timer value in microseconds
function _now() {
  var [s, ns] = process.hrtime();
  return s * 1000000 + Math.round(ns / 1000);
}

async function runner(args) {
  var timeoutInMicroSecs = args.timeout * 1000000;

  var reported = 0;
  var minLatency = Infinity;
  var maxLatency = 0.0;
  var queries = 0;
  var latencyStats = null;
  var data = null;
  var samples = [];

  var app = await getApp(args);
  var ids = _.shuffle((await app.getIDs())[args.query]);
  var idIndex = 0;

  function reportResults(
    runQueries,
    runLatencyStats,
    runMinLatency,
    runMaxLatency,
    runStart
  ) {
    queries += runQueries;

    if (runMaxLatency > maxLatency) {
      maxLatency = runMaxLatency;
    }

    if (runMinLatency < minLatency) {
      minLatency = runMinLatency;
    }

    if (latencyStats === null) {
      latencyStats = runLatencyStats;
    } else {
      for (var i = 0; i < latencyStats.length; i += 1) {
        latencyStats[i] += runLatencyStats[i];
      }
    }

    reported += 1;

    if (reported == args.concurrency) {
      var runEnd = _now();

      data = {
        nqueries: queries,
        duration: (runEnd - runStart) / 1000000,
        min_latency: minLatency,
        max_latency: maxLatency,
        latency_stats: Array.prototype.slice.call(latencyStats),
        samples: samples.slice(0, args.nsamples)
      };
      console.log(JSON.stringify(data));
    }
  }

  async function doRun(app, query, concurrency, runDuration, report, nsamples) {
    var runStart = _now();

    async function queryRunner(app) {
      var queries = 0;
      var latencyStats = new Float64Array(timeoutInMicroSecs / 10);
      var minLatency = Infinity;
      var maxLatency = 0.0;
      var durationInMicroSecs = runDuration * 1000000;
      var reqStart;
      var reqTime;

      // execute queries one after the other in a loop
      do {
        reqStart = _now();

        var id = ids[idIndex];
        var data = await app.benchQuery(query, id);
        idIndex += 1;
        idIndex %= ids.length;

        // record the sample if needed
        if (samples.length < nsamples) {
          samples.push(JSON.stringify(data));
        }

        // Request time in tens of microseconds
        reqTime = Math.round((_now() - reqStart) / 10);

        if (reqTime > maxLatency) {
          maxLatency = reqTime;
        }

        if (reqTime < minLatency) {
          minLatency = reqTime;
        }

        latencyStats[reqTime] += 1;
        queries += 1;
      } while (_now() - runStart < durationInMicroSecs);

      if (report) {
        reportResults(queries, latencyStats, minLatency, maxLatency, runStart);
      }
      // done with this run
    }

    var concurrent = [];
    for (var i = 0; i < concurrency; i += 1) {
      concurrent.push(queryRunner(app.getConnection(i)));
    }
    await Promise.all(concurrent);
  }

  async function run() {
    await doRun(
      app,
      args.query,
      args.concurrency,
      args.duration,
      true,
      args.nsamples
    );
  }

  async function warmupAndRun() {
    if (args.warmup_time) {
      await doRun(
        app,
        args.query,
        args.concurrency,
        args.warmup_time,
        false,
        args.nsamples
      );
    }
    await run();
  }

  await warmupAndRun();
}

async function main() {
  let parser = argparse.ArgumentParser({
    addHelp: true,
    description: "async pg driver benchmark [concurrent]"
  });

  parser.addArgument("--concurrency", {
    type: Number,
    defaultValue: 10,
    help: "number of concurrent connections"
  });
  parser.addArgument("--duration", {
    type: Number,
    defaultValue: 30,
    help: "duration of test in seconds"
  });
  parser.addArgument("--timeout", {
    type: Number,
    defaultValue: 2,
    help: "server timeout in seconds"
  });
  parser.addArgument("--warmup-time", {
    type: Number,
    defaultValue: 5,
    help: "duration of warmup period for each benchmark in seconds"
  });
  parser.addArgument("--output-format", {
    type: String,
    defaultValue: "text",
    help: "output format",
    choices: ["text", "json"]
  });
  parser.addArgument("--host", {
    type: String,
    defaultValue: "127.0.0.1",
    help: "PostgreSQL server host"
  });
  parser.addArgument("--port", {
    type: Number,
    defaultValue: 5432,
    help: "PostgreSQL server port"
  });
  parser.addArgument("--user", {
    type: String,
    help: "PostgreSQL server user"
  });
  parser.addArgument("--nsamples", {
    type: Number,
    defaultValue: 0,
    help: "number of result samples to return"
  });
  parser.addArgument("--query", {
    type: String,
    help: "specific query to run",
    choices: ["get_movie", "get_person", "get_user"]
  });
  parser.addArgument("orm", {
    type: String,
    help: "ORM implementation to use",
    choices: ["loopback", "typeorm", "sequelize", "postgres_js"]
  });

  let args = parser.parseArgs();
  await runner(args);
}

main()
  .then(async () => {
    setTimeout(() => process.exit(0), 500);
  })
  .catch(err => {
    console.log(err);
    process.exit(1);
  });
