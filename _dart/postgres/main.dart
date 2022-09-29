import 'dart:convert';
import 'dart:math';

import 'package:postgres_pool/postgres_pool.dart';

import '../dartbench.dart';

final rand = Random();

class Runner implements DartBenchmarkRunner {
  PgPool pool;

  Runner(opts)
      : pool = PgPool(
          PgEndpoint(
            host: 'localhost',
            port: 15432,
            database: 'postgres_bench',
            username: 'postgres_bench',
            password: 'edgedbbenchmark',
          ),
          settings: PgPoolSettings()..concurrency = opts['concurrency'],
        );

  connect() async {}

  shutdown() async {
    await pool.close();
  }

  final _queries = <String, Future<dynamic> Function(PgPool pool, dynamic val)>{
    'get_user': (pool, id) async {
      final res = await pool.query('''
        SELECT
            users.id,
            users.name,
            users.image,
            q.review_id,
            q.review_body,
            q.review_rating,
            q.movie_id,
            q.movie_image,
            q.movie_title,
            q.movie_avg_rating
        FROM
            users,
            LATERAL (
                SELECT
                    review.id AS review_id,
                    review.body AS review_body,
                    review.rating AS review_rating,
                    movie.id AS movie_id,
                    movie.image AS movie_image,
                    movie.title AS movie_title,
                    movie.avg_rating AS movie_avg_rating
                FROM
                    reviews AS review
                    INNER JOIN movies AS movie
                        ON (review.movie_id = movie.id)
                WHERE
                    review.author_id = users.id
                ORDER BY
                    review.creation_time DESC
                LIMIT 10
            ) AS q
            WHERE
            users.id = @id''', substitutionValues: {'id': id});

      return jsonEncode({
        'id': res.first[0],
        'name': res.first[1],
        'image': res.first[2],
        'latest_reviews': res
            .map((row) => {
                  'id': row[3],
                  'body': row[4],
                  'rating': row[5],
                  'movie': {
                    'id': row[6],
                    'image': row[7],
                    'title': row[8],
                    'avg_rating': double.parse(row[9])
                  }
                })
            .toList()
      });
    },
    'get_person': (pool, id) async {
      // multiple queries need to be wrapped in a transaction so that the data is
      // guaranteed to be consistent
      return await pool.runTx((conn) async {
        final person = (await conn.query('''
          SELECT
              p.id,
              p.full_name,
              p.image,
              p.bio
          FROM
              persons p
          WHERE
              p.id = @id''', substitutionValues: {'id': id})).first;
        final actedIn = await conn.query('''
          SELECT
              movie.id,
              movie.image,
              movie.title,
              movie.year,
              movie.avg_rating
          FROM
              actors
              INNER JOIN movies AS movie
                  ON (actors.movie_id = movie.id)
          WHERE
              actors.person_id = @id
          ORDER BY
              movie.year ASC, movie.title ASC''',
            substitutionValues: {'id': id});
        final directed = await conn.query('''
          SELECT
              movie.id,
              movie.image,
              movie.title,
              movie.year,
              movie.avg_rating
          FROM
              directors
              INNER JOIN movies AS movie
                  ON (directors.movie_id = movie.id)
          WHERE
              directors.person_id = @id
          ORDER BY
              movie.year ASC, movie.title ASC''',
            substitutionValues: {'id': id});

        return jsonEncode({
          'id': person[0],
          'full_name': person[1],
          'image': person[2],
          'bio': person[3],
          'acted_in': actedIn
              .map((row) => {
                    'id': row[0],
                    'image': row[1],
                    'title': row[2],
                    'year': row[3],
                    'avg_rating': double.parse(row[4]),
                  })
              .toList(),
          'directed': directed
              .map((row) => {
                    'id': row[0],
                    'image': row[1],
                    'title': row[2],
                    'year': row[3],
                    'avg_rating': double.parse(row[4]),
                  })
              .toList()
        });
      });
    },
    'get_movie': (pool, id) async {
      return await pool.runTx((conn) async {
        final movie = (await conn.query('''
          SELECT
              movie.id,
              movie.image,
              movie.title,
              movie.year,
              movie.description,
              movie.avg_rating
          FROM
              movies AS movie
          WHERE
              movie.id = @id
          ''', substitutionValues: {'id': id})).first;

        final directors = await conn.query('''
          SELECT
              person.id,
              person.full_name,
              person.image
          FROM
              directors
              INNER JOIN persons AS person
                  ON (directors.person_id = person.id)
          WHERE
              directors.movie_id = @id
          ORDER BY
              directors.list_order NULLS LAST,
              person.last_name
          ''', substitutionValues: {'id': id});

        final cast = await conn.query('''
          SELECT
              person.id,
              person.full_name,
              person.image
          FROM
              actors
              INNER JOIN persons AS person
                  ON (actors.person_id = person.id)
          WHERE
              actors.movie_id = @id
          ORDER BY
              actors.list_order NULLS LAST,
              person.last_name
          ''', substitutionValues: {'id': id});

        final reviews = await conn.query('''
          SELECT
              review.id,
              review.body,
              review.rating,
              author.id AS author_id,
              author.name AS author_name,
              author.image AS author_image
          FROM
              reviews AS review
              INNER JOIN users AS author
                  ON (review.author_id = author.id)
          WHERE
              review.movie_id = @id
          ORDER BY
              review.creation_time DESC
        ''', substitutionValues: {'id': id});

        return jsonEncode({
          'id': movie[0],
          'image': movie[1],
          'title': movie[2],
          'year': movie[3],
          'description': movie[4],
          'avg_rating': double.parse(movie[5]),
          'directors': directors
              .map((row) => {
                    'id': row[0],
                    'full_name': row[1],
                    'image': row[2],
                  })
              .toList(),
          'cast': cast
              .map((row) => {
                    'id': row[0],
                    'full_name': row[1],
                    'image': row[2],
                  })
              .toList(),
          'reviews': reviews
              .map((row) => {
                    'id': row[0],
                    'body': row[1],
                    'rating': row[2],
                    'author': {
                      'id': row[3],
                      'name': row[4],
                      'image': row[5],
                    }
                  })
              .toList(),
        });
      });
    },
    'update_movie': (pool, id) async {
      final res = (await pool.query('''
        UPDATE
            movies
        SET
            title = movies.title || @title
        WHERE
            movies.id = @id
        RETURNING
            movies.id, movies.title
        ''', substitutionValues: {'id': id, 'title': '---$id'})).first;

      return jsonEncode({
        'id': res[0],
        'title': res[1],
      });
    },
    'insert_user': (pool, id) async {
      final num = rand.nextInt(1000000);
      final res = (await pool.query('''
        INSERT INTO users (name, image) VALUES
            (@name, @image)
        RETURNING
            users.id, users.name, users.image
        ''', substitutionValues: {'name': '$id$num', 'image': 'image_$id$num'}))
          .first;

      return jsonEncode({
        'id': res[0],
        'name': res[1],
        'image': res[2],
      });
    },
    'insert_movie': (pool, val) async {
      return await pool.runTx((conn) async {
        final num = rand.nextInt(1000000);
        final movie = (await conn.query('''
          INSERT INTO movies AS M (title, image, description, year) VALUES
              (@title, @image, @description, @year)
          RETURNING
              M.id, M.title, M.image, M.description, M.year''',
                substitutionValues: {
              'title': '${val['prefix']}$num',
              'image': '${val['prefix']}image${num}.jpeg',
              'description': '${val['prefix']}description${num}',
              'year': '${num}',
            }))
            .first;

        final people = (await conn.query('''
          SELECT
              P.id,
              P.full_name,
              P.image
          FROM
              persons AS P
          WHERE
              P.id IN (@1, @2, @3, @4);
          ''', substitutionValues: {
          '1': val['people'][0],
          '2': val['people'][1],
          '3': val['people'][2],
          '4': val['people'][3]
        }))
            .map((row) => {'id': row[0], 'full_name': row[1], 'image': row[2]})
            .toList();

        var directors = [], cast = [];

        for (var p in people) {
          if (p['id'] == val['people'][0]) {
            directors.add(p);
          } else {
            cast.add(p);
          }
        }

        await conn.query('''
          INSERT INTO directors AS M (person_id, movie_id) VALUES
              (@p_id, @m_id);
          ''',
            substitutionValues: {'p_id': directors[0]['id'], 'm_id': movie[0]});
        await conn.query(
          '''
          INSERT INTO actors AS M (person_id, movie_id) VALUES
              (@c_1, @m_id),
              (@c_2, @m_id),
              (@c_3, @m_id);
          ''',
          substitutionValues: {
            'c_1': cast[0]['id'],
            'c_2': cast[1]['id'],
            'c_3': cast[2]['id'],
            'm_id': movie[0]
          },
        );

        return jsonEncode({
          'id': movie[0],
          'title': movie[1],
          'image': movie[2],
          'description': movie[3],
          'year': movie[4],
          'directors': directors,
          'cast': cast
        });
      });
    },
    'insert_movie_plus': (pool, val) async {
      return await pool.runTx((conn) async {
        final num = rand.nextInt(1000000);
        final movie = (await conn.query('''
          INSERT INTO movies AS M (title, image, description, year) VALUES
              (@title, @image, @description, @year)
          RETURNING
              M.id, M.title, M.image, M.description, M.year
          ''', substitutionValues: {
          'title': '$val$num',
          'image': '${val}image${num}.jpeg',
          'description': '${val}description$num',
          'year': '$num',
        }))
            .first;

        final people = (await conn.query(
          '''
          INSERT INTO persons AS P (first_name, last_name, image, bio) VALUES
              (@fn1, @ln1, @img1, ''),
              (@fn2, @ln2, @img2, ''),
              (@fn3, @ln3, @img3, '')
          RETURNING
              P.id, P.full_name, P.image
          ''',
          substitutionValues: {
            'fn1': '${val}Alice',
            'ln1': '${val}Director',
            'img1': '${val}image${num}.jpeg',
            'fn2': '${val}Billie',
            'ln2': '${val}Actor',
            'img2': '${val}image${num + 1}.jpeg',
            'fn3': '${val}Cameron',
            'ln3': '${val}Actor',
            'img3': '${val}image${num + 2}.jpeg',
          },
        ))
            .map((row) => {'id': row[0], 'full_name': row[1], 'image': row[2]})
            .toList();
        ;

        final directors = [people[0]];
        final cast = people.sublist(1);

        await conn.query('''
          INSERT INTO directors AS M (person_id, movie_id) VALUES
              (@p_id, @m_id);
          ''',
            substitutionValues: {'p_id': directors[0]['id'], 'm_id': movie[0]});
        await conn.query('''
          INSERT INTO actors AS M (person_id, movie_id) VALUES
              (@c_1, @m_id),
              (@c_2, @m_id);
          ''', substitutionValues: {
          'c_1': cast[0]['id'],
          'c_2': cast[1]['id'],
          'm_id': movie[0]
        });

        return jsonEncode({
          'id': movie[0],
          'title': movie[1],
          'image': movie[2],
          'description': movie[3],
          'year': movie[4],
          'directors': directors,
          'cast': cast
        });
      });
    }
  };

