import 'dart:convert';
import 'dart:math';

import 'package:edgedb/edgedb.dart';

import '../dartbench.dart';

import './queries.dart';

final rand = Random();

class _BaseRunner implements DartBenchmarkRunner {
  final Client client;

  _BaseRunner(opts)
      : client = createClient(
                concurrency: opts['concurrency'],
                tlsSecurity: TLSSecurity.insecure)
            .withRetryOptions(RetryOptions(attempts: 10));

  connect() async {
    await client.ensureConnected();
  }

  shutdown() async {
    await client.close();
  }

  final _queries =
      <String, Future<dynamic> Function(Client client, dynamic val)>{};

  Future<dynamic> benchQuery(String query, dynamic val) {
    return _queries[query]!(client, val);
  }
}

class JSONRunner extends _BaseRunner {
  JSONRunner(super.opts);

  final _queries = {
    'get_user': (client, id) async {
      return await client.querySingleJSON(queries['user']!, {'id': id});
    },
    'get_person': (client, id) async {
      return await client.querySingleJSON(queries['person']!, {'id': id});
    },
    'get_movie': (client, id) async {
      return await client.querySingleJSON(queries['movie']!, {'id': id});
    },
    'update_movie': (client, id) async {
      return await client.querySingleJSON(queries['updateMovie']!, {
        'id': id,
        'suffix': id.substring(0, 8),
      });
    },
    'insert_user': (client, id) async {
      final num = rand.nextInt(1000000);
      return await client.querySingleJSON(queries['insertUser']!, {
        'name': '${id}${num}',
        'image': '${id}image${num}',
      });
    },
    'insert_movie': (client, val) async {
      final num = rand.nextInt(1000000);
      return await client.querySingleJSON(queries['insertMovie']!, {
        'title': '${val['prefix']}$num',
        'image': '${val['prefix']}image${num}.jpeg',
        'description': '${val['prefix']}description${num}',
        'year': '${num}',
        'd_id': '${val['people'][0]}',
        'cast': '${val['people'].sublist(1, 4)}',
      });
    },
    'insert_movie_plus': (client, val) async {
      final num = rand.nextInt(1000000);
      return await client.querySingleJSON(queries['insertMoviePlus']!, {
        'title': '$val$num',
        'image': '${val}image${num}.jpeg',
        'description': '${val}description${num}',
        'year': '${num}',
        'dfn': '${val}Alice',
        'dln': '${val}Director',
        'dimg': '${val}image${num}.jpeg',
        'cfn0': '${val}Billie',
        'cln0': '${val}Actor',
        'cimg0': '${val}image${num + 1}.jpeg',
        'cfn1': '${val}Cameron',
        'cln1': '${val}Actor',
        'cimg1': '${val}image${num + 2}.jpeg',
      });
    },
  };
}

class RepackRunner extends _BaseRunner {
  RepackRunner(super.opts);

  final _queries = {
    'get_user': (client, id) async {
      return jsonEncode(await client.querySingle(queries['user']!, {'id': id}));
    },
    'get_person': (client, id) async {
      return jsonEncode(
          await client.querySingle(queries['person']!, {'id': id}));
    },
    'get_movie': (client, id) async {
      return jsonEncode(
          await client.querySingle(queries['movie']!, {'id': id}));
    },
    'update_movie': (client, id) async {
      return jsonEncode(await client.querySingle(queries['updateMovie']!, {
        'id': id,
        'suffix': id.substring(0, 8),
      }));
    },
    'insert_user': (client, id) async {
      final num = rand.nextInt(1000000);
      return jsonEncode(await client.querySingle(queries['insertUser']!, {
        'name': '${id}${num}',
        'image': '${id}image${num}',
      }));
    },
    'insert_movie': (client, val) async {
      final num = rand.nextInt(1000000);
      return jsonEncode(await client.querySingle(queries['insertMovie']!, {
        'title': '${val['prefix']}$num',
        'image': '${val['prefix']}image${num}.jpeg',
        'description': '${val['prefix']}description${num}',
        'year': num,
        'd_id': '${val['people'][0]}',
        'cast': val['people'].sublist(1, 4),
      }));
    },
    'insert_movie_plus': (client, val) async {
      final num = rand.nextInt(1000000);
      return jsonEncode(await client.querySingle(queries['insertMoviePlus']!, {
        'title': '$val$num',
        'image': '${val}image${num}.jpeg',
        'description': '${val}description${num}',
        'year': num,
        'dfn': '${val}Alice',
        'dln': '${val}Director',
        'dimg': '${val}image${num}.jpeg',
        'cfn0': '${val}Billie',
        'cln0': '${val}Actor',
        'cimg0': '${val}image${num + 1}.jpeg',
        'cfn1': '${val}Cameron',
        'cln1': '${val}Actor',
        'cimg1': '${val}image${num + 2}.jpeg',
      }));
    },
  };
}

