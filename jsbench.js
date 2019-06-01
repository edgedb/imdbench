#!/usr/bin/env node
//
// Copyright (c) 2019 MagicStack Inc.
// All rights reserved.
//
// See LICENSE for details.
//


"use strict";

const argparse = require('argparse');
const fs = require('fs');
const _ = require('lodash')
const process = require('process');
const loopback_app = require('./_loopback/server/bench');
const typeorm_app = require('./_typeorm/build/index');
const sequelize_app = require('./_sequelize/index');


async function _get_app(args) {
  var app;
  var ncon = args.concurrency;

  if (args.orm == 'loopback') {
    app = loopback_app;
    await app.boot({
      host: args.host,
      port: args.port,
      min: ncon,
      max: ncon
    });
  } else if (args.orm == 'typeorm') {
    app = new typeorm_app.App({
      host: args.host,
      port: args.port,
      extra: {max: ncon}
    });
    await app.connect();
  } else if (args.orm == 'sequelize') {
    app = new sequelize_app.App({
      host: args.host,
      port: args.port,
      pool: {
        min: ncon,
        max: ncon
      }
    });
  } else {
    throw new Error('unexected orm: ' + orm)
  }

  return app;
}


// Return the current timer value in microseconds
function _now() {
  var [s, ns] = process.hrtime();
  return s * 1000000 + Math.round(ns / 1000);
}


async function runner(args) {
  var duration = args.duration;
  var timeout_in_us = args.timeout * 1000000;

  var reported = 0;
  var min_latency = Infinity;
  var max_latency = 0.0;
  var queries = 0;
  var latency_stats = null;
  var data = null;
  var samples = [];

  var app = await _get_app(args);
  var ids = _.shuffle((await app.get_ids())[args.query]);
  var id_index = 0;

  function _report_results(t_queries, t_latency_stats, t_min_latency,
                           t_max_latency, run_start) {
    queries += t_queries;

    if (t_max_latency > max_latency) {
      max_latency = t_max_latency;
    }

    if (t_min_latency < min_latency) {
      min_latency = t_min_latency;
    }

    if (latency_stats === null) {
      latency_stats = t_latency_stats;
    } else {
      for (var i = 0; i < latency_stats.length; i += 1) {
        latency_stats[i] += t_latency_stats[i];
      }
    }

    reported += 1;

    if (reported == args.concurrency) {
      var run_end = _now();

      data = {
        'nqueries': queries,
        'duration': (run_end - run_start) / 1000000,
        'min_latency': min_latency,
        'max_latency': max_latency,
        'latency_stats': Array.prototype.slice.call(latency_stats),
        'samples': samples.slice(0, args.nsamples),
      };
      console.log(JSON.stringify(data));
    }
  }

  async function _do_run(app, query, concurrency, run_duration, report,
                         nsamples) {
    var run_start = _now();
    var copy = null;

    async function query_runner(app) {
      var queries = 0;
      var latency_stats = new Float64Array(timeout_in_us / 10);
      var min_latency = Infinity;
      var max_latency = 0.0;
      var duration_in_us = run_duration * 1000000;
      var req_start;
      var req_time;

      // execute queries one after the other in a loop
      do {
        req_start = _now();

        var id = ids[id_index];
        var data = await app.bench_query(query, id);
        id_index += 1;
        id_index %= ids.length;

        // record the sample if needed
        if (samples.length < nsamples) {
          samples.push(JSON.stringify(data));
        }

        // Request time in tens of microseconds
        req_time = Math.round((_now() - req_start) / 10);

        if (req_time > max_latency) {
          max_latency = req_time;
        }

        if (req_time < min_latency) {
          min_latency = req_time;
        }

        latency_stats[req_time] += 1;
        queries += 1;
      } while (_now() - run_start < duration_in_us);

      if (report) {
        _report_results(queries, latency_stats,
                        min_latency, max_latency,
                        run_start);
      }
      // done with this run
    };

    var concurrent = [];
    for (var i = 0; i < concurrency; i += 1) {
      concurrent.push(query_runner(app));
    }
    await Promise.all(concurrent);
  }

  async function _run() {
    await _do_run(app, args.query, args.concurrency, args.duration,
                  true, args.nsamples);
  }

  async function _warmup_and_run() {
    if (args.warmup_time) {
      await _do_run(app, args.query, args.concurrency, args.warmup_time,
                    false, args.nsamples);
    }
    await _run();
  }

  await _warmup_and_run();
}


async function main() {
    let parser = argparse.ArgumentParser({
        addHelp: true,
        description: 'async pg driver benchmark [concurrent]'
    })

    parser.addArgument(
        '--concurrency',
        {type: Number, defaultValue: 10,
         help: 'number of concurrent connections'})
    parser.addArgument(
        '--duration',
        {type: Number, defaultValue: 30,
         help: 'duration of test in seconds'})
    parser.addArgument(
        '--timeout',
        {type: Number, defaultValue: 2,
         help: 'server timeout in seconds'})
    parser.addArgument(
        '--warmup-time',
        {type: Number, defaultValue: 5,
         help: 'duration of warmup period for each benchmark in seconds'})
    parser.addArgument(
        '--output-format',
        {type: String, defaultValue: 'text',
         help: 'output format',
         choices: ['text', 'json']})
    parser.addArgument(
        '--host',
        {type: String, defaultValue: '127.0.0.1',
         help: 'PostgreSQL server host'})
    parser.addArgument(
        '--port',
        {type: Number, defaultValue: 5432,
         help: 'PostgreSQL server port'})
    parser.addArgument(
        '--user',
        {type: String,
         help: 'PostgreSQL server user'})
    parser.addArgument(
        '--nsamples',
        {type: Number, defaultValue: 0,
         help: 'number of result samples to return'})
    parser.addArgument(
        '--query',
        {type: String,
         help: 'specific query to run',
         choices: ['get_movie', 'get_person', 'get_user']})
    parser.addArgument(
        'orm',
        {type: String, help: 'ORM implementation to use',
         choices: ['loopback', 'typeorm', 'sequelize']})

    let args = parser.parseArgs();
    await runner(args);
}


main().then(async () => {
  setTimeout(() => process.exit(0), 500);
}).catch(err => {
  console.log(err);
  process.exit(1);
});
