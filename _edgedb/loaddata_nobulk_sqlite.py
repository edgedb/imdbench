#
# Copyright (c) 2019 MagicStack Inc.
# All rights reserved.
#
# See LICENSE for details.
##

import sys

sys.path.append("../edgedb/")

import argparse
import asyncio
import edgedb
import json
import uvloop
from edb.tools.experimental_interpreter import new_interpreter
from edb.tools.experimental_interpreter.sqlite import sqlite_adapter
import os
from tqdm import tqdm
import random
TEST_SQLITE_FILE_NAME="imdb_test_1.sqlite"


def import_data(data: dict):

    new_interpreter.interpreter_parser_init()
    if TEST_SQLITE_FILE_NAME:
        if os.path.exists(TEST_SQLITE_FILE_NAME):
            os.remove(TEST_SQLITE_FILE_NAME)

    with open("imdbench/dbschema/default_sqlite.esdl", "r") as f:
        dbschema, db = new_interpreter.dbschema_and_db_with_initial_schema_and_queries(f.read(), "", TEST_SQLITE_FILE_NAME)

    assert isinstance(db.storage, sqlite_adapter.SQLiteEdgeDatabaseStorageProvider)

    users = data['user']
    reviews = data['review']
    movies = data['movie']
    people = data['person']

    id2image_maps = {}
    for cat in ['user', 'person', 'movie']:
        id2image_maps[cat] = {r['id']: r['image'] for r in data[cat]}

    ppl_insert_query = r'''
        INSERT Person {
            first_name := <str>$first_name,
            middle_name := <str>$middle_name,
            last_name := <str>$last_name,
            image := <str>$image,
            bio := <str>$bio,
        };
    '''

    people_data = [
        (
            (ppl_insert_query,),
            dict(
                first_name=p['first_name'],
                middle_name=p['middle_name'],
                last_name=p['last_name'],
                image=p['image'],
                bio=p['bio']
            )
        ) for p in people
    ]

    users_insert_query = r'''
        INSERT User {
            name := <str>$name,
            image := <str>$image,
        };
    '''

    users_data = [
        (
            (users_insert_query,),
            dict(
                name=u['name'],
                image=u['image'],
            )
        ) for u in users
    ]

    movies_ord_insert_query = r'''
        INSERT Movie {
            title := <str>$title,
            description := <str>$description,
            year := <int64>$year,
            image := <str>$image,

            directors := (
                FOR X IN {
                    enumerate(array_unpack(
                        <array<str>>$directors
                    ))
                }
                UNION (
                    SELECT Person {@list_order := X.0}
                    FILTER .image = X.1
                )
            ),
            cast := (
                FOR X IN {
                    enumerate(array_unpack(
                        <array<str>>$cast
                    ))
                }
                UNION (
                    SELECT Person {@list_order := X.0}
                    FILTER .image = X.1
                )
            )
        };
    '''

    movies_unord_insert_query = r'''
        INSERT Movie {
            title := <str>$title,
            description := <str>$description,
            year := <int64>$year,
            image := <str>$image,

            directors := (
                FOR X IN {
                    enumerate(array_unpack(
                        <array<str>>$directors
                    ))
                }
                UNION (
                    SELECT Person {@list_order := X.0}
                    FILTER .image = X.1
                )
            ),
            cast := (
                SELECT Person
                FILTER .image IN array_unpack(
                    <array<str>>$cast
                )
            )
        };
    '''

    movies_data = [
        (
            (
                (movies_ord_insert_query
                    if m['id'] % 10 else movies_unord_insert_query),
            ),
            dict(
                title=m['title'],
                description=m['description'],
                year=m['year'],
                image=m['image'],
                directors=id2image(id2image_maps['person'], m['directors']),
                cast=id2image(id2image_maps['person'], m['cast']),
            )
        ) for m in movies
    ]

    reviews_insert_query = r'''
        INSERT Review {
            body := <str>$body,
            rating := <int64>$rating,
            author := (SELECT User FILTER .image = <str>$uimage LIMIT 1),
            movie := (SELECT Movie FILTER .image = <str>$mimage LIMIT 1),
            creation_time := <cal::local_datetime><str>$creation_time,
        };
    '''

    reviews_data = [
        (
            (reviews_insert_query,),
            dict(
                body=r['body'],
                rating=r['rating'],
                uimage=id2image_maps['user'][r['author']],
                mimage=id2image_maps['movie'][r['movie']],
                creation_time=r['creation_time'][:-6],
            )
        ) for r in reviews
    ]

    # random.shuffle(all_data)

    def go_data(all_data):
        db.storage.pause_disk_commit()
        for i in tqdm(range(0, len(all_data), 1)):
            (query, param) = all_data[i]
            query = query[0]
            assert isinstance(query, str)
            new_interpreter.run_single_str((dbschema, db), query, param)
        db.storage.resume_disk_commit()

    print(f"Number of people: {len(people_data)}")
    print(f"Number of users: {len(users_data)}")
    print(f"Number of movies: {len(movies_data)}")
    print(f"Number of reviews: {len(reviews_data)}")

    go_data(people_data)
    go_data(users_data)
    go_data(movies_data)
    go_data(reviews_data)



def id2image(idmap, ids):
    return [idmap[val] for val in ids]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Load EdgeDB dataset.')
    parser.add_argument('filename', type=str,
                        help='The JSON dataset file')
    args = parser.parse_args()

    with open(args.filename, 'rt') as f:
        records = json.load(f)

    import_data(records)
