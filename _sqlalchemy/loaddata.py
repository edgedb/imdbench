import argparse
import collections
import datetime
import json
import progress.bar

import sqlalchemy as sa
import sqlalchemy.orm as orm

import _sqlalchemy.models as m


def bar(label, total):
    return progress.bar.Bar(label[:32].ljust(32), max=total)


def bulk_insert(db, label, data, into):
    label = f"Creating {len(data)} {label}"
    pbar = bar(label, len(data))

    while data:
        chunk = data[:1000]
        data = data[1000:]
        db.bulk_insert_mappings(into, chunk)
        db.commit()
        pbar.next(len(chunk))
    pbar.finish()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Load a specific fixture, old data will be purged.')
    parser.add_argument('filename', type=str,
                        help='The JSON dataset file')

    args = parser.parse_args()

    engine = sa.create_engine(
        'postgresql://sqlalch_bench:edgedbbenchmark@localhost/sqlalch_bench')

    session_factory = orm.sessionmaker(bind=engine)
    Session = orm.scoped_session(session_factory)
    db = Session()

    # first clear all the existing data
    print(f'purging existing data...')

    db.query(m.Directors).delete()
    db.query(m.Cast).delete()
    db.query(m.Review).delete()
    db.query(m.Movie).delete()
    db.query(m.Person).delete()
    db.query(m.User).delete()
    db.commit()

    # read the JSON data
    print('loading JSON... ', end='', flush=True)
    with open(args.filename, 'rt') as f:
        records = json.load(f)
    data = collections.defaultdict(list)
    for rec in records:
        rtype = rec['model'].split('.')[-1]
        datum = rec['fields']
        if 'pk' in rec:
            datum['id'] = rec['pk']
        # convert datetime
        if rtype == 'review':
            datum['creation_time'] = datetime.datetime.fromisoformat(
                datum['creation_time'])

        data[rtype].append(datum)
    print('done')

    # bulk create all the users
    bulk_insert(db, 'users', data['user'], m.User)

    # bulk create all the people
    bulk_insert(db, 'people', data['person'], m.Person)

    # bulk create all the movies
    bulk_insert(db, 'movies', data['movie'], m.Movie)

    # bulk create all the reviews
    bulk_insert(db, 'reviews', data['review'], m.Review)

    # bulk create all the directors
    bulk_insert(db, 'directors', data['directors'], m.Directors)

    # bulk create all the cast
    bulk_insert(db, 'cast', data['cast'], m.Cast)