  Future<dynamic> benchQuery(String query, dynamic val) {
    return _queries[query]!(pool, val);
  }
}

class PostgresDartApp implements DartBenchmarkApp {
  static const _insertPrefix = "insert_test__";
  int _concurrency;
  late Runner _runner;

  PostgresDartApp({int concurrency = 1})
      : _concurrency = concurrency,
        _runner = Runner({'concurrency': concurrency});

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
    final ids = [
      await _runner.pool.query("SELECT u.id FROM users u ORDER BY random();"),
      await _runner.pool.query("SELECT p.id FROM persons p ORDER BY random();"),
      await _runner.pool.query("SELECT m.id FROM movies m ORDER BY random();")
    ];
    final people = ids[1].map((x) => x[0]).toList();

    return {
      'get_user': ids[0].map((x) => x[0]).toList(),
      'get_person': people,
      'get_movie': ids[2].map((x) => x[0]).toList(),
      // re-use user IDs for update tests
      'update_movie': ids[2].map((x) => x[0]).toList(),
      // generate as many insert stubs as "concurrency" to
      // accommodate concurrent inserts
      'insert_user': List.filled(_concurrency, _insertPrefix),
      'insert_movie': List.filled(_concurrency, {
        'prefix': _insertPrefix,
        'people': people.sublist(0, 4),
      }),
      'insert_movie_plus': List.filled(_concurrency, _insertPrefix),
    };
  }

  Future<dynamic> setup(String query) async {
    switch (query) {
      case 'update_movie':
        return _runner.pool.query('''
          UPDATE
              movies
          SET
              title = split_part(movies.title, '---', 1)
          WHERE
              movies.title LIKE '%---%';''');

      case "insert_user":
        return await _runner.pool.query('''
          DELETE FROM
              users
          WHERE
              users.name LIKE @name;
      ''', substitutionValues: {'name': _insertPrefix + '%'});
      case "insert_movie":
      case "insert_movie_plus":
        await _runner.pool.query('''
          DELETE FROM
              "directors" as D
          USING
              "movies" as M
          WHERE
              D.movie_id = M.id AND M.image LIKE @image;
          ''', substitutionValues: {'image': _insertPrefix + '%'});
        await _runner.pool.query('''
          DELETE FROM
              "actors" as A
          USING
              "movies" as M
          WHERE
              A.movie_id = M.id AND M.image LIKE @image;
          ''', substitutionValues: {'image': _insertPrefix + '%'});
        await _runner.pool.query('''
          DELETE FROM
              "movies" as M
          WHERE
              M.image LIKE @image;
          ''', substitutionValues: {'image': _insertPrefix + '%'});
        return await _runner.pool.query('''
          DELETE FROM
              "persons" as P
          WHERE
              P.image LIKE @image;
          ''', substitutionValues: {'image': _insertPrefix + '%'});
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
      return await setup(query);
    }
  }
}
