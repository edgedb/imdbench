import aiohttp


ASYNC = True


async def connect(ctx):
    conn = aiohttp.ClientSession()
    conn.post_local = lambda **kw: conn.post(
        f'http://{ctx.edgedb_graphql_host}:{ctx.edgedb_graphql_port}',
        **kw)
    return conn


async def close(ctx, conn):
    await conn.close()


async def load_ids(ctx, conn):
    async def extract_ids(typename):
        r = await conn.post_local(
            json={
                'query': '''
                    {
                      %s(first: %s) {
                        id
                      }
                    }
                ''' % (typename, ctx.number_of_ids)
            }
        )
        data = await r.json()
        return [o['id'] for o in data['data'][typename]]

    return dict(
        get_user=await extract_ids('User'),
        get_movie=await extract_ids('Movie'),
        get_person=await extract_ids('Person'),
    )


async def get_user(conn, id):
    r = await conn.post_local(
        json={
            'query': '''
                query user($id: ID) {
                  GraphQLUserDetails(filter: {id: {eq: $id}}) {
                    id
                    name
                    image
                    latest_reviews(
                      order: {creation_time: {dir: DESC}}, first: 3
                    ) {
                      id
                      body
                      rating
                      movie {
                        id
                        image
                        title
                        avg_rating
                      }
                    }
                  }
                }
            ''',
            'variables': {
                'id': id
            }
        }
    )
    return await r.read()


async def get_movie(conn, id):
    r = await conn.post_local(
        json={
            'query': '''
                query movie($id: ID) {
                  GraphQLMovieDetails(filter: {id: {eq: $id}}) {
                    id
                    image
                    title
                    year
                    description
                    directors {
                      id
                      full_name
                      image
                    }
                    cast {
                      id
                      full_name
                      image
                    }
                    avg_rating
                    reviews(order: {creation_time: {dir: DESC}}) {
                      id
                      body
                      rating
                      author {
                        id
                        name
                        image
                      }
                    }
                  }
                }
            ''',
            'variables': {
                'id': id
            }
        }
    )
    return await r.read()


async def get_person(conn, id):
    r = await conn.post_local(
        json={
            'query': '''
                query person($id: ID) {
                  GraphQLPersonDetails(filter: {id: {eq: $id}}) {
                    id
                    full_name
                    image
                    bio
                    acted_in(order: {year: {dir: ASC}, title: {dir: ASC}}) {
                      id
                      image
                      title
                      year
                      avg_rating
                    }
                    directed(order: {year: {dir: ASC}, title: {dir: ASC}}) {
                      id
                      image
                      title
                      year
                      avg_rating
                    }
                  }
                }
            ''',
            'variables': {
                'id': id
            }
        }
    )
    return await r.read()
