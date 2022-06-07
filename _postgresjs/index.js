/* eslint max-len: 0 */

const postgres = require('postgres')

module.exports = function(options) {
  const concurrency = options.max
  const INSERT_PREFIX = 'insert_test__'
  const sql = postgres({
    fetch_types: false,
    user: 'postgres_bench',
    host: 'localhost',
    database: 'postgres_bench',
    password: 'edgedbbenchmark',
    port: 15432,
    ...(options || {})
  })

  const queries = {
    get_user,
    get_person,
    get_movie,
    update_movie,
    insert_user,
    insert_movie,
    insert_movie_plus
  }

  const api = {
    benchQuery: (name, id) => queries[name](id),
    connect: () => sql`select 1`,
    getConnection: () => api,
    getIDs,
    setup,
    cleanup
  }

  return api

  async function get_user(id) {
    const [user] = await sql`
      select
        u.id,
        u.name,
        u.image,
        json_agg(q) as latest_reviews
      from users u, lateral (
        select
          r.id as review_id,
          r.body as review_body,
          r.rating as review_rating,
          json_build_object(
            'id', m.id,
            'image', m.image,
            'title', m.title,
            'avg_rating', m.avg_rating::float
          ) as movie
        from reviews as r
        inner join movies as m on (r.movie_id = m.id)
        where r.author_id = u.id
        order by r.creation_time desc
        limit 10
      ) as q
      where u.id = ${ id }
      group by u.id
    `

    return user
  }

  async function get_movie(id) {
    const [x] = await sql`
      select
        m.id,
        m.image,
        m.title,
        m.year,
        m.description,
        m.avg_rating::float,
        (
          select
            json_agg(q)
          from (
            select p.id, p.full_name, p.image
            from directors
            join persons p on (directors.person_id = p.id)
            where directors.movie_id = m.id
            order by directors.list_order nulls last, p.last_name
          ) q
        ) directors,
        (
          select
            json_agg(q)
          from (
            select p.id, p.full_name, p.image
            from actors
            join persons p on actors.person_id = p.id
            where actors.movie_id = m.id
            order by actors.list_order nulls last, p.last_name
          ) q
        ) actors,
        (
          select
            json_agg(q)
          from (
            select r.id, r.body, r.rating,
              json_build_object(
                'id', a.id,
                'name', a.name,
                'image', a.image
              ) author
            from reviews r
            join users a on r.author_id = a.id
            where r.movie_id = m.id
            order by r.creation_time desc
          ) q
        ) reviews
      from movies m
      where id = ${ id }
    `

    return x
  }

  async function insert_movie(val) {
    const num = Math.floor(Math.random() * 1000000)
    const [user] = await sql`
      with m as (
        insert into movies (title, image, description, year)
        values (
          ${ val.prefix + num },
          ${ val.prefix + 'image' + num + '.jpeg' },
          ${ val.prefix + 'description' + num },
          ${ num }
        )
        returning id, title, image, description, year
      ), d as (
        select
          id,
          p.full_name,
          image
        from persons p
        where id = ${ val.people[0] }
      ), c as (
        select
          id,
          p.full_name,
          image
        from persons p
        where id in (${ val.people[1] }, ${ val.people[1] }, ${ val.people[1] })
      ), dl as (
        insert into directors (person_id, movie_id)
        (select d.id, m.id from m, d)
      ), cl as (
        insert into actors (person_id, movie_id)
        (select c.id, m.id from m, c)
      )
      select
        m.id,
        m.image,
        m.title,
        m.year,
        m.description,
        (
          select
            json_agg(q)
          from (
            select id, full_name, image
            from d
          ) q
        ) directors,
        (
          select
            json_agg(q)
          from (
            select id, full_name, image
            from c
          ) q
        ) actors
      from m
    `

    return user
  }

  async function update_movie() {
    throw new Error('not implemented')
  }

  async function insert_user() {
    throw new Error('not implemented')
  }

  async function get_person() {
    throw new Error('not implemented')
  }

  async function insert_movie_plus() {
    throw new Error('not implemented')
  }

  async function getIDs() {
    const ids = await Promise.all([
      sql`select id from users order by random()`,
      sql`select id from persons order by random()`,
      sql`select id from movies order by random()`
    ])

    const people = ids[1].map(x => x.id)

    return {
      get_user: ids[0].map(x => x.id),
      get_person: people,
      get_movie: ids[2].map(x => x.id),
      update_movie: ids[2].map(x => x.id),
      insert_user: Array(concurrency).fill(INSERT_PREFIX),
      insert_movie: Array(concurrency).fill({ prefix: INSERT_PREFIX, people: people.slice(0, 4) }),
      insert_movie_plus: Array(concurrency).fill(INSERT_PREFIX)
    }
  }

  async function setup(query) {
    return query === 'update_movie'
      ? sql`update movies set title = split_part(movies.title, '---', 1) where movies.title like '%---%'`
      : query === 'insert_user'
      ? sql`delete from users where users.name like ${ INSERT_PREFIX + '%' }`
      : query === 'insert_movie' || query === 'insert_movie_plus' && Promise.all([
        sql`delete from directors as d using movies as m where d.movie_id = m.id and m.image like ${ INSERT_PREFIX + '%' }`,
        sql`delete from actors as a using movies as m where a.movie_id = m.id and m.image like ${ INSERT_PREFIX + '%' }`,
        sql`delete from movies where image like ${ INSERT_PREFIX + '%' }`,
        sql`delete from persons where image like ${ INSERT_PREFIX + '%' }`
      ])
  }

  async function cleanup(query) {
    if (['update_movie', 'insert_user', 'insert_movie', 'insert_movie_plus'].indexOf(query) >= 0)
      return setup(query)
  }

}
