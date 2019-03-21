#
# Copyright (c) 2019 MagicStack Inc.
# All rights reserved.
#
# See LICENSE for details.
##


abstract type HasImage {
    # just a URL to the image
    required property image -> str;
    index image_idx on (__subject__.image);
}


type User extending HasImage {
    required property name -> str;
}


type Review {
    required property body -> str;
    required property rating -> int64 {
        constraint min(0);
        constraint max(5);
    }

    required link author -> User;
    required link movie -> Movie;

    required property creation_time -> datetime {
        default := datetime_current()
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
            __source__.first_name ++ ' ' ++
            (
                (__source__.middle_name ++ ' ')
                IF __source__.middle_name != '' ELSE
                ''
            ) ++
            __source__.last_name
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

    property avg_rating := math::mean(__source__.<movie[IS Review].rating);
}
