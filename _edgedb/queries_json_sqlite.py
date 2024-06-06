#
# Copyright (c) 2019 MagicStack Inc.
# All rights reserved.
#
# See LICENSE for details.
##


import random
import pickle

from . import queries


INSERT_PREFIX = 'insert_test__'

import sys

sys.path.append("../edgedb/")
import os

from edb.tools.experimental_interpreter import new_interpreter
from edb.tools.experimental_interpreter.sqlite import sqlite_adapter

from .loaddata_nobulk_sqlite import TEST_SQLITE_FILE_NAME, IMDBENCH_SDL_FILEPATH

def connect(ctx):
    with open(IMDBENCH_SDL_FILEPATH, "r") as f:
        sdl_defs = f.read()
        return new_interpreter.EdgeQLInterpreter(sdl_defs, TEST_SQLITE_FILE_NAME)


def close(ctx, conn):
    pass


def load_ids(ctx, edgeql_interpreter : new_interpreter.EdgeQLInterpreter):
    print(ctx)
    if not os.path.exists("edgeql_ids.pickle"):
        raise ValueError("Please run 'python queries_json_sqlite.py preload_ids' first ")
    with open("edgeql_ids.pickle", "rb") as f:
        d = pickle.load(f)
        return d

def preload_ids(ctx, edgeql_interpreter : new_interpreter.EdgeQLInterpreter):
    d = edgeql_interpreter.query_single_json('''
        WITH
            U := (select User) {id, r := random()},
            M := (select Movie) {id, r := random()},
            P := (select Person) {id, r := random()}
        SELECT (
            users := array_agg((SELECT U ORDER BY U.r LIMIT <int64>$lim).id),
            movies := array_agg((SELECT M ORDER BY M.r LIMIT <int64>$lim).id),
            people := array_agg((SELECT P ORDER BY P.r LIMIT <int64>$lim).id),
        );
    ''', lim=ctx.number_of_ids)


    movies = list(d['movies'])
    people = list(d['people'])

    return_data = dict(
        get_user=list(d['users']),
        get_movie=movies,
        get_person=people,
        # re-use user IDs for update tests
        update_movie=movies[:],
        # generate as many insert stubs as "concurrency" to
        # accommodate concurrent inserts
        insert_user=[INSERT_PREFIX] * ctx.concurrency,
        insert_movie=[{
            'prefix': INSERT_PREFIX,
            'people': people[:4],
        }] * ctx.concurrency,
        insert_movie_plus=[INSERT_PREFIX] * ctx.concurrency,
    )
    with open("edgeql_ids.pickle", "wb") as f:
        pickle.dump(return_data, f)


def get_user(conn, id):
    return conn.query_single_json(queries.GET_USER, id=id)


def get_movie(conn, id):
    return conn.query_single_json(queries.GET_MOVIE, id=id)


def get_person(conn, id):
    return conn.query_single_json(queries.GET_PERSON, id=id)


def update_movie(conn, id):
    return conn.query_single_json(
        queries.UPDATE_MOVIE, id=id, suffix=str(id)[:8])


def insert_user(conn, val):
    num = random.randrange(1_000_000)
    return conn.query_single_json(
        queries.INSERT_USER, name=f'{val}{num}', image=f'image_{val}{num}')


def insert_movie(conn, val):
    num = random.randrange(1_000_000)
    return conn.query_single_json(
        queries.INSERT_MOVIE,
        title=f'{val["prefix"]}{num}',
        image=f'{val["prefix"]}image{num}.jpeg',
        description=f'{val["prefix"]}description{num}',
        year=num,
        d_id=val["people"][0],
        cast=val["people"][1:4],
    )


def insert_movie_plus(conn, val):
    num = random.randrange(1_000_000)
    return conn.query_single_json(
        queries.INSERT_MOVIE_PLUS,
        title=f'{val}{num}',
        image=f'{val}image{num}.jpeg',
        description=f'{val}description{num}',
        year=num,
        dfn=f'{val}Alice',
        dln=f'{val}Director',
        dimg=f'{val}image{num}.jpeg',
        cfn0=f'{val}Billie',
        cln0=f'{val}Actor',
        cimg0=f'{val}image{num+1}.jpeg',
        cfn1=f'{val}Cameron',
        cln1=f'{val}Actor',
        cimg1=f'{val}image{num+2}.jpeg',
    )


def setup(ctx, conn, queryname):
    if queryname == 'update_movie':
        conn.query_json('''
            update Movie
            filter contains(.title, '---')
            set {
                title := str_split(.title, '---')[0]
            };
        ''')
    elif queryname == 'insert_user':
        conn.query_json('''
            delete User
            filter .name LIKE <str>$prefix
        ''', prefix=f'{INSERT_PREFIX}%')
    elif queryname == 'insert_movie':
        conn.query_json('''
            delete Movie
            filter .image LIKE <str>$prefix
        ''', prefix=f'{INSERT_PREFIX}image%')
    elif queryname == 'insert_movie_plus':
        conn.query_json('''
            delete Movie
            filter .image LIKE <str>$prefix
        ''', prefix=f'{INSERT_PREFIX}image%')
        conn.query_json('''
            delete Person
            filter .image LIKE <str>$prefix
        ''', prefix=f'{INSERT_PREFIX}image%')


def cleanup(ctx, conn, queryname):
    print("Time [if logging enabled]")
    # print(sqlite_adapter.cumulative_time)

    if queryname in {'update_movie', 'insert_user', 'insert_movie',
                     'insert_movie_plus'}:
        # The clean up is the same as setup for mutation benchmarks
        setup(ctx, conn, queryname)


if __name__ == "__main__":
    if sys.argv[1] == 'preload_ids':
        edgeql_interpreter = connect(None)
        class Ctx:
            number_of_ids = 250
            concurrency = 1
        preload_ids(Ctx(), edgeql_interpreter)