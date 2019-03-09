import argparse
import collections
import datetime
import json
import progress.bar
import webapp


def bar(label, total):
    return progress.bar.Bar(label[:32].ljust(32), max=total)


def bulk_insert(label, data, into):
    label = f"Creating {len(data)} {label}"
    pbar = bar(label, len(data))

    while data:
        chunk = data[:1000]
        data = data[1000:]
        db.session.bulk_insert_mappings(into, chunk)
        db.session.commit()
        pbar.next(len(chunk))
    pbar.finish()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Load a specific fixture, old data will be purged.')
    parser.add_argument('filename', type=str,
                        help='The JSON dataset file')

    args = parser.parse_args()

    # get all the tables (useful for bulk operations)
    db = webapp.app.db
    User_t = db.User.__table__
    Directors_t = db.Directors.__table__
    Cast_t = db.Cast.__table__
    Person_t = db.Person.__table__
    Movie_t = db.Movie.__table__
    Review_t = db.Review.__table__

    # first clear all the existing data
    print(f'purging existing data...')
    db.Directors.query.delete(False)
    db.Cast.query.delete(False)
    db.Review.query.delete(False)
    db.Movie.query.delete(False)
    db.Person.query.delete(False)
    db.User.query.delete(False)
    db.session.commit()

    # read the JSON data
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

    # bulk create all the users
    bulk_insert('users', data['user'], db.User)

    # bulk create all the people
    bulk_insert('people', data['person'], db.Person)

    # bulk create all the movies
    bulk_insert('movies', data['movie'], db.Movie)

    # bulk create all the reviews
    bulk_insert('reviews', data['review'], db.Review)

    # bulk create all the directors
    bulk_insert('directors', data['directors'], db.Directors)

    # bulk create all the cast
    bulk_insert('cast', data['cast'], db.Cast)