class EdgeDBDartApp implements DartBenchmarkApp {
  static const _insertPrefix = "insert_test__";
  int _concurrency;
  late _BaseRunner _runner;

  EdgeDBDartApp({int concurrency = 1, String runner = 'json'})
      : _concurrency = concurrency {
    switch (runner) {
      case 'repack':
        _runner = RepackRunner({'concurrency': concurrency});
        break;
      case 'json':
        _runner = JSONRunner({'concurrency': concurrency});
        break;
      default:
        throw ArgumentError('unknown runner: $runner');
    }
  }

  get runner {
    return _runner;
  }

  init() async {
    await _runner.connect();
  }

  shutdown() async {
    await _runner.shutdown();
  }

  Future<Map<String, List<dynamic>>> getIDs() async {
    var ids = await _runner.client.querySingle('''
      WITH
          U := User {id, r := random()},
          M := Movie {id, r := random()},
          P := Person {id, r := random()}
      SELECT (
          users := array_agg((SELECT U ORDER BY U.r).id),
          movies := array_agg((SELECT M ORDER BY M.r).id),
          people := array_agg((SELECT P ORDER BY P.r).id),
      );
    ''');

    return {
      'get_user': ids['users'],
      'get_person': ids['people'],
      'get_movie': ids['movies'],
      // re-use user IDs for update tests
      'update_movie': [...ids['movies']],
      // generate as many insert stubs as "concurrency" to
      // accommodate concurrent inserts
      'insert_user': List.filled(_concurrency, _insertPrefix),
      'insert_movie': List.filled(_concurrency,
          {'prefix': _insertPrefix, 'people': ids['people'].sublist(0, 4)}),
      'insert_movie_plus': List.filled(_concurrency, _insertPrefix),
    };
  }

  Future<dynamic> setup(String query) async {
    switch (query) {
      case "update_movie":
        return await _runner.client.execute('''
        update Movie
        filter contains(.title, '---')
        set {
            title := str_split(.title, '---')[0]
        };
      ''');
      case 'insert_user':
        return await _runner.client.query(r'''
        delete User
        filter .name LIKE <str>$0;
      ''', ['${_insertPrefix}image%']);
      case 'insert_movie':
        return await _runner.client.query(r'''
        delete Movie
        filter .image LIKE <str>$0;
      ''', ['${_insertPrefix}image%']);
      case 'insert_movie_plus':
        await _runner.client.query(r'''
        delete Movie
        filter .image LIKE <str>$0;
      ''', ['${_insertPrefix}image%']);
        return await _runner.client.query(r'''
        delete Person
        filter .image LIKE <str>$0;
      ''', ['${_insertPrefix}image%']);
    }
  }

  cleanup(String query) async {
    if ([
      "update_movie",
      "insert_user",
      "insert_movie",
      "insert_movie_plus",
    ].contains(query)) {
      // The clean up is the same as setup for mutation benchmarks
      return await this.setup(query);
    }
  }
}
