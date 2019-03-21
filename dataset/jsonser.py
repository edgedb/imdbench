#
# Copyright (c) 2019 MagicStack Inc.
# All rights reserved.
#
# See LICENSE for details.
##


import json
import pathlib

import dataset


def to_json(mdb: dict, appname='webapp'):
    output = []

    users = mdb['users']
    reviews = mdb['reviews']
    movies = mdb['movies']
    people = mdb['people']
    # images happen to be unique, so I'll use that instead of nid

    for p in people.values():
        output.append({
            'model': f'{appname}.person',
            # just re-use the nid as id
            'pk': p.nid,
            'fields': {
                'first_name': p.first_name,
                'middle_name': p.middle_name,
                'last_name': p.last_name,
                'image': p.image,
                'bio': p.bio,
            }
        })

    for u in users.values():
        output.append({
            'model': f'{appname}.user',
            'pk': u.nid,
            'fields': {
                'name': u.name,
                'image': u.image,
            }
        })

    for m in movies.values():
        output.append({
            'model': f'{appname}.movie',
            'pk': m.nid,
            'fields': {
                'title': m.title,
                'description': m.description,
                'year': m.year,
                'image': m.image,
            }
        })

        # the cast and directors need their own intermediate objects
        for i, nid in enumerate(m.directors):
            output.append({
                'model': f'{appname}.directors',
                # don't care about the id for this
                'fields': {
                    'list_order': i,
                    'person_id': nid,
                    'movie_id': m.nid,
                }
            })

        for i, nid in enumerate(m.cast):
            output.append({
                'model': f'{appname}.cast',
                # don't care about the id for this
                'fields': {
                    'list_order': i,
                    'person_id': nid,
                    'movie_id': m.nid,
                }
            })
            # only some movies will order cast
            if m.nid % 10:
                output[-1]['list_order'] = i

    for r in reviews.values():
        output.append({
            'model': f'{appname}.review',
            'pk': r.nid,
            'fields': {
                'body': r.body,
                'rating': r.rating,
                'author_id': r.author_nid,
                'movie_id': r.movie_nid,
                'creation_time': f'{r.creation_time.isoformat()}+00:00',
            }
        })

    return json.dumps(output)


def gen_json():
    build_path = pathlib.Path(__file__).resolve().parent / 'build'
    mdb = dataset.load()
    jd = to_json(mdb)
    with open(build_path / 'dataset.json', 'wt') as f:
        f.write(jd)


if __name__ == '__main__':
    gen_json()
