#
# Copyright (c) 2019 MagicStack Inc.
# All rights reserved.
#
# See LICENSE for details.
##

using extension graphql;
using extension edgeql_http;

module default {
    abstract type HasImage {
        # just a URL to the image
        required property image -> str;
        index on (.image);
    }


    type User extending HasImage {
        required property name -> str;
    }


    type Review {
        required property body -> str;
        required property rating -> int64 {
            constraint min_value(0);
            constraint max_value(5);
        }

        required link author -> User;
        required link movie -> Movie;

        required property creation_time -> cal::local_datetime {
            default := cal::to_local_datetime(datetime_current(), 'UTC')
        }
    }


    type Person extending HasImage {
        required property first_name -> str;
        required property middle_name -> str {
            default := '';
        }
        required property last_name -> str;
        property full_name :=
            (
                .first_name ++ ' ' ++
                (
                    (.middle_name ++ ' ')
                    IF .middle_name != '' ELSE
                    ''
                ) ++
                .last_name
            );
        property bio -> str;
    }


    abstract link crew {
        # Provide a way to specify some "natural" ordering, as relevant to
        # the movie. This may be order of importance, appearance, etc.
        property list_order -> int64;
    }


    abstract link directors extending crew;


    abstract link cast extending crew;


    type Movie extending HasImage {
        required property title -> str;
        required property year -> int64;
        required property description -> str;

        multi link directors extending crew -> Person;
        multi link cast extending crew -> Person;

        property avg_rating := math::mean(.<movie[IS Review].rating);
    }

    alias GraphQLUserDetails := (
        SELECT User {
            latest_reviews := (
                SELECT User.<author[IS Review]
                ORDER BY .creation_time DESC
            )
        }
    );


    alias GraphQLPersonDetails := (
        WITH MODULE default
        SELECT Person {
            acted_in := (
                SELECT Person.<cast[IS Movie]
            ),
            directed := (
                SELECT Person.<directors[IS Movie]
            ),
        }
    );


    alias GraphQLMovieDetails := (
        WITH MODULE default
        SELECT Movie {
            reviews := (
                SELECT Movie.<movie[IS Review]
            ),
        }
    );
}
