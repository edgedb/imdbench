#!/usr/bin/env node
//
// Copyright (c) 2019 MagicStack Inc.
// All rights reserved.
//
// See LICENSE for details.
//

'use strict';

const argparse = require('argparse');
const _ = require('lodash');
const process = require('process');

async function getApp(args) {
  var app;
  var ncon = args.concurrency;

  if (args.orm == 'postgresjs') {
    app = require('./_postgresjs/index')({
      host: args.host,
      port: args.port,
      max: ncon
    })
    await app.connect();
  } else if (args.orm == 'typeorm') {
    app = new (require('./_typeorm/build/index').App)({
      host: args.host,
      port: args.port,
      extra: {max: ncon},
    });
    await app.connect();
  } else if (args.orm == 'sequelize') {
    app = new (require('./_sequelize/index').App)({
      host: args.host,
      port: args.port,
      pool: {
        min: ncon,
        max: ncon,
      },
    });
  } else if (args.orm == 'prisma_untuned') {
    app = new (require('./_prisma/index').App)();
  } else if (args.orm == 'prisma') {
    app = new (require('./_prisma/index').TunedApp)();
  } else if (args.orm == 'postgres_pg') {
    app = new (require('./_postgres/index').App)({
      host: args.host,
      port: args.port,
      max: ncon,
    });
  } else if (args.orm == 'edgedb_js_json') {
    app = new (require('./_edgedb_js/index').App)({
      style: 'json',
      host: args.host,
      port: args.port,
      pool: ncon,
    });
    await app.initPool();
  } else if (args.orm == 'edgedb_js') {
    app = new (require('./_edgedb_js/index').App)({
      style: 'repack',
      host: args.host,
      port: args.port,
      pool: ncon,
    });
    await app.initPool();
  } else if (args.orm == 'edgedb_js_qb') {
    app = new (require('./_edgedb_js/index').App)({
      style: 'querybuilder',
      host: args.host,
      port: args.port,
      pool: ncon,
    });
    await app.initPool();
  } else if (args.orm == 'edgedb_js_qb_uncached') {
    app = new (require('./_edgedb_js/index').App)({
      style: 'querybuilder_uncached',
      host: args.host,
      port: args.port,
      pool: ncon,
    });
    await app.initPool();
  } else {
    throw new Error('Unexpected ORM: ' + args.orm);
  }

  return app;
}

// Return the current timer value in microseconds
function _now() {
  var [s, ns] = process.hrtime();
  return s * 1000000 + Math.round(ns / 1000);
}

async function runner(args, app) {
  var timeoutInMicroSecs = args.timeout * 1000000;

  var reported = 0;
  var minLatency = Infinity;
  var maxLatency = 0.0;
  var queries = 0;
  var latencyStats = null;
  var data = null;
  var samples = [];

  var ids = (await app.getIDs())[args.query];
  if (ids.length > args.numner_of_ids) {
    ids = ids.slice(0, args.numner_of_ids);
  }
  ids = _.shuffle(ids);
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
        samples: samples.slice(0, args.nsamples),
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
        idIndex += 1;
        idIndex %= ids.length;
        var data = await app.benchQuery(query, id);

        // record the sample if needed
        if (samples.length < nsamples) {
          samples.push(data);
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

    // Potentially setup the benchmark state
    await app.setup(query);

    var concurrent = [];
    for (var i = 0; i < concurrency; i += 1) {
      concurrent.push(queryRunner(app.getConnection(i)));
    }
    await Promise.all(concurrent);

    // Potentially clean up after the benchmarks
    await app.cleanup(query);
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
    add_help: true,
    description: 'async pg driver benchmark [concurrent]',
  });

  parser.add_argument('--concurrency', {
    type: Number,
    default: 10,
    help: 'number of concurrent connections',
  });
  parser.add_argument('--duration', {
    type: Number,
    default: 30,
    help: 'duration of test in seconds',
  });
  parser.add_argument('--timeout', {
    type: Number,
    default: 2,
    help: 'server timeout in seconds',
  });
  parser.add_argument('--warmup-time', {
    type: Number,
    default: 5,
    help: 'duration of warmup period for each benchmark in seconds',
  });
  parser.add_argument('--output-format', {
    type: String,
    default: 'text',
    help: 'output format',
    choices: ['text', 'json'],
  });
  parser.add_argument('--host', {
    type: String,
    default: '127.0.0.1',
    help: 'PostgreSQL server host',
  });
  parser.add_argument('--port', {
    type: Number,
    default: 15432,
    help: 'PostgreSQL server port',
  });
  parser.add_argument('--user', {
    type: String,
    help: 'PostgreSQL server user',
  });
  parser.add_argument('--nsamples', {
    type: Number,
    default: 0,
    help: 'number of result samples to return',
  });
  parser.add_argument('--number-of-ids', {
    type: Number,
    default: 250,
    help: 'number of random IDs to fetch data with in benchmarks',
  });
  parser.add_argument('--query', {
    type: String,
    help: 'specific query to run',
    choices: [
      'get_movie',
      'get_person',
      'get_user',
      'update_movie',
      'insert_user',
      'insert_movie',
      'insert_movie_plus',
    ],
  });
  parser.add_argument('orm', {
    type: String,
    help: 'ORM implementation to use',
    choices: [
      'typeorm',
      'sequelize',
      'postgres_pg',
      'postgresjs',
      'prisma',
      'prisma_untuned',
      'edgedb_js',
      'edgedb_js_json',
      'edgedb_js_qb',
      'edgedb_js_qb_uncached',
    ],
  });

  let args = parser.parse_args();
  let app = await getApp(args);

  try {
    await runner(args, app);
  } finally {
    if (args.orm == 'prisma_untuned' || args.orm == 'prisma') {
      await app.$disconnect();
    }
  }
}

main()
  .then(async () => {
    setTimeout(() => process.exit(0), 500);
  })
  .catch((err) => {
    console.log(err);
    process.exit(1);
  });
