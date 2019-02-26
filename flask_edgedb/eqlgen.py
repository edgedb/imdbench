def generate_eql(datagen):
    output = ''
    users = datagen.mdb['users']
    reviews = datagen.mdb['reviews']
    movies = datagen.mdb['movies']
    people = datagen.mdb['people']
    # images happen to be unique, so I'll use that instead of nid

    for p in people.values():
        output += f'''
INSERT Person {{
    first_name := {p.first_name!r},
    middle_name := {p.middle_name!r},
    last_name := {p.last_name!r},
    image := {p.image!r},
    bio := {p.bio!r},
}};
        '''

    for u in users.values():
        output += f'''
INSERT User {{
    name := {u.name!r},
    image := {u.image!r},
}};
        '''

    for m in movies.values():
        directors = nid2image(people, m.directors)
        cast = nid2image(people, m.cast)

        output += f'''
INSERT Movie {{
    title := {m.title!r},
    description := {m.description!r},
    year := {m.year},
    image := {m.image!r},

    directors := (
        {_generate_for_person_eql(directors)}
    ),
    cast := (
        {
            _generate_for_person_eql(cast)
            if m.nid % 10 else
            _generate_unordered_person_eql(cast)
        }
    ),
}};
        '''

    for r in reviews.values():
        uimage = users[r.author_nid].image
        mimage = movies[r.movie_nid].image
        output += f'''
INSERT Review {{
    body := {r.body!r},
    rating := {r.rating!r},
    author := (SELECT User FILTER .image = {uimage!r}),
    movie := (SELECT Movie FILTER .image = {mimage!r}),
    creation_time := <datetime>{r.creation_time.isoformat()!r},
}};
        '''

    return output


JOIN = ',\n            '


def _generate_for_person_eql(images, forvar='X'):
    plist = []
    for i, img in enumerate(images):
        plist.append(f'({i}, {img!r})')

    return f'''
        FOR {forvar} in {{
            {JOIN.join(plist)}
        }} UNION (
            SELECT Person {{@list_order := {forvar}.0}}
            FILTER .image = {forvar}.1
        )
    '''


def _generate_unordered_person_eql(images):
    return f'''
        SELECT Person
        FILTER .image IN {{
            {JOIN.join(repr(img) for img in images)}
        }}
    '''


def nid2image(items, nids):
    result = []
    for nid in nids:
        result.append(items[nid].image)

    return result
