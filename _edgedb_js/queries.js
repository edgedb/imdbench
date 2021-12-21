"use strict";

const queries = {
  user: `
    SELECT User {
        id,
        name,
        image,
        latest_reviews := (
            WITH UserReviews := User.<author[IS Review]
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
            WITH M := Person.<cast[IS Movie]
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
            WITH M := Person.<directors[IS Movie]
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
            SELECT Movie.<movie[IS Review] {
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
  `,
  updateMovie: `
    SELECT (
        UPDATE Movie
        FILTER .id = <uuid>$id
        SET {
            title := .title ++ '---' ++ <str>$suffix
        }
    ) {
        id,
        title
    }
  `,
  insertUser: `
      SELECT (
          INSERT User {
              name := <str>$name,
              image := <str>$image,
          }
      ) {
          id,
          name,
          image,
      }
  `,
  insertMovie: `
      SELECT (
          INSERT Movie {
              title := <str>$title,
              image := <str>$image,
              description := <str>$description,
              year := <int64>$year,
              directors := (
                  SELECT Person
                  FILTER .id = (<uuid>$d_id)
              ),
              cast := (
                  SELECT Person
                  FILTER .id IN {<uuid>$c_id0, <uuid>$c_id1, <uuid>$c_id2}
              ),
          }
      ) {
          id,
          title,
          image,
          description,
          year,
          directors: {
              id,
              full_name,
              image,
          }
          ORDER BY .last_name,

          cast: {
              id,
              full_name,
              image,
          }
          ORDER BY .last_name,
      }
  `,
  insertMoviePlus: `
      SELECT (
          INSERT Movie {
              title := <str>$title,
              image := <str>$image,
              description := <str>$description,
              year := <int64>$year,
              directors := (
                  INSERT Person {
                      first_name := <str>$dfn,
                      last_name := <str>$dln,
                      image := <str>$dimg,
                  }
              ),
              cast := {(
                  INSERT Person {
                      first_name := <str>$cfn0,
                      last_name := <str>$cln0,
                      image := <str>$cimg0,
                  }
              ), (
                  INSERT Person {
                      first_name := <str>$cfn1,
                      last_name := <str>$cln1,
                      image := <str>$cimg1,
                  }
              )},
          }
      ) {
          id,
          title,
          image,
          description,
          year,
          directors: {
              id,
              full_name,
              image,
          }
          ORDER BY .last_name,

          cast: {
              id,
              full_name,
              image,
          }
          ORDER BY .last_name,
      }
  `,
};
module.exports = queries;
