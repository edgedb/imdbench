#
# Copyright (c) 2019 MagicStack Inc.
# All rights reserved.
#
# See LICENSE for details.
##


import argparse
import sys
import types
import typing


from _edgedb import queries as edgedb_queries
from _edgedb import queries_async as edgedb_queries_async
from _edgedb import queries_repack as edgedb_queries_repack
from _edgedb_go import queries_edgedb as edgedb_json_golang
from _edgedb_go import queries_graphql as edgedb_graphql_golang
from _edgedb_go import queries_hasura as postgres_hasura_golang
from _edgedb_go import queries_prisma as postgres_prisma_golang
from _edgedb_go import queries_postgraphile as postgres_postgraphile_golang
from _edgedb_go import queries_http as edgedb_edgeql_golang
from _django import queries as django_queries
from _django import queries_restfw as django_queries_restfw
from _mongodb import queries as mongodb_queries
from _sqlalchemy import queries as sqlalchemy_queries
from _postgres import queries as postgres_queries
from _postgres import queries_psycopg as postgres_psycopg_queries


class bench(typing.NamedTuple):
    language: str
    title: str
    module: typing.Optional[types.ModuleType]


BENCHMARKS = {
    'edgedb_json_sync':
        bench('python', 'EdgeDB JSON', edgedb_queries),

    'edgedb_json_async':
        bench('python', 'EdgeDB JSON (asyncio)', edgedb_queries_async),

    'edgedb_repack_sync':
        bench('python', 'EdgeDB', edgedb_queries_repack),

    'edgedb_graphql_go':
        bench('go', 'EdgeDB GraphQL+HTTP golang', edgedb_graphql_golang),

    'edgedb_http_go':
        bench('go', 'EdgeDB EdgeQL+HTTP golang', edgedb_edgeql_golang),

    'edgedb_json_go':
        bench('go', 'EdgeDB GO JSON', edgedb_json_golang),

    'django':
        bench('python', 'Django ORM', django_queries),

    'django_restfw':
        bench('python', 'Django Rest Framework', django_queries_restfw),

    'mongodb':
        bench('python', 'MongoDB', mongodb_queries),

    'sqlalchemy':
        bench('python', 'SQLAlchemy', sqlalchemy_queries),

    'postgres_asyncpg':
        bench('python', 'PostgreSQL asyncpg (asyncio)', postgres_queries),

    'postgres_psycopg':
        bench('python', 'PostgreSQL psycopg2', postgres_psycopg_queries),

    'postgres_hasura_go':
        bench('go', 'Postgres+Hasura HTTP golang', postgres_hasura_golang),

    'postgres_prisma_go':
        bench('go', 'Postgres+Prisma HTTP golang', postgres_prisma_golang),

    'postgres_postgraphile_go':
        bench('go', 'Postgres+Postgraphile HTTP golang',
              postgres_postgraphile_golang),

    'edgedb_json_js':
        bench('js', 'EdgeDB NodeJS JSON', None),

    'edgedb_repack_js':
        bench('js', 'EdgeDB NodeJS Objects', None),

    'loopback':
        bench('js', 'Loopback', None),

    'typeorm':
        bench('js', 'Typeorm', None),

    'sequelize':
        bench('js', 'Sequelize', None),

    'postgres_js':
        bench('js', 'PostgreSQL NodeJS', None),
}


QUERIES = ['get_movie', 'get_person', 'get_user']


def parse_args(*, prog_desc: str, out_to_json: bool = False,
               out_to_html: bool = False):
    parser = argparse.ArgumentParser(
        description=prog_desc,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument(
        '-C', '--concurrency', type=int, default=4,
        help='number of concurrent connections')

    parser.add_argument(
        '-A', '--async-concurrency', type=int, default=1,
        help='number of concurrent async connections in a process')

    parser.add_argument(
        '--db-host', type=str, default='127.0.0.1',
        help='host with databases')

    parser.add_argument(
        '-D', '--duration', type=int, default=30,
        help='duration of test in seconds')
    parser.add_argument(
        '--timeout', default=2, type=int,
        help='server timeout in seconds')
    parser.add_argument(
        '--warmup-time', type=int, default=5,
        help='duration of warmup period for each benchmark in seconds')

    parser.add_argument(
        '--pg-port', type=int, default=5432,
        help='PostgreSQL server port')

    parser.add_argument(
        '--edgedb-port', type=int, default=5656,
        help='EdgeDB server port')
    parser.add_argument(
        '--edgedb-graphql-port', type=int, default=8888,
        help='EdgeDB GraphQL port')
    parser.add_argument(
        '--edgedb-user', type=str, default='edgedb',
        help='PostgreSQL server user')

    parser.add_argument(
        '--mongodb-port', type=int, default=27017,
        help='MongoDB server port')

    parser.add_argument(
        '--number-of-ids', type=int, default=250,
        help='number of random IDs to fetch data with in benchmarks')

    parser.add_argument(
        '--query', dest='queries', action='append',
        help='queries to benchmark',
        choices=QUERIES)

    parser.add_argument(
        'benchmarks', nargs='+', help='benchmarks names',
        choices=list(BENCHMARKS.keys()) + ['all'])

    if out_to_json:
        parser.add_argument(
            '--json', type=str, default='',
            help='filename to dump serialized results in JSON')

    if out_to_html:
        parser.add_argument(
            '--html', type=str, default='',
            help='filename to dump HTML report')

    args = parser.parse_args()
    argv = sys.argv[1:]

    if not args.queries:
        args.queries = QUERIES

    if 'all' in args.benchmarks:
        args.benchmarks = list(BENCHMARKS.keys())

    if out_to_json and args.json:
        i = argv.index('--json')
        del argv[i:i + 2]

    if out_to_html and args.html:
        i = argv.index('--html')
        del argv[i:i + 2]

    return args, argv
