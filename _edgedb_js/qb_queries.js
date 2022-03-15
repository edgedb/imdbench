'use strict';

const {insertMoviePlus, insertUser} = require('./queries');

const e = require('./querybuilder').default;

const queries = {
  user: () =>
    e.params(
      {
        id: e.uuid,
      },
      ($) =>
        e.select(e.User, (user) => ({
          id: true,
          name: true,
          image: true,
          latest_reviews: e.select(
            user['<author[is Review]'],
            (userReview) => ({
              id: true,
              body: true,
              rating: true,
              movie: {
                id: true,
                image: true,
                title: true,
                avg_rating: true,
              },
              order_by: {
                expression: userReview.creation_time,
                direction: e.DESC,
              },
              limit: 10,
            })
          ),
          filter: e.op(user.id, '=', $.id),
        }))
    ),
  person: () =>
    e.params({id: e.uuid}, ($) =>
      e.select(e.Person, (person) => ({
        id: true,
        full_name: true,
        image: true,
        bio: true,
        acted_in: e.select(person['<cast[is Movie]'], (movie) => ({
          id: true,
          image: true,
          title: true,
          year: true,
          avg_rating: true,
          order_by: [
            {expression: movie.year, direction: e.ASC},
            {expression: movie.title, direction: e.ASC},
          ],
        })),
        directed: e.select(person['<directors[is Movie]'], (movie) => ({
          id: true,
          image: true,
          title: true,
          year: true,
          avg_rating: true,
          order_by: [
            {expression: movie.year, direction: e.ASC},
            {expression: movie.title, direction: e.ASC},
          ],
        })),
        filter: e.op(person.id, '=', $.id),
      }))
    ),
  movie: () =>
    e.params({id: e.uuid}, ($) =>
      e.select(e.Movie, (movie) => ({
        id: true,
        image: true,
        title: true,
        year: true,
        description: true,
        avg_rating: true,
        directors: (director) => ({
          id: true,
          full_name: true,
          image: true,
          order_by: [
            {expression: director['@list_order'], empty: e.EMPTY_LAST},
            {expression: director.last_name},
          ],
        }),
        cast: (cast) => ({
          id: true,
          full_name: true,
          image: true,
          order_by: [
            {expression: cast['@list_order'], empty: e.EMPTY_LAST},
            {expression: cast.last_name},
          ],
        }),
        reviews: e.select(movie['<movie[is Review]'], (review) => ({
          id: true,
          body: true,
          rating: true,
          author: {
            id: true,
            name: true,
            image: true,
          },
          order_by: {expression: review.creation_time, direction: e.DESC},
        })),
        filter: e.op(movie.id, '=', $.id),
      }))
    ),
  updateMovie: () =>
    e.params(
      {
        id: e.uuid,
        suffix: e.str,
      },
      ($) =>
        e.select(
          e.update(e.Movie, (movie) => ({
            filter: e.op(movie.id, '=', $.id),
            set: {
              title: e.op(e.op(movie.title, '++', '---'), '++', $.suffix),
            },
          })),
          () => ({
            id: true,
            title: true,
          })
        )
    ),
  insertUser: () =>
    e.params(
      {
        name: e.str,
        image: e.str,
      },
      ($) =>
        e.select(
          e.insert(e.User, {
            name: $.name,
            image: $.image,
          }),
          () => ({
            id: true,
            name: true,
            image: true,
          })
        )
    ),
  insertMovie: () =>
    e.params(
      {
        title: e.str,
        image: e.str,
        description: e.str,
        year: e.int64,
        d_id: e.uuid,
        cast: e.array(e.uuid),
      },
      ($) =>
        e.select(
          e.insert(e.Movie, {
            title: $.title,
            image: $.image,
            description: $.description,
            year: $.year,
            directors: e.select(e.Person, (person) => ({
              filter: e.op(person.id, '=', $.d_id),
            })),
            cast: e.select(e.Person, (person) => ({
              filter: e.op(person.id, 'in', e.array_unpack($.cast)),
            })),
          }),
          () => ({
            id: true,
            title: true,
            image: true,
            description: true,
            year: true,
            directors: (director) => ({
              id: true,
              full_name: true,
              image: true,
              order_by: director.last_name,
            }),
            cast: (cast) => ({
              id: true,
              full_name: true,
              image: true,
              order_by: cast.last_name,
            }),
          })
        )
    ),
  insertMoviePlus: () =>
    e.params(
      {
        title: e.str,
        image: e.str,
        description: e.str,
        year: e.int64,
        dfn: e.str,
        dln: e.str,
        dimg: e.str,
        cfn0: e.str,
        cln0: e.str,
        cimg0: e.str,
        cfn1: e.str,
        cln1: e.str,
        cimg1: e.str,
      },
      ($) =>
        e.select(
          e.insert(e.Movie, {
            title: $.title,
            image: $.image,
            description: $.description,
            year: $.year,
            directors: e.insert(e.Person, {
              first_name: $.dfn,
              last_name: $.dln,
              image: $.dimg,
            }),
            cast: e.set(
              e.insert(e.Person, {
                first_name: $.cfn0,
                last_name: $.cln0,
                image: $.cimg0,
              }),
              e.insert(e.Person, {
                first_name: $.cfn1,
                last_name: $.cln1,
                image: $.cimg1,
              })
            ),
          }),
          () => ({
            id: true,
            title: true,
            image: true,
            description: true,
            year: true,
            directors: (director) => ({
              id: true,
              full_name: true,
              image: true,
              order_by: director.last_name,
            }),
            cast: (cast) => ({
              id: true,
              full_name: true,
              image: true,
              order_by: cast.last_name,
            }),
          })
        )
    ),
};
module.exports = queries;
