"use strict";

const e = require("./querybuilder").default;

const queries = {
  user: () =>
    e.withParams(
      {
        id: e.uuid,
      },
      ($) =>
        e.select(e.User, (user) => ({
          id: true,
          name: true,
          image: true,
          latest_reviews: e.select(
            user["<author[IS default::Review]"],
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
              order: {
                expression: userReview.creation_time,
                direction: e.DESC,
              },
              limit: 10,
            })
          ),
          filter: e.eq(user.id, $.id),
        }))
    ),
  person: () =>
    e.withParams({ id: e.uuid }, ($) =>
      e.select(e.Person, (person) => ({
        id: true,
        full_name: true,
        image: true,
        bio: true,
        acted_in: e.select(person["<cast[IS default::Movie]"], (movie) => ({
          id: true,
          image: true,
          title: true,
          year: true,
          avg_rating: true,
          order: [
            { expression: movie.year, direction: e.ASC },
            { expression: movie.title, direction: e.ASC },
          ],
        })),
        directed: e.select(
          person["<directors[IS default::Movie]"],
          (movie) => ({
            id: true,
            image: true,
            title: true,
            year: true,
            avg_rating: true,
            order: [
              { expression: movie.year, direction: e.ASC },
              { expression: movie.title, direction: e.ASC },
            ],
          })
        ),
        filter: e.eq(person.id, $.id),
      }))
    ),
  movie: () =>
    e.withParams({ id: e.uuid }, ($) =>
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
          order: [
            { expression: director["@list_order"], empty: e.EMPTY_LAST },
            { expression: director.last_name },
          ],
        }),
        cast: (cast) => ({
          id: true,
          full_name: true,
          image: true,
          order: [
            { expression: cast["@list_order"], empty: e.EMPTY_LAST },
            { expression: cast.last_name },
          ],
        }),
        reviews: e.select(movie["<movie[IS default::Review]"], (review) => ({
          id: true,
          body: true,
          rating: true,
          author: {
            id: true,
            name: true,
            image: true,
          },
          order: { expression: review.creation_time, direction: e.DESC },
        })),
        filter: e.eq(movie.id, $.id),
      }))
    ),
  updateMovie: () =>
    e.withParams(
      {
        id: e.uuid,
        suffix: e.str,
      },
      ($) => {
        const selectedMovie = e.select(e.Movie, (movie) => ({
          filter: e.eq(movie.id, $.id),
        }));
        return e.select(
          selectedMovie.update({
            title: e.concat(
              e.concat(selectedMovie.title, e.str("---")),
              $.suffix
            ),
          }),
          {
            id: true,
            title: true,
          }
        );
      }
    ),
  insertUser: () =>
    e.withParams(
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
};
module.exports = queries;
