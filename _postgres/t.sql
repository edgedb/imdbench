explain (analyze, format json)    (SELECT/*<pg.SelectStmt at 0x10d843160>*/
            COALESCE(jsonb_agg("User_serialized~1"), '[]')
        FROM
            (SELECT/*<pg.SelectStmt at 0x10f4d2ba8>*/
                    to_jsonb(jsonb_build_object('id', "User~2".id, 'name', "User~2".name, 'image', "User~2".image, 'latest_reviews',
                (SELECT/*<pg.SelectStmt at 0x10e1e8ac8>*/
                            COALESCE(array_agg("aggw~1"."latest_reviews_serialized~1"), (ARRAY[])::jsonb[])
                        FROM
                            (SELECT/*<pg.SelectStmt at 0x10e1e8940>*/
                                    to_jsonb(jsonb_build_object('id', "default|User@@view~1_latest_reviews~2"."Review_value~2", 'body', "default|User@@view~1_latest_reviews~2"."body_value~3", 'rating', "default|User@@view~1_latest_reviews~2"."rating_value~3", 'movie',
                                (SELECT/*<pg.SelectStmt at 0x10dc595c0>*/
                                            to_jsonb(jsonb_build_object('id', "Movie~1".id, 'image', "Movie~1".image, 'title', "Movie~1".title, 'avg_rating',
                                        (SELECT/*<pg.SelectStmt at 0x10d988160>*/
                                                    to_jsonb("default|Movie@@view~3_avg_rating~2"."expr~17_value~2") AS "avg_rating_serialized~1"
                                                FROM
                                                    LATERAL
                                                (SELECT/*<pg.SelectStmt at 0x10d988080>*/
                                                            "expr-17~2"."expr~17_value~1" AS "expr~17_value~2"
                                                        FROM
                                                            LATERAL
                                                        (SELECT/*<pg.SelectStmt at 0x10d9888d0>*/
                                                                    "q~4"."expr~11_value~4" AS "expr~11_value~5"
                                                                FROM
                                                                    LATERAL
                                                                (SELECT/*<pg.SelectStmt at 0x10d988a20>*/
                                                                            ("m~1" = first_value("m~1") OVER ()) AS "m~1",
                                                                            "q~3"."expr~11_value~2" AS "expr~11_value~4"
                                                                        FROM
                                                                            LATERAL
                                                                        (
                                                                            (SELECT/*<pg.SelectStmt at 0x10d988dd8>*/
                                                                                    1 AS "m~1",
                                                                                    "q~2"."expr~11_value~1" AS "expr~11_value~2"
                                                                                FROM
                                                                                    LATERAL
                                                                                (SELECT/*<pg.SelectStmt at 0x10d988f28>*/
                                                                                            (avg("expr-10~2"."expr~9_value~1"))::float8 AS "expr~11_value~1"
                                                                                        FROM
                                                                                            LATERAL
                                                                                        (SELECT/*<pg.SelectStmt at 0x10d99fa20>*/
                                                                                                    "expr-9~2"."rating_value~6" AS "expr~9_value~1"
                                                                                                FROM
                                                                                                    LATERAL
                                                                                                (SELECT/*<pg.SelectStmt at 0x10d99fd68>*/
                                                                                                            "Review_rating~2"."rating_value~5" AS "rating_value~6"
                                                                                                        FROM
                                                                                                            LATERAL
                                                                                                        (SELECT/*<pg.SelectStmt at 0x10d99ff60>*/
                                                                                                                    "q~1"."rating_value~4" AS "rating_value~5"
                                                                                                                FROM
                                                                                                                    LATERAL
                                                                                                                (SELECT/*<pg.SelectStmt at 0x10d92b048>*/
                                                                                                                            "Review~6".rating AS "rating_value~4"
                                                                                                                        FROM
                                                                                                                            "edgedb_1b30653a-45fb-11e9-b3d1-3ff49de03a62"."43fc1398-45fc-11e9-a673-cb6c92599486" AS "movie~2"
                                                                                                                            INNER JOIN "edgedb_1b30653a-45fb-11e9-b3d1-3ff49de03a62"."43f74cb4-45fc-11e9-b7d6-879437569c65" AS "Review~6"
                                                                                                                                ON ("movie~2".source = "Review~6".id)
                                                                                                                        WHERE
                                                                                                                            (("Movie~1".id = "movie~2".target) AND
                                                                                                                              ("Review~6".rating IS NOT NULL))
                                                                                                                    ) AS "q~1"
                                                                                                            ) AS "Review_rating~2"
                                                                                                    ) AS "expr-9~2"
                                                                                            ) AS "expr-10~2"
                                                                                    ) AS "q~2"
                                                                                WHERE
                                                                                    ("q~2"."expr~11_value~1" IS NOT NULL)
                                                                            ) UNION ALL
                                                                        (SELECT/*<pg.SelectStmt at 0x10d988fd0>*/
                                                                                    2 AS "m~1",
                                                                                    "v~1"."v~2" AS "expr~11_value~3"
                                                                                FROM
                                                                                    (SELECT (NULL)::float8 AS "v~2") AS "v~1"
                                                                            )
                                                                            ) AS "q~3"
                                                                    ) AS "q~4"
                                                                WHERE
                                                                    "q~4"."m~1"
                                                            ) AS "expr-11~2"
                                                            CROSS JOIN LATERAL
                                                        (SELECT/*<pg.SelectStmt at 0x10d988630>*/
                                                                    COALESCE("expr-11~2"."expr~11_value~5", "expr-16~2"."expr~16_value~4") AS "expr~17_value~1"
                                                                FROM
                                                                    LATERAL
                                                                (SELECT/*<pg.SelectStmt at 0x10d92b7f0>*/
                                                                            "q~7"."expr~16_value~3" AS "expr~16_value~4"
                                                                        FROM
                                                                            LATERAL
                                                                        (SELECT/*<pg.SelectStmt at 0x10d92b9b0>*/
                                                                                    ("m~2" = first_value("m~2") OVER ()) AS "m~2",
                                                                                    "q~6"."expr~16_value~1" AS "expr~16_value~3"
                                                                                FROM
                                                                                    LATERAL
                                                                                (
                                                                                    (SELECT/*<pg.SelectStmt at 0x10d92b898>*/
                                                                                            1 AS "m~2",
                                                                                            "q~5"."expr~15_value~2" AS "expr~16_value~1"
                                                                                        FROM
                                                                                            LATERAL
                                                                                        (SELECT/*<pg.SelectStmt at 0x10d92bc50>*/
                                                                                                    "expr-15~2"."expr~15_value~1" AS "expr~15_value~2"
                                                                                                FROM
                                                                                                    LATERAL
                                                                                                (SELECT/*<pg.SelectStmt at 0x10d6ccd30>*/
                                                                                                            ("expr-14~2"."expr~13_value~1")::float8 AS "expr~15_value~1"
                                                                                                        FROM
                                                                                                            LATERAL
                                                                                                        (SELECT/*<pg.SelectStmt at 0x10d92b3c8>*/
                                                                                                                    (0)::bigint AS "expr~13_value~1"
                                                                                                            ) AS "expr-14~2"
                                                                                                    ) AS "expr-15~2"
                                                                                            ) AS "q~5"
                                                                                    ) UNION ALL
                                                                                (SELECT/*<pg.SelectStmt at 0x10d92b4a8>*/
                                                                                            2 AS "m~2",
                                                                                            "v~3"."v~4" AS "expr~16_value~2"
                                                                                        FROM
                                                                                            (SELECT (NULL)::float8 AS "v~4") AS "v~3"
                                                                                    )
                                                                                    ) AS "q~6"
                                                                            ) AS "q~7"
                                                                        WHERE
                                                                            "q~7"."m~2"
                                                                    ) AS "expr-16~2"
                                                            ) AS "expr-17~2"
                                                    ) AS "default|Movie@@view~3_avg_rating~2"
                                            ))) AS "movie_serialized~1"
                                        FROM
                                            "edgedb_1b30653a-45fb-11e9-b3d1-3ff49de03a62"."43fc1398-45fc-11e9-a673-cb6c92599486" AS "movie~1"
                                            INNER JOIN "edgedb_1b30653a-45fb-11e9-b3d1-3ff49de03a62"."43f75542-45fc-11e9-9b96-5149e7450322" AS "Movie~1"
                                                ON ("movie~1".target = "Movie~1".id)
                                        WHERE
                                            ("default|User@@view~1_latest_reviews~2"."Review_identity~2" = "movie~1".source)
                                    ))) AS "latest_reviews_serialized~1"
                                FROM
                                    LATERAL
                                (SELECT/*<pg.SelectStmt at 0x10e1e8358>*/
                                            "Review~5"."Review_value~1" AS "Review_value~2",
                                            "Review~5"."body_value~2" AS "body_value~3",
                                            "Review~5"."rating_value~2" AS "rating_value~3",
                                            "Review~5"."Review_identity~1" AS "Review_identity~2"
                                        FROM
                                            LATERAL
                                        (SELECT/*<pg.SelectStmt at 0x10e1e8278>*/
                                                    "Review~4"."author_value~1" AS "Review_value~1",
                                                    "Review~4"."body_value~1" AS "body_value~2",
                                                    "Review~4"."rating_value~1" AS "rating_value~2",
                                                    "Review~4"."author_identity~1" AS "Review_identity~1"
                                                FROM
                                                    LATERAL
                                                (SELECT/*<pg.SelectStmt at 0x10ce040b8>*/
                                                            "Review~3".id AS "author_value~1",
                                                            "Review~3".creation_time AS "creation_time_value~1",
                                                            "Review~3".body AS "body_value~1",
                                                            "Review~3".rating AS "rating_value~1",
                                                            "author~1".source AS "author_identity~1"
                                                        FROM
                                                            "edgedb_1b30653a-45fb-11e9-b3d1-3ff49de03a62"."43fbccb4-45fc-11e9-bbc3-b3088f83e621" AS "author~1"
                                                            INNER JOIN "edgedb_1b30653a-45fb-11e9-b3d1-3ff49de03a62"."43f74cb4-45fc-11e9-b7d6-879437569c65" AS "Review~3"
                                                                ON ("author~1".source = "Review~3".id)
                                                        WHERE
                                                            ("User~2".id = "author~1".target)
                                                    ) AS "Review~4"
                                                ORDER BY
                                                    (SELECT/*<pg.SelectStmt at 0x10e176e48>*/
                                                            "expr-5~2"."creation_time_value~2"
                                                        FROM
                                                            LATERAL
                                                        (SELECT/*<pg.SelectStmt at 0x10ce04358>*/
                                                                    "Review~4"."creation_time_value~1" AS "creation_time_value~2"
                                                            ) AS "expr-5~2"
                                                    ) DESC NULLS LAST
                                            ) AS "Review~5"
                                        LIMIT
                                    (SELECT/*<pg.SelectStmt at 0x10e1e81d0>*/
                                                (10)::bigint AS "expr~7_value~1"
                                        )
                                    ) AS "default|User@@view~1_latest_reviews~2"
                            ) AS "aggw~1"
                    ))) AS "User_serialized~1"
                FROM
                    "edgedb_1b30653a-45fb-11e9-b3d1-3ff49de03a62"."43f74a48-45fc-11e9-90a7-ad15c2ea6e03" AS "User~2"
                    CROSS JOIN LATERAL
                (SELECT/*<pg.SelectStmt at 0x10d9881d0>*/
                            ("User~2".id = "expr-21~2"."expr~21_value~1") AS "expr~23_value~1"
                        FROM
                            LATERAL
                        (SELECT/*<pg.SelectStmt at 0x10d843c50>*/
                                    (('5af527ec-45fc-11e9-ac40-bbd8f6abec2a')::text)::uuid AS "expr~21_value~1"
                            ) AS "expr-21~2"
                    ) AS "expr-23~2"
                WHERE
                    "expr-23~2"."expr~23_value~1"
            ) AS "aggw~2"
    );
