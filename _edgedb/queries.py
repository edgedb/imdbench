#
# Copyright (c) 2019 MagicStack Inc.
# All rights reserved.
#
# See LICENSE for details.
##


GET_USER = """
    SELECT User {
        id,
        name,
        image,
        latest_reviews := (
            WITH UserReviews := .<author[IS Review]
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
"""


GET_MOVIE = """
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
        ORDER BY @list_order EMPTY LAST
            THEN .last_name,

        cast: {
            id,
            full_name,
            image,
        }
        ORDER BY @list_order EMPTY LAST
            THEN .last_name,
        
        reviews := (
            SELECT .<movie[IS Review] {
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
"""


GET_PERSON = """
    SELECT Person {
        id,
        full_name,
        image,
        bio,

        acted_in := (
            WITH M := .<cast[IS Movie]
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
            WITH M := .<directors[IS Movie]
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
"""


UPDATE_MOVIE = """
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
"""


INSERT_USER = """
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
"""


INSERT_MOVIE = """
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
                FILTER .id IN array_unpack(<array<uuid>>$cast)
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
"""


INSERT_MOVIE_PLUS = """
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
"""
