import argparse
import collections
import datetime
import json
import sqlalchemy as sa
import webapp


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
    print(f"Creating {len(data['user'])} users...")
    db.session.bulk_insert_mappings(db.User, data['user'])
    db.session.commit()

    # bulk create all the people
    print(f"Creating {len(data['person'])} people...")
    db.session.bulk_insert_mappings(db.Person, data['person'])
    db.session.commit()

    # bulk create all the movies
    print(f"Creating {len(data['movie'])} movies...")
    db.session.bulk_insert_mappings(db.Movie, data['movie'])
    db.session.commit()

    # bulk create all the reviews
    print(f"Creating {len(data['review'])} reviews...")
    db.session.bulk_insert_mappings(db.Review, data['review'])
    db.session.commit()

    # bulk create all the directors
    print(f"Creating {len(data['directors'])} directors...")
    db.session.bulk_insert_mappings(db.Directors, data['directors'])
    db.session.commit()

    # bulk create all the cast
    print(f"Creating {len(data['cast'])} cast...")
    db.session.bulk_insert_mappings(db.Cast, data['cast'])
    db.session.commit()
