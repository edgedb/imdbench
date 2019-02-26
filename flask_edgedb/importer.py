import edgedb
import progress.bar


def bar(label, it):
    return progress.bar.Bar(label).iter(it)


def import_data(datagen):
    users = datagen.mdb['users']
    reviews = datagen.mdb['reviews']
    movies = datagen.mdb['movies']
    people = datagen.mdb['people']

    # assume that the DB and the schema have been initialized separately
    con = edgedb.connect(user='edgedb', database='edgedb_bench')

    for p in bar('People', people.values()):
        con.fetch(
            r'''
            INSERT Person {
                first_name := <str>$first_name,
                middle_name := <str>$middle_name,
                last_name := <str>$last_name,
                image := <str>$image,
                bio := <str>$bio,
            };
            ''',
            first_name=p.first_name,
            middle_name=p.middle_name,
            last_name=p.last_name,
            image=p.image,
            bio=p.bio,
        )

    for u in bar('Users', users.values()):
        con.fetch(
            r'''
            INSERT User {
                name := <str>$name,
                image := <str>$image,
            };
            ''',
            name=u.name,
            image=u.image,
        )

    ord_eql = r'''
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

    unord_eql = r'''
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

    for m in bar('Movies', movies.values()):
        directors = nid2image(people, m.directors)
        cast = nid2image(people, m.cast)

        if m.nid % 10:
            eql = ord_eql
        else:
            eql = unord_eql

        try:
            con.fetch(
                eql,
                title=m.title,
                description=m.description,
                year=m.year,
                image=m.image,
                directors=directors,
                cast=cast,
            )
        except:
            print(f'''
                {eql}
                {m.title}
                {m.description}
                {m.year}
                {m.image}
                {directors}
                {cast}
            ''')
            raise

    for r in bar('Reviews', reviews.values()):
        uimage = users[r.author_nid].image
        mimage = movies[r.movie_nid].image

        con.fetch(
            r'''
            INSERT Review {
                body := <str>$body,
                rating := <int64>$rating,
                author := (SELECT User FILTER .image = <str>$uimage),
                movie := (SELECT Movie FILTER .image = <str>$mimage),
                creation_time := <datetime>$creation_time,
            };
            ''',
            body=r.body,
            rating=r.rating,
            uimage=uimage,
            mimage=mimage,
            creation_time=r.creation_time,
        )


def nid2image(items, nids):
    result = []
    for nid in nids:
        result.append(items[nid].image)

    return result
