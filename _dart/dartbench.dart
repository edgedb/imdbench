#!/usr/bin/env dart
//
// Copyright (c) 2019 MagicStack Inc.
// All rights reserved.
//
// See LICENSE for details.
//

import 'dart:convert';

import 'package:args/args.dart';

import './edgedb/main.dart' show EdgeDBDartApp;
import './postgres/main.dart' show PostgresDartApp;

final argsParser = ArgParser()
  ..addOption('concurrency',
      defaultsTo: '10', help: 'number of concurrent connections')
  ..addOption('duration', defaultsTo: '30', help: 'duration of test in seconds')
  ..addOption('timeout', defaultsTo: '2', help: 'server timeout in seconds')
  ..addOption('warmup-time',
      defaultsTo: '5',
      help: 'duration of warmup period for each benchmark in seconds')
  ..addOption('output-format',
      defaultsTo: 'text', allowed: ['text', 'json'], help: 'output format')
  ..addOption('host', defaultsTo: '127.0.0.1', help: 'server host')
  ..addOption('port', defaultsTo: '15432', help: 'server port')
  ..addOption('user', help: 'server user')
  ..addOption('nsamples',
      defaultsTo: '0', help: 'number of result samples to return')
  ..addOption('number-of-ids',
      defaultsTo: '250',
      help: 'number of random IDs to fetch data with in benchmarks')
  ..addOption('query',
      help: 'specific query to run',
      mandatory: true,
      allowed: [
        'get_movie',
        'get_person',
        'get_user',
        'update_movie',
        'insert_user',
        'insert_movie',
        'insert_movie_plus',
      ]);

final intArgs = {
  'concurrency',
  'duration',
  'timeout',
  'warmup-time',
  'port',
  'nsamples',
  'number-of-ids'
};

Map<String, dynamic> parseArgs(List<String> _args) {
  final args = argsParser.parse(_args);

  return {
    'app': args.rest.first,
    ...{
      for (var key in args.options)
        key: intArgs.contains(key) ? int.parse(args[key], radix: 10) : args[key]
    },
  };
}

void main(List<String> _args) {
  final args = parseArgs(_args);

  final app = getApp(args);

  runner(args, app);
}

abstract class DartBenchmarkApp {
  DartBenchmarkApp({int? concurrency, String? runner});

  DartBenchmarkRunner get runner;

  Future<void> init();

  Future<void> shutdown();

  Future<Map<String, List<dynamic>>> getIDs();

  Future<dynamic> setup(String query);

  Future<dynamic> cleanup(String query);
}

abstract class DartBenchmarkRunner {
  DartBenchmarkRunner(dynamic opts);

  Future<void> connect();

  Future<void> shutdown();

  Future<dynamic> benchQuery(String query, dynamic val);
}

DartBenchmarkApp getApp(Map<String, dynamic> args) {
  switch (args['app']) {
    case 'edgedb_dart':
      return EdgeDBDartApp(concurrency: args['concurrency'], runner: 'repack')
        ..init();
    case 'edgedb_dart_json':
      return EdgeDBDartApp(concurrency: args['concurrency'], runner: 'json')
        ..init();
    case 'postgres_dart':
      return PostgresDartApp(concurrency: args['concurrency']);
    default:
      throw ArgumentError('unknown app: ${args['app']}');
  }
}

Future<void> runner(Map<String, dynamic> args, DartBenchmarkApp app) async {
  var timeoutInMicroSecs = args['timeout'] * 1000000;

  var reported = 0;
  var minLatency = double.infinity;
  var maxLatency = 0.0;
  var queries = 0;
  List<int>? latencyStats = null;
  var samples = <String>[];

  var ids = (await app.getIDs())[args['query']]!;
  if (ids.length > args['number-of-ids']) {
    ids = ids.sublist(0, args['number-of-ids']);
  }
  ids.shuffle();
  var idIndex = 0;

  reportResults(int runQueries, List<int> runLatencyStats, double runMinLatency,
      double runMaxLatency, Stopwatch timer) {
    if (reported == args['concurrency']) {
      timer.stop();
    }

    queries += runQueries;

    if (runMaxLatency > maxLatency) {
      maxLatency = runMaxLatency;
    }

    if (runMinLatency < minLatency) {
      minLatency = runMinLatency;
    }

    if (latencyStats == null) {
      latencyStats = runLatencyStats;
    } else {
      for (var i = 0; i < latencyStats!.length; i += 1) {
        latencyStats![i] += runLatencyStats[i];
      }
    }

    reported += 1;

    if (reported == args['concurrency']) {
      print(jsonEncode({
        'nqueries': queries,
        'duration': timer.elapsedMicroseconds / 1000000,
        'min_latency': minLatency,
        'max_latency': maxLatency,
        'latency_stats': latencyStats,
        'samples': samples.sublist(0, args['nsamples']),
      }));
    }
  }

  doRun(DartBenchmarkApp app, String query, int concurrency, int runDuration,
      bool report, int nsamples) async {
    final timer = Stopwatch();
    timer.start();

    queryRunner(DartBenchmarkRunner runner) async {
      var queries = 0;
      final latencyStats = List.filled(timeoutInMicroSecs ~/ 10, 0);
      var minLatency = double.infinity;
      var maxLatency = 0.0;
      final durationInMicroSecs = runDuration * 1000000;

      // execute queries one after the other in a loop
      do {
        final reqStart = timer.elapsedMicroseconds;
        var id = ids[idIndex];
        idIndex += 1;
        idIndex %= ids.length;
        final data = await runner.benchQuery(query, id);

        // record the sample if needed
        if (samples.length < nsamples) {
          samples.add(data);
        }

        // Request time in tens of microseconds
        final reqTime = ((timer.elapsedMicroseconds - reqStart) / 10).round();

        if (reqTime > maxLatency) {
          maxLatency = reqTime.toDouble();
        }
        if (reqTime < minLatency) {
          minLatency = reqTime.toDouble();
        }

        latencyStats[reqTime] += 1;
        queries += 1;
      } while (timer.elapsedMicroseconds < durationInMicroSecs);

      if (report) {
        reportResults(queries, latencyStats, minLatency, maxLatency, timer);
      }
      // done with this run
    }

    // Potentially setup the benchmark state
    await app.setup(query);

    var concurrent = <Future<void>>[];
    for (var i = 0; i < concurrency; i += 1) {
      concurrent.add(queryRunner(app.runner));
    }
    await Future.wait(concurrent);

    // Potentially clean up after the benchmarks
    await app.cleanup(query);
  }

  run() async {
    await doRun(app, args['query'], args['concurrency'], args['duration'], true,
        args['nsamples']);
  }

  warmupAndRun() async {
    if (args['warmup-time'] != null) {
      await doRun(app, args['query'], args['concurrency'], args['warmup-time'],
          false, args['nsamples']);
    }
    await run();
  }

  await warmupAndRun();

  await app.shutdown();
}
