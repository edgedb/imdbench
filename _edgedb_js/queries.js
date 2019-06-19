"use strict";

const queries = {
  user: `
    SELECT User {
        id,
        name,
        image,
        latest_reviews := (
            WITH UserReviews := User.<author
            SELECT UserReviews {
                id,
                body,
                rating,
                movie: {
                    id,
                    image,
                    title,
                    avg_rating
                }
            }
            ORDER BY .creation_time DESC
            LIMIT 10
        )
    }
    FILTER .id = <uuid>$id
  `,
  person: `
    SELECT Person {
        id,
        full_name,
        image,
        bio,

        acted_in := (
            WITH M := Person.<cast
            SELECT M {
                id,
                image,
                title,
                year,
                avg_rating
            }
            ORDER BY .year ASC THEN .title ASC
        ),

        directed := (
            WITH M := Person.<directors
            SELECT M {
                id,
                image,
                title,
                year,
                avg_rating
            }
            ORDER BY .year ASC THEN .title ASC
        ),
    }
    FILTER .id = <uuid>$id
  `,
  movie: `
    SELECT Movie {
        id,
        image,
        title,
        year,
        description,
        avg_rating,

        directors: {
            id,
            full_name,
            image,
        }
        ORDER BY Movie.directors@list_order EMPTY LAST
            THEN Movie.directors.last_name,

        cast: {
            id,
            full_name,
            image,
        }
        ORDER BY Movie.cast@list_order EMPTY LAST
            THEN Movie.cast.last_name,

        reviews := (
            SELECT Movie.<movie {
                id,
                body,
                rating,
                author: {
                    id,
                    name,
                    image,
                }
            }
            ORDER BY .creation_time DESC
        ),
    }
    FILTER .id = <uuid>$id
  `
};
module.exports = queries;
