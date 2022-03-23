#
# Copyright (c) 2021 MagicStack Inc.
# All rights reserved.
#
# See LICENSE for details.
##


import itertools
import json
import pathlib


# Use a globally unique numeric ID, because that affords the most
# compatibility with the different ORMs that we need to import data
# into.
gid = 0
gid_map = {'user': {}, 'person': {}, 'movie': {}, 'review': {}}


def new_id(oldid, cat):
    global gid
    global gid_map

    gid += 1
    gid_map[cat][oldid] = gid
    return gid


def get_id(oldid, cat):
    global gid_map
    return gid_map[cat][oldid]


def clean(data: dict):
    directors = data.pop('director')
    people = data['person']

    # first record all directors
    data['person'] = directors

    # now add the rest of "person" records from the id > directors
    lastid = directors[-1]['id']

    data['person'].extend(
        p for p in people if p['id'] > lastid
    )

    # Use '' instead of None for 'middle_name'
    for rec in data['person']:
        rec['middle_name'] = rec['middle_name'] or ''

    # Check that we generated unique image names as we use that
    # fact when importing data into EdgeDB.
    imgs = set()
    for i, rec in enumerate(itertools.chain(
            data['user'], data['person'], data['movie'])):
        if rec['image'] in imgs:
            rec['image'] = f"{rec['image'].split('.')[0]}-{i}.jpeg"

        imgs.add(rec['image'])

    return data


def normalize(data: dict, appname='webapp'):
    output = []

    users = data['user']
    reviews = data['review']
    movies = data['movie']
    people = data['person']

    for p in people:
        p['id'] = new_id(p['id'], 'person')
        output.append({
            'model': f'{appname}.person',
            'fields': p
        })

    for u in users:
        u['id'] = new_id(u['id'], 'user')
        output.append({
            'model': f'{appname}.user',
            'fields': u
        })

    for m in movies:
        dirs = m.pop('directors')
        cast = m.pop('cast')
        origid = m['id']  # used later for deciding whether to have list_order

        m['id'] = new_id(m['id'], 'movie')
        output.append({
            'model': f'{appname}.movie',
            'fields': m
        })

        # the cast and directors need their own intermediate objects
        for i, nid in enumerate(dirs):
            output.append({
                'model': f'{appname}.directors',
                # don't care about the id for this
                'fields': {
                    'list_order': i,
                    'person_id': get_id(nid, 'person'),
                    'movie_id': m['id'],
                }
            })

        for i, nid in enumerate(cast):
            output.append({
                'model': f'{appname}.cast',
                # don't care about the id for this
                'fields': {
                    # only some movies will order cast
                    'list_order': i if origid % 10 else None,
                    'person_id': get_id(nid, 'person'),
                    'movie_id': m['id'],
                }
            })

    for i, r in enumerate(reviews):
        r['author_id'] = get_id(r.pop('author'), 'user')

        # The first reviews just get linked to each movie in turn to
        # avoid having a Movie without reviews. This is to simplify
        # the average score queries for all the versions of the
        # benchmarks. It's a smaller change to adjust the dataset than
        # it is to adjust all the benchmarks.
        r_id = r.pop('movie')
        if i < len(movies):
            r['movie_id'] = get_id(i, 'movie')
        else:
            r['movie_id'] = get_id(r_id, 'movie')

        r['id'] = new_id(r['id'], 'review')
        output.append({
            'model': f'{appname}.review',
            'fields': r
        })

    return output


def clean_json():
    build_path = pathlib.Path(__file__).resolve().parent / 'build'
    with open(build_path / 'protodataset.json', 'rt') as f:
        data = json.load(f)

    with open(build_path / 'edbdataset.json', 'wt') as f:
        data = clean(data)
        f.write(json.dumps(data))

    with open(build_path / 'dataset.json', 'wt') as f:
        data = normalize(data)
        f.write(json.dumps(data))


if __name__ == '__main__':
    clean_json()
