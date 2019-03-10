import argparse
import pathlib

import edgedb
import pymongo


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Generate ID files for benchmarks.')
    parser.add_argument('pickle', type=str,
                        help='the dataset pickle file')

    args = parser.parse_args()

    mdb = pathlib.Path(args.pickle).resolve()
    if not mdb.exists():
        print(f'error: could not find {mdb}')
        exit(1)

    base_path = pathlib.Path(__file__).resolve().parent / 'build'
    tail = mdb.name.split('_', 1)[1].split('.')[0]

    # extract the UUIDs from EdgeDB
    con = edgedb.connect(user='edgedb', database='edgedb_bench')

    with open(base_path / f'edgedb_user_ids.txt', 'wt') as f:
        for res in con.fetch('SELECT User.id'):
            f.write(f'{res}\n')

    with open(base_path / f'edgedb_person_ids.txt', 'wt') as f:
        for res in con.fetch('SELECT Person.id'):
            f.write(f'{res}\n')

    with open(base_path / f'edgedb_movie_ids.txt', 'wt') as f:
        for res in con.fetch('SELECT Movie.id'):
            f.write(f'{res}\n')

    con.close()

    client = pymongo.MongoClient()
    mongodb = client.movies

    with open(base_path / f'mongo_user_ids.txt', 'wt') as f:
        for res in mongodb.users.find({}, {'_id': 1}):
            f.write(f'{res["_id"]}\n')

    with open(base_path / f'mongo_person_ids.txt', 'wt') as f:
        for res in mongodb.people.find({}, {'_id': 1}):
            f.write(f'{res["_id"]}\n')

    with open(base_path / f'mongo_movie_ids.txt', 'wt') as f:
        for res in mongodb.movies.find({}, {'_id': 1}):
            f.write(f'{res["_id"]}\n')
